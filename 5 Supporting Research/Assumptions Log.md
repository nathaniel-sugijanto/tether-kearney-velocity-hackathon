# Assumptions Log

Note (2026-11-13 11:19 PM CT): we switched to Track 3, BOM Cost Linkage. Sections A, B and D mostly still apply. Section C (core vs module method) is parked as the next-step story. Track 3 assumptions get added as section F when the new Velocity answers arrive.

Every assumption we are building on that is not confirmed by a source we verified. Tag shows where it came from. Status: Open (unchecked), Asked (put to Kearney), Confirmed, Rejected.
Ask-Kearney column: Y = worth a mentor's time, N = we can decide it ourselves.
Linked file: `Questions for Kearney.md`. Q numbers in section F match the current question list (reworded for Track 3 on 2026-11-14). Q numbers in sections A to E were assigned before the rewording and may be off by topic; section F is what to check with mentors first.

## A. About the client and the problem

| # | Assumption | Source | Why it matters | Ask Kearney? | Status |
|---|---|---|---|---|---|
| A1 | The typical client is a discrete manufacturer (industrial machinery or equipment), not process manufacturing. | V1 default; our choice | Sets the demo industry and every example | Y (Q4) | Open |
| A2 | An engagement starts with one bounded product family, not the whole portfolio. | V1 | Sets demo scale (8 to 15 machine variants) | Y (Q4) | Open |
| A3 | Clients send BOMs, orders, cost and spend as CSV/XLSX exports from PLM, ERP, and CRM/CPQ, plus PDFs, CAD, and free text. | V1 (Velocity inference, not Kearney data) | Decides which file types the tool must accept | Y (Q2) | Open |
| A4 | Sales order history is available alongside BOMs and can be linked to configurations. | Our brainstorm, from Nathaniel's SD experience | The whole demand-weighting idea depends on it | Y (Q2) | Open |
| A5 | A long tail of rarely ordered variants carries a large share of part count and little revenue. | Our brainstorm (Nathaniel's SD experience) | The headline example of an obvious target | Y (Q3) | Open |
| A6 | PERLab's biggest pain with new clients is tying BOMs to spend data (Track 3). The rep never said so outright; he only went deep on the BOM track and called it painstaking. Earlier notes wrongly recorded Track 1 as the stated top pain. | K1, Nathaniel's observation at kickoff; inference | Decides which track we enter | Y (Q1) | Confirmed by Kearney mentor (M1, 2026-11-14): Track 3 costs them the most time |
| A7 | The tool's user is a PERLab consultant or analyst, not the client's engineers. | Our choice | Sets the interface and how we explain results | Y (Q5) | Open |

## B. About effort and time saved

| # | Assumption | Source | Why it matters | Ask Kearney? | Status |
|---|---|---|---|---|---|
| B1 | The first four weeks take about 21 to 39 analyst-days for one family. | V1, Velocity's own estimate, not Kearney data | Our time-saved number | Y (Q6) | Open |
| B2 | About 12 to 22 of those days (roughly 55 to 60%) go to demand coding, BOM expansion and comparison, and cross-system reconciliation. | V1 ranges; the sum and share are our arithmetic | Which steps the tool targets | Y (Q6) | Open |
| B3 | The tool can remove most of that grind but not the engineer review in function and interface mapping. | Our judgment, supported by V1 and V2 | Honest claim about scope | Y (Q6) | Open |
| B4 | Client data extraction time is outside our estimate and outside the tool. | V1 | Avoids overclaiming | N | Open |

## C. About the method

| # | Assumption | Source | Why it matters | Ask Kearney? | Status |
|---|---|---|---|---|---|
| C1 | "Same part" has three levels: identical part, same design with different parameters, shared interface. | V1 (Velocity inference) | Match labels and confidence | Y (Q7) | Open |
| C2 | Core / module / unique is a recommendation for engineer review, not a final label. | V2 | Output design | Y (Q7) | Open |
| C3 | The four tests (requirement, interfaces, cost of sharing, demand and life cycle) are a fair way to judge a candidate. | V2, Velocity synthesis, not a PERLab checklist | Recommendation logic | Y (Q7) | Open |
| C4 | DCI, unit-weighted reuse coverage, part-number proliferation per function, and order coverage are the metrics we can compute from exports and defend. | V2 plus our choice | Metrics shown in the demo | Y (Q7) | Open |
| C5 | PCI needs engineering judgment on eligibility and attributes, so it is not our headline metric. | V2 | Why we skip it | N | Open |
| C6 | Order coverage (share of past orders the core plus modules could meet without new engineering) is the main test that the platform meets customer needs. | V2 operational measure; our choice | Answers the "meets all customers' needs" half of the prompt | Y (Q7) | Open |
| C7 | Matching can use size/shape, material/process, assembly method, and description text, with confidence scores and accept/reject. | V2 (PCI attributes) plus our design | Match logic | N | Open |

## D. About savings

| # | Assumption | Source | Why it matters | Ask Kearney? | Status |
|---|---|---|---|---|---|
| D1 | No universal savings percentage applies; each case is built component by component. | V3 | Savings screen design | Y (Q8) | Open |
| D2 | Direct material scenarios of 0%, 3%, 8% price reduction on addressable spend. | V3, Velocity's own estimate, not a benchmark | Demo inputs | Y (Q8) | Open |
| D3 | Inventory carrying cost of 20 to 30% of average inventory value per year. | V3, commonly cited planning range, no consensus | Inventory column | Y (Q8) | Open |
| D4 | Tooling avoidance between 0 and 100% of a duplicate tool's future replacement cost. | V3, Velocity estimate | Tooling column | N | Open |
| D5 | Savings are reported in three columns: recurring annual, one-time cost, working capital released. | V3 | Presentation | Y (Q8) | Open |
| D6 | Part-count reduction is a complexity metric, not dollars. | V3 | Avoids overclaiming | N | Open |
| D7 | Supplier, PO, engineering-hour, and one-time-cost inputs in the demo are our own labeled estimates. | Our choice | Demo credibility | Y (Q8) | Open |
| D8 | Savings are screening hypotheses to validate, not guaranteed results. | V1, Kearney framing | Tone of the pitch | N | Open |

## E. About the demo

| # | Assumption | Source | Why it matters | Ask Kearney? | Status |
|---|---|---|---|---|---|
| E1 | A synthetic machinery manufacturer with 8 to 15 machine variants and planted duplicates is acceptable for a demo. | Our brainstorm | The demo relies on it | Y (Q9) | Confirmed (M1 follow-up, 2026-11-14): Kearney can share no data, and Nathaniel reports Nick Lanzon said building synthetic data is exactly what we should do. The dataset built is a pump maker with 6 models at 2 plants, not 8 to 15 machine variants Changed 11/14 after M3: the demo product is now a coffee maker line with 4 models (source D2), because a second mentor asked for a simpler product. The pump data is archived. |
| E2 | Judges accept a deck plus a working demo, and no real client data is needed. | Kickoff; not confirmed | Scope | Y (Q10) | Open |
| E3 | We can use Velocity's outputs as inputs and cite them. | Hackathon requirement | Process story | N | Open |
| E4 | We can build three screens (upload, review matches, platform recommendation with savings) in the time available. | Our estimate | Feasibility | N | Open |

## F. Track 3, BOM Cost Linkage

| # | Assumption | Source | Why it matters | Ask Kearney? | Status |
|---|---|---|---|---|---|
| F1 | Demo scope is one machinery product family including spare and warranty parts, across two plants on different ERP instances with their own part numbering, plus some uncoded or free-text spend. | Our choice, given to Velocity as the scope for V4 | Sets demo data and how hard the matching is | Y (Q2, Q4) | Open |
| F2 | A first pass linking BOMs to spend for one family takes about 20 to 40 analyst-days. | V4, Velocity's own estimate, not Kearney data | Our time-saved number | Y (Q6) | Partly confirmed (M2): Nick said 20 days for a full family sounds correct but depends on family size. Use 20 as the conservative figure and state the family size it refers to |
| F3 | Identity resolution, building the spend base, and building the product-side part list are the three heaviest steps (12 to 24 days, about 60%). | V4 ranking; share is our arithmetic | Which steps the tool targets | Y (Q1, Q6) | Open. Q1 confirmed the tie costs the most time (M1); the 60% share was not discussed (M2) |
| F4 | Clients can provide line-level PO and invoice extracts, not only a pre-aggregated spend cube. | V4 recommendation | Whether our input format is realistic | Y (Q2) | Partly (M1): PO and invoices exist and come after RFP/RFQ; line-level availability not confirmed |
| F5 | The same physical part commonly carries different part numbers at different plants, and a meaningful share of spend lines have no item ID. | V4 inference; our scope choice | The core matching problem we demo | Y (Q2) | Partly confirmed (M2): Nick said mismatched part numbers are a valid problem (wrong parts get quarantined) and that consumables like gaskets and bearings often have no part number |
| F6 | Spend is counted on invoiced net value, once, with production, spare, and warranty kept separate. | V4 recommendation | Spend totals and allocation | Y (Q8) | Partly (M2): returns and warranty are documented separately, often in Excel, and reconciled by finance later. Invoiced-net basis not discussed |
| F7 | PERLab would rather see matched versus unresolved coverage with an exception queue than a forced full match. | V4 recommendation | Output design and honesty of the claim | Y (Q5) | Open |
| F8 | A plant-aware crosswalk reviewed by engineers and buyers is the right bridge; the tool proposes links and people approve them. | V4 | Human-in-the-loop design | Y (Q5) | Open |
| F9 | The eight mismatch causes in V5 cover most of what PERLab sees, and no major cause is missing. | V5, built on SAP and Oracle documentation, not Kearney experience | Reason codes and planted demo cases | Y (Q2) | Confirmed (M2): Nick said all eight are valid. Biggest by magnitude are superseded parts and make versus buy |
| F10 | Clients' systems hold supporting records we can lean on: purchasing-info records, manufacturer part numbers, unit conversions, supersession tables, even if incomplete. | V5 (SAP documents these exist, not that clients maintain them) | How much the tool can resolve without people | Y (Q2) | Open |
| F11 | Identity matching and cost attribution are separate steps, and PERLab would want them reported separately. | V5, Velocity inference | Two-stage design | Y (Q7) | Open |
| F12 | Client systems are SAP or Oracle style. Velocity drew every system fact from those two vendors' documentation. | V5 sources | Demo file layouts; other ERPs may differ | Y (Q2) | Rejected (M1): mentor said go beyond SAP and work across ERPs |
| F13 | Allocating shared-part spend by BOM quantity x build volume is an acceptable proxy when production-order issue data is missing. | V6, Velocity's own calculation | The allocation method in the tool | Y (Q7) | Partly (M2): depends on data granularity. Kearney builds spend from a volume forecast and compares actuals against it; he did not reject BOM quantity times volume |
| F14 | Clients usually cannot give order-level material issue data in the first weeks, so a modeled cost is what PERLab works with. | Our assumption (V6 treats issue data as "best available", says nothing about how often it exists) | Whether "modeled" is the normal case or a weakness | Y (Q2) | Partly (M2): 'depends on how granular your data is and how well you track data' |
| F15 | "Financial impact of one BOM" in the prompt means direct purchased-material cost, not full unit cost with labor and overhead. | Our reading of the prompt; V6 boundary | Scope of what we claim | Y (Q8) | Rejected (M2): Nick said full cost. Our tool models purchased-material cost only, so we must present it as the material part of a full-cost baseline and say what is missing |
| F16 | Weighted purchase price per plant is the right price basis for the demo, with standard cost as an alternative. | V6 options; our choice | Cost and savings numbers | Y (Q8) | Open |
| F17 | Build volumes by product and plant are available from the client. | V6 formula input | Allocation needs them | Y (Q2) | Partly (M2): Kearney works from volume forecasts by product; availability from clients not stated |
| F18 | Roughly 70 to 80% value-weighted part match is enough to start screening for savings. | V7, Velocity's own working estimate, not a benchmark | The "ready to screen" marker in the tool | Y (Q7) | Open. Not answered in M2 |
| F19 | Same-part price gaps, volume consolidation, and duplicate parts are the analyses PERLab runs first once the data ties. | V7 framework | Which analyses we build | Y (Q8) | Partly confirmed (M2): duplicate parts are the low-hanging fruit. Nick added lead times as the biggest issue. Price gaps and consolidation were not ranked |
| F20 | Recent build volumes are an acceptable stand-in for future demand in savings screening. | Our simplification | Size of every savings figure | Y (Q8) | Challenged (M2): Kearney bases spend on a forecast (volume grows x% a year) and compares actuals to it. Add a growth input instead of assuming flat volumes |
| F21 | PERLab treats a screened price gap as a lead, not a saving, and would expect a status ladder to realized savings. | V7 recommendation | How we word savings in the pitch | Y (Q8) | Open |
| F22 | PERLab teams build this bridge today mostly with spreadsheets, SQL, and manual review, not with a dedicated tool. | V8 inference (Kearney's tool stack is undisclosed) | Whether our tool fills a real gap or duplicates something they have | Y (Q3) | Confirmed (M2): mature companies do it manually with paper forms ('J9s') and Excel, on systems Nick called 2005 tech |
| F23 | Spend-analytics and PLM cost tools do not already give PERLab an engineering-approved BOM-to-spend link on day one of an engagement. | V8 inference | Our positioning | Y (Q3) | Supported (M2): Nick described no dedicated tool; clients want less manual work without an overhaul |
| F24 | A refreshable bridge (re-run on new extracts, keep approved links) is valued over a one-time match. | V8 inference | Design effort on persistence | Y (Q5) | Open |
| F25 | Exceptions need different approvers by type (procurement, finance, engineering, service). | V8 inference | Review queue routing | Y (Q5) | Open |
| F26 | "gbmts" in the mentor notes means GD&T (geometric dimensioning and tolerancing). | Our reading of M1 | Part spec fields in the data model | Y | Confirmed by Nathaniel 2026-11-14: it was GD&T |
| F27 | RFQ and quote data is available alongside POs and invoices, and can be tied to part numbers. | M1 implies the process runs RFI to invoice; availability as data not stated | Quote to PO to invoice chain | Y | Open |
| F28 | A column-mapping step to a canonical model is an acceptable answer to "work across ERPs". | Our design response to M1 | ERP-agnostic claim | Y | Partly (M2): the direction is confirmed (plug into and retrofit old systems, no complete revamp). The column-mapping approach itself was not discussed |
| F29 | Supplier qualifications, ISO certifications, capabilities, lead times and MOQs matter to PERLab as context for cost comparison, not only as sourcing checklist items. | Our reading of M1 | How much of this we model | Y | Confirmed and strengthened (M2): Nick called lead times 'our biggest issue', with pivoting between suppliers and early sight of delays as the value |
| F30 | A 'J9' is a paper form or manual record used in this process. | Our guess from M2; the term is not explained | How we describe the status quo in the pitch | Y | Open |
| F31 | The 'supplier notification' Nick described is what industry calls a product change notification (PCN), typically sent months before a part changes or is discontinued. | Our reading of M2; the PCN label is ours | The alert feature and the data it needs | Y | Open |
| F32 | 'Plug into and retrofit' can be met by reading exports (CSV or Excel) from the client's systems and handing back files, with no change to the systems themselves. | Our design response to M2 | Feasibility claim | Y | Open |
| F33 | Clients' ERPs can hold warranty claims (SAP, Oracle and Infor all document a warranty claim function, source W1), but many clients keep returns in Excel, as Nick described. The tool must accept either. | W1 and M2 | Warranty input design | N | Open |
| F34 | By 'full cost' Nick means material plus labor, overhead and other conversion cost, and a tool that delivers the purchased-material part with the rest taken from standard cost is still useful to him. | Our reading of M2 | What we claim the cost figure is | Y | Open |
| F35 | Near-identical parts fall into three groups: the same part under two numbers, a close spec that needs an engineering decision, and look-alikes that must not be merged. | Our reading of M3; the three groups are ours | Similar-parts feature and the D2 answer key | Y | Open |
| F36 | Supplier consolidation should be sized against the best qualified supplier (ISO 9001 plus the certification the commodity needs), not the cheapest. Our qualification rule is a simplification. | Our design response to M3 and M2 | The savings number | Y | Open |
| F37 | Savings sized on price alone are a fair first cut. Freight between regions, tooling moves and requalification are not netted off in D2. | Our simplification | How we caveat the savings figure | Y | Open |
| F38 | Planted savings of about 3% of spend are a believable size for a demo. The figure is a design choice in D2, not a benchmark. | Our choice | Credibility of the demo numbers | Y | Open |
