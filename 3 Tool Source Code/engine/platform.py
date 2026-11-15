"""Step 8. Platform view: which parts a product family shares, what each model adds,
and where plants build the same thing differently.

Everything here is read from tables the earlier steps built (linked BOMs, part groups,
look-alike relations, costs). Nothing is typed in by hand except which models form the
family, which a consultant sets in config/mapping.json under "platform".

Words used:
  unit     one purchasable thing in a build: a part group, or an assembly (made or bought)
  slot     one job in the product (housing, power cord, heater). Units that do the same job
           in different builds share a slot.
  CORE     the slot is filled by the same unit in every build of the family
  SPLIT    the slot is in every build, but more than one unit fills it
  MODULE   the slot is only in some models; slots used by the same models form a module
"""
import json
import re

from . import text as T
from .export import nice, rows


def function_name(names):
    """A name for the job, from the parts that do it: 'HOUSING, BL-12, PP, BLACK' -> 'Housing, PP, black'."""
    for n in names:
        if "," in n:
            segs = [s.strip() for s in n.split(",")]
            keep = [s for s in segs if not re.search(r"\d", s)]
            return nice(", ".join(keep[:3]) or segs[0])
    return nice(names[0])


def build_platform(db, config_path="config/mapping.json"):
    with open(config_path) as f:
        cfg = json.load(f).get("platform", {})
    products = rows(db, "SELECT site, model FROM product ORDER BY model, site")
    fam_models = cfg.get("models") or sorted({p["model"] for p in products})
    builds = [p for p in products if p["model"] in fam_models]
    others = [p for p in products if p["model"] not in fam_models]
    bkey = lambda site, model: f"{site}|{model}"
    fam_keys = [bkey(b["site"], b["model"]) for b in builds]
    gname = dict(db.execute("SELECT DISTINCT group_id, group_name FROM part_group").fetchall())
    gid_of = {(s, i): g for s, i, g in db.execute("SELECT site, item, group_id FROM part_group")}

    # ---- assemblies made in house: their purchased children roll up into one unit --------------
    made = {}          # (site, model, child item) -> made assembly item
    for site, model, fg, item in db.execute("SELECT DISTINCT site, model, fg_item, item FROM bom_flat WHERE item_type='MAKE'").fetchall():
        for (child,) in db.execute("SELECT DISTINCT child FROM bom WHERE site=? AND parent=?", (site, item)):
            made[(site, model, child)] = item
    descr = {(s, i): d for s, i, d in db.execute("SELECT site, item, descr FROM parts")}
    bought_assy = {}   # normalised description -> group of an assembly some plant buys complete
    for site, item in db.execute("SELECT DISTINCT site, item FROM make_buy_changes").fetchall():
        bought_assy[T.norm(descr[(site, item)])] = gid_of[(site, item)]

    def unit_of(site, model, item, gid):
        """(unit id, how it is sourced, made-assembly item or None)"""
        parent = made.get((site, model, item))
        if not parent:
            return gid, "BOUGHT", None
        twin = bought_assy.get(T.norm(descr[(site, parent)]))
        return twin or gid_of[(site, parent)], "MADE", parent

    # ---- one record per (build, unit, sourcing) ------------------------------------------------
    use = {}           # (unit, how) -> {build key: {...}}
    for r in rows(db, "SELECT site, model, item, group_id, descr, qty_per_unit, cost_per_unit, note FROM product_cost_line"):
        unit, how, parent = unit_of(r["site"], r["model"], r["item"], r["group_id"])
        cell = use.setdefault((unit, how), {}).setdefault(bkey(r["site"], r["model"]),
                                                          {"cost": 0.0, "items": [], "note": None, "parent": parent})
        cell["cost"] += r["cost_per_unit"] or 0
        cell["items"].append(r["item"])
        cell["note"] = cell["note"] or r["note"]
    unit_name = {}
    for (unit, how), cells in use.items():
        parent = next((c["parent"] for c in cells.values() if c["parent"]), None)
        site = next(iter(cells)).split("|")[0]
        unit_name[(unit, how)] = descr[(site, parent)] if parent else gname[unit]

    # ---- slots: units that do the same job -----------------------------------------------------
    units = sorted({u for u, _ in use})
    builds_of = {u: set() for u in units}
    for (u, how), cells in use.items():
        builds_of[u] |= set(cells)
    parent = {u: u for u in units}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def join(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    relation = {}
    for a, b, rel, diff in db.execute("SELECT group_a, group_b, relation, differences FROM group_pair"):
        relation[(a, b)] = relation[(b, a)] = (rel, diff)
        if a in parent and b in parent:
            join(a, b)                      # look-alikes found in step 3 do the same job
    core = {u: frozenset(T.core_words(next(n for (uu, _), n in unit_name.items() if uu == u))) for u in units}
    for i, a in enumerate(units):
        for b in units[i + 1:]:
            # same describing words, and never used together in one build -> same job, different size or model
            if core[a] and core[a] == core[b] and not (builds_of[a] & builds_of[b]):
                join(a, b)
    slots = {}
    for u in units:
        slots.setdefault(find(u), []).append(u)

    saving = dict(db.execute("SELECT group_id, saving FROM opportunity WHERE opp_type='CLOSE_SPEC'").fetchall())
    out_slots = []
    for root, us in slots.items():
        variants = sorted(((u, how) for (u, how) in use if u in us),
                          key=lambda v: (-len([k for k in use[v] if k in fam_keys]), v))
        fam_variants = [v for v in variants if any(k in fam_keys for k in use[v])]
        if not fam_variants:
            continue                        # only used outside the family (e.g. 5-cup parts)
        covered = {k for v in fam_variants for k in use[v] if k in fam_keys}
        models = sorted({k.split("|")[1] for k in covered})
        cat = "MODULE" if covered != set(fam_keys) else ("CORE" if len(fam_variants) == 1 else "SPLIT")
        letters = {v: "ABCDEFGH"[i] for i, v in enumerate(variants)}
        cells = {}
        for v in variants:
            for k, c in use[v].items():
                cells[k] = {"v": letters[v], "cost": round(c["cost"], 4), "note": c["note"]}
        # what stands between this slot and one common part
        status, kinds = [], set()
        fam_units = sorted({u for u, _ in fam_variants})
        hows = {how for _, how in fam_variants}
        if hows == {"MADE", "BOUGHT"}:
            kinds.add("MAKE_BUY")
            status.append("Made in house at one plant, bought complete at the other")
        slot_saving = 0
        for i, a in enumerate(fam_units):
            for b in fam_units[i + 1:]:
                rel = relation.get((a, b))
                if rel and rel[0] == "CLOSE_SPEC":
                    kinds.add("REVIEW")
                    status.append(f"Near-identical ({rel[1]}): engineering review could make this one part")
                    slot_saving += saving.get(a, 0) + saving.get(b, 0)
                elif rel:
                    kinds.add("APART")
                    status.append(f"Must stay separate ({rel[1]})")
                elif len(fam_units) > 1 and "BY_MODEL" not in kinds:
                    kinds.add("BY_MODEL")
                    status.append("A different part per model, by design")
        by_plant = {}
        for v in fam_variants:
            for k in use[v]:
                if k in fam_keys:
                    by_plant.setdefault(k.split("|")[0], set()).add(letters[v])
        plant_split = len(fam_variants) > 1 and len(by_plant) > 1 and \
            not set.intersection(*by_plant.values())
        out_slots.append({
            "slot_id": root, "name": function_name([unit_name[v] for v in fam_variants]) if len(fam_variants) > 1 else nice(unit_name[fam_variants[0]]),
            "category": cat, "models": models, "kinds": sorted(kinds), "status": status, "saving": slot_saving,
            "plant_split": plant_split,
            "variants": [{"key": letters[v], "unit": v[0], "how": v[1], "name": nice(unit_name[v]),
                          "items": sorted({i for c in use[v].values() for i in c["items"]}),
                          "in_family": v in fam_variants} for v in variants],
            "cells": cells,
            "cost": max((cells[k]["cost"] for k in covered), default=0),
        })

    # ---- modules: slots that travel with the same models ---------------------------------------
    order = {"CORE": 0, "SPLIT": 1, "MODULE": 2}
    out_slots.sort(key=lambda s: (order[s["category"]], ",".join(s["models"]), -s["cost"]))
    modules = {}
    for s in out_slots:
        if s["category"] == "MODULE":
            modules.setdefault(",".join(s["models"]), []).append(s)
    out_modules = []
    for key, ss in modules.items():
        cost = {k: round(sum(s["cells"].get(k, {}).get("cost", 0) for s in ss), 4) for k in fam_keys
                if k.split("|")[1] in key.split(",")}
        out_modules.append({"models": key.split(","), "lead": ss[0]["name"], "slots": [s["slot_id"] for s in ss],
                            "parts": len(ss), "cost": cost})
        for s in ss:
            s["module"] = key

    # ---- cost of core, split and modules in each build -----------------------------------------
    material = {bkey(s, m): v for s, m, v in db.execute("SELECT site, model, material FROM product_cost")}
    out_builds = []
    for b in builds + others:
        k = bkey(b["site"], b["model"])
        tot = {"CORE": 0.0, "SPLIT": 0.0, "MODULE": 0.0}
        n = {"CORE": 0, "SPLIT": 0, "MODULE": 0}
        for s in out_slots:
            if k in s["cells"]:
                tot[s["category"]] += s["cells"][k]["cost"]
                n[s["category"]] += 1
        out_builds.append({"site": b["site"], "model": b["model"], "key": k, "in_family": b in builds,
                           "core": tot["CORE"], "split": tot["SPLIT"], "module": tot["MODULE"],
                           "n_core": n["CORE"], "n_split": n["SPLIT"], "n_module": n["MODULE"],
                           "material": material.get(k), "family_parts": sum(n.values()),
                           "all_parts": db.execute("SELECT COUNT(*) FROM product_cost_line WHERE site=? AND model=?",
                                                   (b["site"], b["model"])).fetchone()[0]})

    # ---- make or buy, on a full-cost basis -----------------------------------------------------
    std = {(p, i): (float(mins), float(rate), float(oh)) for p, i, mins, rate, oh in db.execute(
        "SELECT plant, item, std_minutes_per_unit, labor_rate_usd_per_hour, overhead_multiple_of_labor "
        "FROM sh_labor_and_overhead_standards")}
    make_buy = []
    for s in out_slots:
        if "MAKE_BUY" not in s["kinds"]:
            continue
        for (u, how), cells in use.items():
            if u not in slots[s["slot_id"]]:
                continue
            for k, c in cells.items():
                if k not in fam_keys:
                    continue
                site, model = k.split("|")
                labor = overhead = 0.0
                if how == "MADE":
                    mins, rate, oh = std.get((site, c["parent"]), (0, 0, 0))
                    labor = mins / 60 * rate
                    overhead = labor * oh
                change = db.execute("SELECT eff_date, note FROM make_buy_changes WHERE site=? AND item IN (%s)" %
                                    ",".join("?" * len(c["items"])), [site] + c["items"]).fetchone()
                make_buy.append({"slot": s["name"], "name": nice(unit_name[(u, how)]), "site": site, "model": model,
                                 "how": how, "parts": len(c["items"]), "material": c["cost"], "labor": labor,
                                 "overhead": overhead, "full": c["cost"] + labor + overhead,
                                 "changed": change[0] if change else None})
    make_buy.sort(key=lambda r: (r["name"], r["site"], r["model"]))

    fam_slots = out_slots
    review = [s for s in fam_slots if "REVIEW" in s["kinds"]]
    fam_units = {v["unit"] for s in fam_slots for v in s["variants"] if v["in_family"]}
    return {
        "family": {"name": cfg.get("family_name", "All products"), "models": fam_models,
                   "builds": [bkey(b["site"], b["model"]) for b in builds],
                   "others": [bkey(b["site"], b["model"]) for b in others]},
        "slots": out_slots, "modules": out_modules, "builds": out_builds, "make_buy": make_buy,
        "summary": {
            "units": len(fam_units), "slots": len(fam_slots),
            "part_numbers": db.execute("SELECT COUNT(DISTINCT site || item) FROM product_cost_line WHERE model IN (%s)"
                                       % ",".join("?" * len(fam_models)), fam_models).fetchone()[0],
            "parts": db.execute("SELECT COUNT(DISTINCT group_id) FROM product_cost_line WHERE model IN (%s)"
                                % ",".join("?" * len(fam_models)), fam_models).fetchone()[0],
            "core_review": len([s for s in review if s["category"] == "SPLIT"]),
            "core": len([s for s in fam_slots if s["category"] == "CORE"]),
            "split": len([s for s in fam_slots if s["category"] == "SPLIT"]),
            "module_slots": len([s for s in fam_slots if s["category"] == "MODULE"]),
            "review_slots": len(review), "review_saving": sum(s["saving"] for s in review),
            "apart_slots": len([s for s in fam_slots if "APART" in s["kinds"]]),
        },
    }
