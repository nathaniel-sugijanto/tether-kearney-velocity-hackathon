-- =====================================================================================
-- Step 5. Size the savings. Every opportunity is one row with its evidence.
--
--   PRICE_ALIGNMENT   the same part is bought at different prices (by plant or supplier):
--                     saving = (price paid - best qualified price) x quantity         READY
--   CLOSE_SPEC        a near-identical part could move to the family's standard part:
--                     saving = (its best price - standard's best price) x quantity    REVIEW
--   QUOTE_LEAKAGE     invoiced above the quote that was awarded:
--                     saving = (invoiced price - quoted price) x quantity             READY
--
-- "Best qualified price" is never simply the cheapest: the supplier must pass the
-- qualification check for that part and must carry real volume (not a one-off buy).
-- Each dollar is counted once: the CLOSE_SPEC saving starts from the part's own best price.
-- =====================================================================================

-- Supplier delivery record, from receipts (promised against actual).
DROP TABLE IF EXISTS supplier_delivery;
CREATE TABLE supplier_delivery AS
SELECT sx.supplier_key, r.site,
       COUNT(*) AS receipts,
       AVG(CASE WHEN r.rec_date <= r.promised THEN 1.0 ELSE 0.0 END) AS on_time,
       AVG(MAX(0, JULIANDAY(r.rec_date) - JULIANDAY(r.promised)))    AS avg_days_late,
       AVG(JULIANDAY(r.rec_date) - JULIANDAY(p.po_date))             AS actual_lead_days
FROM receipts r
JOIN po_lines p    ON p.site = r.site AND p.po_number = r.po_number AND p.po_line = r.po_line
JOIN supplier_x sx ON sx.site = p.site AND sx.supplier_id = p.supplier_id
GROUP BY sx.supplier_key, r.site;

-- Best qualified price for each part.
DROP TABLE IF EXISTS best_price;
CREATE TABLE best_price AS
WITH tot AS (SELECT group_id, SUM(qty) AS qty FROM price_point GROUP BY group_id),
ranked AS (
  SELECT pp.*, ROW_NUMBER() OVER (PARTITION BY pp.group_id ORDER BY pp.price) AS rk
  FROM price_point pp
  JOIN supplier_part_check c ON c.group_id = pp.group_id AND c.supplier_key = pp.supplier_key
  JOIN tot t ON t.group_id = pp.group_id
  WHERE c.qualified = 1 AND pp.qty >= 0.05 * t.qty          -- real volume only
)
SELECT group_id, site AS best_site, supplier_key AS best_supplier, price AS best_price
FROM ranked WHERE rk = 1;

DROP TABLE IF EXISTS opportunity;
CREATE TABLE opportunity (
  opp_id TEXT, opp_type TEXT, readiness TEXT, title TEXT, group_id TEXT, family_id TEXT,
  saving REAL, spend REAL, best_supplier TEXT, best_site TEXT, best_price REAL,
  detail TEXT, caution TEXT);

-- 1. Same part, different prices.
INSERT INTO opportunity
SELECT 'PA-' || pp.group_id, 'PRICE_ALIGNMENT', 'READY',
       NULL, pp.group_id, NULL,
       SUM(CASE WHEN pp.price > b.best_price THEN (pp.price - b.best_price) * pp.qty ELSE 0 END),
       SUM(pp.spend), b.best_supplier, b.best_site, b.best_price,
       COUNT(*) || ' price points across ' || COUNT(DISTINCT pp.supplier_key) || ' suppliers and '
         || COUNT(DISTINCT pp.site) || ' plants', NULL
FROM price_point pp JOIN best_price b ON b.group_id = pp.group_id
GROUP BY pp.group_id
HAVING COUNT(*) > 1;

-- 2. Near-identical parts: move to the family's standard part (the one with the lowest best price).
DROP TABLE IF EXISTS family_standard;
CREATE TABLE family_standard AS
SELECT family_id, group_id AS standard_group, best_price AS standard_price FROM (
  SELECT f.family_id, f.group_id, b.best_price,
         ROW_NUMBER() OVER (PARTITION BY f.family_id ORDER BY b.best_price) AS rk
  FROM part_family f JOIN best_price b ON b.group_id = f.group_id
  -- only groups that are close-spec to something can be a standard
  WHERE EXISTS (SELECT 1 FROM group_pair gp WHERE gp.relation = 'CLOSE_SPEC'
                 AND (gp.group_a = f.group_id OR gp.group_b = f.group_id))
) WHERE rk = 1;

INSERT INTO opportunity
SELECT 'CS-' || f.group_id, 'CLOSE_SPEC', 'REVIEW', NULL, f.group_id, f.family_id,
       (SELECT SUM(MAX(0, MIN(pp.price, b.best_price) - fs.standard_price) * pp.qty)
          FROM price_point pp WHERE pp.group_id = f.group_id),
       (SELECT SUM(spend) FROM price_point pp WHERE pp.group_id = f.group_id),
       sb.best_supplier, sb.best_site, fs.standard_price,
       gp.differences, NULL
FROM part_family f
JOIN family_standard fs ON fs.family_id = f.family_id AND fs.standard_group <> f.group_id
JOIN best_price b  ON b.group_id = f.group_id
JOIN best_price sb ON sb.group_id = fs.standard_group
JOIN group_pair gp ON gp.relation = 'CLOSE_SPEC'
                  AND ((gp.group_a = f.group_id AND gp.group_b = fs.standard_group)
                    OR (gp.group_b = f.group_id AND gp.group_a = fs.standard_group))
WHERE b.best_price > fs.standard_price;

-- 3. Invoiced above the awarded quote.
DROP TABLE IF EXISTS quote_leak_line;
CREATE TABLE quote_leak_line AS
SELECT s.site, s.invoice_no, s.inv_line, s.inv_date, s.item, s.group_id, s.supplier_key,
       s.base_qty, s.base_price, q.price AS quoted_price, q.quote_no, q.quote_date,
       (s.base_price - q.price) * s.base_qty AS leak
FROM spend_fact s
JOIN quotes q ON q.site = s.site AND q.item = s.item AND q.supplier_id = s.supplier_id
             AND q.awarded = 'Y' AND q.quote_date <= s.inv_date
WHERE s.base_qty > 0 AND s.base_price > q.price * 1.01;

INSERT INTO opportunity
SELECT 'QL-' || site || '-' || item, 'QUOTE_LEAKAGE', 'READY', NULL, group_id, NULL,
       SUM(leak), SUM(base_qty * base_price), supplier_key, site, MIN(quoted_price),
       COUNT(*) || ' invoice lines from ' || MIN(inv_date) || ' priced '
         || CAST(ROUND(100.0 * (SUM(base_qty * base_price) / SUM(base_qty * quoted_price) - 1), 1) AS TEXT)
         || '% above quote ' || MIN(quote_no), NULL
FROM quote_leak_line
GROUP BY site, item, supplier_key
HAVING COUNT(*) >= 3;          -- a pattern, not a one-off

-- When one supplier raises most of its parts by the same percentage from the same time, that is
-- an across-the-board increase (a surcharge), not part-by-part leakage. It is still money paid
-- above the awarded quotes, so it is shown, but for a commercial check rather than as ready savings.
DROP TABLE IF EXISTS supplier_increase;
CREATE TABLE supplier_increase AS
WITH per_part AS (
  SELECT site, supplier_key, item,
         SUM(base_qty * base_price) / SUM(base_qty * quoted_price) - 1 AS pct
  FROM quote_leak_line GROUP BY site, supplier_key, item HAVING COUNT(*) >= 3
)
SELECT site, supplier_key, COUNT(*) AS parts, AVG(pct) AS typical_pct
FROM per_part p
WHERE ABS(pct - (SELECT AVG(p2.pct) FROM per_part p2 WHERE p2.site = p.site AND p2.supplier_key = p.supplier_key
                                                      AND p2.pct < 0.06)) < 0.01
GROUP BY site, supplier_key HAVING COUNT(*) >= 3;

UPDATE opportunity
SET opp_type = 'SUPPLIER_INCREASE', readiness = 'REVIEW',
    detail = detail || '. The supplier raised ' ||
             (SELECT si.parts FROM supplier_increase si WHERE si.site = opportunity.best_site AND si.supplier_key = opportunity.best_supplier)
             || ' parts by about the same percentage: an across-the-board increase to check against the contract'
WHERE opp_type = 'QUOTE_LEAKAGE'
  AND EXISTS (SELECT 1 FROM supplier_increase si
               WHERE si.site = opportunity.best_site AND si.supplier_key = opportunity.best_supplier
                 AND ABS(opportunity.saving / (opportunity.spend - opportunity.saving) - si.typical_pct) < 0.01);

DELETE FROM opportunity WHERE saving IS NULL OR saving < 250;   -- too small to be worth a card

-- Spend with suppliers that fail the qualification check for the part they supply.
DROP TABLE IF EXISTS unqualified_spend;
CREATE TABLE unqualified_spend AS
SELECT pp.supplier_key, pp.site, pp.group_id, pp.spend, pp.qty, pp.price, c.fail_reason
FROM price_point pp JOIN supplier_part_check c
  ON c.group_id = pp.group_id AND c.supplier_key = pp.supplier_key
WHERE c.qualified = 0;
