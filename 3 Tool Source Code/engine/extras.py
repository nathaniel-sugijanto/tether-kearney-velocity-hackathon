"""Helpers that need text handling: supplier kits and supplier change notices."""
import re

from . import text as T


def build_kits(db):
    """A kit is one purchased part that covers several BOM lines.
    'BL12T Box+Tray+Manual+Bag pkg kit' covers the box, tray, manual and bag lines of the BL-12T."""
    db.execute("DROP TABLE IF EXISTS kit_cover")
    db.execute("CREATE TABLE kit_cover (site TEXT, kit_item TEXT, model TEXT, fg_item TEXT, covered_item TEXT, word TEXT)")
    kits = db.execute("""SELECT site, item, descr FROM parts
                         WHERE item_type='BUY' AND status='ACTIVE' AND UPPER(descr) LIKE '%KIT%'""").fetchall()
    for site, kit, descr in kits:
        model = T.attributes(descr).get("model")
        words = [w.upper() for tok in descr.split() if "+" in tok for w in tok.split("+")]
        if not model or not words:
            continue
        for fg, fdescr in db.execute("SELECT item, descr FROM parts WHERE site=? AND item_type='FG'", (site,)).fetchall():
            if T.attributes(fdescr).get("model") != model:
                continue
            lines = db.execute("""SELECT b.child, p.descr FROM bom b JOIN parts p ON p.site=b.site AND p.item=b.child
                                  WHERE b.site=? AND (b.parent=? OR b.top=?)""", (site, fg, fg)).fetchall()
            for w in words:
                for child, cdescr in lines:
                    if w in T.token_set(cdescr):
                        db.execute("INSERT INTO kit_cover VALUES (?,?,?,?,?,?)", (site, kit, "BL-" + model, fg, child, w))
    db.commit()


def build_notices(db):
    """Tie each supplier change notice to the parts, plants, products and spend it touches."""
    db.executescript("""
        DROP TABLE IF EXISTS notice;       DROP TABLE IF EXISTS notice_part;
        CREATE TABLE notice (notice_id TEXT, received_date TEXT, site_received TEXT, supplier_key TEXT,
            supplier_name TEXT, notice_type TEXT, notice_text TEXT, effective_date TEXT, last_order_date TEXT,
            scope TEXT, internal_status TEXT, is_open INTEGER, matched_by TEXT);
        CREATE TABLE notice_part (notice_id TEXT, group_id TEXT);
    """)
    for (nid, rec, site, sname, spart, ntype, ntext, eff, repl, last, status) in db.execute(
            "SELECT * FROM sh_supplier_change_notices").fetchall():
        skey = T.norm_supplier(sname)
        groups, how = set(), None
        # 1. the supplier's own part number, as either plant has it on file
        for (g,) in db.execute("""SELECT DISTINCT g.group_id FROM item_supplier x
                                  JOIN part_group g ON g.site=x.site AND g.item=x.item
                                  WHERE x.supplier_item=?""", (spart,)):
            groups.add(g)
            how = f"Supplier part number {spart} is on file"
        # 2. a manufacturer part number in the part master
        if not groups:
            for (g,) in db.execute("""SELECT DISTINCT g.group_id FROM parts p
                                      JOIN part_group g ON g.site=p.site AND g.item=p.item WHERE p.mpn=?""", (spart,)):
                groups.add(g)
                how = f"Manufacturer part number {spart} is in the part master"
        # 3. no part number: a material or product group. Expand to every matching part this supplier sells.
        if not groups:
            # the scope field names a product group; if it holds a part number we do not know,
            # fall back to the words of the notice text
            scope_text = spart if (spart and " " in spart.strip() and not re.search(r"\d", spart)) else ntext
            scope_words = {w.rstrip("S") for w in T.token_set(scope_text or "") if not re.search(r"\d", w)}
            food = "FOOD-CONTACT" in (spart or "").upper() or "FOOD CONTACT" in (spart or "").upper()
            sold = db.execute("""SELECT DISTINCT pp.group_id, g.group_name, r.needs_nsf + r.needs_fda
                                 FROM price_point pp JOIN part_group g ON g.group_id=pp.group_id
                                 LEFT JOIN group_requirement r ON r.group_id=pp.group_id
                                 WHERE pp.supplier_key=?""", (skey,)).fetchall()
            for g, name, food_part in sold:
                name_words = {w.rstrip("S") for w in T.token_set(name)}
                if (food and food_part) or (not food and len(scope_words & name_words) >= 2):
                    groups.add(g)
            if groups:
                how = f"No part number on the notice; expanded to the {len(groups)} matching parts this supplier sells"
        if not groups:
            how = "No part we buy matches this notice"
        is_open = 0 if (status or "").upper().startswith("CLOSED") else 1
        db.execute("INSERT INTO notice VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (nid, rec, site, skey, sname, ntype, ntext, eff, last, spart, status, is_open, how))
        db.executemany("INSERT INTO notice_part VALUES (?,?)", [(nid, g) for g in sorted(groups)])
    db.commit()
