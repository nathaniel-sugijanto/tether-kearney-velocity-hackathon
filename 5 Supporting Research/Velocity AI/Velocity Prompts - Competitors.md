# Velocity prompts: competitors (Sievo and others)

Written Sat 2026-11-14, 10:20 PM CT, for the three-advantage framing of the pitch:
Tether is (1) cheaper to implement, (2) faster to use, (3) keeps the data in-house.
Purpose: get sourced facts on what the platforms cost, how long they take and where client data goes,
so slides 3 and 4 of the five-part deck can carry numbers we can defend.

How to use
- Paste the Context block first, once, then one prompt at a time. Save each answer word for word in
  `Velocity Responses/` as V9, V10, V11, V12, V13 and add a row for each to the source index in `Data Gathering Log.md`.
- Every prompt asks for a source and a label on each figure. Last time about half of Velocity's specific
  figures did not hold up when we opened the source, so nothing goes on a slide until its source is checked.
- If Velocity says a figure is not published, that is a usable answer. "Vendors do not publish prices" is
  itself a point for slide 4.

## Context block (paste first)

We are a two-person team at the Kearney PERLab hackathon working on BOM cost linkage: tying a manufacturer's
bills of materials to its purchase order and invoice spend, then sizing savings. We built a lightweight tool
that runs on a consultant's laptop on raw CSV or Excel exports, using rules and SQL, with no AI at run time and
no data leaving the machine. We want to compare it honestly with commercial software a client could buy instead:
Sievo, LevaData, GEP, Ivalua, Coupa, aPriori, Siemens Teamcenter Product Cost Management and Verusen.
Assume a discrete manufacturer with 500 million to 2 billion US dollars of revenue, 2 to 5 plants and at least
two different ERP systems. For every figure, give the source (name, URL, date) and label it as one of:
vendor's own claim, third-party report, customer-reported, or your own estimate. If nothing is published, say
"not published" and do not estimate unless we ask.

## C1 (save as V9). What it costs

For each of Sievo, LevaData, GEP, Ivalua, Coupa, aPriori, Siemens Teamcenter Product Cost Management and Verusen:
what is publicly known about the cost to a client of the profile above? Split it into (a) annual licence or
subscription, (b) one-time implementation and integration fees, (c) who does the implementation (vendor, systems
integrator, client IT) and what that typically costs, (d) ongoing cost to maintain data feeds and mappings.
Give a range where one is published, and say plainly where the vendor does not publish prices. Put the answer in
a table with one row per vendor and a source for every cell. Finish with one sentence on the realistic total
first-year cost range for the two vendors closest to BOM-to-spend linkage, labeled as your estimate if it is one.

## C2 (save as V10). How long it takes

For the same vendors and client profile: how long from signed contract to the first usable output, and to the
first savings opportunity a client could act on? List the steps in between (data extraction, connector or
integration build, data mapping and cleansing, taxonomy or classification setup, user training) with typical
durations and who does each. How much client IT and procurement staff time is needed? What most often delays
these projects? Then, for comparison, how long does a consulting team typically take to do a first BOM-to-spend
tie by hand for one product family? Sources and labels on every duration.

## C3 (save as V11). Where the client's data goes

For Sievo and LevaData first, then the others briefly: where is client data hosted (vendor cloud, client cloud,
on-premise option)? What data has to leave the client's systems, and how (file upload, API, ERP connector)? Is
client data used to build benchmarks, train models or feed features that other customers see, and can a client
opt out? What do the vendors publish on certifications (SOC 2, ISO 27001), data residency, retention and deletion
at contract end? Separately: when a consulting firm like Kearney works on a client's spend data for a few weeks,
what contractual or security hurdles come up if the consultants want to load that data into a third-party cloud
platform, compared with analysing it on firm laptops? Sources and labels throughout.

## C4 (save as V12). What they do that we do not, and the reverse

Compare the commercial tools with a lightweight week-one tool like ours, capability by capability. First, what do
the platforms do that a rules-and-SQL laptop tool does not (for example external price benchmarks, should-cost
models, live ERP integration, sourcing workflows, savings tracking against baselines, scale and access control)?
Second, do any of them document the following, and where: sorting each saving into "ready to act" versus "needs
review"; checking a supplier's qualification before recommending it as the cheaper source; giving a reason and a
confidence for each part match; refusing to merge look-alike parts that differ on a safety-relevant spec? If their
public material does not mention a capability, say "not documented publicly" and do not conclude they lack it.
Be blunt about where our tool is weaker.

## C5 (save as V13). Red team our three claims

Our pitch claims three advantages over platforms like Sievo for a consulting team's first weeks at a client:
cheaper to implement, faster to first result, and the client's data stays in-house. Act as a sceptical Kearney
partner and then as a Sievo sales engineer. For each claim, give the strongest objection, the evidence that would
settle it, and the fairest wording we could use on a slide without overstating. Then tell us when a client
should buy the platform anyway, and how a lightweight tool and a platform could work together (for example, our
tool used in week one and its cleaned part crosswalk handed to the platform later). Finish with the three
questions a judge is most likely to ask us on this and a two-sentence answer to each.

## Where the answers go

| Prompt | Feeds | What to pull out |
|---|---|---|
| C1 | Slide 4, "Cheaper to implement" column | A sourced cost range, or "vendors do not publish prices" |
| C2 | Slide 4, "Faster to use" column | Weeks or months to first output, with a source |
| C3 | Slide 4, "Data stays in-house" column | Hosting model and whether data leaves the client |
| C4 | Appendix competitor table and Q&A | What they do that we do not; keeps us honest |
| C5 | Speaker notes and Q&A prep | Fair wording, likely judge questions |
