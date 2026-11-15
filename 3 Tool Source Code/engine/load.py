"""Step 1. Load every site's files into one common layout.

Reads config/mapping.json, which says for each site which file holds which
table and how the client's column names map to the tool's common names.
Nothing here is specific to one ERP: a new system needs a new block in the
mapping file, not new code.

The answer_key folder is never read here.
"""
import csv
import json
import os
import re
import sqlite3
from datetime import datetime

# Common layout: table name -> columns. Every table also gets a "site" column.
SCHEMA = {
    "parts": ["item", "descr", "item_type", "base_uom", "purch_uom", "commodity", "mfr", "mpn",
              "material", "tolerance", "std_cost", "status", "superseded_by", "rating",
              "compliance", "dimensions"],
    "bom": ["top", "parent", "child", "qty", "uom", "eff_from", "eff_to", "source", "level"],
    "suppliers": ["supplier_id", "name", "supplier_type", "state", "iso9001", "certs",
                  "capabilities", "status"],
    "item_supplier": ["item", "supplier_id", "supplier_item", "order_uom", "lead_days", "moq"],
    "quotes": ["rfq", "quote_date", "item", "supplier_id", "quote_no", "price", "lead_days",
               "moq", "annual_qty", "awarded"],
    "po_lines": ["po_number", "po_line", "po_date", "supplier_id", "item_raw", "supplier_item",
                 "line_text", "qty", "uom", "price", "per", "amount", "cost_center", "ship_to",
                 "quote_ref"],
    "invoice_lines": ["invoice_no", "inv_line", "inv_date", "supplier_id", "po_number", "po_line",
                      "item_raw", "line_text", "qty", "uom", "price", "per", "amount", "line_type"],
    "supersessions": ["old_item", "new_item", "eff_date", "reason"],
    "uom_conv": ["item", "alt_uom", "base_uom", "factor"],
    "receipts": ["doc", "rec_date", "po_number", "po_line", "item_raw", "qty", "uom", "promised"],
    "open_pos": ["po_number", "po_line", "po_date", "supplier_id", "item_raw", "line_text",
                 "open_qty", "uom", "promised", "confirmed"],
    "make_buy_changes": ["item", "change", "eff_date", "supplier_id", "note"],
}
NUMERIC = {"qty", "price", "per", "amount", "factor", "lead_days", "moq", "annual_qty", "std_cost",
           "open_qty", "level"}
DATES = {"po_date", "inv_date", "quote_date", "eff_from", "eff_to", "eff_date", "rec_date",
         "promised", "confirmed"}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_num(v):
    if v is None or str(v).strip() == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def to_date(v, fmt):
    v = (v or "").strip()
    if not v:
        return None
    for f in (fmt, "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(v, f).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def load_all(data_dir, config_path, db_path):
    cfg = json.load(open(config_path))
    uom_alias = cfg["uom_aliases"]
    type_alias = cfg["item_type_aliases"]
    if os.path.exists(db_path):
        os.remove(db_path)
    db = sqlite3.connect(db_path)
    for table, cols in SCHEMA.items():
        db.execute(f"CREATE TABLE {table} (site TEXT, {', '.join(c + ' ' + ('REAL' if c in NUMERIC else 'TEXT') for c in cols)})")
    db.execute("CREATE TABLE purpose_rules (site TEXT, kind TEXT, code TEXT, purpose TEXT)")
    db.execute("CREATE TABLE load_log (site TEXT, table_name TEXT, file TEXT, rows INTEGER)")

    def uom(v):
        v = (v or "").strip().upper()
        return uom_alias.get(v, v)

    for site, sc in cfg["sites"].items():
        fmt = sc["date_format"]
        folder = os.path.join(data_dir, sc["folder"])
        for kind, mapping in sc["purpose_rules"]["cost_center"].items():
            db.execute("INSERT INTO purpose_rules VALUES (?,?,?,?)", (site, "cost_center", kind, mapping))
        for s in sc["purpose_rules"]["service_ship_to"]:
            db.execute("INSERT INTO purpose_rules VALUES (?,?,?,?)", (site, "ship_to", s, "SPARE"))
        for table, tc in sc["tables"].items():
            rows = read_csv(os.path.join(folder, tc["file"]))
            cmap = tc["columns"]
            out = []
            stack = {}  # for indented BOMs: level -> part
            for r in rows:
                rec = {c: (r.get(src) or "").strip() for c, src in cmap.items()}
                # ---- table-specific tidy-ups -------------------------------------
                if table == "bom" and tc.get("layout") == "indented":
                    lvl = int(float(rec["level"]))
                    child = rec["child"].lstrip(". ")
                    rec["parent"] = rec["top"] if lvl == 1 else stack.get(lvl - 1)
                    rec["child"] = child
                    stack[lvl] = child
                    rec["eff_to"] = "9999-12-31"
                if table == "bom" and tc.get("layout") == "parent_child":
                    rec["level"] = None
                    rec["top"] = None
                if table == "invoice_lines" and "po_ref" in rec:
                    ref = rec.pop("po_ref")
                    rec["po_number"], _, rec["po_line"] = ref.partition("/")
                if table == "quotes" and "lead_weeks" in rec:
                    w = to_num(rec.pop("lead_weeks"))
                    rec["lead_days"] = None if w is None else round(w * 7)
                if table == "quotes":
                    rec["awarded"] = "Y" if rec.get("awarded", "").upper() in ("Y", "AWARDED", "YES") else "N"
                if table == "suppliers":
                    certs = rec.get("certs", "")
                    if "iso9001" not in rec or rec["iso9001"] == "":
                        rec["iso9001"] = "Y" if "ISO 9001" in certs.upper() else "N"
                    rec["certs"] = certs
                if table == "parts":
                    rec["item_type"] = type_alias.get(rec["item_type"].upper(), rec["item_type"].upper())
                    st = rec.get("status", "").upper()
                    rec["status"] = "ACTIVE" if st in ("ACTIVE", "Y") else "INACTIVE"
                    rec["base_uom"], rec["purch_uom"] = uom(rec["base_uom"]), uom(rec["purch_uom"])
                for c in ("uom", "order_uom", "alt_uom", "base_uom"):
                    if c in rec and table != "parts":
                        rec[c] = uom(rec[c])
                if table in ("po_lines", "invoice_lines") and not rec.get("per"):
                    rec["per"] = 1
                # line numbers as plain integers in text form ("10", not "10.0")
                for c in ("po_line", "inv_line"):
                    if rec.get(c):
                        rec[c] = str(int(float(rec[c])))
                # ---- types -------------------------------------------------------
                row = [site]
                for c in SCHEMA[table]:
                    v = rec.get(c)
                    if c in NUMERIC:
                        v = to_num(v)
                    elif c in DATES:
                        v = to_date(v, fmt) if v not in (None, "9999-12-31") else v
                    elif v == "":
                        v = None
                    row.append(v)
                out.append(row)
            db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * (len(SCHEMA[table]) + 1))})", out)
            db.execute("INSERT INTO load_log VALUES (?,?,?,?)", (site, table, tc["file"], len(out)))

    # ---- shared files (already one layout for both sites) -----------------------
    shared = os.path.join(data_dir, cfg["shared_folder"])
    for name in sorted(os.listdir(shared)):
        if not name.endswith(".csv"):
            continue
        rows = read_csv(os.path.join(shared, name))
        t = "sh_" + re.sub(r"\W+", "_", name[:-4])
        cols = list(rows[0].keys())
        db.execute(f"CREATE TABLE {t} ({', '.join(c + ' TEXT' for c in cols)})")
        db.executemany(f"INSERT INTO {t} VALUES ({','.join('?' * len(cols))})",
                       [[(r[c] or None) for c in cols] for r in rows])
        db.execute("INSERT INTO load_log VALUES (?,?,?,?)", ("shared", t, name, len(rows)))
    db.commit()
    return db


if __name__ == "__main__":
    import sys
    d = load_all(sys.argv[1], "config/mapping.json", "out/linkage.db")
    for r in d.execute("SELECT * FROM load_log"):
        print(r)
