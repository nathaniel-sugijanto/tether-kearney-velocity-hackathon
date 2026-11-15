-- =====================================================================================
-- Step 4b. Which product uses which part, and what each product costs.
-- =====================================================================================

-- Finished products at each plant, with a model name both plants share ("BL-12").
DROP TABLE IF EXISTS product;
CREATE TABLE product AS
SELECT site, item AS fg_item, model_of(descr) AS model, descr
FROM parts WHERE item_type = 'FG';

-- BOM flattened to "one finished unit needs this much of this part", using today's structure.
--   costed = 1 for lines the plant actually buys or makes at that level;
--   costed = 0 for "Reference" lines: parts that sit inside an assembly bought complete.
DROP TABLE IF EXISTS bom_flat;
CREATE TABLE bom_flat AS
WITH RECURSIVE walk(site, fg_item, item, qty, costed, depth) AS (
  SELECT b.site, b.parent, b.child, b.qty,
         CASE WHEN UPPER(COALESCE(b.source, '')) = 'REFERENCE' THEN 0 ELSE 1 END, 1
  FROM bom b JOIN product p ON p.site = b.site AND p.fg_item = b.parent
  WHERE b.eff_to >= '2026-10-31' AND (b.top IS NULL OR b.top = b.parent)
  UNION ALL
  SELECT b.site, w.fg_item, b.child, w.qty * b.qty,
         CASE WHEN UPPER(COALESCE(b.source, '')) = 'REFERENCE' THEN 0 ELSE w.costed END, w.depth + 1
  FROM bom b JOIN walk w ON w.site = b.site AND w.item = b.parent
  WHERE b.eff_to >= '2026-10-31' AND (b.top IS NULL OR b.top = w.fg_item) AND w.depth < 6
)
SELECT w.site, w.fg_item, pr.model, w.item, g.group_id, pt.item_type, pt.descr,
       SUM(w.qty) AS qty_per_unit, MIN(w.costed) AS costed, MIN(w.depth) AS depth
FROM walk w
JOIN product pr ON pr.site = w.site AND pr.fg_item = w.fg_item
JOIN parts pt   ON pt.site = w.site AND pt.item = w.item
LEFT JOIN part_group g ON g.site = w.site AND g.item = w.item
GROUP BY w.site, w.fg_item, w.item;

-- Units built in the period, by plant and model.
DROP TABLE IF EXISTS units_built;
CREATE TABLE units_built AS
SELECT plant AS site, model, SUM(CAST(units_completed AS REAL)) AS units
FROM sh_build_volumes GROUP BY plant, model;

-- Price each plant pays for each part today: production purchases, whole period, all suppliers.
DROP TABLE IF EXISTS site_price;
CREATE TABLE site_price AS
SELECT site, group_id, SUM(amount) / SUM(base_qty) AS price, SUM(amount) AS spend, SUM(base_qty) AS qty
FROM spend_fact
WHERE item IS NOT NULL AND uom_missing = 0 AND base_qty > 0 AND bucket = 'PRODUCTION'
GROUP BY site, group_id;

-- Purchased material per finished unit, line by line. Only lines the plant buys are costed:
-- a bought assembly is costed at its own price, never together with the parts inside it.
DROP TABLE IF EXISTS product_cost_line;
CREATE TABLE product_cost_line AS
-- ordinary purchased lines; a line covered by a supplier kit costs nothing here (the kit carries it)
SELECT f.site, f.model, f.item, f.group_id, f.descr, f.qty_per_unit,
       CASE WHEN k.kit_item IS NULL THEN sp.price END                        AS price,
       CASE WHEN k.kit_item IS NULL THEN f.qty_per_unit * sp.price ELSE 0 END AS cost_per_unit,
       CASE WHEN k.kit_item IS NULL AND sp.price IS NULL THEN 1 ELSE 0 END    AS price_missing,
       CASE WHEN k.kit_item IS NOT NULL THEN 'Bought inside kit ' || k.kit_item
            WHEN sp.price IS NULL THEN 'No comparable price: unit conversion missing or no purchases' END AS note
FROM bom_flat f
LEFT JOIN site_price sp ON sp.site = f.site AND sp.group_id = f.group_id
LEFT JOIN kit_cover k   ON k.site = f.site AND k.fg_item = f.fg_item AND k.covered_item = f.item
WHERE f.costed = 1 AND f.item_type = 'BUY'
UNION ALL
-- the kit itself, once per finished unit
SELECT DISTINCT k.site, k.model, k.kit_item, g.group_id, p.descr, 1.0,
       sp.price, sp.price, CASE WHEN sp.price IS NULL THEN 1 ELSE 0 END,
       'Supplier kit covering ' || (SELECT COUNT(*) FROM kit_cover k2 WHERE k2.site = k.site AND k2.kit_item = k.kit_item) || ' BOM lines'
FROM kit_cover k
JOIN parts p ON p.site = k.site AND p.item = k.kit_item
JOIN part_group g ON g.site = k.site AND g.item = k.kit_item
LEFT JOIN site_price sp ON sp.site = k.site AND sp.group_id = g.group_id;

-- Labor and overhead from the plant's standards (final assembly plus any sub-assembly made in house).
DROP TABLE IF EXISTS product_labor;
CREATE TABLE product_labor AS
SELECT pr.site, pr.model,
       SUM(CAST(l.std_minutes_per_unit AS REAL) / 60.0 * CAST(l.labor_rate_usd_per_hour AS REAL)) AS labor,
       SUM(CAST(l.std_minutes_per_unit AS REAL) / 60.0 * CAST(l.labor_rate_usd_per_hour AS REAL)
           * CAST(l.overhead_multiple_of_labor AS REAL)) AS overhead
FROM product pr
JOIN sh_labor_and_overhead_standards l
  ON l.plant = pr.site
 AND (l.item = pr.fg_item
      OR l.item IN (SELECT f.item FROM bom_flat f WHERE f.site = pr.site AND f.fg_item = pr.fg_item
                                                   AND f.item_type = 'MAKE'))
GROUP BY pr.site, pr.model;

DROP TABLE IF EXISTS product_cost;
CREATE TABLE product_cost AS
SELECT pr.site, pr.model, pr.fg_item, pr.descr,
       (SELECT SUM(c.cost_per_unit) FROM product_cost_line c WHERE c.site = pr.site AND c.model = pr.model) AS material,
       COALESCE(pl.labor, 0) AS labor, COALESCE(pl.overhead, 0) AS overhead,
       (SELECT SUM(c.price_missing) FROM product_cost_line c WHERE c.site = pr.site AND c.model = pr.model) AS lines_without_price,
       u.units
FROM product pr
LEFT JOIN product_labor pl ON pl.site = pr.site AND pl.model = pr.model
LEFT JOIN units_built u    ON u.site = pr.site AND u.model = pr.model;

-- Shared parts: split each part's production spend across the products that use it,
-- in proportion to (quantity per unit x units built).
DROP TABLE IF EXISTS product_spend;
CREATE TABLE product_spend AS
WITH use AS (
  SELECT f.site, f.model, f.group_id, SUM(f.qty_per_unit) * u.units AS usage
  FROM bom_flat f JOIN units_built u ON u.site = f.site AND u.model = f.model
  WHERE f.item_type = 'BUY' GROUP BY f.site, f.model, f.group_id
)
SELECT u.site, u.model, u.group_id,
       sp.spend * u.usage / SUM(u.usage) OVER (PARTITION BY u.site, u.group_id) AS spend,
       u.usage / SUM(u.usage) OVER (PARTITION BY u.site, u.group_id)            AS share
FROM use u JOIN site_price sp ON sp.site = u.site AND sp.group_id = u.group_id;

-- Plan against actual, and next year's purchased-material spend from the forecast.
DROP TABLE IF EXISTS plan_vs_actual;
CREATE TABLE plan_vs_actual AS
SELECT pc.site, pc.model, pc.units AS actual_units,
       (SELECT SUM(CAST(f.forecast_units AS REAL)) FROM sh_build_forecast f
         WHERE f.plant = pc.site AND f.model = pc.model AND f.forecast_version LIKE 'FY26%') AS plan_units,
       (SELECT SUM(CAST(f.forecast_units AS REAL)) FROM sh_build_forecast f
         WHERE f.plant = pc.site AND f.model = pc.model AND f.forecast_version LIKE 'FY27%') AS next_year_units,
       pc.material
FROM product_cost pc;
