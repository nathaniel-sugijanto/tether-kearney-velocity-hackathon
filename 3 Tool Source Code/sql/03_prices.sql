-- =====================================================================================
-- Step 4a. One price basis for everything: dollars per base unit of the part.
--
-- Dayton buys screws by the box of 1,000; El Paso prices them per 1,000 each.
-- Dayton buys tube in 50 m rolls; El Paso buys it by the foot. Prices are only
-- comparable after converting every line to the part's base unit (each, or metre).
-- A line whose unit cannot be converted is kept, flagged, and left out of price comparisons.
-- =====================================================================================

-- Suppliers: one key per real supplier, whatever each plant calls it locally.
DROP TABLE IF EXISTS supplier_x;
CREATE TABLE supplier_x AS
SELECT s.site, s.supplier_id,
       norm_supplier(s.name)                                   AS supplier_key,
       s.name, s.supplier_type, s.state, s.iso9001,
       UPPER(COALESCE(s.certs, ''))                            AS certs,
       s.capabilities, s.status
FROM suppliers s;

-- One display name per supplier (the longest spelling reads best).
DROP TABLE IF EXISTS supplier_name;
CREATE TABLE supplier_name AS
SELECT supplier_key,
       (SELECT title_case(s2.name) FROM supplier_x s2 WHERE s2.supplier_key = s.supplier_key
         ORDER BY LENGTH(s2.name) DESC LIMIT 1)               AS supplier_name,
       MAX(iso9001)                                            AS iso9001,
       MAX(certs)                                              AS certs,
       MAX(supplier_type)                                      AS supplier_type,
       COUNT(DISTINCT site)                                    AS sites
FROM supplier_x s GROUP BY supplier_key;

-- Every invoice line with its quantity in base units and its price per base unit.
DROP TABLE IF EXISTS spend_fact;
CREATE TABLE spend_fact AS
WITH f AS (
  SELECT i.*, sx.supplier_key,
         p.base_uom,
         CASE
           WHEN i.item IS NULL                                  THEN NULL
           WHEN i.uom = p.base_uom                              THEN 1.0
           ELSE COALESCE(
             (SELECT c.factor FROM uom_conv c WHERE c.site = i.site AND c.item = COALESCE(i.item_raw, i.item)
                                               AND c.alt_uom = i.uom AND c.base_uom = p.base_uom),
             (SELECT c.factor FROM uom_conv c WHERE c.site = i.site AND c.item = i.item
                                               AND c.alt_uom = i.uom AND c.base_uom = p.base_uom),
             (SELECT c.factor FROM uom_conv c WHERE c.site = i.site AND c.item IS NULL
                                               AND c.alt_uom = i.uom AND c.base_uom = p.base_uom),
             -- a duplicate part number borrows the conversion of its twin in the same group
             (SELECT c.factor FROM uom_conv c
                JOIN part_group g1 ON g1.site = c.site AND g1.item = c.item
                JOIN part_group g2 ON g2.group_id = g1.group_id AND g2.site = i.site AND g2.item = i.item
               WHERE c.site = i.site AND c.alt_uom = i.uom AND c.base_uom = p.base_uom))
         END AS to_base
  FROM invoice_link i
  LEFT JOIN supplier_x sx ON sx.site = i.site AND sx.supplier_id = i.supplier_id
  LEFT JOIN parts p       ON p.site = i.site AND p.item = i.item
)
SELECT f.site, f.invoice_no, f.inv_line, f.inv_date, f.supplier_id, f.supplier_key,
       f.po_number, f.po_line, f.item_raw, f.item, g.group_id, f.line_text,
       f.qty, f.uom, f.price, f.per, f.amount, f.line_type,
       f.method, f.confidence, f.reason, f.bucket, f.po_ref_missing,
       f.base_uom,
       f.qty * f.to_base                                         AS base_qty,
       CASE WHEN f.qty * f.to_base <> 0 THEN f.amount / (f.qty * f.to_base) END AS base_price,
       CASE WHEN f.item IS NOT NULL AND f.to_base IS NULL THEN 1 ELSE 0 END    AS uom_missing,
       -- When several old parts were replaced by one new part (a two-piece lid by a one-piece lid),
       -- the old parts' prices say nothing about the new part's price: keep the spend, skip the price.
       CASE WHEN f.item_raw IS NOT NULL AND f.item_raw <> f.item
             AND (SELECT COUNT(*) FROM item_current ic WHERE ic.site = f.site AND ic.current_item = f.item
                                                         AND ic.how = 'SUPERSESSION') > 1
            THEN 0 ELSE 1 END                                                  AS price_comparable
FROM f
LEFT JOIN part_group g ON g.site = f.site AND g.item = f.item;

CREATE INDEX spend_fact_group ON spend_fact (group_id);

-- Price paid for each part, by plant and supplier, over the period.
DROP TABLE IF EXISTS price_point;
CREATE TABLE price_point AS
SELECT group_id, site, supplier_key,
       SUM(base_qty)                         AS qty,
       SUM(amount)                           AS spend,
       SUM(amount) / SUM(base_qty)           AS price,
       COUNT(*)                              AS lines,
       MIN(inv_date) AS first_date, MAX(inv_date) AS last_date,
       GROUP_CONCAT(DISTINCT item)           AS items
FROM spend_fact
WHERE item IS NOT NULL AND uom_missing = 0 AND base_qty > 0 AND price_comparable = 1
GROUP BY group_id, site, supplier_key;

-- What each part must have from its supplier, read from the part's compliance field.
DROP TABLE IF EXISTS group_requirement;
CREATE TABLE group_requirement AS
SELECT g.group_id,
       MAX(CASE WHEN UPPER(p.compliance) LIKE '%NSF%' THEN 1 ELSE 0 END) AS needs_nsf,
       MAX(CASE WHEN UPPER(p.compliance) LIKE '%FDA%' THEN 1 ELSE 0 END) AS needs_fda,
       MAX(CASE WHEN UPPER(p.compliance) LIKE '%UL %' OR UPPER(p.compliance) LIKE 'UL%' THEN 1 ELSE 0 END) AS needs_ul
FROM part_group g JOIN parts p ON p.site = g.site AND p.item = g.item
GROUP BY g.group_id;

-- Is this supplier qualified for this part?
--   ISO 9001 is required of everyone.
--   The certificate the part calls for (food contact, UL) is required of manufacturers
--   and importers. A distributor resells the maker's certified part, so it is exempt.
DROP TABLE IF EXISTS supplier_part_check;
CREATE TABLE supplier_part_check AS
SELECT pp.group_id, pp.supplier_key,
       CASE WHEN sn.iso9001 <> 'Y' THEN 0
            WHEN sn.supplier_type = 'Distributor' THEN 1
            WHEN r.needs_nsf = 1 AND sn.certs NOT LIKE '%NSF%' THEN 0
            WHEN r.needs_fda = 1 AND sn.certs NOT LIKE '%FDA%' THEN 0
            WHEN r.needs_ul  = 1 AND sn.certs NOT LIKE '%UL%'  THEN 0
            ELSE 1 END AS qualified,
       TRIM(
         CASE WHEN sn.iso9001 <> 'Y' THEN 'No ISO 9001. ' ELSE '' END ||
         CASE WHEN sn.supplier_type <> 'Distributor' AND r.needs_nsf = 1 AND sn.certs NOT LIKE '%NSF%' THEN 'No food-contact (NSF/ANSI 51) certificate. ' ELSE '' END ||
         CASE WHEN sn.supplier_type <> 'Distributor' AND r.needs_fda = 1 AND sn.certs NOT LIKE '%FDA%' THEN 'No FDA food-contact certificate. ' ELSE '' END ||
         CASE WHEN sn.supplier_type <> 'Distributor' AND r.needs_ul  = 1 AND sn.certs NOT LIKE '%UL%'  THEN 'No UL file. ' ELSE '' END
       ) AS fail_reason
FROM (SELECT DISTINCT group_id, supplier_key FROM price_point) pp
JOIN supplier_name sn ON sn.supplier_key = pp.supplier_key
LEFT JOIN group_requirement r ON r.group_id = pp.group_id;
