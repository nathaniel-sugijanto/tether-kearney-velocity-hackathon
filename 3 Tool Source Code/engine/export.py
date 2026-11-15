"""Step 7. Collect everything the dashboard shows into one data package,
and write the dashboard as a single HTML file that opens with a double-click."""
import csv
import json
import os

TYPE_LABEL = {
    "PRICE_ALIGNMENT": "Supplier consolidation and price alignment",
    "CLOSE_SPEC": "Near-identical part",
    "QUOTE_LEAKAGE": "Invoiced above quote",
    "SUPPLIER_INCREASE": "Across-the-board increase",
}
METHOD_LABEL = {
    "EXACT": "Exact part number", "SUPERSESSION": "Replaced part number followed to the current one",
    "SERVICE_XREF": "Service part, via the service catalogue",
    "SERVICE_DESCRIPTION": "Service part, inferred from its description",
    "RENUMBER_SUGGESTED": "Renumbered part with no record (suggested)",
    "VENDOR_PART": "Supplier's part number", "QUOTE_REF": "Quote reference",
    "DESCRIPTION": "Free-text description match", "NON_PRODUCT": "Not a product part (freight, tooling, testing)",
    "UNRESOLVED": "Could not be identified",
}
PLAIN = {"EXACT"}   # what a plain part-number join would also get


def nice(name):
    """'CARAFE, 12-CUP, GLASS, BLACK HANDLE' -> 'Carafe, 12-cup, glass, black handle'.
    El Paso's shorthand is spelled out on the way ('pwr cord' -> 'power cord')."""
    import re
    from . import text as T
    if not name:
        return ""
    keep = {"PP", "LED", "LCD", "UL", "ZN", "SPST", "NC", "PET", "LDPE", "EN", "ES", "FR", "SPT-2"}
    spell = dict(T.ABBREVIATIONS, PH="PAN HEAD", ZP="ZN")
    for k in ("SELF-TAPPING", "CLOCK/TIMER", "EN/ES/FR", "BOARDS", "IND", "ZINC", "TUBING", "POLYBAG"):
        spell.pop(k, None)
    words = []
    for w in name.upper().split():
        core, tail = w.rstrip(","), "," if w.endswith(",") else ""
        core = spell.get(core, core)
        for c in core.split():
            if c in keep or c.startswith("BL-"):
                words.append(c)
            elif re.fullmatch(r"\d+-[A-Z]+", c):
                words.append(c.lower())
            elif re.search(r"\d", c):
                words.append(re.sub(r"MM$", " mm", c) if re.fullmatch(r"[\d.X]+MM", c) else c)
            else:
                words.append(c.lower())
        words[-1] += tail
    s = " ".join(words)
    return s[0].upper() + s[1:]


def rows(db, sql, args=()):
    cur = db.execute(sql, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def build_data(db):
    d = {}
    one = lambda sql, args=(): db.execute(sql, args).fetchone()
    sup_name = dict(db.execute("SELECT supplier_key, supplier_name FROM supplier_name").fetchall())
    group_name = {g: nice(n) for g, n in db.execute("SELECT DISTINCT group_id, group_name FROM part_group")}
    sn = lambda k: sup_name.get(k, k)

    # ------------------------------------------------------------------ meta
    total = one("SELECT SUM(amount) FROM spend_fact")[0]
    d["meta"] = {
        "period": "%s to %s" % one("SELECT MIN(inv_date), MAX(inv_date) FROM spend_fact"),
        "sites": [r[0] for r in db.execute("SELECT DISTINCT site FROM parts ORDER BY 1")],
        "total_spend": total,
        "po_lines": one("SELECT COUNT(*) FROM po_link")[0],
        "invoice_lines": one("SELECT COUNT(*) FROM spend_fact")[0],
        "suppliers": one("SELECT COUNT(*) FROM supplier_name")[0],
        "files": rows(db, "SELECT site, table_name, file, rows FROM load_log"),
    }

    # ------------------------------------------------------------------ page 1: linkage health
    plain = one("""SELECT SUM(CASE WHEN EXISTS (SELECT 1 FROM bom b WHERE b.site=i.site AND b.child=i.item_raw)
                                THEN amount ELSE 0 END) FROM invoice_link i""")[0]
    linked = one("SELECT SUM(amount) FROM spend_fact WHERE item IS NOT NULL")[0]
    by_method = rows(db, "SELECT method, SUM(amount) AS spend, COUNT(*) AS lines FROM spend_fact GROUP BY method ORDER BY 2 DESC")
    for m in by_method:
        m["label"] = METHOD_LABEL.get(m["method"], m["method"])
    d["health"] = {
        "plain_share": plain / total, "tool_share": linked / total,
        "plain_spend": plain, "tool_spend": linked,
        "non_product": one("SELECT SUM(amount) FROM spend_fact WHERE bucket='NON_PRODUCT'")[0],
        "unresolved": one("SELECT SUM(amount) FROM spend_fact WHERE bucket='UNRESOLVED'")[0],
        "by_method": by_method,
        "by_bucket": rows(db, "SELECT bucket, SUM(amount) AS spend, COUNT(*) AS lines FROM spend_fact GROUP BY bucket ORDER BY 2 DESC"),
        "unresolved_lines": rows(db, """SELECT s.site, s.inv_date, s.supplier_key, s.line_text, s.amount, s.reason
                                        FROM spend_fact s WHERE s.bucket='UNRESOLVED' ORDER BY s.amount DESC"""),
        "review_queue": rows(db, """SELECT site, method, item_raw, item, line_text, supplier_key,
                                           MIN(confidence) AS confidence, MIN(reason) AS reason,
                                           SUM(amount) AS spend, COUNT(*) AS lines
                                    FROM spend_fact WHERE item IS NOT NULL AND confidence < 0.9
                                    GROUP BY site, method, COALESCE(item_raw, line_text), item ORDER BY spend DESC"""),
        "uom_missing": rows(db, """SELECT site, item, MIN(line_text) AS line_text, uom, SUM(amount) AS spend, COUNT(*) AS lines
                                   FROM spend_fact WHERE uom_missing=1 GROUP BY site, item, uom"""),
        "legacy_xref": rows(db, "SELECT * FROM legacy_xref_check ORDER BY verdict"),
        "same_part_links": one("SELECT COUNT(*) FROM part_pair WHERE relation='SAME' AND site_a<>site_b")[0],
        "legacy_links": one("SELECT COUNT(*) FROM sh_legacy_part_crossref_2023")[0],
        "spare_on_production": one("""SELECT SUM(amount) FROM spend_fact WHERE bucket IN ('SPARE','WARRANTY','PURPOSE_UNKNOWN')
                                       AND item_raw IN (SELECT child FROM bom)""")[0],
    }
    for r in d["health"]["unresolved_lines"] + d["health"]["review_queue"]:
        r["supplier"] = sn(r.pop("supplier_key"))
    for r in d["health"]["review_queue"]:
        r["method_label"] = METHOD_LABEL.get(r["method"], r["method"])
        r["part"] = group_name.get(one("SELECT group_id FROM part_group WHERE site=? AND item=?", (r["site"], r["item"]))[0], "")

    # ------------------------------------------------------------------ page 2: product cost
    products = rows(db, "SELECT site, model, fg_item, descr, material, labor, overhead, lines_without_price, units FROM product_cost ORDER BY model, site")
    for p in products:
        p["lines"] = rows(db, """SELECT c.item, c.group_id, c.descr, c.qty_per_unit, c.price, c.cost_per_unit, c.note,
                                        (SELECT COUNT(DISTINCT f.site || f.model) FROM bom_flat f WHERE f.group_id = c.group_id) AS used_in
                                 FROM product_cost_line c WHERE c.site=? AND c.model=? ORDER BY c.cost_per_unit DESC""",
                          (p["site"], p["model"]))
        for ln in p["lines"]:
            ln["name"] = group_name.get(ln["group_id"], nice(ln["descr"]))
    plan = rows(db, "SELECT * FROM plan_vs_actual ORDER BY model, site")
    shared = rows(db, """SELECT ps.group_id, ps.site, ps.model, ps.spend, ps.share FROM product_spend ps
                         WHERE ps.group_id IN (SELECT group_id FROM product_spend GROUP BY group_id HAVING COUNT(*) > 1)""")
    shared_by_group = {}
    for r in shared:
        shared_by_group.setdefault(r["group_id"], []).append(r)
    d["products"] = {
        "products": products, "plan": plan,
        "shared": sorted(({"group_id": g, "name": group_name.get(g, g), "uses": u, "spend": sum(x["spend"] for x in u)}
                          for g, u in shared_by_group.items()), key=lambda x: -x["spend"]),
    }

    # ------------------------------------------------------------------ page 3: opportunities
    delivery = {}
    for k, site, n, ot, late, lead in db.execute("SELECT * FROM supplier_delivery"):
        delivery[(k, site)] = {"receipts": n, "on_time": ot, "avg_days_late": late, "lead_days": lead}

    def price_points(gid):
        pts = rows(db, """SELECT pp.site, pp.supplier_key, pp.qty, pp.spend, pp.price, pp.items, c.qualified, c.fail_reason
                          FROM price_point pp JOIN supplier_part_check c ON c.group_id=pp.group_id AND c.supplier_key=pp.supplier_key
                          WHERE pp.group_id=? ORDER BY pp.price""", (gid,))
        for p in pts:
            p["supplier"] = sn(p["supplier_key"])
            p.update(delivery.get((p["supplier_key"], p["site"]), {}))
        return pts

    def models_of(gid):
        return [r[0] for r in db.execute("SELECT DISTINCT model || ' (' || site || ')' FROM bom_flat WHERE group_id=? ORDER BY 1", (gid,))]

    def parts_of(gid):
        return rows(db, """SELECT g.site, g.item, p.descr, p.status, p.material, p.rating, p.dimensions, p.compliance, p.mfr, p.mpn
                           FROM part_group g JOIN parts p ON p.site=g.site AND p.item=g.item WHERE g.group_id=? ORDER BY g.site, g.item""", (gid,))

    def evidence(gid, where="", args=()):
        ev = rows(db, f"""SELECT site, invoice_no, inv_date, supplier_key, item, qty, uom, base_qty, base_uom, base_price, amount, po_number, po_line
                          FROM spend_fact WHERE group_id=? AND uom_missing=0 {where} ORDER BY amount DESC LIMIT 40""", (gid,) + args)
        for e in ev:
            e["supplier"] = sn(e.pop("supplier_key"))
        return ev

    opps = []
    inc = {}
    for o in rows(db, "SELECT * FROM opportunity ORDER BY saving DESC"):
        gid = o["group_id"]
        name = group_name.get(gid, gid)
        o["part_name"] = name
        o["type_label"] = TYPE_LABEL[o["opp_type"]]
        o["best_supplier_name"] = sn(o["best_supplier"])
        short = ", ".join(name.split(", ")[:3])
        if o["opp_type"] == "SUPPLIER_INCREASE":
            inc.setdefault((o["best_supplier"], o["best_site"]), []).append(o)
            continue
        o["price_points"] = price_points(gid)
        o["models"] = models_of(gid)
        o["parts"] = parts_of(gid)
        if o["opp_type"] == "PRICE_ALIGNMENT":
            n_sup = len({p["supplier_key"] for p in o["price_points"]})
            o["title"] = (f"One price for {short}: {n_sup} suppliers today" if n_sup > 1
                          else f"One price for {short} across both plants")
            o["action"] = (f"Move volume to, or negotiate down to, {o['best_supplier_name']}'s price at {o['best_site']} "
                           f"(${o['best_price']:.4f} per unit), the lowest price from a qualified supplier with real volume.")
            o["evidence"] = evidence(gid)
            dups = one("SELECT COUNT(*) FROM part_group g JOIN parts p ON p.site=g.site AND p.item=g.item WHERE g.group_id=? AND p.status='ACTIVE' AND p.item_type='BUY'", (gid,))[0]
            o["numbers"] = dups
        elif o["opp_type"] == "CLOSE_SPEC":
            std = one("SELECT standard_group FROM family_standard WHERE family_id=?", (o["family_id"],))[0]
            o["standard_name"] = group_name.get(std, std)
            o["standard_parts"] = parts_of(std)
            o["standard_points"] = price_points(std)
            o["title"] = f"Replace {short} with the near-identical standard part"
            o["action"] = (f"Ask engineering whether {o['standard_name']} can replace this part. "
                           f"The only difference found: {o['detail']}. If yes, buy the standard part at ${o['best_price']:.4f} per unit.")
            o["evidence"] = evidence(gid)
        elif o["opp_type"] == "QUOTE_LEAKAGE":
            o["title"] = f"Recover overbilling on {short}"
            o["action"] = f"{o['best_supplier_name']} invoices above its awarded quote. Claim the difference and correct the PO price."
            ev = rows(db, """SELECT site, invoice_no, inv_date, base_qty, base_price, quoted_price, quote_no, leak
                             FROM quote_leak_line WHERE group_id=? AND site=? ORDER BY inv_date""", (gid, o["best_site"]))
            o["leak_lines"] = ev
        opps.append(o)
    for (skey, site), items in inc.items():
        opps.append({
            "opp_id": f"SI-{site}-{skey}".replace(" ", "_"), "opp_type": "SUPPLIER_INCREASE", "readiness": "REVIEW",
            "type_label": TYPE_LABEL["SUPPLIER_INCREASE"],
            "title": f"{sn(skey)} raised {len(items)} parts at {site} by about the same percentage",
            "saving": sum(i["saving"] for i in items), "spend": sum(i["spend"] for i in items),
            "best_supplier_name": sn(skey), "best_site": site, "part_name": f"{len(items)} molded parts",
            "action": "Check the contract: is an across-the-board surcharge allowed, and was it agreed? If not, claim it back.",
            "detail": f"Every part shows the same step above its awarded quote, starting within weeks of each other.",
            "caution": None, "models": [],
            "increase_parts": [{"part": i["part_name"], "paid_above_quote": i["saving"], "spend": i["spend"], "detail": i["detail"].split(". The supplier")[0]} for i in items],
        })
    opps.sort(key=lambda o: -o["saving"])
    d["opportunities"] = opps

    # look-alike families (all three outcomes, including the ones that must stay apart)
    fams = []
    for (fid,) in db.execute("SELECT DISTINCT family_id FROM part_family ORDER BY 1").fetchall():
        gs = [r[0] for r in db.execute("SELECT group_id FROM part_family WHERE family_id=?", (fid,))]
        std = one("SELECT standard_group FROM family_standard WHERE family_id=?", (fid,))
        pairs = rows(db, f"""SELECT group_a, group_b, relation, differences FROM group_pair
                             WHERE group_a IN ({','.join('?' * len(gs))}) AND group_b IN ({','.join('?' * len(gs))})""", gs + gs)
        for p in pairs:
            p["name_a"], p["name_b"] = group_name.get(p["group_a"]), group_name.get(p["group_b"])
        fams.append({"family_id": fid, "standard": std[0] if std else None,
                     "members": [{"group_id": g, "name": group_name.get(g), "parts": parts_of(g),
                                  "spend": one("SELECT COALESCE(SUM(spend),0) FROM price_point WHERE group_id=?", (g,))[0]} for g in gs],
                     "pairs": pairs})
    d["families"] = fams
    d["duplicates"] = rows(db, """SELECT site_a AS site, item_a, item_b, evidence FROM part_pair WHERE relation='SAME' AND site_a=site_b""")

    # ------------------------------------------------------------------ page 4: watchlist
    notices = rows(db, "SELECT * FROM notice ORDER BY is_open DESC, effective_date")
    for n in notices:
        n["parts"] = [group_name.get(g) for (g,) in db.execute("SELECT group_id FROM notice_part WHERE notice_id=?", (n["notice_id"],))]
        n["exposure"] = rows(db, "SELECT site, was_told, spend_with_supplier, spend_on_parts, models, open_orders FROM notice_exposure WHERE notice_id=?", (n["notice_id"],))
        # a plant is exposed if it buys the affected parts from this supplier but never got the notice
        n["not_told"] = [e["site"] for e in n["exposure"] if not e["was_told"] and (e["spend_with_supplier"] or 0) > 0]
        n["spend_exposed"] = sum(e["spend_with_supplier"] or 0 for e in n["exposure"])
    late = rows(db, """SELECT site, po_number, po_line, po_date, supplier_key, group_name, open_qty, uom, promised, confirmed,
                              days_slip, models, on_old_number, old_number_note, open_notices, item_raw, line_text
                       FROM open_order_x WHERE days_slip >= 14 OR on_old_number = 1 OR open_notices IS NOT NULL
                       ORDER BY on_old_number DESC, days_slip DESC""")
    for r in late:
        r["supplier"] = sn(r.pop("supplier_key"))
        r["part"] = nice(r.pop("group_name") or r["line_text"])
    deliv = rows(db, """SELECT supplier_key, SUM(receipts) AS receipts, SUM(on_time*receipts)/SUM(receipts) AS on_time,
                               SUM(avg_days_late*receipts)/SUM(receipts) AS avg_days_late, SUM(actual_lead_days*receipts)/SUM(receipts) AS lead_days
                        FROM supplier_delivery GROUP BY supplier_key HAVING SUM(receipts) >= 10 ORDER BY on_time""")
    unq = dict(db.execute("SELECT supplier_key, SUM(spend) FROM unqualified_spend GROUP BY 1").fetchall())
    spend_by_sup = dict(db.execute("SELECT supplier_key, SUM(amount) FROM spend_fact GROUP BY 1").fetchall())
    for r in deliv:
        r["supplier"] = sn(r["supplier_key"])
        r["unqualified_spend"] = unq.get(r["supplier_key"], 0)
        r["spend"] = spend_by_sup.get(r["supplier_key"], 0)
    d["watch"] = {
        "notices": notices, "orders": late, "delivery": deliv,
        "open_orders": one("SELECT COUNT(*) FROM open_order_x")[0],
        "expedite": one("SELECT COALESCE(SUM(amount),0) FROM expedite_spend")[0],
        "expedite_lines": rows(db, "SELECT site, inv_date, line_text, amount FROM expedite_spend ORDER BY inv_date"),
        "unqualified": [{"supplier": sn(k), "spend": v,
                         "reason": one("SELECT MAX(fail_reason) FROM unqualified_spend WHERE supplier_key=?", (k,))[0]}
                        for k, v in sorted(unq.items(), key=lambda x: -x[1])],
        "unqualified_total": sum(unq.values()),
    }
    return d


def write_outputs(db, out_dir="out", scorecard=None):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = build_data(db)
    from . import platform
    data["platform"] = platform.build_platform(db, os.path.join(here, "config", "mapping.json"))
    if scorecard:
        data["scorecard"] = scorecard
    with open(os.path.join(here, "app", "template.html")) as f:
        html = f.read()
    html = html.replace("/*__DATA__*/null", json.dumps(data, default=str).replace("</", "<\\/"))
    with open(os.path.join(out_dir, "dashboard.html"), "w") as f:
        f.write(html)
    # the opportunity list as a file a consultant can hand over
    with open(os.path.join(out_dir, "opportunities.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Rank", "Opportunity", "Type", "Status", "Annual saving (USD)", "Spend in scope (USD)",
                    "Best qualified supplier", "Plant", "Target price per unit", "What to do", "Caution"])
        for i, o in enumerate(data["opportunities"], 1):
            w.writerow([i, o["title"], o["type_label"], "Ready to act" if o["readiness"] == "READY" else "Needs review",
                        round(o["saving"]), round(o["spend"]), o.get("best_supplier_name", ""), o.get("best_site", ""),
                        o.get("best_price", ""), o.get("action", ""), o.get("caution") or ""])
    return data
