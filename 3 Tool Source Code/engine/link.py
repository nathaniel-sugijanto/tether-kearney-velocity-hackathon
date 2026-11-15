"""Step 2. Tie spend lines to parts.

Builds two small helper tables in Python (they need text handling that plain SQL
lacks), then runs sql/02_link_spend.sql, which holds the matching order itself.
"""
import os
import re

from . import text as T

ACCEPT = 0.72   # share of words that must agree before a description match is accepted


def register_functions(db):
    db.create_function("norm", 1, T.norm, deterministic=True)
    db.create_function("sim", 2, T.similarity, deterministic=True)
    db.create_function("norm_supplier", 1, T.norm_supplier, deterministic=True)

    def quote_no_in(text):
        m = re.search(r"\bQ-\d+\b", text or "", re.I)
        return m.group(0).upper() if m else None
    db.create_function("quote_no_in", 1, quote_no_in, deterministic=True)

    def title_case(name):
        keep = {"EMS", "E.M.S.", "LLC"}
        small = {"AND": "and", "OF": "of"}
        return " ".join(w if w.upper() in keep else small.get(w.upper(), w.capitalize()) for w in (name or "").split())
    db.create_function("title_case", 1, title_case, deterministic=True)

    def model_of(descr):
        m = T.attributes(descr).get("model")
        return "BL-" + m if m else None
    db.create_function("model_of", 1, model_of, deterministic=True)


def build_item_current(db):
    """Every part number -> the part number that carries its spend today."""
    db.execute("DROP TABLE IF EXISTS item_current")
    db.execute("CREATE TABLE item_current (site TEXT, item TEXT, current_item TEXT, how TEXT, note TEXT)")
    parts = db.execute("SELECT site, item, descr, item_type, status, superseded_by FROM parts").fetchall()
    by_site = {}
    for site, item, descr, typ, status, sup in parts:
        by_site.setdefault(site, []).append((item, descr, typ, status))
    supers = {(s, o): (n, d, r) for s, o, n, d, r in
              db.execute("SELECT site, old_item, new_item, eff_date, reason FROM supersessions")}
    catalogue = {r[0]: r[1] for r in db.execute(
        "SELECT service_sku, production_item_dayton FROM sh_service_parts_catalog")}
    rows = []
    for site, item, descr, typ, status, sup in parts:
        if (site, item) in supers:
            new, date, reason = supers[(site, item)]
            rows.append((site, item, new, "SUPERSESSION",
                         f"{item} was replaced by {new} on {date} ({reason.lower()})"))
        elif sup:
            rows.append((site, item, sup, "SUPERSESSION", f"{item} is marked superseded by {sup}"))
        elif typ == "SERVICE":
            prod = catalogue.get(item)
            if prod:
                rows.append((site, item, prod, "SERVICE_XREF",
                             f"Service part {item} is {prod} in the service catalogue"))
            else:
                best = best_match(descr, [(i, d) for i, d, t, s in by_site[site] if t == "BUY" and s == "ACTIVE"])
                if best and best[1] >= ACCEPT:
                    rows.append((site, item, best[0], "SERVICE_DESCRIPTION",
                                 f"Service part {item} has no production part in the service catalogue; "
                                 f"its description matches {best[0]}. Needs review"))
                else:
                    rows.append((site, item, None, "UNRESOLVED", f"Service part {item} has no production part on file"))
        elif status != "ACTIVE":
            twins = [i for i, d, t, s in by_site[site]
                     if s == "ACTIVE" and i != item and T.norm(d) == T.norm(descr)]
            if twins:
                rows.append((site, item, twins[0], "RENUMBER_SUGGESTED",
                             f"{item} is inactive and {twins[0]} has the identical description; "
                             f"no supersession is on record. Needs review"))
            else:
                rows.append((site, item, item, "EXACT", None))
        else:
            rows.append((site, item, item, "EXACT", None))
    db.executemany("INSERT INTO item_current VALUES (?,?,?,?,?)", rows)
    db.execute("CREATE INDEX item_current_key ON item_current (site, item)")


def best_match(text, candidates, prefer=()):
    """Best description match among (item, description) candidates.
    Returns (item, score, runner_up_score). Parts this supplier already sells win ties."""
    words = T.token_set(text)
    scored = sorted(((T.jaccard(words, T.token_set(d)), i in prefer, i) for i, d in candidates), reverse=True)
    if not scored:
        return None
    top = scored[0]
    # among accepted candidates, a part the supplier is known to sell beats a slightly closer one
    known = [s for s in scored if s[0] >= ACCEPT and s[1]]
    if known:
        top = known[0]
    others = [s[0] for s in scored if s[2] != top[2]]
    return top[2], round(top[0], 3), round(others[0], 3) if others else 0.0


def build_text_match(db):
    """Best description match for every distinct free-text line that has no part number."""
    db.execute("DROP TABLE IF EXISTS text_match")
    db.execute("CREATE TABLE text_match (site TEXT, supplier_id TEXT, line_text TEXT, item TEXT, score REAL, runner_up REAL)")
    cands = {}
    for site, item, descr in db.execute("SELECT site, item, descr FROM parts WHERE item_type='BUY' AND status='ACTIVE'"):
        cands.setdefault(site, []).append((item, descr))
    # which parts each supplier is already known to sell (from lines that do carry a part number)
    sells = {}
    for site, sup, item in db.execute("""
            SELECT DISTINCT site, supplier_id, item_raw FROM po_lines WHERE item_raw IS NOT NULL
            UNION SELECT DISTINCT site, supplier_id, item FROM item_supplier"""):
        sells.setdefault((site, sup), set()).add(item)
    texts = db.execute("""
        SELECT DISTINCT site, supplier_id, line_text FROM po_lines      WHERE item_raw IS NULL AND line_text IS NOT NULL
        UNION SELECT DISTINCT site, supplier_id, line_text FROM invoice_lines WHERE item_raw IS NULL AND line_text IS NOT NULL
        UNION SELECT DISTINCT site, supplier_id, line_text FROM open_pos WHERE item_raw IS NULL AND line_text IS NOT NULL
    """).fetchall()
    rows = []
    for site, sup, text in texts:
        m = best_match(text, cands.get(site, []), sells.get((site, sup), ()))
        if m:
            rows.append((site, sup, text, m[0], m[1], m[2]))
    db.executemany("INSERT INTO text_match VALUES (?,?,?,?,?,?)", rows)
    db.execute("CREATE INDEX text_match_key ON text_match (site, supplier_id, line_text)")


def run_sql(db, name):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "sql", name)) as f:
        db.executescript(f.read())


def link(db):
    register_functions(db)
    build_item_current(db)
    build_text_match(db)
    run_sql(db, "02_link_spend.sql")
    db.commit()
