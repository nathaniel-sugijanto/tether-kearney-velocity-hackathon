## Corporate track problem
Corporate Track 3, BOM Cost Linkage: tying each product's bill of materials to the PO and invoice spend behind it, across plants and ERPs, so cost and savings can be seen by part, product and supplier.

## What does your product seek to do and how? (max 150 words)
Tether turns the 20-plus analyst-days it takes to tie one product family's BOM to its spend into a list of savings a Kearney team can safely promise in week one.

It runs on the exports a client already has from each plant and ERP. A one-time column mapping brings them into one layout. Tether links every PO and invoice line to a part through a fixed order of checks (exact number, superseded number, supplier part number, quote reference, description), and records the method and reason for each link. It decides which part numbers are the same part, which need engineering review, and which must never be merged. It sizes savings, such as price alignment to the best qualified supplier, and splits them into safe to promise and needs review.

On synthetic data: 95.4% of spend tied versus 86.2% with a plain join, zero wrong links, $230,096 safe to promise.

## How did you utilize Velocity AI? (max 200 words)
Velocity was our research starting point, across nine prompts.

For Track 3 we asked five questions: how BOM-to-spend linkage is done today and how long each step takes; why BOM part numbers fail to match PO and invoice records, and how analysts resolve each cause; how to allocate shared-part spend to products, spares and warranty; which savings analyses follow once spend is linked, and how much coverage is enough; and which existing tools do this and where they fall short. Three earlier prompts on platforming gave us the core-versus-module ideas behind our Platform view.

Velocity's answers shaped the product. Its list of mismatch causes became Tether's matching order, its savings analyses became our opportunity types, and its estimate of 20-plus analyst-days per product family, which our Kearney mentor called conservative, framed our value.

We opened every source Velocity cited: about half of its specific figures held up, and we used only those. We then turned its open questions into questions for our Kearney mentors. Velocity went down before answering our competitor prompts, so our competitor research is our own reading of vendor pages.

## Tryout link to present with
We will present with the Tether dashboard (one HTML file, run live on our synthetic Larkfield data) alongside our pitch deck.
