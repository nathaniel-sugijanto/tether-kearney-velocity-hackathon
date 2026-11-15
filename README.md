# Tether: BOM-to-spend savings you can safely promise

Kearney PERLab Hackathon, November 2026. Corporate Track 3: BOM Cost Linkage.
Team: Nathaniel Sugijanto and Caleb Brownlee.

Tether ties every BOM part to the POs and invoices behind it, across plants and ERPs, and shows which savings a Kearney team can safely promise in week one.

**All data in this repository is synthetic.** Larkfield Home Appliances is an invented company. Results on it are an upper bound, because the matching rules were written while looking at this dataset.

## Results on the synthetic test company

| Measure | Result |
|---|---|
| Spend tied to a BOM | 95.4%, against 86.2% with a plain part-number join |
| PO and invoice lines tied to the wrong part | 0 of 3,422 |
| Savings safe to promise | $230,096 a year |
| Savings that need review | $59,609 a year |
| Setup and run time | A few days of one-time setup, about 4 seconds to run |

## What is in this repository

| Folder | Contents |
|---|---|
| `1 Pitch Deck` | Final pitch deck: five main slides plus appendix, with speaker notes |
| `2 Dashboard` | `Tether dashboard.html`: the working dashboard in one file. Download it and open it in a browser; no server or install needed |
| `3 Tool Source Code` | The engine (Python and SQLite, standard library only) that builds the dashboard. See its README |
| `4 Synthetic Data` | The Larkfield dataset: two plants on two ERPs, the generator and validator scripts, and the answer key used only for scoring |
| `5 Supporting Research` | Velocity AI prompts and raw responses (V1 to V9), our check of Velocity's cited sources, mentor feedback (M1 to M4), competitor research, data gathering log, assumptions log, and questions for Kearney |
| `6 Devpost Text` | The text of our Devpost submission |

## Run it yourself

Needs Python 3 only.

```
cd "3 Tool Source Code"
python3 run.py "../4 Synthetic Data/data"     # builds out/dashboard.html in about 4 seconds
python3 score.py "../4 Synthetic Data/data"   # same, plus scores the result against the answer key
```

The tool never reads the answer key; only `score.py` does.

## How we used Velocity AI

Velocity was our research starting point: eight research prompts plus a scoping exchange for competitor research (`5 Supporting Research/Velocity AI`). Its list of mismatch causes became Tether's matching order, and its savings analyses became our opportunity types. We checked every source Velocity cited (`Source Check.md`) and used only the figures that held up. Velocity went down before answering our competitor prompts, so the competitor research is our own reading of vendor pages, not Velocity.

Tools used: Kearney Velocity AI, Claude, Python, SQLite, HTML, JavaScript.
