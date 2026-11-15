# Tether: BOM to spend linkage tool

Ties purchase order and invoice lines to parts, parts to bills of materials, and
bills of materials to finished products, then sizes the savings the links make visible.
Demo data is synthetic (Larkfield Home Appliances, an invented coffee maker company).

## Run it

Needs Python 3 only. Nothing to install.

    python3 run.py <data folder>      # builds out/linkage.db, out/dashboard.html, out/opportunities.csv
    python3 score.py <data folder>    # same, plus scores the result against the answer key

`<data folder>` is the `data` folder of the synthetic dataset
(Data Gathering/Synthetic Data - Coffee Maker/data). Open `out/dashboard.html` with a double-click.
The whole run takes about 4 seconds.

## What is where

| Path | What it does |
|---|---|
| `config/mapping.json` | Which client column feeds which common field, per plant. A new ERP needs a new mapping, not new code. |
| `engine/load.py` | Reads each plant's CSV exports into one SQLite database in a common layout. |
| `engine/text.py` | Cleans descriptions: abbreviations, buyer noise, and the numbers that matter (216 C, 900 W, M3 x 8). |
| `engine/link.py`, `sql/02_link_spend.sql` | The matching order: exact number, replaced number, service part, supplier part number, quote reference, description. Every link keeps its method, confidence and reason. |
| `engine/group.py` | Decides which part numbers are the same part, which are close (engineering review) and which must stay apart. Rules are plain data in `SPEC_RULES`. |
| `sql/03_prices.sql` | Prices on one basis (per base unit) and supplier qualification checks. |
| `sql/04_products.sql` | BOM roll-up and cost per finished unit; shared parts split across products. |
| `sql/05_savings.sql` | The opportunity list: price alignment, near-identical parts, invoiced above quote, across-the-board increases. |
| `engine/extras.py`, `sql/06_watch.sql` | Kits, supplier change notices, open orders, delivery record. |
| `engine/platform.py` | Platform view: common core, add-on modules, plant differences and make or buy, for the product family named under `platform` in the mapping file. |
| `engine/export.py`, `app/template.html` | Writes the dashboard as one HTML file with the data inside it. |
| `score.py` | The only file that reads `answer_key`. The tool itself never does. |

## Honest limits

The matching rules and abbreviation list were written while looking at this dataset, so the
scores on the Test results page are an upper bound. On real client files the rules need
tuning in the first days and the review queue will be longer.
