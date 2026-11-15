# Synthetic demo data, coffee maker edition (source D2)

Built Saturday 2026-11-14 for the Track 3 (BOM Cost Linkage) demo. This replaces the pump dataset (source D1) as the demo data. The pump dataset is kept as an archive in `Synthetic Data` and is not deleted.

**Everything here is invented.** The company (Larkfield Home Appliances), the product line (BrewLine drip coffee makers), every supplier, part, price and date are made up. No Kearney or client data is in it. Every headline number below is a design choice of ours, not a finding about the real world. On a slide, say "in our synthetic dataset".

## Why we rebuilt it

Two mentor comments drove the change (see `Mentor Notes/M3.md`):

1. The demo product should be simple, like a consumer product or a coffee maker, with data across different suppliers.
2. Real data has many parts whose specs are almost the same, so the data must contain those, so the tool can show supplier consolidation and cost savings.

The pump data had identical parts under two numbers and look-alikes that must not be merged, but nothing in between, and mostly one supplier per commodity per plant. This dataset fixes both.

## The company in one paragraph

Larkfield makes four drip coffee makers: BL-5 (5-cup, switch), BL-12 (12-cup, switch), BL-12P (12-cup, programmable) and BL-12T (12-cup, programmable, thermal carafe). Dayton, Ohio builds BL-5, BL-12 and BL-12P on a system called Atlas. El Paso, Texas (acquired in 2023) builds BL-12, BL-12P and BL-12T on a system called Meridian. The two plants use unrelated part numbers, different column names, different date formats and different units of purchase. The extract covers 12 months, November 2025 to October 2026: 418,010 coffee makers, 1,481 PO lines, 1,941 invoice lines and $7.14M of invoiced spend across 28 suppliers.

## What is in the folder

| Folder | What it is |
|---|---|
| `data/plant_A_dayton_atlas/` | Dayton's files: item master, BOM (parent and child rows with dates), PO lines, invoice lines, suppliers, item-to-supplier records, quotes, supersessions, unit conversions, receipts, open orders |
| `data/plant_B_elpaso_meridian/` | El Paso's files with the same content in a different layout, plus an indented BOM and a short make-to-buy change list |
| `data/shared/` | Build volumes, build forecast, labor and overhead standards, supplier change notices, service parts catalogue, warranty claims, the partial 2023 part cross-reference |
| `data/answer_key/` | The truth. The tool must never read this folder. It exists so we can score the tool |
| `generate_data.py` | Rebuilds every file. Same seed, same files |
| `validate_data.py` | 43 consistency checks, and the plain-join versus truth numbers |

The file names and columns match the pump dataset, so anything built against that one carries over. Three columns were added to both item masters: rating, compliance and dimensions. El Paso also has `B_Make_Buy_Changes.csv`, and `shared/` has `labor_and_overhead_standards.csv`.

## The headline numbers (all by design)

| Measure | Value |
|---|---|
| Invoiced spend in the extract | $7,142,785 |
| Spend a plain part-number join ties to a BOM | 86.2% |
| Spend that can truly be tied to a part | 95.4% |
| Spend that cannot be identified from the data | 1.8% |
| Spend that is not product (freight, testing, tooling, supplies) | 2.8% |
| Purchased parts found at both plants under unrelated numbers | 27, of which the old cross-reference covers 10 |
| Near-identical part families | 9 |
| Sized savings on supplier and part consolidation | $221,928 a year, 3.1% of spend |
| Spend with suppliers that lack a required qualification | $501,274 |
| Supplier change notices, and those with no completed action | 8, and 6 |
| Receipts on time | 71.0% overall; the two worst suppliers 28% and 41% |
| Open order lines confirmed two weeks or more late | 9 of 59 |

## What Shouvik asked for, and where it is

**Parts that are too similar.** `answer_key/key_near_duplicate_families.csv` holds nine families and gives each member one of three outcomes:

| Outcome | Meaning | Examples in the data |
|---|---|---|
| Same part, duplicate number | Merge the numbers | The M4 screw entered twice at Dayton; the 12-cup glass carafe entered twice at El Paso, each copy bought from a different supplier at a different price |
| Close spec, engineering review | Probably one part could serve, but an engineer must agree first | Power cord 0.9 m and 1.0 m; M3 screw 8 mm and 10 mm; silicone tube wall 1.5 and 1.6 mm; rubber foot 12.0 and 12.5 mm; rocker switch 10 A and 16 A; master carton board ECT-29 and ECT-32; thermal fuse from two makers at the same rating |
| Do not merge | Looks the same, must stay separate | Thermal fuse 216 C and 229 C; heating element 900 W and 1000 W; wire harness with and without the warming plate lead |

The 229 C fuse is the sharpest case. It looks identical to the 216 C fuse, it is a safety part, and the old 2023 cross-reference wrongly links the two. A tool that merges on description alone fails here.

**Several suppliers per part.** Most commodities are bought from two suppliers at each plant, and from different suppliers across the plants, at prices 3% to 20% apart. `answer_key/key_price_by_part_and_supplier.csv` has the price each plant pays each supplier for each part.

**Supplier consolidation and cost savings.** `answer_key/key_savings_opportunities.csv` has one row per part or family with the suppliers today, the best qualified supplier, and the saving sized on 12 months of purchases. Each dollar is counted once. `key_summary.json` gives the true total by opportunity type, so the pitch can say how much of the planted savings the tool found:

| Opportunity type | True total (12 months) |
|---|---|
| Same part, several suppliers or two plants: align to the best qualified price | $183,662 |
| Near-identical family: align the standard part's own price | $7,650 |
| Near-identical family: move close-spec parts to the standard, after engineering review | $30,617 |
| Invoiced above the awarded quote at Dayton (4 parts, from March 2026) | $36,581 |
| Air freight already spent on late carafes | $36,002 |

The first three rows add up to the $221,928. The last two are separate findings and are not in that total.

**Why "cheapest" is not the answer.** Three things are planted so that a price-only tool gets it wrong:

- Three suppliers have no ISO 9001. One of them, a molder, also has no food-contact certification, yet it supplies water tanks and filter baskets and is the cheapest source. The savings key never picks an unqualified supplier.
- The two unqualified suppliers at El Paso are also the two that deliver late.
- The cheapest qualified source of the 12-cup glass carafe is the importer whose lead time doubled from 4 to 8 weeks in September 2026. That row carries a caution, and $40,836 of the sized savings depends on it.

## What Nick asked for, and where it is

| Nick's point | In the data |
|---|---|
| Superseded parts and supplier notifications | 8 supplier change notices in `shared/supplier_change_notices.csv`. One was handled properly. One explains a renumbering that El Paso never recorded. One reached Dayton only while El Paso uses the same thermostat. One reached El Paso only, which had stopped buying that element, while Dayton buys all of its elements from that supplier. Two name a material or product group and no part number. One concerns a part the company does not buy. Two open orders were placed on superseded numbers in late October |
| Make versus buy changes over a part's life | El Paso assembled the heater assembly in house until 2026-04-30 and buys it complete since 2026-05-01. Before the switch it bought the element, thermostat, fuses and bracket. After it, one assembly. `answer_key/key_make_vs_buy.csv` compares the two: buying is about $0.23 a unit cheaper than the full standard make cost and about $0.13 dearer than material plus labor, so the saving is real only if the overhead went away |
| Full cost, not only purchased parts | `shared/labor_and_overhead_standards.csv` gives assembly minutes, labor rates and overhead. `answer_key/key_modeled_cost_per_unit.csv` shows material, labor and overhead per coffee maker. Full cost runs from $18.33 (Dayton BL-5) to $29.70 (El Paso BL-12T), with purchased material at 71% to 83% of it |
| Lead times | Receipts carry promised and actual dates. Open orders carry promised and confirmed dates. The carafe importer's lead time doubles in September, three open carafe orders are confirmed about four weeks late, and the air freight to cover it is in the PO lines |
| Forecast versus actual | `shared/build_forecast.csv` has the FY26 plan and the FY27 plan. The thermal model ran 25% above plan and the 5-cup 16% below. The FY27 plan implies $7.62M of purchased material |
| Duplicates are low-hanging fruit | The two duplicate numbers above, plus the 27 cross-plant same parts |

## What makes the tie hard (the mismatch causes)

All 37 planted cases are listed in `answer_key/key_planted_cases.csv` with where to look and what the tool should do. In short: unrelated part numbers at the two plants; a partial and partly wrong legacy cross-reference; distributor part numbers only; superseded numbers, one to one, many to one, and one with no record; boxes of 1,000 against a price per 1,000, rolls against feet against metres, and one conversion missing; the make-to-buy switch; a packaging kit; spares on service numbers and on production numbers; free text that can be resolved, free text that points at a quote, and free text that cannot be resolved; freight and other non-product spend; split invoices, missing PO references, credit notes and timing.

`answer_key/key_po_line_truth.csv` and `key_invoice_line_truth.csv` give, for every line, the true part, the true bucket, the causes and the match method a tool would need.

## How to rebuild and check

```
python3 generate_data.py data
python3 validate_data.py data
```

The generator gives the same files on every run. This was tested under five different Python hash seeds, because the pump generator once failed on exactly that.

## Honest limits

- The savings are sized on price alone at the supplier's current plant. Freight from a Dayton-area supplier to El Paso, capacity, tooling moves and minimum orders are not modeled. A real case would net those off.
- "Qualified" is a simple rule: ISO 9001, plus the certification the commodity needs (food contact, UL, FDA). Real supplier approval has more to it.
- Labor and overhead are flat standards per plant. Full cost here means purchased material plus those standards. Logistics, warranty and tooling amortization are not in it.
- The spec fields are short text. Real drawings, tolerances and GD&T are richer. Tolerance classes are given for molded and stamped parts only.
- The product is deliberately simple, about 30 parts per coffee maker. That is the point of the rebuild, and it also means the long-tail complexity of a real client is not represented. The pump archive is closer to that.
- One company, two plants, one currency.
