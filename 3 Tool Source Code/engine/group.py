"""Step 3. Decide which part numbers are the same part, which are close, and which only look alike.

Every pair of purchased parts (within a plant and across plants) gets one of:
  SAME          identical on every spec the data holds -> one part, several numbers
  CLOSE_SPEC    differs on a field an engineer may accept -> engineering review
  DO_NOT_MERGE  differs on a field that changes function or safety -> keep separate
  (no relation) different parts

The rules live in SPEC_RULES below as plain data, so an engineer can read and change them.
"""
import itertools

from . import text as T

# What a difference in each attribute means.
#   DISTINCT      the parts fit different products; not a look-alike at all
#   CRITICAL      changes function or safety -> DO_NOT_MERGE
#   REVIEW        may be acceptable -> engineering review, if the gap is within max_gap
SPEC_RULES = {
    "model":             ("DISTINCT", None),
    "cup size":          ("DISTINCT", None),
    "holds":             ("DISTINCT", None),
    "thread":            ("DISTINCT", None),
    "wire gauge AWG":    ("DISTINCT", None),
    "volume L":          ("DISTINCT", None),
    "temperature C":     ("CRITICAL", None),
    "power W":           ("CRITICAL", None),
    "voltage V":         ("CRITICAL", None),
    "wires":             ("CRITICAL", None),
    "current A":         ("REVIEW", 1.00),   # a higher current rating can often replace a lower one
    "thread length mm":  ("REVIEW", 0.25),
    "wall mm":           ("REVIEW", 0.25),
    "diameter mm":       ("REVIEW", 0.25),
    "length m":          ("REVIEW", 0.25),
    "size mm":           ("REVIEW", 0.25),
    "board grade ECT":   ("REVIEW", 0.25),
}


def shape(s):
    """A field with its digits masked: '8 LEADS, 320 MM' -> '# LEADS, # MM'."""
    import re
    return re.sub(r"[\d.]+", "#", (s or "").upper()).strip()


def compare(a, b):
    """Compare two part records (dicts). Returns (relation, confidence, differences, evidence) or None."""
    core_a, core_b = T.core_words(a["descr"]), T.core_words(b["descr"])
    cw = T.jaccard(core_a, core_b)
    full = T.similarity(a["descr"], b["descr"])
    same_mpn = bool(a["mpn"]) and a["mpn"] == b["mpn"]
    same_shapes = bool(a["rating"] or a["dimensions"]) and shape(a["rating"]) == shape(b["rating"]) \
        and shape(a["dimensions"]) == shape(b["dimensions"]) and bool(a["dimensions"]) and bool(a["rating"])
    if not (same_mpn or cw >= 0.6 or full >= 0.7 or (cw >= 0.5 and same_shapes)):
        return None

    attrs_a = T.attributes(a["descr"], a["rating"], a["dimensions"], a["material"])
    attrs_b = T.attributes(b["descr"], b["rating"], b["dimensions"], b["material"])
    diffs, level = [], "SAME"
    for key in sorted(set(attrs_a) & set(attrs_b)):
        if attrs_a[key] == attrs_b[key]:
            continue
        kind, max_gap = SPEC_RULES.get(key, ("REVIEW", 0.25))
        try:
            va, vb = float(attrs_a[key]), float(attrs_b[key])
        except ValueError:          # a text value such as model "12P"
            va, vb = 0.0, 1.0
        if va == vb:
            continue
        gap = abs(va - vb) / max(va, vb)
        if kind == "DISTINCT" or (kind == "REVIEW" and gap > max_gap):
            return None
        diffs.append(f"{key}: {attrs_a[key]} vs {attrs_b[key]}")
        if kind == "CRITICAL":
            level = "DO_NOT_MERGE"
        elif level != "DO_NOT_MERGE":
            level = "CLOSE_SPEC"
    # fields compared as text
    if a["mfr"] and b["mfr"] and a["mfr"].upper() != b["mfr"].upper():
        diffs.append(f"maker: {a['mfr']} vs {b['mfr']}")
        if level == "SAME":
            level = "CLOSE_SPEC"
    ma, mb = T.token_set(a["material"]), T.token_set(b["material"])
    if ma and mb and not (ma <= mb or mb <= ma) and not any(d.startswith("board grade") for d in diffs):
        diffs.append(f"material: {a['material']} vs {b['material']}")
        if level == "SAME":
            level = "CLOSE_SPEC"
    if level == "SAME" and not (same_mpn or cw >= 0.8 or full >= 0.7):
        return None

    # how sure: missing spec fields on either side lower the confidence
    evidence = []
    if same_mpn:
        evidence.append(f"same manufacturer part number {a['mpn']}")
    evidence.append(f"descriptions share {round(full * 100)}% of words")
    compared = sorted(set(attrs_a) & set(attrs_b))
    if compared:
        evidence.append("compared: " + ", ".join(compared))
    missing = [f for f in ("material", "rating", "dimensions", "compliance")
               if bool(a[f]) != bool(b[f])]
    if missing:
        evidence.append("missing at one plant: " + ", ".join(missing))
    conf = 0.98 if same_mpn else 0.90
    conf -= 0.05 * len(missing)
    if not compared and not same_mpn:
        conf -= 0.05
    return level, round(max(conf, 0.5), 2), "; ".join(diffs), "; ".join(evidence)


def group_parts(db):
    cols = ["site", "item", "descr", "mfr", "mpn", "material", "rating", "compliance", "dimensions"]
    parts = [dict(zip(cols, r)) for r in db.execute(f"""
        SELECT {', '.join('p.' + c for c in cols)} FROM parts p
        JOIN item_current ic ON ic.site = p.site AND ic.item = p.item AND ic.current_item = p.item
        WHERE p.item_type = 'BUY' AND p.status = 'ACTIVE' ORDER BY p.site, p.item""")]
    for p in parts:
        for c in cols:
            p[c] = p[c] or ""
    legacy = {(r[0], r[1]): r[2] for r in db.execute(
        "SELECT dayton_item, elpaso_part, status FROM sh_legacy_part_crossref_2023")}

    pairs = []
    for a, b in itertools.combinations(parts, 2):
        res = compare(a, b)
        if not res:
            continue
        level, conf, diffs, evidence = res
        key = (a["item"], b["item"]) if a["site"] == "Dayton" else (b["item"], a["item"])
        if key in legacy and level == "SAME":
            evidence += f"; also in the 2023 cross-reference ({legacy[key].lower()})"
            conf = min(0.99, conf + 0.05)
        pairs.append((a["site"], a["item"], b["site"], b["item"], level, conf, diffs, evidence))

    db.execute("DROP TABLE IF EXISTS part_pair")
    db.execute("""CREATE TABLE part_pair (site_a TEXT, item_a TEXT, site_b TEXT, item_b TEXT,
                  relation TEXT, confidence REAL, differences TEXT, evidence TEXT)""")
    db.executemany("INSERT INTO part_pair VALUES (?,?,?,?,?,?,?,?)", pairs)

    # ---- groups: part numbers joined by SAME are one part --------------------------------
    parent = {(p["site"], p["item"]): (p["site"], p["item"]) for p in parts}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for sa, ia, sb, ib, level, *_ in pairs:
        if level == "SAME":
            ra, rb = find((sa, ia)), find((sb, ib))
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    members = {}
    for p in parts:
        members.setdefault(find((p["site"], p["item"])), []).append(p)
    db.execute("DROP TABLE IF EXISTS part_group")
    db.execute("CREATE TABLE part_group (group_id TEXT, group_name TEXT, site TEXT, item TEXT, numbers_in_group INTEGER)")
    gid_of = {}
    for n, (root, ms) in enumerate(sorted(members.items()), 1):
        gid = f"G{n:03d}"
        # the Dayton description reads best as a name ("NOUN, DETAIL, DETAIL")
        name = sorted(ms, key=lambda m: (m["site"] != "Dayton", m["item"]))[0]["descr"].upper()
        for m in ms:
            gid_of[(m["site"], m["item"])] = gid
            db.execute("INSERT INTO part_group VALUES (?,?,?,?,?)", (gid, name, m["site"], m["item"], len(ms)))
    # old and service numbers follow their current part into its group
    db.execute("""INSERT INTO part_group
                  SELECT g.group_id, g.group_name, ic.site, ic.item, g.numbers_in_group
                  FROM item_current ic JOIN part_group g ON g.site = ic.site AND g.item = ic.current_item
                  WHERE ic.item <> ic.current_item""")
    # parts that are not purchased (made in house, finished goods) get a group of their own
    n = len(members)
    for site, item, descr in db.execute("""SELECT p.site, p.item, p.descr FROM parts p
            WHERE NOT EXISTS (SELECT 1 FROM part_group g WHERE g.site = p.site AND g.item = p.item)""").fetchall():
        n += 1
        db.execute("INSERT INTO part_group VALUES (?,?,?,?,1)", (f"G{n:03d}", descr.upper(), site, item))
    db.execute("CREATE INDEX part_group_key ON part_group (site, item)")

    # ---- families: groups tied by CLOSE_SPEC or DO_NOT_MERGE ----------------------------------
    fparent = {g: g for g in set(gid_of.values())}

    def ffind(x):
        while fparent[x] != x:
            fparent[x] = fparent[fparent[x]]
            x = fparent[x]
        return x
    db.execute("DROP TABLE IF EXISTS group_pair")
    db.execute("CREATE TABLE group_pair (group_a TEXT, group_b TEXT, relation TEXT, differences TEXT, confidence REAL)")
    seen = {}
    for sa, ia, sb, ib, level, conf, diffs, _ in pairs:
        if level == "SAME":
            continue
        ga, gb = sorted((gid_of[(sa, ia)], gid_of[(sb, ib)]))
        if ga == gb:
            continue
        # if two groups are tied by several pairs, the most severe relation wins
        if (ga, gb) not in seen or level == "DO_NOT_MERGE":
            seen[(ga, gb)] = (level, diffs, conf)
        fa, fb = ffind(ga), ffind(gb)
        if fa != fb:
            fparent[max(fa, fb)] = min(fa, fb)
    db.executemany("INSERT INTO group_pair VALUES (?,?,?,?,?)", [(a, b, *v) for (a, b), v in seen.items()])
    db.execute("DROP TABLE IF EXISTS part_family")
    db.execute("CREATE TABLE part_family (family_id TEXT, group_id TEXT)")
    fam = {}
    for g in fparent:
        fam.setdefault(ffind(g), []).append(g)
    n = 0
    for root, gs in sorted(fam.items()):
        if len(gs) > 1:
            n += 1
            db.executemany("INSERT INTO part_family VALUES (?,?)", [(f"F{n:02d}", g) for g in sorted(gs)])

    # ---- check the old cross-reference against the specs -------------------------------------
    db.execute("DROP TABLE IF EXISTS legacy_xref_check")
    db.execute("CREATE TABLE legacy_xref_check (dayton_item TEXT, elpaso_part TEXT, legacy_status TEXT, verdict TEXT, detail TEXT)")
    rel = {}
    for sa, ia, sb, ib, level, conf, diffs, ev in pairs:
        rel[(ia, ib)] = rel[(ib, ia)] = (level, diffs)
    cur = {(s, i): c for s, i, c in db.execute("SELECT site, item, current_item FROM item_current")}
    for (d, e), status in legacy.items():
        e_cur = cur.get(("El Paso", e), e)
        note = "" if e_cur == e else f" ({e} is inactive; checked against its current number {e_cur})"
        r = rel.get((d, e_cur))
        if r and r[0] == "SAME":
            verdict, detail = "CONFIRMED", "Specs agree" + note
        elif r:
            verdict, detail = "CONFLICT", f"Specs disagree: {r[1]}. Do not use this row" + note
        else:
            verdict, detail = "NOT CONFIRMED", "The two descriptions and specs do not point to the same part" + note
        db.execute("INSERT INTO legacy_xref_check VALUES (?,?,?,?,?)", (d, e, status, verdict, detail))
    db.commit()
