"""Run the whole tool: python3 run.py <data folder>

Reads the client's files (never the answer key), links spend to parts and products,
sizes the savings, and writes out/linkage.db plus the dashboard.
"""
import sys
import time

from engine import export, extras, group, link, load


def build(data_dir, db_path="out/linkage.db"):
    t = time.time()
    db = load.load_all(data_dir, "config/mapping.json", db_path)
    link.link(db)                      # 02_link_spend.sql
    group.group_parts(db)
    link.run_sql(db, "03_prices.sql")
    extras.build_kits(db)
    link.run_sql(db, "04_products.sql")
    link.run_sql(db, "05_savings.sql")
    extras.build_notices(db)
    link.run_sql(db, "06_watch.sql")
    db.commit()
    return db, time.time() - t


if __name__ == "__main__":
    db, secs = build(sys.argv[1] if len(sys.argv) > 1 else "data")
    print(f"Built in {secs:.1f} seconds")
    for row in db.execute("SELECT readiness, opp_type, COUNT(*), ROUND(SUM(saving)) FROM opportunity GROUP BY 1, 2"):
        print(row)
    export.write_outputs(db, "out", scorecard={"build_seconds": round(secs, 1), "partial": True})
    print("Wrote out/dashboard.html and out/opportunities.csv")
