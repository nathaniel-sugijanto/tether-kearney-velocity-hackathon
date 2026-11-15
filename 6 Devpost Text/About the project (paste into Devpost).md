## Inspiration

Before grad school, Nathaniel spent three years at Deloitte in tax technology, and the same problem kept coming up: mapping fields between systems was painstaking, manual work. His team even commissioned a project much like Tether, a tool that mapped SAP and Oracle data into a tax engine, so we had seen firsthand how much time a good mapping layer saves.

When Kearney's mentors described BOM cost linkage, it was the same problem in a new place. Product and supply chain teams have never had a good way to tie the bill of materials to what was actually spent. Today it is done by hand, with paper part lists and Excel lookups, and it takes 20 or more analyst-days to tie one product family. Two plants on two ERPs call the same part by different numbers, parts get superseded, and invoices carry free text, so a plain part-number join quietly drops the spend that matters most.

Clients want change, but not a complete overhaul. They also care about cost and about data security. That is why we built Tether: a light tool that runs on the exports a client already has, needs no new system, and keeps the data on the client's machine.

## What it does

Tether takes each plant's existing exports (BOMs, item masters, POs, invoices, receipts, quotes) and:

1. **Ties spend to parts, parts to BOMs, and BOMs to finished products**, across different ERPs. Every link keeps its method, confidence and reason.
2. **Decides which part numbers are the same part**: same part (merge), close spec (send to engineering), or look-alike (never merge).
3. **Sizes the savings** the links make visible and splits them into **safe to promise** and **needs review**: price alignment to the best qualified supplier, standard parts inside near-identical families, invoices above the awarded quote, and across-the-board price increases.
4. **Says no when it should**: it will not recommend an unqualified supplier, will not merge look-alike parts, and shows unresolved spend instead of guessing.
5. **Builds one dashboard organized by who acts**: savings by owner, product cost per unit, a risk watchlist, and a Platform view of the common core across a product family.

On our synthetic test company (2 plants, 2 ERPs, $7.14M of spend, 3,422 PO and invoice lines):

- **95.4%** of spend tied to a BOM, against 86.2% with a plain part-number join
- **0** lines tied to the wrong part
- **$230,096** a year safe to promise, plus $59,609 that needs review
- A few days to set up, **4 seconds** to run

Because the data is synthetic and we wrote the rules while looking at it, these numbers are an upper bound. Real client files will need rule tuning and a longer review queue.

## How we built it

We started with research in **Kearney's Velocity AI**: how BOM-to-spend linkage is done today, why part numbers do not match spend records, how to allocate shared parts, and which savings analyses follow. Velocity's list of mismatch causes became Tether's matching order. We then checked every source Velocity cited and used only the figures that held up.

Next we talked to three Kearney mentors and asked each one for their pain points. Their answers shaped the product: the status quo is manual, clients want no overhaul, superseded parts and make-versus-buy changes cause the worst mismatches, and lead times are the biggest operational issue. Each of those became a feature.

Kearney cannot share client data, so we built a realistic synthetic dataset with planted problems and a separate answer key to score ourselves against. The tool is Python and SQLite with readable SQL at each step, one mapping file per client, and a one-file HTML dashboard, built with help from Claude. There is no AI at run time, so every number is auditable and the data never leaves the client's machine.

## Challenges we ran into

- **Aggregating different opinions.** Each mentor saw the problem from a different angle, and some of their advice pulled in different directions. We had to decide what to keep and what to leave out.
- **Conveying our value for Kearney.** Linking data is not the point on its own. We had to find the value a consulting team actually needs, which became "savings you can safely promise."
- **Fitting it into a 4-minute pitch.** We had far more material than time, and cut it down to the problem, the solution, our advantages, and the savings.
- **No real data.** We had to build a test dataset hard enough to be honest, then make sure the tool linked more spend without a single wrong link.

## Accomplishments that we're proud of

- 0 wrong links across 3,422 lines, scored against an answer key the tool never reads
- A working tool and dashboard, not just a concept, built in 36 hours
- A savings list where every dollar traces back to invoices and has an owner

## What we learned

- Procurement and the source-to-pay lifecycle have many layers, and each one has its own room for optimization.
- Each mentor we talked to highlighted a different angle on how to present our work. By aggregating their responses, we arrived at a pitch that none of them gave us on their own.
- An AI research tool is a fast starting point, not a final source. Checking its citations changed what we were willing to claim.

## What's next for Tether

- Test it alongside live engagements, using the team's manual work as the answer key, to see whether accuracy holds on real data.
- Add mappings for more ERPs and tune the rules on real client exports.
- Grow the Platform view into a full core-and-modules analysis for product platforming.
