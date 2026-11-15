# R1: Competitor answers to prompts C1 to C5

**This is Claude's research, not Velocity output.** Velocity answered only the scope exchange (saved in `Velocity Responses/V9.md`) and then appeared to be down, so Nathaniel asked me to answer the five prompts in `Velocity Prompts - Competitors.md` instead. Do not cite anything below as "Velocity says". If Velocity comes back, its answers go in V9 to V13 and can be compared with this file.

Pages were read on Saturday 2026-11-14 between about 10:40 and 10:50 PM CT, through a page reader. Words in quotation marks are the page's own words. Every figure carries one of the four labels from the context block: **vendor's own claim**, **third-party report**, **customer-reported**, **own estimate** (mine). "Not published" means the pages I read do not give it. I did not read every page of every vendor, so "not published" should be said aloud as "their public pages do not show this", never as "they cannot" or "they do not".

## The five things worth carrying into the pitch

1. **None of the eight vendors publishes a price for a client like ours.** The only two hard price anchors I found are a $240,000 twelve-month list contract for Verusen on AWS Marketplace, and a $94,519 median annual contract for Coupa in Vendr's deal data. Neither is a like-for-like BOM-to-spend tool.
2. **Sievo's own material says "a few months" to be up and running**, charges a "one-time implementation fee" plus an annual subscription, and prices the subscription on the customer's spend. No page gives a number of weeks or a dollar amount.
3. **Sievo and LevaData both pool customer data.** Sievo sells benchmarks "derived from aggregated & anonymized cross-customer data" and says its AI is "trained on the 2%+ global GDP that we process annually". LevaData says "The benchmark comes from what other customers bought the same part for." Neither page I read mentions an opt-out.
4. **The platforms are certified and the data-leaves-the-client point must be worded carefully.** Sievo holds ISO 27001 and SOC 2 Type II and hosts in Europe; LevaData is SOC 2 Type II on AWS. Our claim is not "safer". It is "no new vendor, no upload, no pooling".
5. **They do things we do not**: outside price benchmarks, should-cost models, live connections to the ERP, savings tracking over years. The honest position is "week one, before a platform", not "instead of a platform".

---

## C1. What it costs

| Vendor | (a) Annual subscription | (b) One-time implementation | (c) Who implements | (d) Ongoing data feeds and mappings |
|---|---|---|---|---|
| **Sievo** (closest to BOM-to-spend) | Not published. Model only: "Fixed annual subscription costs, no hidden fees" (vendor's own claim, sievo.com/solutions/procurement-leaders and /solutions/direct-procurement). "Pricing based on customer spend & unlimited user seats." (third-party listing of vendor information, g2.com Sievo pricing page, listing updated 2026-04-09). Capterra says "Contact vendor"; ERP Research says "Sievo does not publish a price list" | A fee exists, amount not published: "Sievo's one-time implementation fee and annual subscription ensure predictable costs." (vendor's own claim, hub.sievo.com/sievo-vs-in-house-procurement-analytics) | Sievo does the extraction: "Sievo manages the entire data extraction process" (vendor's own claim, sievo.com/solutions pages). Client IT grants access: "Initial setup may require some collaboration with your IT team" and "clear list of tasks will be provided to your IT teams" (sievo.com/integrations). Cost of that client time: not published | Included in the subscription: "end-to-end data responsibility (extraction, cleansing, enrichment, harmonization, and classifications), software updates, maintenance, account support" (vendor's own claim, sievo.com/solutions pages) |
| **LevaData** (closest on part-level price) | Not published. "Pricing Model: Quotation Based", "The starting price is not disclosed by LevaData." (third-party listing, spotsaas.com, updated 2026-10-15) | Not published | Not published. Their site says "Bring one spend file" (vendor's own claim, levadata.com) | Not published |
| **GEP** | Not published on GEP's spend analysis page. One comparison site (costbench.com) shows figures that contradict each other on the same page ($41,667 to $75,000 "per user per month" in the headline, the same amounts "per year" in the table, and a $3.5K median from 10 Vendr deals). **Do not use** | costbench.com says "20-35% of license costs", source not named. **Do not use** | Not published | Not published |
| **Ivalua** | Not published. costbench.com: "no public list price found", "Custom pricing" | costbench.com shows "Implementation $845,000" from one unnamed source. **Do not use** | Not published on the pages read. Ivalua's own blog "surveyed 31 system integrators", which suggests integrators do this work (own estimate) | Not published |
| **Coupa** (full purchasing suite, not a like-for-like tool) | "Median buyer pays $94,519 per year", "Based on data from 128 purchases", range $20,804 to $331,084 (third-party report from Vendr's own deal data, vendr.com/marketplace/coupa, updated February 2026; the same page also says 85 deals). "Coupa does not publish standard list pricing." | "often range from $50,000 to $500,000+ for enterprise deployments" and "50% to 150% of the first-year subscription cost for complex deployments" (third-party report, Vendr, basis not stated) | Not stated on the page read | Not published |
| **aPriori** (should-cost from CAD, not spend matching) | Not published. "Please contact aPriori directly for pricing information." (g2.com aPriori pricing page) | Not published | Not published | Not published |
| **Siemens Teamcenter Product Cost Management** | Not published. The Teamcenter X pricing page lists four plans with "Request a quote" and no prices; "Product cost management" is ticked only in the top plan, Premium (vendor's own page, siemens.com Teamcenter X plans and pricing) | Not published | "operated by Siemens" for the cloud version (vendor's own claim) | Not published |
| **Verusen** (spare parts and maintenance inventory, not production BOMs) | **$240,000 for a 12-month contract**, "Annual Commit of Trusted Material", "unlimited users"; "The vendor sizes unit count by the number of plants and systems you connect" (vendor's own list price, AWS Marketplace listing prodview-u24lv6diikofs) | Not published | Not published | Not published |

**First-year total for the two closest vendors (Sievo and LevaData): not published.** My own estimate, for our understanding only and not for a slide: a low-to-mid six-figure sum in year one for a client of this size, because the only two public anchors for software in this area are $240,000 (Verusen list) and $94,519 (Coupa median), and Sievo adds an implementation fee on top. I have no source that prices Sievo or LevaData themselves.

**For slide 4, "Cheaper to implement":** "Platform prices are not public. Sievo charges a one-time implementation fee plus an annual subscription priced on the client's spend. Tether: no licence and no integration project." If you want one number, the Verusen list price is the only vendor-published one, and it must be called what it is: a neighbouring product's list price.

---

## C2. How long it takes

| Vendor | Time to first usable output | Source and label |
|---|---|---|
| **Sievo** | "In just a few months, we were up and running with insights that we could use immediately" (one customer, a "Procurement Excellence Executive"). "Sievo's platform was operational for the customer within months." | Customer-reported, quoted on Sievo's blog, sievo.com/blog/procurement-analytics-time-to-value-bob-vs-power-bi |
| Sievo, one data connector | "often enabling setup within just a few days" for "widely used systems—such as SAP, Oracle"; timing "depends on the complexity of the source system and the availability of access" | Vendor's own claim, sievo.com/integrations |
| Sievo's claim about building it in house (Power BI) | "It often takes over 10 months just to achieve basic functionality." "Sievo's TTV is less than a fifth of the time it would take to build even a basic Power BI setup." By Sievo's own arithmetic that is about two months (own estimate from their two sentences) | Vendor's own claim, no source given, same blog |
| **LevaData** | Not published. The site says "Bring one spend file." | Vendor's own claim, levadata.com |
| **Verusen** | "Onboarded and optimizing in 60 days" (menu text; page last modified 2022) | Vendor's own claim, verusen.com/the-verusen-comparison |
| **aPriori** | "Time to Implement" "6 months"; "Return on Investment" "18 months" | Customer-reported (average of G2 user reviews), g2.com aPriori pricing page |
| **Coupa** | "buyers should plan for 12–24 month rollouts" (companies with 5,000 or more employees, the whole suite) | Third-party report, Vendr, basis not stated |
| **Ivalua** | "organizations report phases lasting anywhere from several weeks to months" (each phase, source-to-pay projects generally, not Ivalua only) | Vendor's own claim from its survey of 31 integrators, ivalua.com/blog/s2p-challenges |
| **GEP** | Not published on the page read | |
| **Teamcenter PCM** | Not published. Only "Get up and running quickly" | Vendor's own claim |

**Time to the first saving a client could act on: not published by any of the eight.**

**Steps in between, and who does each (Sievo, the only vendor that describes it):** the client's IT grants access to the source systems and works through a task list; Sievo extracts the data with its own extractor or connectors, then cleanses, enriches, harmonizes and classifies it; the client names a super user who "is trained to lead adoption". Durations per step: not published. Client staff hours: not published; Sievo says only that after setup "ongoing maintenance is minimal".

**What delays these projects.** Sievo names two things itself: "the complexity of the source system and the availability of access". My own estimate of the usual causes, from general experience and not from a source: the client's security review of a new vendor, the data-processing agreement, getting extraction rights on each ERP, and agreeing a classification scheme.

**The manual comparison.** A first BOM-to-spend tie for one product family by hand: about 20 to 40 analyst-days (Velocity's estimate in V4; 21 to 39 in V1). Nick said 20 days for a full family "sounds correct but really depends on how big the family is" (M2). That is four to eight weeks for one analyst, and it is the number our tool is really competing with.

**For slide 4, "Faster to use":** "Sievo's own customer story: 'In just a few months, we were up and running.' By hand: 20 to 40 analyst-days per product family. Tether: a first tie from exports the client already has, after a one-time column mapping." Do not state our time in hours for a real client. We have only run it on our own synthetic data.

---

## C3. Where the client's data goes

### Sievo

| Question | What the pages say | Source |
|---|---|---|
| Hosting | "Hosting and Data processing in Europe". Cloud provider and region: not published | sievo.com/integrations |
| What leaves the client, and how | "Sievo automatically extracts and unifies all your internal transactional data (invoices, payments, purchase orders, etc.)" from "all ERPs, MRPs, data lakes, and procurement systems". On-premise systems: "Sievo Data Extractor pulls data directly from the source system". Cloud systems: "Sievo Connectors". Delivery can also be "through SFTP or Azure Data Share" | sievo.com/solutions pages and /integrations |
| Used for benchmarks or other customers' features | Yes. "Proprietary insights & benchmarks derived from aggregated & anonymized cross-customer data". "Leverage Sievo's cross-customer Community Data". "our AI capabilities are trained on the 2%+ global GDP that we process annually." | sievo.com/solutions pages |
| Opt-out | Not published | |
| Certifications | "ISO/IEC 27001 and SOC2 Type II"; "ISO 27001 and ISAE 3000 Type II (SOC2 Type II EU equivalent) certified"; audited yearly by a third party. "All customer data encrypted in transit and at rest." GDPR compliance stated | sievo.com/security-and-compliance and trust center page (updated 2026-05-28) |
| Retention, deletion at contract end | Not published | |

### LevaData

| Question | What the pages say | Source |
|---|---|---|
| Hosting | "All production workloads are hosted on Amazon Web Services (AWS)". "Each customer tenancy is logically isolated." | support.levadata.com, "How is my data transferred and secured" |
| What leaves the client, and how | Spend by manufacturer part number, by file: "Load your spend by manufacturer part number", "Bring one spend file." SFTP, API or ERP connector: not published | levadata.com |
| Used for benchmarks | Yes. "When customer data is shared with the community data pool, that data is fully anonymized and analyzed." "The benchmark comes from what other customers bought the same part for." Also "benchmarking prices from over 117 data sources." | support.levadata.com and levadata.com |
| Opt-out | Not published | |
| Certifications | "currently SOC 2 Type II certified"; yearly third-party audit and penetration test. ISO 27001: not published | support.levadata.com |
| Retention, deletion | Not published | |

### The others, briefly

- **Verusen:** "Software as a Service (SaaS)", "Deployed on AWS: Yes", uses "Amazon EKS, RDS, Bedrock, and SageMaker" (AWS Marketplace listing). Certifications and data sharing: not published there.
- **Siemens Teamcenter X:** "SaaS delivery ... on the cloud, operated by Siemens"; the Premium plan offers "Choice of provider (AWS or Azure)". Certifications not named on the pages read.
- **Ivalua:** "ISO 27001, SOC 1, and SOC 2 Type II", "TISAX certified" for automotive, "regional data residency", and "Your data stays private, access stays controlled" (ivalua.com/technology/security-and-compliance). Cloud provider, retention and AI training: not published on that page.
- **GEP:** the spend analysis page describes an engine trained on a large set of procurement transactions that keeps learning on the client's data. This comes from a machine summary of the lower half of the page, not a verbatim quote, so **do not quote it**. Hosting and certifications sit in a separate "GEP Trust Center" that I did not read.
- **aPriori and Coupa:** hosting pages not read. Say nothing about them on this point.

### The consulting-firm question (my own estimate; ask Nick to confirm)

I found no public source on this, so everything in this paragraph is my own reasoning. When consultants hold a client's spend data for a few weeks, the engagement contract and confidentiality terms normally say who may hold it and where. Loading it into a third-party cloud platform adds a party the client has not approved, which usually means the client's vendor-risk or security review, a data-processing agreement, and sometimes a separate contract with the vendor. Any of those can take longer than the weeks the analysis itself needs. Analysing it on the firm's own machines stays inside terms that are already signed. **One question for Nick would turn this into a mentor-backed line:** "When you need a client's spend data in a third-party tool, what approval does that take and how long?"

**A weak spot in our own claim.** "The data stays in-house" is only strictly true if the tool runs on the client's machine. On a consultant's laptop the data has still left the client. It has gone to the firm the client already hired, and to no one else. The defensible wording is narrower than "in-house".

**For slide 4, "Data stays in-house":** "Platforms: data is extracted to the vendor's cloud (Sievo: hosted in Europe, ISO 27001 and SOC 2 certified) and feeds anonymized cross-customer benchmarks. Tether: runs on the engagement team's or the client's own machine. No upload, no new vendor to approve, no pooled data."

---

## C4. What they do that we do not, and the reverse

### What the platforms do that our tool does not

| Capability | Who documents it | Our tool |
|---|---|---|
| Outside price benchmarks | LevaData ("over 117 data sources", plus what other customers paid). Sievo (cross-customer community data) | None. We compare a client only with itself |
| Should-cost models | aPriori ("upload your CAD files ... detailed simulation of the manufacturing process"). Teamcenter PCM ("modeling the production process from the bottom-up") | None |
| Live, refreshed data from the ERP | Sievo ("2700+" "active integrations", "1060+" "data sources managed") | None. A one-time export, re-run by hand |
| Managed data cleaning as a service | Sievo ("over 100 skilled experts dedicated to managing diverse data sets and connectors") | The consultant does the mapping |
| Automatic de-duplication of materials at scale | Sievo ("De-duplicate 6-23% of your materials without any manual work", checked earlier in Source Check). Verusen ("Duplicate Material Identification") | Yes, but by rules written for the data in front of us |
| Sourcing and purchasing workflow | Coupa, Ivalua, GEP (full suites) | None |
| Many users, access control, audit trail, support desk | All of them, as enterprise products (own estimate; not read page by page) | Single user, no access control |
| Tying BOMs to spend | Sievo documents it: "map spend data to BOMs for COGS analysis and financial forecasting" (Source Check) | Yes, this is all we do |

### Do they document our four specific behaviours?

I did not search each vendor's full documentation for these, so the answer for all four is **"not seen on the pages I read"**. That is weaker than "not documented publicly", and far weaker than "they do not do it". Do not claim on a slide that competitors lack any of these.

| Behaviour | Seen on the pages read? |
|---|---|
| Sorting each saving into "ready to act" and "needs review" | Not seen |
| Checking a supplier's qualification before naming it the cheaper source | Not seen |
| A reason and a confidence for each part match | Not seen |
| Refusing to merge look-alike parts that differ on a safety spec | Not seen |

### Where our tool is weaker, bluntly

- It has only ever run on synthetic data that we built, and its rules were tuned on that data. Its near-perfect score is an upper bound.
- It knows nothing about what a part should cost or what others pay. It can only find a client paying two prices for the same thing.
- Each new client needs a column mapping, and odd data needs new rules. A platform has people for that.
- It does not stay current. The answer is a snapshot.
- It has no track record, no support, no certification, and no savings tracking after the first answer.
- It is one of several tools that find savings. Sievo advertises "$20M average additional savings per $1B spend" and LevaData sells savings identification outright. Finding savings is not our difference.

---

## C5. Red team of the three claims

### Claim 1: cheaper to implement

- **Sceptical Kearney partner:** "Cheaper for whom? The client pays our fees either way, and an unsupported script that one analyst understands is a cost to me, not a saving. And you cannot say cheaper than a price you do not know."
- **Sievo sales engineer:** "Our subscription includes all the extraction, cleansing and classification work, every refresh, forever. You are comparing a one-time script with a managed service."
- **Evidence that would settle it:** a real quote from Sievo or LevaData for this client profile, and our own hours on one real client dataset.
- **Fairest slide wording:** "No licence and no integration project before the first answer. Platform prices are not public; Sievo charges an implementation fee plus a subscription priced on spend."

### Claim 2: faster to first result

- **Kearney partner:** "Fast on data you wrote yourselves. How long on a client's SAP export you have never seen?"
- **Sievo sales engineer:** "A connector to SAP or Oracle is often set up 'within just a few days'. And after go-live our answer refreshes itself; yours is stale next month."
- **Evidence that would settle it:** a timed run on a dataset we did not build (the second-seed dataset is a first step; a mentor-supplied file would be better), and a dated Sievo project plan.
- **Fairest slide wording:** "A first BOM-to-spend tie in the first week, from exports the client already has. Sievo's own customer story says 'a few months'; by hand it is 20 to 40 analyst-days per family."

### Claim 3: the client's data stays in-house

- **Kearney partner:** "It is on your laptop. That is not in-house, and a laptop is easier to lose than a certified data centre."
- **Sievo sales engineer:** "We are ISO 27001 and SOC 2 Type II certified, hosted in Europe, encrypted in transit and at rest. What certification does your laptop tool have?"
- **Evidence that would settle it:** a client or mentor saying that approving a new cloud vendor is a real delay, and that pooled benchmarks worry them.
- **Fairest slide wording:** "Runs on the engagement team's or the client's own machine. No upload, no new vendor to approve, and the client's prices never enter a shared benchmark." Never say "more secure".

### When a client should buy the platform anyway

When it wants spend watched every month and not once; when it needs outside price benchmarks or should-cost models to negotiate; when many buyers across many categories need the same numbers; when savings must be tracked against a baseline for years; or when it has no team to maintain mappings.

### How the two work together

Tether goes first, in week one, on raw exports: it produces the part crosswalk across plants, the list of superseded and duplicate numbers, and a first sized set of savings split into ready and needs-review. If the client later buys a platform, that cleaned crosswalk and the mapping file are exactly the inputs the platform's onboarding needs, and the first findings tell the client whether the platform is worth buying. This fits Nick's point that clients want no overhaul.

### The three questions a judge is most likely to ask

1. **"Why would a client not just buy Sievo?"** Many should, later. Tether is for the first weeks, before any contract or integration, and what it produces makes a platform cheaper to adopt.
2. **"You say cheaper and faster. Where are your numbers?"** The vendors do not publish prices or timelines, so we quote their own words: an implementation fee plus a subscription, and "a few months" to be up and running. Our side is no licence and a first tie in week one, which so far we have shown only on synthetic data.
3. **"Is a laptop really safer than a certified cloud?"** We do not claim safer. We claim no upload, no new vendor for the client to approve, and no pooled benchmark, which removes a step at the start of an engagement.

---

## Sources read (all on 2026-11-14, about 10:40 to 10:50 PM CT)

| Vendor | Pages |
|---|---|
| Sievo | sievo.com/security-and-compliance; sievo.com/company/trust-center/iso-certificates; sievo.com/solutions/procurement-leaders; sievo.com/solutions/direct-procurement; sievo.com/integrations; sievo.com/blog/procurement-analytics-time-to-value-bob-vs-power-bi; hub.sievo.com/sievo-vs-in-house-procurement-analytics; sievo.com/sievo-vs-spendhq; sievo.com/your-long-term-success-with-sievo; listings on g2.com, capterra.com and erpresearch.com |
| LevaData | support.levadata.com ("How is my data transferred and secured"); levadata.com; levadata.com/faq; spotsaas.com pricing listing |
| Coupa | vendr.com/marketplace/coupa |
| Verusen | aws.amazon.com/marketplace/pp/prodview-u24lv6diikofs; verusen.com/the-verusen-comparison |
| aPriori | g2.com aPriori pricing page; apriori.com |
| Siemens | siemens.com Teamcenter Product Cost Management page; Teamcenter X plans and pricing page |
| GEP | gep.com spend analysis page; costbench.com GEP SMART vs Ivalua (unreliable, not used) |
| Ivalua | ivalua.com/blog/s2p-challenges; ivalua.com/technology/security-and-compliance; spendflo.com Ivalua vs GEP (a seller's page, not used) |

Pages that would not load: vendr.com pages for Ivalua and GEP; ivalua.com/technology/security; one Coupa pricing blog.

## Limits of this file

- I read each page once, through a page reader, late at night. Before any quoted phrase goes on a slide, open the page and check the words are still there.
- The G2 quotes for Sievo's pricing model sit on a listing page. Treat them as a listing's description, not as Sievo's contract terms.
- Vendr's Coupa page contradicts itself on the number of deals (128 and 85).
- Nothing here is Kearney data, and nothing here came from Velocity.
