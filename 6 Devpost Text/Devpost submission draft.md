# Devpost submission draft: Tether

Draft for Nathaniel to paste into Devpost. Standard Devpost sections; reshape once we see the real form.
All numbers come from the synthetic Larkfield dataset and `product/out/scorecard.json`.

---

## Project name

Tether

## Tagline (Devpost limit is about 200 characters)

Ties every BOM part to the POs and invoices behind it, across ERPs, and tells a Kearney team which savings are safe to promise in week one.

## Track

Corporate Track 3: BOM Cost Linkage

## Team

Nathaniel Sugijanto, Caleb Brownlee

---

## Inspiration

Kearney's mentors told us BOM cost linkage is the work that costs them the most time. It applies to any company that makes a physical product, and product and supply chain teams have never had a good way to tie the bill of materials to what was actually spent. Today it is done by hand: paper part lists, Excel lookups, and 20 or more analyst-days to tie one product family (Velocity's estimate, which our Kearney mentor called conservative). Clients do not want a system overhaul to fix it.

The hard part is not the join. Two plants on two ERPs call the same part by different numbers, parts get superseded, suppliers use their own numbers, invoices carry free text, and some parts look alike but must never be merged. A plain part-number join quietly drops the spend that matters most.

## What it does

Tether takes a client's existing exports (BOMs, item masters, POs, invoices, receipts, quotes) from each plant and:

1. **Ties spend to parts, parts to BOMs, BOMs to finished products.** It follows a fixed matching order: exact number, replaced number, service part, supplier part number, quote reference, then cleaned description. Every link keeps its method, confidence and reason.
2. **Decides which part numbers are the same part.** Same part (merge), close spec (send to engineering), or look-alike (do not merge).
3. **Sizes the savings the links make visible,** and splits them into **safe to promise** and **needs review**: price alignment to the best qualified supplier, the standard part inside near-identical families, invoices above the awarded quote, and across-the-board price increases.
4. **Says no when it should.** It will not recommend an unqualified supplier, will not merge look-alike parts, and shows unresolved spend instead of guessing.
5. **Builds one dashboard,** organized by who acts: Start here, linkage health, product cost per unit, opportunities with evidence, a watchlist (open orders on superseded parts, late confirmations, supplier change notices), and a Platform view that shows the common core and add-on modules of a product family.

**On our synthetic demo company** (Larkfield Home Appliances: 4 coffee maker models, 2 plants on 2 different ERPs, $7.14M invoiced spend, 3,422 PO and invoice lines):

- 95.4% of spend tied to a BOM, against 86.2% with a plain part-number join
- 0 lines tied to the wrong part, out of 3,422
- $230,096 a year safe to promise, plus $59,609 that needs engineering or contract review
- A person checks 48 of 1,941 invoice lines; the rest need no human input
- About 4 seconds to run

Because the data is synthetic, these numbers are an upper bound: we wrote the matching rules while looking at this dataset. On real client files the rules need tuning in the first days and the review queue will be longer.

## How we built it

- **Research with Velocity first.** We used Kearney's Velocity AI for eight research prompts before writing any code: the BOM-to-spend linkage workflow and effort by step, why BOM part numbers do not match spend records and how analysts resolve each cause, how to allocate shared-part spend to products, which savings analyses follow once spend is linked, and what existing tools do and miss. Velocity's list of mismatch causes became Tether's matching order, and its savings analyses became the opportunity types.
- **Checked Velocity against its sources.** We opened every source Velocity cited. About half of its specific figures held up and half did not, so the pitch uses only the confirmed ones. Every input is logged by source (Velocity answers, mentor notes, our own data) in a decision log.
- **Mentor input shaped the product.** Kearney mentors told us the status quo is manual, clients want no overhaul, the biggest mismatches are superseded parts and make-versus-buy changes, full cost matters, and lead times are the biggest operational issue. Each of those is a feature: supersession matching, make-or-buy flags, full cost per unit, and the watchlist.
- **Synthetic data with an answer key.** Kearney cannot share client data, so we generated a realistic two-plant, two-ERP dataset with 37 planted problems (cross-plant duplicates, superseded parts, near-identical specs, look-alikes, quote leakage, price increases) and a separate answer key. The tool never reads the answer key; a separate scoring script does.
- **Stack.** Python and SQLite with readable SQL for each step (load, link, prices, product roll-up, savings, watchlist). One mapping file says which client column feeds which common field, so a new ERP needs a new mapping, not new code. The output is a single HTML dashboard with the data inside it. No AI at run time, nothing to install, and the client's data never leaves their machine.

## Challenges we ran into

- **No real data.** We had to build a dataset hard enough to be honest: two ERPs with different column names, units and part numbering, and traps a plain join falls into.
- **Knowing when not to match.** Matching more lines is easy; matching them without a single wrong link is the hard part. Look-alike parts that differ on one spec (a temperature rating, a wattage) had to stay apart.
- **AI citations that did not hold up.** Roughly half of the specific figures from our AI research were wrong or not at the cited source, so we checked everything before it went on a slide.
- **Scope.** We chose to do one thing well, the week-one tie and a savings list a team can stand behind, rather than rebuild a procurement platform.

## Accomplishments that we're proud of

- 0 wrong links across 3,422 PO and invoice lines, scored against an answer key the tool never sees
- Found all 27 parts that sit at both plants under unrelated numbers, all 7 close-spec parts, and kept all 3 look-alikes apart
- Found $221,942 of the $221,928 in planted consolidation savings
- A savings list where every dollar traces back to invoices, with an owner for each action
- A Platform view that turns the same links into the first step of product platforming

## What we learned

- The value is not the link, it is a savings number a consultant can safely promise to a client.
- An AI research tool is a fast starting point and an unreliable final source; checking citations changed what we were willing to say.
- Setup is judgment work. Column mapping and rule tuning stay with an analyst: a few days to set up, 4 seconds to run.

## What's next for Tether

- Validate it in the shadow of live engagements, using the team's manual tie as the answer key to see whether accuracy holds on real data.
- Add mappings for more ERPs and tune the rules on real client exports.
- Extend the Platform view into a full core-plus-modules analysis for product platforming.
- Feed the linked cost baseline into variance reduction and should-cost work.

## Built with

Python, SQLite, SQL, HTML, JavaScript, Kearney Velocity AI, Claude (AI coding and research assistant)

---

## Files and links to attach

| What | Where |
|---|---|
| Pitch deck (5-part, 25 slides with appendix) | `Pitch Deck/Tether pitch deck (5-part).pptx` (export a PDF too if Devpost wants one) |
| Working dashboard | `Product/Tether dashboard.html` (one file, opens by double-click) |
| Source code | `Product/tool/` or zip it; Devpost often asks for a GitHub link |
| Synthetic data | `Data Gathering/Synthetic Data - Coffee Maker/larkfield_coffee_synthetic_data.zip` |
| Screenshots for the image gallery | dashboard page screenshots (Start here, Opportunities, Platform view) |
| Demo video | only if required |
