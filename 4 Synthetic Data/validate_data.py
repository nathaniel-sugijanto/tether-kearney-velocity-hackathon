#!/usr/bin/env python3
"""Consistency checks for the coffee maker synthetic dataset. Run: python3 validate_data.py <data_dir>"""
import csv, json, os, sys
from collections import defaultdict
D = sys.argv[1] if len(sys.argv) > 1 else "data"
PA, PB, SH, AK = (os.path.join(D, s) for s in ("plant_A_dayton_atlas", "plant_B_elpaso_meridian", "shared", "answer_key"))


def rd(*p):
    with open(os.path.join(*p), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


FAILS = []; N = [0]


def check(name, cond, detail=""):
    N[0] += 1
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


f = lambda x: float(x) if x not in ("", None) else 0.0
summary = json.load(open(os.path.join(AK, "key_summary.json")))
for rel, n in summary["file_row_counts"].items():
    if not os.path.exists(os.path.join(D, rel)):
        check(f"file exists {rel}", False)
check("every file listed in the summary exists with the stated row count",
      all(len(rd(D, rel)) == n for rel, n in summary["file_row_counts"].items()))

A_items = rd(PA, "A_item_master.csv"); B_items = rd(PB, "B_Part_Master.csv")
a_no = {r["ITEM_NO"] for r in A_items}; b_no = {r["Part Number"] for r in B_items}
check("A item numbers unique", len(a_no) == len(A_items)); check("B part numbers unique", len(b_no) == len(B_items))
A_bom = rd(PA, "A_bom_parent_child.csv"); B_bom = rd(PB, "B_Indented_BOM.csv")
check("A BOM parents and components are in the item master", all(r["PARENT_ITEM"] in a_no and r["COMPONENT_ITEM"] in a_no for r in A_bom))
check("B BOM parts are in the part master", all(r["Top Model"] in b_no and r["Part (indented)"].lstrip(".") in b_no for r in B_bom))
A_po = rd(PA, "A_po_lines.csv"); B_po = rd(PB, "B_PO_Detail.csv")
check("A PO line keys unique", len({(r["PO_NUMBER"], r["PO_LINE"]) for r in A_po}) == len(A_po))
check("B PO line keys unique", len({(r["PO Number"], r["Ln"]) for r in B_po}) == len(B_po))
check("A PO items, when given, are in the item master", all(r["ITEM_NO"] in a_no for r in A_po if r["ITEM_NO"]))
check("B PO parts, when given, are in the part master", all(r["Part Number"] in b_no for r in B_po if r["Part Number"]))
check("A PO amount = quantity x price", all(abs(f(r["ORDER_QTY"]) * f(r["NET_PRICE"]) - f(r["LINE_AMOUNT"])) < 0.02 for r in A_po))
check("B PO amount = quantity x price / per", all(abs(f(r["Order Qty"]) * f(r["Unit Price"]) / f(r["Per"]) - f(r["Ext Amount"])) < 0.02 for r in B_po))
a_sup = {r["SUPPLIER_ID"] for r in rd(PA, "A_supplier_master.csv")}; b_sup = {r["Vendor"] for r in rd(PB, "B_Vendors.csv")}
check("A PO suppliers are in the supplier master", all(r["SUPPLIER_ID"] in a_sup for r in A_po))
check("B PO vendors are in the vendor list", all(r["Vendor"] in b_sup for r in B_po))
A_inv = rd(PA, "A_invoice_lines.csv"); B_inv = rd(PB, "B_AP_Invoice_Lines.csv")
check("A invoice line keys unique", len({(r["INVOICE_NO"], r["INV_LINE"]) for r in A_inv}) == len(A_inv))
check("B invoice line keys unique", len({(r["Invoice #"], r["Inv Line"]) for r in B_inv}) == len(B_inv))
check("all invoices fall inside the 12-month extract", all("2025-11-01" <= r["INVOICE_DATE"] <= "2026-10-31" for r in A_inv))
po_truth = rd(AK, "key_po_line_truth.csv"); inv_truth = rd(AK, "key_invoice_line_truth.csv")
check("one truth row per PO line", len(po_truth) == len(A_po) + len(B_po))
check("one truth row per invoice line", len(inv_truth) == len(A_inv) + len(B_inv))
canon = {r["canonical_id"]: r for r in rd(AK, "key_canonical_parts.csv")}
check("truth rows point at known canonical parts", all(r["canonical_id"] in canon for r in po_truth + inv_truth if r["canonical_id"]))
po_keys = {("A", r["PO_NUMBER"], r["PO_LINE"]): f(r["ORDER_QTY"]) for r in A_po}
po_keys.update({("B", r["PO Number"], r["Ln"]): f(r["Order Qty"]) for r in B_po})
check("every invoice truth row names an existing PO", all((r["plant"], r["true_po_number"], r["true_po_line"]) in po_keys for r in inv_truth if r["true_po_line"]))
i2c = rd(AK, "key_item_to_canonical.csv")
mapped = {(r["plant"], r["item_or_sku"]) for r in i2c}
check("every item number in both masters maps to a canonical part", all(("A", x) in mapped for x in a_no) and all(("B", x) in mapped for x in b_no))
# receipts and open orders
A_gr = rd(PA, "A_goods_receipts.csv"); B_gr = rd(PB, "B_Receipts.csv"); A_op = rd(PA, "A_open_po_lines.csv"); B_op = rd(PB, "B_Open_PO_Report.csv")
recd = defaultdict(float)
for r in A_gr:
    recd[("A", r["PO_NUMBER"], r["PO_LINE"])] += f(r["RECEIVED_QTY"])
for r in B_gr:
    recd[("B", r["PO Number"], r["Ln"])] += f(r["Qty Recd"])
check("receipts reference existing PO lines", all(k in po_keys for k in recd))
openq = {("A", r["PO_NUMBER"], r["PO_LINE"]): f(r["OPEN_QTY"]) for r in A_op}; openq.update({("B", r["PO Number"], r["Ln"]): f(r["Open Qty"]) for r in B_op})
check("open lines reference existing PO lines", all(k in po_keys for k in openq))
nonprod = {(r["plant"], r["po_number"], r["po_line"]) for r in po_truth if r["true_bucket"] == "NON_PRODUCT"}
check("received + open = ordered on every material PO line", all(abs(recd.get(k, 0) + openq.get(k, 0) - q) < 0.01 for k, q in po_keys.items() if k not in nonprod))
# quotes
A_q = rd(PA, "A_rfq_quotes.csv"); B_q = rd(PB, "B_Quotes.csv")
aw = defaultdict(int)
for r in A_q:
    aw[("A", r["RFQ_NO"])] += r["AWARDED"] == "Y"
for r in B_q:
    aw[("B", r["RFQ"])] += r["Award"] == "Awarded"
check("exactly one awarded quote per RFQ", all(v == 1 for v in aw.values()))
check("quoted items are in the masters", all(r["ITEM_NO"] in a_no for r in A_q) and all(r["Part"] in b_no for r in B_q))
# shared
bv = rd(SH, "build_volumes.csv"); fc = rd(SH, "build_forecast.csv")
check("build volumes: 6 plant-model lines x 12 months", len(bv) == 72); check("forecast: 6 plant-model lines x 24 months", len(fc) == 144)
notices = rd(SH, "supplier_change_notices.csv"); nkey = rd(AK, "key_supplier_change_notices.csv")
check("every supplier notice has an answer key row", {r["notice_id"] for r in notices} == {r["notice_id"] for r in nkey})
xref = rd(SH, "legacy_part_crossref_2023.csv")
check("legacy cross-reference rows name real item numbers", all(r["dayton_item"] in a_no and r["elpaso_part"] in b_no for r in xref))
truth_pair = {(r["plant"], r["item_or_sku"]): r["canonical_id"] for r in i2c}
wrong = [r for r in xref if truth_pair[("A", r["dayton_item"])] != truth_pair[("B", r["elpaso_part"])]]
check("legacy cross-reference holds exactly one wrong row (planted)", len(wrong) == 1)
# near-duplicate families
fam = rd(AK, "key_near_duplicate_families.csv")
fams = defaultdict(list)
for r in fam:
    fams[r["family_id"]].append(r)
check("every near-identical family has a standard part", all(any(r["relation_to_family_standard"] == "STANDARD" for r in v) for k, v in fams.items() if k.startswith("FAM")))
rels = {r["relation_to_family_standard"] for r in fam}
check("all three outcomes are present (same part, close spec, do not merge)",
      {"SAME_PART_DUPLICATE_NUMBER", "CLOSE_SPEC_NEEDS_ENGINEERING_REVIEW", "DO_NOT_MERGE"} <= rels)
spec = lambda r: (r["material"], r["dimensions"], r["rating"], r["mfr_part_no"])
ok = True
for k, v in fams.items():
    if not k.startswith("FAM"):
        continue
    std = [r for r in v if r["relation_to_family_standard"] == "STANDARD"][0]
    ok &= all(spec(r) != spec(std) for r in v if r["relation_to_family_standard"] != "STANDARD")
check("every non-standard family member differs from its standard in a visible spec field", ok)
check("family items are in the masters", all((r["item"] in a_no) if r["plant"] == "Dayton" else (r["item"] in b_no) for r in fam))
# savings
opp = rd(AK, "key_savings_opportunities.csv")
check("savings rows add up to the summary total", abs(sum(f(r["total_sized_saving_12m_usd"]) for r in opp) - summary["sized_supplier_and_part_savings_total_usd"]) < 1)
t = summary["true_savings_by_opportunity_type_usd"]
check("savings by type add up to the total", abs(t["same_part_price_alignment_across_suppliers_and_plants"] + t["near_identical_family_standard_part_price_alignment"] + t["near_identical_family_after_engineering_review"] - summary["sized_supplier_and_part_savings_total_usd"]) < 1)
ids = [c for r in opp for c in r["canonical_ids"].split("; ")]
check("no part is counted in two savings rows", len(ids) == len(set(ids)))
pbs = rd(AK, "key_price_by_part_and_supplier.csv")
check("best qualified supplier is always a qualified one", all(any(p["supplier_name"] == r["best_qualified_supplier"] and p["supplier_qualified_for_this_part"] == "Y" for p in pbs) for r in opp))
att = rd(AK, "key_open_orders_needing_attention.csv")
check("open orders on superseded numbers are planted", sum(r["reason"] == "ORDERED_ON_SUPERSEDED_NUMBER" for r in att) == 2)
mvb = rd(AK, "key_make_vs_buy.csv")
check("make versus buy: buy price sits between material plus labor and full make cost", all(f(r["make_material_plus_labor_usd"]) < f(r["buy_price_usd"]) < f(r["make_full_cost_usd"]) for r in mvb))
cost = rd(AK, "key_modeled_cost_per_unit.csv")
check("full cost = material + labor + overhead", all(abs(f(r["purchased_material_usd"]) + f(r["labor_usd"]) + f(r["overhead_usd"]) - f(r["modeled_full_cost_usd"])) < 0.002 for r in cost))
tot = sum(f(r["amount_usd"]) for r in inv_truth)
check("invoice truth total matches the summary", abs(tot - summary["invoiced_spend_total_usd"]) < 1)

# what a plain join gets, against the truth
a_comp = {r["COMPONENT_ITEM"] for r in A_bom}; b_comp = {r["Part (indented)"].lstrip(".") for r in B_bom}
naive = sum(f(r["LINE_AMOUNT"]) for r in A_inv if r["ITEM_NO"] in a_comp) + sum(f(r["Amount"]) for r in B_inv if r["Part"] in b_comp)
truth = sum(f(r["amount_usd"]) for r in inv_truth if r["true_bucket"] in ("PRODUCTION", "SPARE", "WARRANTY"))
prod = sum(f(r["amount_usd"]) for r in inv_truth if r["true_bucket"] == "PRODUCTION")
spare_on_prod = sum(f(r["amount_usd"]) for r in inv_truth if r["true_bucket"] in ("SPARE", "WARRANTY") and "SERVICE_SKU" not in r["mismatch_causes"])
print()
print(f"Invoiced spend in the extract:                          ${tot:,.0f}")
print(f"Plain join (invoice item number is on that plant's BOM): {naive / tot:.1%} of spend")
print(f"Truly linkable to a part (answer key):                   {truth / tot:.1%} of spend")
print(f"  of which production:                                   {prod / tot:.1%}")
print(f"Cannot be identified from the data:                      {summary['share_of_spend_unresolvable']:.1%}")
print(f"Not product spend (freight, testing, tooling, supplies): {summary['share_of_spend_non_product']:.1%}")
print(f"Spare and warranty spend booked on production numbers:   ${spare_on_prod:,.0f}")
print(f"Sized savings (answer key):                              ${summary['sized_supplier_and_part_savings_total_usd']:,.0f} ({summary['sized_savings_pct_of_invoiced_spend']:.1%} of spend)")
print()
print(f"{N[0] - len(FAILS)} of {N[0]} checks passed" if FAILS else f"ALL {N[0]} CHECKS PASSED")
sys.exit(1 if FAILS else 0)
