"""Score the tool against the answer key: python3 score.py <data folder>

This is the ONLY file that reads data/answer_key. The tool itself (run.py and engine/)
never does. A real client has no answer key; we have one because we wrote the data,
and it lets us say how much of what was planted the tool actually found.
"""
import csv
import json
import os
import sys

from run import build


def rd(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main(data_dir):
    db, secs = build(data_dir)
    K = os.path.join(data_dir, "answer_key")
    P = {"Dayton": "A", "El Paso": "B"}
    q = lambda s: db.execute(s).fetchall()
    i2c = {(r["plant"], r["item_or_sku"]): r["canonical_id"] for r in rd(f"{K}/key_item_to_canonical.csv")}
    summary = json.load(open(f"{K}/key_summary.json"))
    out = {"build_seconds": round(secs, 1)}

    # --- links ---------------------------------------------------------------------------
    for name, table, keyfile, kcols in (
            ("po_lines", "po_link", "key_po_line_truth.csv", ("po_number", "po_line")),
            ("invoice_lines", "invoice_link", "key_invoice_line_truth.csv", ("invoice_no", "inv_line"))):
        truth = {(r["plant"],) + tuple(r[c] for c in kcols): r for r in rd(f"{K}/{keyfile}")}
        n = part_ok = bucket_ok = rolled = 0
        for site, a, b, item, bucket in q(f"SELECT site, {kcols[0]}, {kcols[1]}, item, bucket FROM {table}"):
            t = truth[(P[site], a, b)]
            mine = i2c.get((P[site], item)) if item else None
            n += 1
            if mine == (t["canonical_id"] or None):
                part_ok += 1
            elif "SUPERSEDED_ITEM" in t["mismatch_causes"]:
                rolled += 1      # old two-piece lid rolled up to the new lid: intended, the key keeps them apart
            if bucket == t["true_bucket"] or (bucket == "PURPOSE_UNKNOWN" and "PURPOSE_UNTAGGED" in t["mismatch_causes"]):
                bucket_ok += 1
        out[name] = {"lines": n, "right_part": part_ok, "rolled_up_by_design": rolled,
                     "wrong_part": n - part_ok - rolled, "right_purpose": bucket_ok}

    # --- same parts, near-identical parts ----------------------------------------------------
    key_same = {(r["dayton_item"], r["elpaso_part"]) for r in rd(f"{K}/key_cross_plant_same_part.csv")}
    mine_same = set(q("SELECT item_a, item_b FROM part_pair WHERE relation='SAME' AND site_a='Dayton' AND site_b='El Paso'"))
    fam = rd(f"{K}/key_near_duplicate_families.csv")
    g_of = {(s, i): g for s, i, g in q("SELECT site, item, group_id FROM part_group")}
    std_of = {}
    for r in fam:
        if r["relation_to_family_standard"] == "STANDARD":
            std_of.setdefault(r["family_id"], g_of.get((r["plant"], r["item"])))
    rel = {}
    for a, b, relation in q("SELECT group_a, group_b, relation FROM group_pair"):
        rel[(a, b)] = rel[(b, a)] = relation
    found = {"CLOSE_SPEC_NEEDS_ENGINEERING_REVIEW": [0, 0], "DO_NOT_MERGE": [0, 0], "SAME_PART_DUPLICATE_NUMBER": [0, 0]}
    for r in fam:
        k = r["relation_to_family_standard"]
        if k not in found:
            continue
        found[k][1] += 1
        g = g_of.get((r["plant"], r["item"]))
        if k == "SAME_PART_DUPLICATE_NUMBER":
            twins = q(f"SELECT COUNT(*) FROM part_group WHERE group_id='{g}' AND site='{r['plant']}' AND item IN (SELECT item FROM parts WHERE status='ACTIVE')")[0][0]
            found[k][0] += twins >= 2
        else:
            want = "CLOSE_SPEC" if k.startswith("CLOSE") else "DO_NOT_MERGE"
            found[k][0] += rel.get((g, std_of[r["family_id"]])) == want
    dup_items = {r["item"] for r in fam if r["relation_to_family_standard"] == "SAME_PART_DUPLICATE_NUMBER"}
    out["parts"] = {
        "cross_plant_same_part": {"planted": len(key_same), "found": len(key_same & mine_same),
                                  "wrongly_merged": len([p for p in mine_same - key_same if not (set(p) & dup_items)])},
        "duplicate_numbers": dict(zip(("found", "planted"), found["SAME_PART_DUPLICATE_NUMBER"])),
        "close_spec": dict(zip(("found", "planted"), found["CLOSE_SPEC_NEEDS_ENGINEERING_REVIEW"])),
        "do_not_merge": dict(zip(("found", "planted"), found["DO_NOT_MERGE"])),
        "legacy_crossref_errors_flagged": q("SELECT COUNT(*) FROM legacy_xref_check WHERE verdict='CONFLICT'")[0][0],
    }

    # --- money ----------------------------------------------------------------------------
    sav = rd(f"{K}/key_savings_opportunities.csv")
    key_total = sum(float(r["total_sized_saving_12m_usd"]) for r in sav)
    key_review = sum(float(r["saving_after_engineering_review_usd"]) for r in sav)
    mine = dict(q("SELECT opp_type, SUM(saving) FROM opportunity GROUP BY 1"))
    leak = sum(float(r["paid_above_quote_usd"]) for r in rd(f"{K}/key_quote_to_invoice_leakage.csv"))
    total, plain, linked = q("""SELECT SUM(amount),
        SUM(CASE WHEN EXISTS (SELECT 1 FROM bom b WHERE b.site=i.site AND b.child=i.item_raw) THEN amount ELSE 0 END),
        SUM(CASE WHEN item IS NOT NULL THEN amount ELSE 0 END) FROM invoice_link i""")[0]
    out["money"] = {
        "invoiced_spend": round(total),
        "plain_join_share": round(plain / total, 4), "tool_linked_share": round(linked / total, 4),
        "consolidation_savings": {"planted": round(key_total),
                                  "found": round(mine.get("PRICE_ALIGNMENT", 0) + mine.get("CLOSE_SPEC", 0)),
                                  "of_which_needs_review_planted": round(key_review),
                                  "of_which_needs_review_found": round(mine.get("CLOSE_SPEC", 0))},
        "quote_leakage": {"planted": round(leak), "found": round(mine.get("QUOTE_LEAKAGE", 0)),
                          "note": "The key counts from March 2026; the tool counts every invoice above quote"},
        "across_the_board_increase_found": round(mine.get("SUPPLIER_INCREASE", 0)),
        "spend_with_unqualified_suppliers": {"found": round(q("SELECT SUM(spend) FROM unqualified_spend")[0][0])},
        "air_freight_already_spent": {"found": round(q("SELECT SUM(amount) FROM expedite_spend")[0][0])},
    }
    key_cost = {(r["plant"], r["model"]): float(r["purchased_material_usd"]) for r in rd(f"{K}/key_modeled_cost_per_unit.csv")}
    out["material_cost_per_unit"] = [
        {"site": s, "model": m, "tool": round(v, 3), "key": key_cost.get((s, m)), "lines_without_price": n}
        for s, m, v, n in q("SELECT site, model, material, lines_without_price FROM product_cost")]
    out["watchlist"] = dict(zip(
        ("open_orders", "on_superseded_numbers", "confirmed_14_days_late", "under_an_open_notice"),
        q("SELECT COUNT(*), SUM(on_old_number), SUM(days_slip>=14), SUM(open_notices IS NOT NULL) FROM open_order_x")[0]))
    json.dump(out, open("out/scorecard.json", "w"), indent=2)
    # rewrite the dashboard so its "Test results" page shows this scorecard
    from engine import export
    export.write_outputs(db, "out", scorecard=out)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
