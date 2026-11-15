-- =====================================================================================
-- Step 2. Tie every PO line and invoice line to a part, and say how.
--
-- The tool tries the most reliable evidence first and stops at the first that works:
--   1 EXACT           the line carries a part number that exists in the part master
--   2 SUPERSESSION    the part number was replaced; follow it to the current number
--   3 SERVICE_XREF    a service SKU; follow the service catalogue to the production part
--   4 VENDOR_PART     no part number, but the supplier's own part number is on file
--   5 QUOTE_REF       no part number, but the line names a quote that names the part
--   6 NON_PRODUCT     freight, testing, tooling, supplies: real spend, not a BOM part
--   7 DESCRIPTION     free text close enough to one part's description
--   8 UNRESOLVED      nothing above worked; the line stays visible with its value
--
-- Helper tables built just before this script runs (engine/link.py):
--   item_current(site, item, current_item, how, note)  old/service numbers -> current part
--   text_match(site, supplier_id, line_text, item, score, runner_up)  best description match
-- =====================================================================================

DROP TABLE IF EXISTS non_product_words;
CREATE TABLE non_product_words (word TEXT);
INSERT INTO non_product_words VALUES ('FREIGHT'),('PALLETS'),('STRETCH WRAP'),('SHOP SUPPLIES'),
  ('MOLD REPAIR'),('SAFETY TESTING'),('CALIBRATION'),('TOOLING');

DROP TABLE IF EXISTS po_link;
CREATE TABLE po_link AS
WITH base AS (
  SELECT p.*,
         pr.purpose                                         AS cc_purpose,
         (SELECT 1 FROM purpose_rules s WHERE s.site = p.site AND s.kind = 'ship_to'
                                          AND s.code = p.ship_to)           AS service_ship_to,
         (SELECT 1 FROM non_product_words w WHERE UPPER(p.line_text) LIKE '%' || w.word || '%')
                                                            AS non_product_word,
         ic.current_item, ic.how AS ic_how, ic.note AS ic_note,
         (SELECT x.item FROM item_supplier x
           WHERE x.site = p.site AND x.supplier_item = p.supplier_item
             AND p.supplier_item IS NOT NULL LIMIT 1)                        AS vendor_part_item,
         (SELECT q.item FROM quotes q
           WHERE q.site = p.site
             AND q.quote_no = COALESCE(p.quote_ref, quote_no_in(p.line_text)) LIMIT 1) AS quote_item,
         tm.item AS text_item, tm.score AS text_score, tm.runner_up AS text_runner_up
  FROM po_lines p
  LEFT JOIN purpose_rules pr ON pr.site = p.site AND pr.kind = 'cost_center' AND pr.code = p.cost_center
  LEFT JOIN item_current ic  ON ic.site = p.site AND ic.item = p.item_raw
  LEFT JOIN text_match tm    ON tm.site = p.site AND tm.supplier_id = p.supplier_id
                            AND tm.line_text = p.line_text AND p.item_raw IS NULL
)
SELECT site, po_number, po_line, po_date, supplier_id, item_raw, supplier_item, line_text,
       qty, uom, price, per, amount, cost_center, ship_to,
       -- ---------------------------------------------------------------- which part
       CASE
         WHEN current_item IS NOT NULL                               THEN current_item
         WHEN vendor_part_item IS NOT NULL                           THEN vendor_part_item
         WHEN quote_item IS NOT NULL                                 THEN quote_item
         WHEN cc_purpose = 'NON_PRODUCT' OR non_product_word = 1     THEN NULL
         WHEN text_score >= 0.72                                     THEN text_item
       END AS item,
       -- ---------------------------------------------------------------- how we know
       CASE
         WHEN current_item IS NOT NULL                               THEN ic_how
         WHEN vendor_part_item IS NOT NULL                           THEN 'VENDOR_PART'
         WHEN quote_item IS NOT NULL                                 THEN 'QUOTE_REF'
         WHEN cc_purpose = 'NON_PRODUCT' OR non_product_word = 1     THEN 'NON_PRODUCT'
         WHEN text_score >= 0.72                                     THEN 'DESCRIPTION'
         ELSE 'UNRESOLVED'
       END AS method,
       -- ---------------------------------------------------------------- how sure
       CASE
         WHEN current_item IS NOT NULL AND ic_how = 'EXACT'          THEN 1.00
         WHEN current_item IS NOT NULL AND ic_how = 'SUPERSESSION'   THEN 0.97
         WHEN current_item IS NOT NULL AND ic_how = 'SERVICE_XREF'   THEN 0.95
         WHEN current_item IS NOT NULL                               THEN 0.80  -- suggested links
         WHEN vendor_part_item IS NOT NULL                           THEN 0.95
         WHEN quote_item IS NOT NULL                                 THEN 0.93
         WHEN cc_purpose = 'NON_PRODUCT' OR non_product_word = 1     THEN 0.95
         WHEN text_score >= 0.72                                     THEN ROUND(0.55 + 0.35 * text_score, 2)
         ELSE 0.0
       END AS confidence,
       CASE
         WHEN current_item IS NOT NULL AND ic_how = 'EXACT'          THEN 'Part number ' || item_raw || ' is in the part master'
         WHEN current_item IS NOT NULL                               THEN ic_note
         WHEN vendor_part_item IS NOT NULL                           THEN 'Supplier part number ' || supplier_item || ' is on file for ' || vendor_part_item
         WHEN quote_item IS NOT NULL                                 THEN 'Quote ' || COALESCE(quote_ref, quote_no_in(line_text)) || ' is for ' || quote_item
         WHEN cc_purpose = 'NON_PRODUCT'                             THEN 'Booked to a non-product account (' || cost_center || ')'
         WHEN non_product_word = 1                                   THEN 'Line text names freight, tooling, testing or supplies'
         WHEN text_score >= 0.72                                     THEN 'Description matches ' || text_item || ' (' || CAST(ROUND(text_score * 100) AS INT) || '% of words)'
         WHEN text_item IS NOT NULL                                  THEN 'Closest description is ' || text_item || ' at ' || CAST(ROUND(text_score * 100) AS INT) || '% of words: too weak to accept'
         ELSE 'No part number, supplier part number, quote or usable description'
       END AS reason,
       -- ---------------------------------------------------------------- what the spend was for
       CASE
         WHEN current_item IS NULL AND vendor_part_item IS NULL AND quote_item IS NULL
              AND (cc_purpose = 'NON_PRODUCT' OR non_product_word = 1) THEN 'NON_PRODUCT'
         WHEN ic_how IN ('SERVICE_XREF', 'SERVICE_DESCRIPTION')        THEN 'SPARE'
         WHEN cc_purpose IN ('SPARE', 'WARRANTY', 'PRODUCTION')        THEN cc_purpose
         WHEN service_ship_to = 1                                      THEN 'SPARE'
         WHEN current_item IS NULL AND vendor_part_item IS NULL AND quote_item IS NULL
              AND COALESCE(text_score, 0) < 0.72                       THEN 'UNRESOLVED'
         ELSE 'PURPOSE_UNKNOWN'
       END AS bucket,
       CASE
         WHEN cc_purpose IS NOT NULL                THEN 'Account ' || cost_center
         WHEN service_ship_to = 1                   THEN 'No account on the line; delivered to the service location ' || ship_to
         WHEN ic_how IN ('SERVICE_XREF', 'SERVICE_DESCRIPTION') THEN 'Ordered on a service part number'
         ELSE 'No account and no delivery location on the line'
       END AS bucket_reason
FROM base;

CREATE INDEX po_link_key ON po_link (site, po_number, po_line);

-- -------------------------------------------------------------------------------------
-- Invoice lines. An invoice line inherits the part and purpose of its PO line.
-- If the PO reference is missing, recover it from supplier + part + price; failing that,
-- link the invoice line on its own evidence, exactly as for a PO line.
-- -------------------------------------------------------------------------------------
DROP TABLE IF EXISTS invoice_link;
CREATE TABLE invoice_link AS
WITH with_po AS (
  SELECT i.*,
         COALESCE(
           (SELECT l.po_number || '/' || l.po_line FROM po_link l
             WHERE l.site = i.site AND l.po_number = i.po_number AND l.po_line = i.po_line),
           (SELECT l.po_number || '/' || l.po_line FROM po_link l
             WHERE i.po_number IS NULL AND l.site = i.site AND l.supplier_id = i.supplier_id
               AND ((i.item_raw IS NOT NULL AND l.item_raw = i.item_raw)
                    OR (i.item_raw IS NULL AND l.item_raw IS NULL AND l.line_text = i.line_text))
               AND ABS(l.price - i.price) <= 0.10 * ABS(l.price) AND l.po_date <= i.inv_date
               AND i.qty <= l.qty * 1.001
             ORDER BY ABS(l.price - i.price), ABS(l.qty - i.qty), l.po_date DESC LIMIT 1)
         ) AS po_key,
         CASE WHEN i.po_number IS NULL THEN 1 ELSE 0 END AS po_ref_missing
  FROM invoice_lines i
)
SELECT w.site, w.invoice_no, w.inv_line, w.inv_date, w.supplier_id, w.item_raw, w.line_text,
       w.qty, w.uom, w.price, w.per, w.amount, w.line_type,
       l.po_number, l.po_line, w.po_ref_missing,
       CASE WHEN UPPER(w.line_type) LIKE 'FR%' THEN NULL
            WHEN l.po_number IS NOT NULL THEN l.item
            ELSE COALESCE(ic.current_item, CASE WHEN tm.score >= 0.72 THEN tm.item END) END AS item,
       CASE WHEN UPPER(w.line_type) LIKE 'FR%' THEN 'NON_PRODUCT'
            WHEN l.po_number IS NOT NULL THEN l.method
            WHEN ic.current_item IS NOT NULL THEN ic.how
            WHEN tm.score >= 0.72 THEN 'DESCRIPTION'
            ELSE 'UNRESOLVED' END AS method,
       CASE WHEN UPPER(w.line_type) LIKE 'FR%' THEN 0.95
            WHEN l.po_number IS NOT NULL AND w.po_ref_missing = 0 THEN l.confidence
            WHEN l.po_number IS NOT NULL THEN ROUND(l.confidence * 0.9, 2)
            WHEN ic.current_item IS NOT NULL THEN 0.9
            WHEN tm.score >= 0.72 THEN ROUND(0.5 + 0.35 * tm.score, 2)
            ELSE 0.0 END AS confidence,
       CASE WHEN UPPER(w.line_type) LIKE 'FR%' THEN 'Freight line added on the invoice'
            WHEN l.po_number IS NOT NULL AND w.po_ref_missing = 1
              THEN 'No PO reference on the invoice; recovered PO ' || l.po_number || '/' || l.po_line || ' from supplier, part and price. ' || l.reason
            WHEN l.po_number IS NOT NULL THEN l.reason
            WHEN ic.current_item IS NOT NULL THEN 'No PO found; ' || ic.note
            WHEN tm.score >= 0.72 THEN 'No PO found; description matches ' || tm.item
            ELSE 'No PO found and no usable part evidence on the invoice line' END AS reason,
       CASE WHEN UPPER(w.line_type) LIKE 'FR%' THEN 'NON_PRODUCT'
            WHEN l.po_number IS NOT NULL THEN l.bucket
            WHEN ic.current_item IS NOT NULL OR tm.score >= 0.72 THEN 'PURPOSE_UNKNOWN'
            ELSE 'UNRESOLVED' END AS bucket
FROM with_po w
LEFT JOIN po_link l ON l.site = w.site AND l.po_number || '/' || l.po_line = w.po_key
LEFT JOIN item_current ic ON ic.site = w.site AND ic.item = w.item_raw
LEFT JOIN text_match tm ON tm.site = w.site AND tm.supplier_id = w.supplier_id
                       AND tm.line_text = w.line_text AND w.item_raw IS NULL;
