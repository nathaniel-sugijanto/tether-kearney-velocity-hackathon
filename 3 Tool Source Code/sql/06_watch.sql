-- =====================================================================================
-- Step 6. Watchlist: what needs attention now.
-- =====================================================================================

-- Open orders with the part they are really for.
DROP TABLE IF EXISTS open_order;
CREATE TABLE open_order AS
SELECT o.site, o.po_number, o.po_line, o.po_date, o.supplier_id, sx.supplier_key,
       o.item_raw, o.line_text, o.open_qty, o.uom, o.promised, o.confirmed,
       COALESCE(ic.current_item,
                (SELECT q.item FROM quotes q WHERE q.site = o.site AND q.quote_no = quote_no_in(o.line_text) LIMIT 1),
                CASE WHEN tm.score >= 0.72 THEN tm.item END)                         AS item,
       CASE WHEN ic.how IN ('SUPERSESSION', 'RENUMBER_SUGGESTED') THEN 1 ELSE 0 END  AS on_old_number,
       ic.note                                                                        AS old_number_note,
       CAST(JULIANDAY(o.confirmed) - JULIANDAY(o.promised) AS INTEGER)                AS days_slip
FROM open_pos o
LEFT JOIN supplier_x sx   ON sx.site = o.site AND sx.supplier_id = o.supplier_id
LEFT JOIN item_current ic ON ic.site = o.site AND ic.item = o.item_raw
LEFT JOIN text_match tm   ON tm.site = o.site AND tm.supplier_id = o.supplier_id
                         AND tm.line_text = o.line_text AND o.item_raw IS NULL;

DROP TABLE IF EXISTS open_order_x;
CREATE TABLE open_order_x AS
SELECT o.*, g.group_id, g.group_name,
       (SELECT GROUP_CONCAT(DISTINCT f.model) FROM bom_flat f WHERE f.site = o.site AND f.group_id = g.group_id) AS models,
       (SELECT GROUP_CONCAT(DISTINCT n.notice_id) FROM notice n JOIN notice_part np ON np.notice_id = n.notice_id
         WHERE n.is_open = 1 AND np.group_id = g.group_id AND n.supplier_key = o.supplier_key)                    AS open_notices
FROM open_order o LEFT JOIN part_group g ON g.site = o.site AND g.item = o.item;

-- Each notice: which plants buy or use the affected parts, how much they spent with this
-- supplier on them, and whether that plant is the one that received the notice.
DROP TABLE IF EXISTS notice_exposure;
CREATE TABLE notice_exposure AS
WITH sites AS (SELECT DISTINCT site FROM parts)
SELECT n.notice_id, s.site,
       CASE WHEN s.site = n.site_received THEN 1 ELSE 0 END AS was_told,
       (SELECT COALESCE(SUM(pp.spend), 0) FROM price_point pp JOIN notice_part np ON np.group_id = pp.group_id
         WHERE np.notice_id = n.notice_id AND pp.site = s.site AND pp.supplier_key = n.supplier_key) AS spend_with_supplier,
       (SELECT COALESCE(SUM(pp.spend), 0) FROM price_point pp JOIN notice_part np ON np.group_id = pp.group_id
         WHERE np.notice_id = n.notice_id AND pp.site = s.site)                                      AS spend_on_parts,
       (SELECT GROUP_CONCAT(DISTINCT f.model) FROM bom_flat f JOIN notice_part np ON np.group_id = f.group_id
         WHERE np.notice_id = n.notice_id AND f.site = s.site)                                       AS models,
       (SELECT COUNT(*) FROM open_order_x o JOIN notice_part np ON np.group_id = o.group_id
         WHERE np.notice_id = n.notice_id AND o.site = s.site AND o.supplier_key = n.supplier_key)    AS open_orders
FROM notice n CROSS JOIN sites s;

-- Money already spent on expediting (air freight).
DROP TABLE IF EXISTS expedite_spend;
CREATE TABLE expedite_spend AS
SELECT site, invoice_no, inv_date, line_text, amount FROM spend_fact
WHERE bucket = 'NON_PRODUCT' AND UPPER(line_text) LIKE '%AIR FREIGHT%';

-- Cautions on opportunities: the best-priced supplier is late, or has an open notice.
UPDATE opportunity SET caution = TRIM(
  COALESCE((SELECT 'Delivery record: ' || CAST(ROUND(100 * SUM(d.on_time * d.receipts) / SUM(d.receipts)) AS INT) || '% of receipts on time. '
              FROM supplier_delivery d WHERE d.supplier_key = opportunity.best_supplier
            HAVING SUM(d.receipts) >= 20 AND SUM(d.on_time * d.receipts) / SUM(d.receipts) < 0.6), '') ||
  COALESCE((SELECT 'Open supplier notice ' || n.notice_id || ' (' || LOWER(REPLACE(n.notice_type, '_', ' ')) || '): ' || n.notice_text || ' '
              FROM notice n JOIN notice_part np ON np.notice_id = n.notice_id
             WHERE n.is_open = 1 AND n.supplier_key = opportunity.best_supplier AND np.group_id = opportunity.group_id
               AND n.notice_type IN ('LEAD_TIME_CHANGE', 'DISCONTINUATION') LIMIT 1), '')
) WHERE opp_type IN ('PRICE_ALIGNMENT', 'CLOSE_SPEC');
UPDATE opportunity SET caution = NULL WHERE caution = '';
