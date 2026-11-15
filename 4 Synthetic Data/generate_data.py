#!/usr/bin/env python3
"""Synthetic demo data for the BOM Cost Linkage tool (Kearney PERLab hackathon, Track 3). Coffee maker edition.

Fictional company: Larkfield Home Appliances, "BrewLine" drip coffee makers (4 models).
Two plants on two different systems with different part numbering and file layouts:
  Plant A = Dayton, OH   (system "Atlas",    UPPER_SNAKE columns, ISO dates)
  Plant B = El Paso, TX  (system "Meridian", spaced column names, US dates, acquired 2023)
Everything here is invented. Company and supplier names are fictional. No client data.

Run:  python3 generate_data.py <output_dir>
Deterministic: same seed, same files, on every run (no Python sets feed the random stream).
"""
import csv, json, math, os, random, sys
from datetime import date, timedelta
from collections import defaultdict, OrderedDict

SEED = 20261115
R = random.Random(SEED)
OUT = sys.argv[1] if len(sys.argv) > 1 else "data"
MONTHS = [(2025, 11), (2025, 12)] + [(2026, m) for m in range(1, 11)]
NEXT = [(2026, 11), (2026, 12)] + [(2027, m) for m in range(1, 11)]
PERIOD_END = date(2026, 10, 31)
PLANT_NAME = {"A": "Dayton", "B": "El Paso"}

MODELS = OrderedDict([
    ("BL-5",   dict(size="5",  ctrl="S", carafe="GLASS",   watt=650,  name="5-CUP COMPACT")),
    ("BL-12",  dict(size="12", ctrl="S", carafe="GLASS",   watt=900,  name="12-CUP CLASSIC")),
    ("BL-12P", dict(size="12", ctrl="P", carafe="GLASS",   watt=900,  name="12-CUP PROGRAMMABLE")),
    ("BL-12T", dict(size="12", ctrl="P", carafe="THERMAL", watt=1000, name="12-CUP THERMAL")),
])
PLANT_MODELS = {"A": ["BL-5", "BL-12", "BL-12P"], "B": ["BL-12", "BL-12P", "BL-12T"]}
BASE_BUILDS = OrderedDict([(("A", "BL-5"), 6000), (("A", "BL-12"), 9000), (("A", "BL-12P"), 5000),
                           (("B", "BL-12"), 7000), (("B", "BL-12P"), 6000), (("B", "BL-12T"), 1500)])
SHAKEUP_FROM = date(2026, 9, 1)         # imported glass carafes: lead time 4 weeks becomes 8
MAKE_TO_BUY_B = date(2026, 5, 1)       # El Paso stops assembling the heater assembly and buys it complete

# ---------------------------------------------------------------- canonical parts (the truth)
CP = OrderedDict()


def add(key, noun, attrs, comm, price, uom="EA", material="", dims="", rating="", comp="", tol="", mfr="", mpn="", lead=21, moq=500, kind="buy", dwg=False, note=""):
    CP[key] = dict(key=key, noun=noun, attrs=attrs, comm=comm, price=price, uom=uom, material=material, dims=dims, rating=rating, comp=comp, tol=tol,
                   mfr=mfr, mpn=mpn, lead=lead, moq=moq, kind=kind, dwg=dwg, note=note)


FOOD = "NSF/ANSI 51 FOOD CONTACT"
for m, pr in (("BL-5", 1.85), ("BL-12", 2.40), ("BL-12P", 2.55), ("BL-12T", 2.70)):
    add(f"HOUSING:{m}", "HOUSING", [m, "PP", "BLACK"], "PLASTICS", pr, material="PP COPOLYMER UL94 HB", dims="SEE DRAWING", tol="ISO 20457 TG6", lead=21, moq=500, dwg=True)
for s, d in (("5", "150X190"), ("12", "180X230")):
    add(f"BASE:{s}", "BASE PLATE", [f"{s}-CUP", "PP", "BLACK"], "PLASTICS", {"5": 0.62, "12": 0.78}[s], material="PP COPOLYMER", dims=d + " MM", tol="ISO 20457 TG6", dwg=True)
    add(f"TANK:{s}", "WATER TANK", [f"{s}-CUP", "PP", "CLEAR"], "PLASTICS", {"5": 0.95, "12": 1.20}[s], material="PP CLARIFIED", dims={"5": "0.75 L", "12": "1.8 L"}[s], comp=FOOD, tol="ISO 20457 TG6", dwg=True)
    add(f"LID:{s}", "TANK LID", [f"{s}-CUP", "PP", "BLACK"], "PLASTICS", {"5": 0.30, "12": 0.36}[s], material="PP COPOLYMER", comp=FOOD, tol="ISO 20457 TG6", dwg=True)
    add(f"BASKET:{s}", "FILTER BASKET", [f"{s}-CUP", "PP", "BLACK"], "PLASTICS", {"5": 0.42, "12": 0.55}[s], material="PP COPOLYMER", dims={"5": "#2 CONE", "12": "#4 CONE"}[s], comp=FOOD, tol="ISO 20457 TG6", dwg=True)
    add(f"CARAFE:{s}:GLASS", "CARAFE", [f"{s}-CUP", "GLASS", "BLACK HANDLE"], "GLASS", {"5": 1.90, "12": 2.45}[s], material="BOROSILICATE 3.3", dims={"5": "0.75 L", "12": "1.8 L"}[s], comp="FDA FOOD CONTACT", lead=28, moq=500, dwg=True)
    add(f"CLID:{s}", "CARAFE LID", [f"{s}-CUP", "PP", "BLACK", "ONE-PIECE"], "PLASTICS", {"5": 0.22, "12": 0.26}[s], material="PP COPOLYMER", comp=FOOD, tol="ISO 20457 TG6", dwg=True)
    add(f"WARMPLATE:{s}", "WARMING PLATE", [f"{s}-CUP", "STEEL", "NON-STICK"], "METAL", {"5": 0.85, "12": 1.05}[s], material="SPCC 0.8 MM", dims={"5": "DIA 105", "12": "DIA 125"}[s] + " MM", tol="FLATNESS 0.3", dwg=True)
    add(f"INSERT:{s}", "PULP TRAY", [f"{s}-CUP", "MOLDED FIBER"], "PACKAGING", {"5": 0.21, "12": 0.26}[s], material="RECYCLED FIBER", lead=14, moq=1000)
add("CLID:5:TOP", "CARAFE LID TOP", ["5-CUP", "PP", "BLACK"], "PLASTICS", 0.14, material="PP COPOLYMER", comp=FOOD, dwg=True, note="obsolete from 2026-04")
add("CLID:5:HINGE", "CARAFE LID HINGE", ["5-CUP", "PP", "BLACK"], "PLASTICS", 0.10, material="PP COPOLYMER", comp=FOOD, dwg=True, note="obsolete from 2026-04")
add("SHOWER", "SHOWERHEAD", ["PP", "BLACK", "9-HOLE"], "PLASTICS", 0.18, material="PP COPOLYMER", dims="DIA 60 MM", comp=FOOD, tol="ISO 20457 TG6", dwg=True)
add("CARAFE:12:THERMAL", "THERMAL CARAFE", ["12-CUP", "STAINLESS", "DOUBLE WALL", "WITH LID"], "DRINKWARE", 7.80, material="SS 304", dims="1.8 L", comp="FDA FOOD CONTACT", mfr="SteelBrew", mpn="SB-TC18", lead=42, moq=300)
for w, pr in ((650, 1.60), (900, 1.95), (1000, 2.20)):
    add(f"HEATER:{w}W", "HEATING ELEMENT", [f"{w}W", "120V", "ALUMINUM TUBE", "U-SHAPE"], "HEATING", pr, material="AL 6063 / NICR", dims="U 95X120 MM", rating=f"{w} W 120 V", comp="UL RECOGNIZED", tol="FLATNESS 0.2", lead=28, moq=500, dwg=True)
add("TSTAT:105C", "THERMOSTAT", ["BIMETAL", "105C", "NC", "10A"], "THERMAL", 0.28, rating="105 C OPEN, 10 A 250 V", comp="UL RECOGNIZED", mfr="Thermotek", mpn="TS-105-NC", lead=21, moq=1000)
add("TFUSE:216C:TT", "THERMAL FUSE", ["216C", "10A", "AXIAL"], "THERMAL", 0.11, rating="216 C, 10 A 250 V", comp="UL RECOGNIZED", mfr="Thermotek", mpn="TF-216-10", lead=21, moq=2000)
add("TFUSE:216C:SF", "THERMAL FUSE", ["216C", "10A", "AXIAL"], "THERMAL", 0.12, rating="216 C, 10 A 250 V", comp="UL RECOGNIZED", mfr="Sunfuse", mpn="SF216", lead=21, moq=2000, note="other maker, same rating")
add("TFUSE:229C:SF", "THERMAL FUSE", ["229C", "10A", "AXIAL"], "THERMAL", 0.12, rating="229 C, 10 A 250 V", comp="UL RECOGNIZED", mfr="Sunfuse", mpn="SF229", lead=21, moq=2000, note="higher trip temperature for the 1000 W thermal model")
add("HBRACKET", "HEATER BRACKET", ["STEEL", "ZN"], "METAL", 0.14, material="SPCC 1.0 MM ZN", dims="110X22 MM", dwg=True)
add("TUBE:8x1.5", "SILICONE TUBE", ["8MM ID", "1.5MM WALL", "TRANSLUCENT"], "RUBBER", 0.62, uom="M", material="SILICONE 60 SHORE A", dims="ID 8.0 WALL 1.5 MM", comp="FDA 21 CFR 177.2600", lead=14, moq=100)
add("TUBE:8x1.6", "SILICONE TUBE", ["8MM ID", "1.6MM WALL", "TRANSLUCENT"], "RUBBER", 0.66, uom="M", material="SILICONE 60 SHORE A", dims="ID 8.0 WALL 1.6 MM", comp="FDA 21 CFR 177.2600", lead=14, moq=100, note="0.1 mm thicker wall")
add("CHKVALVE", "CHECK VALVE", ["8MM", "SILICONE", "DUCKBILL"], "RUBBER", 0.09, material="SILICONE 50 SHORE A", dims="8 MM", comp="FDA 21 CFR 177.2600", lead=14, moq=2000)
add("CLAMP:12", "HOSE CLAMP", ["SPRING", "12MM", "ZN"], "FASTENERS", 0.02, material="SPRING STEEL ZN", dims="12 MM", lead=10, moq=5000)
add("CORD:0.9M", "POWER CORD", ["2-PRONG", "SPT-2 18AWG", "0.9M", "BLACK"], "CORDS", 0.92, dims="0.9 M", rating="10 A 125 V", comp="UL LISTED", lead=21, moq=1000, dwg=True)
add("CORD:1.0M", "POWER CORD", ["2-PRONG", "SPT-2 18AWG", "1.0M", "BLACK"], "CORDS", 0.97, dims="1.0 M", rating="10 A 125 V", comp="UL LISTED", lead=21, moq=1000, dwg=True, note="0.1 m longer")
add("SWITCH:10A", "ROCKER SWITCH", ["SPST", "10A", "RED LED"], "ELECTRONICS", 0.31, dims="CUTOUT 19X13 MM", rating="10 A 125 V", comp="UL RECOGNIZED", mfr="Kontakt", mpn="KR-10-RL", lead=21, moq=1000)
add("SWITCH:16A", "ROCKER SWITCH", ["SPST", "16A", "RED LED"], "ELECTRONICS", 0.36, dims="CUTOUT 19X13 MM", rating="16 A 125 V", comp="UL RECOGNIZED", mfr="Kontakt", mpn="KR-16-RL", lead=21, moq=1000, note="higher current rating, same cutout")
add("PCB:P1", "CONTROL BOARD", ["PROGRAMMABLE", "LCD", "CLOCK/TIMER"], "ELECTRONICS", 3.10, dims="82X46 MM", rating="120 V", comp="UL RECOGNIZED; ROHS", lead=35, moq=500, dwg=True)
add("KEYPAD", "KEYPAD MEMBRANE", ["5-BUTTON", "ADHESIVE"], "ELECTRONICS", 0.35, dims="90X30 MM", lead=28, moq=1000, dwg=True)
add("HARNESS:S", "WIRE HARNESS", ["SWITCH MODELS", "5-WIRE"], "CORDS", 0.38, dims="5 LEADS, 280 MM", rating="105 C WIRE", comp="UL RECOGNIZED", lead=21, moq=1000, dwg=True)
add("HARNESS:P", "WIRE HARNESS", ["PROGRAMMABLE", "8-WIRE"], "CORDS", 0.55, dims="8 LEADS, 320 MM", rating="105 C WIRE", comp="UL RECOGNIZED", lead=21, moq=1000, dwg=True)
add("HARNESS:PT", "WIRE HARNESS", ["PROGRAMMABLE", "7-WIRE", "NO PLATE LEAD"], "CORDS", 0.53, dims="7 LEADS, 320 MM", rating="105 C WIRE", comp="UL RECOGNIZED", lead=21, moq=500, dwg=True, note="thermal model: no warming plate lead")
add("SCREW:M3x8", "SCREW", ["PAN HEAD", "SELF-TAPPING", "M3X8", "ZN"], "FASTENERS", 0.006, material="STEEL ZN", dims="M3 X 8", lead=10, moq=10000)
add("SCREW:M3x10", "SCREW", ["PAN HEAD", "SELF-TAPPING", "M3X10", "ZN"], "FASTENERS", 0.0065, material="STEEL ZN", dims="M3 X 10", lead=10, moq=10000, note="one length step longer")
add("SCREW:M4x12", "SCREW", ["PAN HEAD", "SELF-TAPPING", "M4X12", "ZN"], "FASTENERS", 0.009, material="STEEL ZN", dims="M4 X 12", lead=10, moq=10000)
add("FOOT:12", "RUBBER FOOT", ["12MM", "BLACK", "ADHESIVE"], "RUBBER", 0.015, material="SBR 60 SHORE A", dims="DIA 12.0 MM", lead=14, moq=5000)
add("FOOT:12.5", "RUBBER FOOT", ["12.5MM", "BLACK", "ADHESIVE"], "RUBBER", 0.016, material="SBR 60 SHORE A", dims="DIA 12.5 MM", lead=14, moq=5000, note="0.5 mm larger")
for m, pr in (("BL-5", 0.58), ("BL-12", 0.66), ("BL-12P", 0.70), ("BL-12T", 0.74)):
    add(f"GIFTBOX:{m}", "GIFT BOX", [m, "4-COLOR", "E-FLUTE"], "PACKAGING", pr, material="E-FLUTE CORRUGATED", lead=14, moq=1000, dwg=True)
add("MANUAL:S", "MANUAL", ["SWITCH MODELS", "EN/ES/FR"], "PRINT", 0.07, lead=14, moq=5000)
add("MANUAL:P", "MANUAL", ["PROGRAMMABLE", "EN/ES/FR"], "PRINT", 0.09, lead=14, moq=5000)
add("RATINGLABEL", "RATING LABEL", ["SILVER PET", "UL MARK"], "PRINT", 0.012, lead=14, moq=10000)
add("POLYBAG", "POLY BAG", ["LDPE", "400X500MM"], "PACKAGING", 0.02, material="LDPE 40 MICRON", dims="400X500 MM", lead=10, moq=10000)
add("MC:5", "MASTER CARTON", ["HOLDS 6", "5-CUP", "ECT-32"], "PACKAGING", 0.95, material="C-FLUTE ECT-32", lead=14, moq=500)
add("MC:12:ECT32", "MASTER CARTON", ["HOLDS 4", "12-CUP", "ECT-32"], "PACKAGING", 1.10, material="C-FLUTE ECT-32", dims="490X400X370 MM", lead=14, moq=500, note="heavier board")
add("MC:12:ECT29", "MASTER CARTON", ["HOLDS 4", "12-CUP", "ECT-29"], "PACKAGING", 0.96, material="C-FLUTE ECT-29", dims="490X400X370 MM", lead=14, moq=500)
add("PACKKIT:12T", "PACKAGING KIT", ["BL-12T", "BOX+TRAY+MANUAL+BAG"], "PACKAGING", 0, lead=14, moq=300, kind="kit")
KIT_CONTENTS = {"PACKKIT:12T": [("GIFTBOX:BL-12T", 1), ("INSERT:12", 1), ("MANUAL:P", 1), ("POLYBAG", 1)]}
CP["PACKKIT:12T"]["price"] = round(sum(CP[k]["price"] * q for k, q in KIT_CONTENTS["PACKKIT:12T"]) * 0.98, 4)
for w in (650, 900, 1000):
    add(f"HTR:{w}", "HEATER ASSY", [f"{w}W", "WITH THERMOSTAT AND FUSES"], "ASSEMBLY", 0, kind="make", dwg=True)
for m, p in MODELS.items():
    add(f"FG:{m}", "COFFEE MAKER", [m, p["name"]], "FINISHED", 0, kind="fg")
for i, k in enumerate(CP):
    CP[k]["cid"] = f"CP-{i + 1:04d}"

# ---------------------------------------------------------------- BOM (truth)
def pv(slot, plant, model):
    """Plant variants: the two plants grew up apart, so the 'same' slot is not always the same part."""
    b = plant == "B"
    return {"CORD": "CORD:1.0M" if b else "CORD:0.9M", "SCREW:M3": "SCREW:M3x10" if b else "SCREW:M3x8",
            "TFUSE": ("TFUSE:229C:SF" if model == "BL-12T" else "TFUSE:216C:SF") if b else "TFUSE:216C:TT",
            "TUBE": "TUBE:8x1.6" if b else "TUBE:8x1.5", "FOOT": "FOOT:12.5" if b else "FOOT:12",
            "SWITCH": "SWITCH:16A" if b else "SWITCH:10A", "MC:12": "MC:12:ECT29" if b else "MC:12:ECT32"}[slot]


DUP_TAG = {("B", "CARAFE:12:GLASS", "BL-12P"), ("A", "SCREW:M4x12", "BL-5")}     # same part entered twice under two numbers at one plant


def bom_edges(model, plant):
    """List of (parent_key, child_key, qty, tag). tag 'DUP' = the duplicate item number is used on this BOM line."""
    p = MODELS[model]; s = p["size"]; fg = f"FG:{model}"; h = f"HTR:{p['watt']}"
    t = lambda k: "DUP" if (plant, k, model) in DUP_TAG else ""
    E = [(fg, f"HOUSING:{model}", 1), (fg, f"BASE:{s}", 1), (fg, f"TANK:{s}", 1), (fg, f"LID:{s}", 1), (fg, f"BASKET:{s}", 1), (fg, "SHOWER", 1)]
    if p["carafe"] == "GLASS":
        E += [(fg, f"CARAFE:{s}:GLASS", 1), (fg, f"CLID:{s}", 1), (fg, f"WARMPLATE:{s}", 1)]
    else:
        E += [(fg, "CARAFE:12:THERMAL", 1)]
    E += [(fg, h, 1), (h, f"HEATER:{p['watt']}W", 1), (h, "TSTAT:105C", 1), (h, pv("TFUSE", plant, model), 2), (h, "HBRACKET", 1)]
    E += [(fg, pv("TUBE", plant, model), 0.36), (fg, "CHKVALVE", 1), (fg, "CLAMP:12", 4), (fg, pv("CORD", plant, model), 1)]
    if p["ctrl"] == "S":
        E += [(fg, pv("SWITCH", plant, model), 1), (fg, "HARNESS:S", 1)]
    else:
        E += [(fg, "PCB:P1", 1), (fg, "KEYPAD", 1), (fg, "HARNESS:PT" if model == "BL-12T" else "HARNESS:P", 1)]
    E += [(fg, pv("SCREW:M3", plant, model), 10), (fg, "SCREW:M4x12", 4), (fg, pv("FOOT", plant, model), 4)]
    E += [(fg, f"GIFTBOX:{model}", 1), (fg, f"INSERT:{s}", 1), (fg, f"MANUAL:{p['ctrl']}", 1), (fg, "RATINGLABEL", 1), (fg, "POLYBAG", 1),
          (fg, "MC:5" if s == "5" else pv("MC:12", plant, model), round(1 / 6, 4) if s == "5" else 0.25)]
    return [(a, b, q, t(b)) for a, b, q in E]


def heater_bought(plant, d):
    return plant == "B" and d >= MAKE_TO_BUY_B


def purchased_requirements(model, plant, d):
    """Truth: what is actually bought per finished unit at this plant on date d -> {(key, tag): qty}."""
    E = bom_edges(model, plant); req = OrderedDict()
    for a, b, q, tag in E:
        if CP[b]["kind"] == "make":
            if heater_bought(plant, d):
                req[(b, "")] = req.get((b, ""), 0) + q
            continue
        if CP[a]["kind"] == "make" and heater_bought(plant, d):
            continue                                   # children of a bought assembly are reference only
        req[(b, tag)] = req.get((b, tag), 0) + q
    if plant == "B" and model == "BL-12T":             # El Paso buys the BL-12T packaging as a kit
        for k, q in KIT_CONTENTS["PACKKIT:12T"]:
            req.pop((k, ""), None)
        req[("PACKKIT:12T", "")] = 1
    if plant == "A" and model == "BL-5" and d < date(2026, 4, 1):      # two-piece carafe lid until the redesign
        req.pop(("CLID:5", ""), None); req[("CLID:5:TOP", "")] = 1; req[("CLID:5:HINGE", "")] = 1
    return req


# ---------------------------------------------------------------- suppliers (truth)
def sup(name, typ, state, iso9001, iso14001, certs, cap, group=""):
    return dict(name=name, type=typ, state=state, iso9001=iso9001, iso14001=iso14001, certs=certs, cap=cap, group=group)


SUP = OrderedDict([
    ("MVMO", sup("Miami Valley Molding", "Manufacturer", "OH", "Y", "Y", ["NSF/ANSI 51"], "Injection molding 80-650 t; food-contact PP; tool maintenance")),
    ("SUNB", sup("Sunbelt Plastics", "Manufacturer", "TX", "Y", "N", ["NSF/ANSI 51"], "Injection molding 120-450 t; food-contact PP")),
    ("TRES", sup("Tres Rios Molding", "Manufacturer", "TX", "N", "N", [], "Injection molding 90-300 t; no food-contact certification")),
    ("EMBR", sup("Emberline Heating Elements", "Manufacturer", "TN", "Y", "Y", ["UL"], "Tubular and cast-in heating elements; brazing")),
    ("HOTW", sup("Hotwire Components", "Manufacturer", "TX", "Y", "N", ["UL"], "Heating elements; heater sub-assembly with thermostat and fuses")),
    ("THRM", sup("Thermotek Controls", "Manufacturer", "OH", "Y", "Y", ["UL", "CSA"], "Bimetal thermostats; thermal fuses", group="Thermotek Group")),
    ("SUNF", sup("Sunfuse Devices", "Manufacturer", "CA", "Y", "N", ["UL"], "Thermal fuses and cutoffs")),
    ("ALLD", sup("Allied Industrial Supply", "Distributor", "IL", "Y", "N", [], "Distribution: fasteners, electrical components, MRO")),
    ("BUCK", sup("Buckeye Wire & Cable", "Manufacturer", "OH", "Y", "N", ["UL"], "Power cords; wire harnesses; overmolding")),
    ("RIOG", sup("Rio Grande Cable Assemblies", "Manufacturer", "TX", "Y", "N", ["UL"], "Power cords; wire harnesses")),
    ("LONE", sup("Lone Star Cordsets", "Manufacturer", "TX", "N", "N", [], "Power cords; UL file pending")),
    ("CIRC", sup("Circuitline EMS", "Manufacturer", "IL", "Y", "Y", ["UL", "IPC-A-610"], "PCB assembly; switches and keypads sourcing; functional test")),
    ("PASO", sup("Paso Electronics Assembly", "Manufacturer", "TX", "Y", "N", ["UL"], "PCB assembly; box build")),
    ("CRYS", sup("Crystal River Glassworks", "Manufacturer", "WV", "Y", "N", ["FDA"], "Borosilicate blow molding; handle assembly")),
    ("VIDR", sup("Vidrio Norte Glass", "Importer", "TX", "Y", "N", ["FDA"], "Imported borosilicate carafes; ocean freight via Houston")),
    ("STEE", sup("SteelBrew Vacuumware", "Importer", "CA", "Y", "N", ["FDA"], "Imported stainless vacuum carafes")),
    ("STMP", sup("Stampwell Metal Products", "Manufacturer", "OH", "Y", "N", [], "Progressive die stamping; non-stick coating")),
    ("MESA", sup("Mesa Metal Stamping", "Manufacturer", "TX", "Y", "N", [], "Stamping; zinc plating outsourced")),
    ("ELFX", sup("Elastoflex Silicone", "Manufacturer", "OH", "Y", "N", ["FDA"], "Silicone extrusion and molding; food-grade compounds")),
    ("GULF", sup("Gulf Rubber Products", "Manufacturer", "TX", "Y", "N", ["FDA"], "Silicone and rubber extrusion; die cutting")),
    ("GMFA", sup("Great Miami Fastener", "Distributor", "OH", "Y", "N", [], "Fastener distribution; vendor-managed inventory")),
    ("BORD", sup("Border Fastener Supply", "Distributor", "TX", "N", "N", [], "Fastener distribution")),
    ("DAYC", sup("Dayton Corrugated", "Manufacturer", "OH", "Y", "N", ["FSC"], "Corrugated boxes; 4-color litho lamination; molded fiber")),
    ("SWBX", sup("Southwest Box & Label", "Manufacturer", "TX", "Y", "N", [], "Corrugated boxes; packaging kits")),
    ("PRNT", sup("PrintWorks Label & Manual", "Manufacturer", "KY", "Y", "N", ["UL label printer"], "Manuals; rating labels")),
    ("FRGT", sup("FreightLine Logistics", "Service", "IL", "N", "N", [], "LTL, truckload and air freight")),
    ("SAFE", sup("SafeMark Testing Laboratories", "Service", "IL", "Y", "N", ["ISO/IEC 17025"], "Electrical safety and food-contact testing")),
    ("MOLD", sup("Precision Mold Service", "Service", "OH", "N", "N", [], "Injection mold repair and maintenance")),
])
NAME_VARIANTS_B = {"EMBR": "EMBERLINE HEATING ELEMENTS, INC.", "THRM": "Thermotek Ctrls", "ALLD": "Allied Ind. Supply", "CIRC": "Circuitline E.M.S.",
                   "CRYS": "Crystal River Glass Works", "DAYC": "Dayton Corrugated Co.", "PRNT": "Printworks Label and Manual", "STMP": "Stampwell Metal Prod.",
                   "FRGT": "Freightline Logistics LLC", "SUNB": "SUNBELT PLASTICS"}
# who supplies what at each plant: commodity -> [(supplier, share of volume, price factor)]
SOURCING = {
    "A": {"PLASTICS": [("MVMO", 0.75, 1.00), ("SUNB", 0.25, 1.09)], "HEATING": [("EMBR", 1, 1.00)], "THERMAL": [("THRM", 0.8, 1.00), ("ALLD", 0.2, 1.14)],
          "CORDS": [("BUCK", 0.7, 1.00), ("RIOG", 0.3, 1.08)], "ELECTRONICS": [("CIRC", 1, 1.00)], "GLASS": [("CRYS", 1, 1.00)], "METAL": [("STMP", 1, 1.00)],
          "RUBBER": [("ELFX", 1, 1.00)], "FASTENERS": [("GMFA", 0.6, 1.00), ("ALLD", 0.4, 1.15)], "PACKAGING": [("DAYC", 1, 1.00)], "PRINT": [("PRNT", 1, 1.00)]},
    "B": {"PLASTICS": [("SUNB", 0.6, 1.08), ("TRES", 0.4, 0.96)], "HEATING": [("HOTW", 0.7, 1.13), ("EMBR", 0.3, 1.04)], "THERMAL": [("SUNF", 1, 1.00)],
          "CORDS": [("RIOG", 0.5, 1.10), ("LONE", 0.5, 0.97)], "ELECTRONICS": [("PASO", 0.8, 1.09), ("CIRC", 0.2, 1.03)], "GLASS": [("VIDR", 0.7, 0.95), ("CRYS", 0.3, 1.07)],
          "DRINKWARE": [("STEE", 1, 1.00)], "METAL": [("MESA", 0.6, 1.12), ("STMP", 0.4, 1.06)], "RUBBER": [("GULF", 1, 1.12)],
          "FASTENERS": [("BORD", 0.5, 1.22), ("ALLD", 0.5, 1.15)], "PACKAGING": [("SWBX", 0.7, 1.10), ("DAYC", 0.3, 1.14)], "PRINT": [("PRNT", 1, 1.04)],
          "ASSEMBLY": [("HOTW", 1, 1.00)]},
}
SOURCING_KEY = {("B", "TSTAT:105C"): [("ALLD", 0.6, 1.18), ("THRM", 0.4, 1.06)], ("B", "PACKKIT:12T"): [("SWBX", 1, 1.00)], ("B", "FOOT:12.5"): [("GULF", 1, 1.10)]}
DISTRIBUTORS = ("ALLD", "GMFA", "BORD")
NEEDS = {"PLASTICS": "NSF/ANSI 51", "CORDS": "UL", "HEATING": "UL", "THERMAL": "UL", "GLASS": "FDA", "DRINKWARE": "FDA"}     # certification a supplier must hold, besides ISO 9001
FOOD_RUBBER = ("TUBE:", "CHKVALVE")


def sources(plant, key):
    return SOURCING_KEY.get((plant, key)) or SOURCING[plant][CP[key]["comm"]]


def qualified(s, key):
    v = SUP[s]; c = CP[key]
    if v["iso9001"] != "Y":
        return False
    need = NEEDS.get(c["comm"]) or ("FDA" if key.startswith(FOOD_RUBBER) else None)
    if c["comm"] == "PLASTICS" and not c["comp"]:
        need = None                                         # housings and base plates are not food-contact parts
    if s in DISTRIBUTORS and need:
        return True                                         # distributors resell the certified maker's part
    return need is None or need in v["certs"]


# stable small price differences per supplier and part, drawn once in a fixed order
JIT = {}
for plant in ("A", "B"):
    for key in CP:
        if CP[key]["kind"] in ("buy", "kit") or key.startswith("HTR:"):
            for s, share, fac in (SOURCING_KEY.get((plant, key)) or SOURCING[plant].get(CP[key]["comm"], [])):
                JIT[(plant, key, s)] = round(R.uniform(0.975, 1.025), 4)
for w in (900, 1000):          # price El Paso pays for the bought heater assembly: parts plus the supplier's assembly charge
    fz = "TFUSE:229C:SF" if w == 1000 else "TFUSE:216C:SF"
    CP[f"HTR:{w}"]["price"] = round((CP[f"HEATER:{w}W"]["price"] * 1.12 + CP["TSTAT:105C"]["price"] + 2 * CP[fz]["price"] + CP["HBRACKET"]["price"]) * 1.0 + 0.45, 4)
CP["HTR:650"]["price"] = 0
LEAKAGE_A = {"HOUSING:BL-12": 1.05, "CARAFE:12:GLASS": 1.06, "HEATER:900W": 1.04, "PCB:P1": 1.03}     # invoiced above the awarded quote from March 2026


def unit_price(key, plant, s, d, quoted=False):
    c = CP[key]
    fac = dict((x[0], x[2]) for x in sources(plant, key)).get(s, 1.0)
    p = c["price"] * fac * JIT.get((plant, key, s), 1.0)
    if quoted:
        return p
    if c["comm"] == "PLASTICS" and d >= date(2026, 5, 1):
        p *= 1.04                                           # resin surcharge
    if plant == "A" and key in LEAKAGE_A and d >= date(2026, 3, 1):
        p *= LEAKAGE_A[key]
    return p


# ---------------------------------------------------------------- plant item numbers
COMM_A = {"PLASTICS": "10", "METAL": "12", "HEATING": "20", "THERMAL": "22", "CORDS": "24", "ELECTRONICS": "26", "GLASS": "30", "DRINKWARE": "31",
          "RUBBER": "32", "FASTENERS": "50", "PACKAGING": "60", "PRINT": "62", "ASSEMBLY": "80", "FINISHED": "90"}
COMM_B = {"PLASTICS": "PLS", "METAL": "MTL", "HEATING": "HTG", "THERMAL": "THM", "CORDS": "CRD", "ELECTRONICS": "ELC", "GLASS": "GLS", "DRINKWARE": "DRK",
          "RUBBER": "RBR", "FASTENERS": "FST", "PACKAGING": "PKG", "PRINT": "PRT", "ASSEMBLY": "ASM", "FINISHED": "FGS"}
ABBR_B = {"HOUSING": "hsg", "BASE PLATE": "base plt", "WATER TANK": "water tank", "TANK LID": "tank lid", "FILTER BASKET": "filter bskt", "SHOWERHEAD": "showerhead",
          "CARAFE": "carafe", "CARAFE LID": "carafe lid", "WARMING PLATE": "warm plt", "THERMAL CARAFE": "thermal carafe", "HEATING ELEMENT": "htg element",
          "THERMOSTAT": "t-stat", "THERMAL FUSE": "thermal fuse", "HEATER BRACKET": "htr brkt", "SILICONE TUBE": "silicone tubing", "CHECK VALVE": "chk valve",
          "HOSE CLAMP": "hose clamp", "POWER CORD": "pwr cord", "ROCKER SWITCH": "rocker sw", "CONTROL BOARD": "ctrl board", "KEYPAD MEMBRANE": "keypad",
          "WIRE HARNESS": "harness", "SCREW": "PH tapping screw", "RUBBER FOOT": "rubber foot", "GIFT BOX": "gift box", "PULP TRAY": "pulp tray", "MANUAL": "manual",
          "RATING LABEL": "rating label", "POLY BAG": "polybag", "MASTER CARTON": "master ctn", "PACKAGING KIT": "pkg kit", "HEATER ASSY": "heater assy",
          "COFFEE MAKER": "coffee maker"}


def desc_a(key):
    c = CP[key]
    return (c["noun"] + ", " + ", ".join(c["attrs"])).upper()


def desc_b(key):
    c = CP[key]
    attrs = [a.replace("PAN HEAD", "").replace("SELF-TAPPING", "").replace("/", " ").title().replace("Mm", "mm").replace("Pp", "PP").replace("Zn", "ZP").replace("Bl-", "BL")
             .replace("Awg", "AWG").replace("Spt", "SPT").replace("Led", "LED").replace("Lcd", "LCD").replace("Spst", "SPST").replace("Ldpe", "LDPE").replace("Ect", "ECT")
             .replace("Nc", "NC").replace("En Es Fr", "EN ES FR").replace("Ul", "UL").replace("Pet", "PET") for a in c["attrs"]]
    return " ".join((" ".join(a for a in attrs if a) + " " + ABBR_B.get(c["noun"], c["noun"].lower())).split())


def uniq(seq):
    seen = {}; out = []
    for x in seq:
        if x not in seen:
            seen[x] = 1; out.append(x)
    return out


used = {"A": [], "B": []}
for plant, models in PLANT_MODELS.items():
    for m in models:
        used[plant].append(f"FG:{m}")
        for a, b, q, tag in bom_edges(m, plant):
            used[plant] += [a, b]
used["A"] += ["CLID:5:TOP", "CLID:5:HINGE"]; used["B"] += ["PACKKIT:12T"]
used = {p: uniq(v) for p, v in used.items()}
ITEM = {}; ITEM_OLD = {}; ALIAS = {}
seqA = defaultdict(lambda: R.randint(1000, 1400)); seqB = defaultdict(lambda: R.randint(100, 400))
for key in CP:
    c = CP[key]
    if key in used["A"]:
        pre = COMM_A[c["comm"]]; seqA[pre] += R.randint(3, 40); ITEM[("A", key)] = f"{pre}-{seqA[pre]}-00"
    if key in used["B"]:
        pre = COMM_B[c["comm"]]; seqB[pre] += R.randint(2, 30); ITEM[("B", key)] = f"{pre}{seqB[pre]:05d}"
seqA["50"] += R.randint(60, 120); ALIAS[("A", "SCREW:M4x12")] = f"50-{seqA['50']}-00"          # duplicate item numbers for the same part
seqB["GLS"] += R.randint(40, 90); ALIAS[("B", "CARAFE:12:GLASS")] = f"GLS{seqB['GLS']:05d}"
old = ITEM[("A", "CORD:0.9M")]; ITEM_OLD[("A", "CORD:0.9M")] = (old, date(2026, 1, 31)); ITEM[("A", "CORD:0.9M")] = old[:-2] + "01"      # recorded revision
seqB["RBR"] += R.randint(150, 300)
ITEM_OLD[("B", "CHKVALVE")] = (ITEM[("B", "CHKVALVE")], date(2026, 2, 28)); ITEM[("B", "CHKVALVE")] = f"RBR{seqB['RBR']:05d}"                 # renumbered, no record
LID_SWITCH = date(2026, 4, 1)


def item_on(plant, key, d, tag=""):
    if tag == "DUP":
        return ALIAS[(plant, key)]
    if (plant, key) in ITEM_OLD and d <= ITEM_OLD[(plant, key)][1]:
        return ITEM_OLD[(plant, key)][0]
    return ITEM[(plant, key)]


SUPID = {}
n = 200100
for s in SUP:
    n += R.randint(7, 90); SUPID[("A", s)] = str(n)
n = 20010
for s in SUP:
    n += R.randint(1, 30); SUPID[("B", s)] = f"V-{n}"

# purchase unit per plant: key -> (uom code, base units per purchase unit, price per)
PUOM = {"A": {}, "B": {}}
for k in CP:
    if k.startswith(("SCREW", "CLAMP", "FOOT", "POLYBAG")):
        PUOM["A"][k] = ("BX", 1000, 1)           # box of 1000
        PUOM["B"][k] = ("EA", 1, 1000)           # each, priced per 1000
    if k.startswith("TUBE"):
        PUOM["A"][k] = ("RL", 50, 1)             # 50 m roll
        PUOM["B"][k] = ("FT", 0.3048, 1)         # by the foot
PUOM["A"]["RATINGLABEL"] = ("RL", 1000, 1)       # roll of 1000 labels; this conversion is NOT in the client's table
PUOM["B"]["RATINGLABEL"] = ("EA", 1, 1000)
UOM_NAME_B = {"EA": "Each", "M": "Meter", "FT": "Foot"}

# ---------------------------------------------------------------- build volumes
BUILD = OrderedDict()
SEASON = {11: 1.10, 12: 0.85, 1: 0.80, 2: 0.85, 3: 0.92, 4: 0.95, 5: 1.00, 6: 1.00, 7: 1.05, 8: 1.15, 9: 1.25, 10: 1.25}    # builds peak ahead of the holidays
for (plant, m), base in BASE_BUILDS.items():
    for ym in MONTHS:
        BUILD[(plant, m, ym)] = int(round(base * SEASON[ym[1]] * R.uniform(0.92, 1.08) / 10.0)) * 10

# ---------------------------------------------------------------- transactions
PO = []
po_seq = {"A": 4700012000, "B": 600}
COST_A = {"PRODUCTION": "PROD-410", "SPARE": "SVC-900", "WARRANTY": "WTY-950"}; ACCT_B = {"PRODUCTION": "5000", "SPARE": "5400", "WARRANTY": "6100"}
SHIP_A = {"PRODUCTION": "DAY-MAIN", "SPARE": "SDC-01", "WARRANTY": "SDC-01"}; SHIP_B = {"PRODUCTION": "ELP RECEIVING", "SPARE": "ELP SERVICE CAGE", "WARRANTY": "ELP SERVICE CAGE"}


def new_po(plant):
    po_seq[plant] += R.randint(1, 9)
    return str(po_seq[plant]) if plant == "A" else f"EP{po_seq[plant]:06d}"


def rand_day(ym, lo=1, hi=24):
    return date(ym[0], ym[1], R.randint(lo, hi))


SUPP_PN = {}


def supp_pn(key, s):
    if (key, s) not in SUPP_PN:
        SUPP_PN[(key, s)] = f"{s[:3]}-{R.randint(100000, 999999)}" if s in DISTRIBUTORS else (CP[key]["mpn"] or f"{s[:2]}{R.randint(10000, 99999)}")
    return SUPP_PN[(key, s)]


def add_po_line(plant, d, s, key, base_qty, bucket="PRODUCTION", tag="", cost=None, ship=None, item_override=None, po=None, line=None, cause=None, method="EXACT_ITEM"):
    c = CP[key]
    uom, conv, per = PUOM[plant].get(key, (c["uom"], 1, 1))
    qty = int(math.ceil(base_qty / conv - 1e-9))
    up_base = unit_price(key, plant, s, d) * R.uniform(0.996, 1.004)
    up = round(up_base * conv * per, 4 if up_base * conv * per < 5 else 2)
    item = item_override if item_override is not None else item_on(plant, key, d, tag)
    causes = list(cause or [])
    if (plant, key) in ITEM_OLD and item == ITEM_OLD[(plant, key)][0] and item_override is None:
        causes.append("SUPERSEDED_ITEM"); method = "SUPERSESSION_TABLE" if plant == "A" else "DESCRIPTION_SIMILARITY"
    if key in ("CLID:5:TOP", "CLID:5:HINGE"):
        causes.append("SUPERSEDED_ITEM"); method = "SUPERSESSION_TABLE"
    if tag == "DUP":
        causes.append("DUPLICATE_ITEM_NUMBER")
    if conv != 1 or per != 1:
        causes.append("UOM_CONVERSION")
    if key.startswith("HTR:") or key.startswith("PACKKIT"):
        causes.append("MAKE_VS_BUY_LEVEL" if key.startswith("HTR:") else "SUPPLIER_KIT"); method = "EXACT_ITEM" if key.startswith("HTR:") else "KIT_CONTENTS"
    row = dict(plant=plant, po=po or "", line=line or 0, date=d, sup=s, item=item, supp_pn="", desc=desc_a(key) if plant == "A" else desc_b(key), qty=qty, uom=uom,
               price=up, per=per, amount=round(qty * up / per, 2), cost=(COST_A if plant == "A" else ACCT_B)[bucket] if cost is None else cost,
               ship=(SHIP_A if plant == "A" else SHIP_B)[bucket] if ship is None else ship, quote="", key=key, tag=tag, bucket=bucket, causes=causes, method=method,
               base_qty=round(qty * conv, 4), resolvable="Y")
    PO.append(row)
    return row


# 1) production replenishment: high-value parts monthly from every approved source, small parts quarterly
ANNUAL = defaultdict(float)
for plant, models in PLANT_MODELS.items():
    for m in models:
        for ym in MONTHS:
            for (k, tag), q in purchased_requirements(m, plant, date(ym[0], ym[1], 15)).items():
                ANNUAL[(plant, k, tag)] += q * BUILD[(plant, m, ym)]
for plant, models in PLANT_MODELS.items():
    slots = uniq([kt for m in models for ym in MONTHS for kt in purchased_requirements(m, plant, date(ym[0], ym[1], 15))])
    for (key, tag) in slots:
        cadence = 1 if ANNUAL[(plant, key, tag)] * CP[key]["price"] > 20000 else 3
        for i, ym in enumerate(MONTHS):
            if i % cadence != 0:
                continue
            need = sum(purchased_requirements(m, plant, date(y2[0], y2[1], 15)).get((key, tag), 0) * BUILD[(plant, m, y2)]
                       for m in models for y2 in MONTHS[i:i + cadence])
            if need <= 0:
                continue
            srcs = sources(plant, key)
            if tag == "DUP":                         # the duplicate number is bought from the second source only
                srcs = [srcs[-1]]
            if cadence == 3:                         # small parts: one supplier per order
                x = R.random(); acc = 0.0; pick = srcs[-1]
                for sr in srcs:
                    acc += sr[1]
                    if x < acc:
                        pick = sr
                        break
                srcs = [(pick[0], 1.0, pick[2])]
            tot_share = sum(sr[1] for sr in srcs)
            for s, share, fac in srcs:
                add_po_line(plant, rand_day(ym), s, key, need * share / tot_share * R.uniform(0.97, 1.05), tag=tag)
by = OrderedDict()
for r in PO:
    by.setdefault((r["plant"], r["sup"], r["date"].year, r["date"].month), []).append(r)
for (plant, s, y, mth), rows in by.items():
    R.shuffle(rows)
    while rows:
        grp = rows[:R.randint(3, 8)]; rows = rows[len(grp):]
        po = new_po(plant); d = min(g["date"] for g in grp)
        for j, g in enumerate(grp):
            g["po"] = po; g["line"] = (j + 1) * 10 if plant == "A" else j + 1; g["date"] = d

# 2) spare parts: replacement carafes, baskets and lids sold through the service centre in Dayton; El Paso buys a few locally
SERVICE_KEYS = ["CARAFE:5:GLASS", "CARAFE:12:GLASS", "CLID:5", "CLID:12", "BASKET:5", "BASKET:12", "LID:12", "SHOWER"]
SVC = OrderedDict(); n = 8000
for k in SERVICE_KEYS:
    n += R.randint(3, 25); SVC[k] = f"SP-{n}"
SERVICE_KEYS_B = ["CARAFE:12:GLASS", "CLID:12", "BASKET:12", "CARAFE:12:THERMAL"]
for i, ym in enumerate(MONTHS):
    po = new_po("A"); d = rand_day(ym, 3, 26)
    for j, key in enumerate(R.sample(SERVICE_KEYS, 5)):
        if key == "CLID:5" and d < LID_SWITCH:
            key = "CLID:12"
        q = R.randint(150, 600) if key.startswith("CARAFE") else R.randint(100, 400)
        s = sources("A", key)[0][0]; mode = R.random()
        if mode < 0.65:
            r = add_po_line("A", d, s, key, q, bucket="SPARE", item_override=SVC[key], po=po, line=(j + 1) * 10, cause=["SERVICE_SKU"], method="SERVICE_CROSSREF")
            r["desc"] = "SERVICE PART - " + desc_a(key)
        elif mode < 0.85:
            add_po_line("A", d, s, key, q, bucket="SPARE", po=po, line=(j + 1) * 10, cause=["SPARE_ON_PRODUCTION_ITEM"])
        else:
            r = add_po_line("A", d, s, key, q, bucket="SPARE", cost="", ship="" if R.random() < 0.5 else SHIP_A["SPARE"], po=po, line=(j + 1) * 10,
                            cause=["SPARE_ON_PRODUCTION_ITEM", "PURPOSE_UNTAGGED"])
            if not r["ship"]:
                r["resolvable"] = "IDENTITY_ONLY"
    if i % 2 == 0:
        poB = new_po("B"); dB = rand_day(ym, 3, 26)
        for j, key in enumerate(R.sample(SERVICE_KEYS_B, 3)):
            tagged = R.random() < 0.7
            r = add_po_line("B", dB, sources("B", key)[0][0], key, R.randint(60, 250), bucket="SPARE", cost=ACCT_B["SPARE"] if tagged else "",
                            ship=SHIP_B["SPARE"] if tagged or R.random() < 0.5 else "", po=poB, line=j + 1,
                            cause=["SPARE_ON_PRODUCTION_ITEM"] + ([] if tagged else ["PURPOSE_UNTAGGED"]))
            if not tagged and not r["ship"]:
                r["resolvable"] = "IDENTITY_ONLY"

# 3) warranty claims (kept in a spreadsheet by the service team) and a few rush purchases against them
CLAIMS = []; serial = 5100000
FAIL = [("Carafe cracked on arrival", "CARAFE"), ("Does not heat", "HEATER"), ("Leaks from base", "TUBE"), ("Switch or display dead", "CTRL"), ("Lid hinge broken", "CLID"), ("Shuts off early", "TSTAT")]
for n_c in range(80):
    plant = R.choice(["A", "A", "B"]); m = R.choice(PLANT_MODELS[plant]); ym = R.choice(MONTHS); p = MODELS[m]
    f, kind = R.choice(FAIL)
    key = {"CARAFE": "CARAFE:12:THERMAL" if p["carafe"] == "THERMAL" else f"CARAFE:{p['size']}:GLASS", "HEATER": f"HEATER:{p['watt']}W", "TUBE": pv("TUBE", plant, m),
           "CTRL": "PCB:P1" if p["ctrl"] == "P" else pv("SWITCH", plant, m), "CLID": f"CLID:{p['size']}" if p["carafe"] == "GLASS" else "CARAFE:12:THERMAL",
           "TSTAT": "TSTAT:105C"}[kind]
    serial += R.randint(50, 4000); d = rand_day(ym, 1, 27)
    CLAIMS.append(dict(claim=f"WC-{26000 + n_c}", date=d, plant=plant, model=m, serial=f"BL{serial}", key=key,
                       part_ref=(ITEM[(plant, key)] if R.random() < 0.6 else (desc_b(key) if plant == "B" else desc_a(key))), qty=1,
                       cost=round(CP[key]["price"] * R.uniform(1.0, 1.1), 2), failure=f, resolution=R.choice(["Part replaced", "Unit replaced", "Unit replaced", "Refund"])))
for cl in R.sample([c for c in CLAIMS if c["key"].startswith("CARAFE")], 10):
    add_po_line(cl["plant"], cl["date"] + timedelta(days=2), sources(cl["plant"], cl["key"])[0][0], cl["key"], R.randint(20, 60), bucket="WARRANTY", po=new_po(cl["plant"]),
                line=10 if cl["plant"] == "A" else 1, cause=["WARRANTY_RUSH"])

# 3b) superseded numbers still on order at period end: a buyer copied an old PO
r = add_po_line("A", date(2026, 10, 21), "BUCK", "CORD:0.9M", 4000, item_override=ITEM_OLD[("A", "CORD:0.9M")][0], po=new_po("A"), line=10,
                cause=["SUPERSEDED_ITEM", "ORDERED_ON_OBSOLETE_NUMBER"], method="SUPERSESSION_TABLE")
r = add_po_line("B", date(2026, 10, 23), "GULF", "CHKVALVE", 12000, item_override=ITEM_OLD[("B", "CHKVALVE")][0], po=new_po("B"), line=1,
                cause=["SUPERSEDED_ITEM", "ORDERED_ON_OBSOLETE_NUMBER"], method="DESCRIPTION_SIMILARITY")

# 4) what makes the tie hard: free text, supplier part numbers only, quote references
QUOTE_NO = {}
prod = [r for r in PO if r["bucket"] == "PRODUCTION" and "ORDERED_ON_OBSOLETE_NUMBER" not in r["causes"]]
for r in prod:                                               # distributor lines keyed with the distributor's number only
    if r["sup"] in DISTRIBUTORS and R.random() < (0.30 if r["plant"] == "A" else 0.45):
        r["supp_pn"] = supp_pn(r["key"], r["sup"]); r["item"] = ""; r["desc"] = desc_b(r["key"]).upper()
        r["causes"].append("SUPPLIER_PART_NO_ONLY"); r["method"] = "VENDOR_PART_XREF"
for r in prod:                                               # El Paso orders the control board as free text against a quote
    if r["plant"] == "B" and r["key"] == "PCB:P1" and r["sup"] == "PASO":
        qn = QUOTE_NO.setdefault(("B", "PCB:P1"), f"Q-{R.randint(20000, 29999)}")
        r["item"] = ""; r["desc"] = f"Control boards per quote {qn}"; r["quote"] = qn; r["causes"].append("FREE_TEXT"); r["method"] = "QUOTE_REFERENCE"
FT = ["{d} for {m} line", "{d} - urgent", "{d} per buyer", "{d} (stock out)", "re-order {d}", "{d}"]
for r in prod:
    if r["item"] and "UOM_CONVERSION" not in r["causes"] and not r["tag"] and R.random() < (0.04 if r["plant"] == "A" else 0.07):
        r["item"] = ""; r["desc"] = R.choice(FT).format(d=desc_b(r["key"]), m=R.choice(PLANT_MODELS[r["plant"]]))
        if r["plant"] == "A":
            r["desc"] = r["desc"].upper()
        r["causes"].append("FREE_TEXT"); r["method"] = "DESCRIPTION_SIMILARITY"
UNRES = ["MISC PARTS PER QUOTE {n}", "REPLACEMENT PARTS", "AS PER ATTACHED LIST", "MATERIALS - SEE EMAIL", "SUNDRY ITEMS", "SAMPLES", "PARTS FOR LINE 2", "RUSH ORDER {n}"]
NONPROD = [("FRGT", "FREIGHT CHARGES {mon}", (900, 5200), "FREIGHT"), ("SAFE", "SAFETY TESTING - QUARTERLY FOLLOW-UP", (1800, 4200), "SERVICE"),
           ("MOLD", "MOLD REPAIR - {t}", (2400, 9800), "TOOLING"), ("DAYC", "PALLETS 48X40", (400, 1500), "MRO"), ("ALLD", "SHOP SUPPLIES", (150, 900), "MRO")]


def misc_line(plant, d, s, desc, amount, bucket, cause, resolvable, method):
    PO.append(dict(plant=plant, po=new_po(plant), line=10 if plant == "A" else 1, date=d, sup=s, item="", supp_pn="", desc=desc if plant == "A" else desc.capitalize(),
                   qty=1, uom="EA", price=amount, per=1, amount=amount, cost={"A": "", "B": ""}[plant] if bucket == "UNRESOLVED" else ("7200" if plant == "B" else "OH-700"),
                   ship="", quote="", key="", tag="", bucket=bucket, causes=[cause], method=method, base_qty=1, resolvable=resolvable))


for plant in ("A", "B"):
    for ym in MONTHS:
        misc_line(plant, rand_day(ym, 20, 27), "FRGT", f"FREIGHT CHARGES {ym[0]}-{ym[1]:02d}", round(R.uniform(900, 5200), 2), "NON_PRODUCT", "NON_PRODUCT_FREIGHT", "Y", "NON_PRODUCT_RULE")
        if ym[1] % 3 == 0:
            misc_line(plant, rand_day(ym), "SAFE", "SAFETY TESTING - QUARTERLY FOLLOW-UP", round(R.uniform(1800, 4200), 2), "NON_PRODUCT", "NON_PRODUCT_SERVICE", "Y", "NON_PRODUCT_RULE")
        if R.random() < 0.5:
            misc_line(plant, rand_day(ym), R.choice(["DAYC", "ALLD"]), R.choice(["PALLETS 48X40", "SHOP SUPPLIES", "STRETCH WRAP"]), round(R.uniform(150, 1500), 2), "NON_PRODUCT", "NON_PRODUCT_MRO", "Y", "NON_PRODUCT_RULE")
    for t in (["HOUSING BL-12 TOOL", "TANK 12-CUP TOOL", "BASKET TOOL"] if plant == "A" else ["HOUSING BL-12T TOOL", "CARAFE LID TOOL"]):
        misc_line(plant, rand_day(R.choice(MONTHS)), "MOLD", f"MOLD REPAIR - {t}", round(R.uniform(2400, 9800), 2), "NON_PRODUCT", "NON_PRODUCT_TOOLING", "Y", "NON_PRODUCT_RULE")
    for n_u in range(11 if plant == "A" else 13):
        s = R.choice(["ALLD", "SUNB", "RIOG", "PRNT", "DAYC"] if plant == "A" else ["ALLD", "BORD", "TRES", "LONE", "SWBX"])
        misc_line(plant, rand_day(R.choice(MONTHS)), s, R.choice(UNRES).format(n=R.randint(1000, 9999)), round(R.uniform(400, 9000), 2), "UNRESOLVED", "FREE_TEXT_NO_DETAIL", "N", "NONE")
# air freight to rescue late carafes at El Paso in the autumn (the lead time shake-up shows up as cost)
for ym in ((2026, 9), (2026, 10)):
    for k in range(2):
        misc_line("B", rand_day(ym), "FRGT", "AIR FREIGHT - EXPEDITE CARAFES", round(R.uniform(6800, 11500), 2), "NON_PRODUCT", "NON_PRODUCT_FREIGHT", "Y", "NON_PRODUCT_RULE")
PO.sort(key=lambda r: (r["plant"], r["date"], r["po"], r["line"]))

# ---------------------------------------------------------------- invoices
INV = []
inv_seq = {}
for r in PO:
    n_split = 1
    if r["bucket"] != "NON_PRODUCT" and r["qty"] >= 4:
        x = R.random(); n_split = 1 if x < 0.74 else (2 if x < 0.96 else 3)
    lead = CP[r["key"]]["lead"] if r["key"] in CP else 10
    if r["sup"] == "VIDR" and r["date"] >= SHAKEUP_FROM:
        lead = 56
    if "ORDERED_ON_OBSOLETE_NUMBER" in r["causes"]:
        n_split = 1
    remaining = r["qty"]
    for s in range(n_split):
        q = remaining if s == n_split - 1 else max(1, int(round(r["qty"] / n_split * R.uniform(0.7, 1.2))))
        q = min(q, remaining - (n_split - 1 - s)) if s < n_split - 1 else remaining
        remaining -= q
        d = r["date"] + timedelta(days=int(lead * R.uniform(0.8, 1.6)) + s * R.randint(5, 20))
        price = r["price"]; causes = []
        if R.random() < 0.025 and r["bucket"] != "NON_PRODUCT":
            price = round(price * R.uniform(1.01, 1.04), 4 if price < 5 else 2); causes.append("INVOICE_PRICE_VARIANCE")
        k = (r["plant"], r["sup"])
        if k not in inv_seq:
            inv_seq[k] = R.randint(10000, 80000)
        inv_seq[k] += R.randint(1, 60)
        row = dict(plant=r["plant"], inv=f"{r['sup']}{inv_seq[k]}", line=1, date=d, sup=r["sup"], po=r["po"], po_line=r["line"], item=r["item"], desc=r["desc"], qty=q,
                   uom=r["uom"], price=price, per=r["per"], amount=round(q * price / r["per"], 2),
                   type="MAT" if r["bucket"] != "NON_PRODUCT" else ("FRT" if "FREIGHT" in r["causes"][0] else "SVC"), key=r["key"], tag=r["tag"], bucket=r["bucket"],
                   causes=list(r["causes"]) + causes, method=r["method"], resolvable=r["resolvable"], true_po=r["po"], true_po_line=r["line"],
                   base_qty=round(q * (r["base_qty"] / r["qty"]) if r["qty"] else 0, 4), po_date=r["date"])
        if R.random() < 0.03 and r["bucket"] != "NON_PRODUCT":
            row["po"] = ""; row["po_line"] = ""; row["causes"].append("INVOICE_WITHOUT_PO_REF")
        INV.append(row)
for row in R.sample([i for i in INV if i["type"] == "MAT"], int(len(INV) * 0.06)):
    amt = round(R.uniform(35, 480), 2)
    INV.append(dict(row, line=2, po=row["true_po"], po_line="", item="", desc="FREIGHT" if row["plant"] == "A" else "Shipping & handling", qty=1, uom="EA", price=amt, per=1,
                    amount=amt, type="FRT", key="", tag="", bucket="NON_PRODUCT", causes=["NON_PRODUCT_FREIGHT"], method="NON_PRODUCT_RULE", resolvable="Y", true_po_line="", base_qty=1))
for row in R.sample([i for i in INV if i["type"] == "MAT" and i["qty"] >= 4 and i["key"] in CP], 12):
    q = max(1, row["qty"] // 5)
    INV.append(dict(row, inv=row["inv"] + "C", line=1, date=row["date"] + timedelta(days=R.randint(6, 30)), qty=-q, amount=round(-q * row["price"] / row["per"], 2), type="CRD",
                    causes=row["causes"] + ["CREDIT_NOTE"], base_qty=round(-q * (row["base_qty"] / row["qty"]), 4)))
INV_ALL = len(INV)
INV_LATE = [i for i in INV if i["date"] > PERIOD_END]
INV = [i for i in INV if i["date"] <= PERIOD_END]
INV.sort(key=lambda r: (r["plant"], r["date"], r["inv"], r["line"]))

# ---------------------------------------------------------------- RFQ / quotes
ALT = {"PLASTICS": ["MVMO", "SUNB", "TRES"], "HEATING": ["EMBR", "HOTW"], "THERMAL": ["THRM", "SUNF"], "CORDS": ["BUCK", "RIOG", "LONE"], "ELECTRONICS": ["CIRC", "PASO"],
       "GLASS": ["CRYS", "VIDR"], "METAL": ["STMP", "MESA"], "RUBBER": ["ELFX", "GULF"], "FASTENERS": ["GMFA", "BORD", "ALLD"], "PACKAGING": ["DAYC", "SWBX"],
       "DRINKWARE": ["STEE"], "PRINT": ["PRNT"], "ASSEMBLY": ["HOTW", "EMBR"]}
QUOTES = []; rfq_n = {"A": 8300, "B": 700}
for plant in ("A", "B"):
    keys = uniq([r["key"] for r in PO if r["plant"] == plant and r["bucket"] == "PRODUCTION" and r["key"] in CP])
    for key in keys:
        c = CP[key]
        if c["price"] < 0.2 or key.startswith("CLID:5:"):
            continue
        awarded = sources(plant, key)[0][0]
        rfq_n[plant] += R.randint(1, 4); rfq = f"RFQ-{rfq_n[plant]}" if plant == "A" else f"RQ{rfq_n[plant]:05d}"
        qd = date(2025, R.choice([8, 9, 10]), R.randint(1, 26)) if not key.startswith("HTR:") else date(2026, 3, R.randint(2, 20))
        est = int(sum(v for (p, k, t), v in ANNUAL.items() if p == plant and k == key))
        base = round(unit_price(key, plant, awarded, qd, quoted=True), 4 if c["price"] < 5 else 2)
        rows = [(awarded, base, c["lead"], c["moq"], "Y")]
        for s in ALT.get(c["comm"], []):
            if s == awarded or R.random() < 0.25:
                continue
            if not qualified(s, key) or R.random() < 0.2:      # cheaper on price, with a catch: no certification, or long lead time and a big minimum
                rows.append((s, base * R.uniform(0.88, 0.95), int(c["lead"] * R.uniform(1.5, 2.2)), c["moq"] * R.choice([3, 5, 10]), "N"))
            else:
                rows.append((s, base * R.uniform(1.02, 1.12), int(c["lead"] * R.uniform(0.8, 1.3)), c["moq"], "N"))
        for s, pr, lt, mq, aw in rows:
            qn = QUOTE_NO.get((plant, key)) if aw == "Y" else None
            QUOTES.append(dict(plant=plant, rfq=rfq, date=qd, item=ITEM_OLD[(plant, key)][0] if (plant, key) in ITEM_OLD else ITEM[(plant, key)], key=key, sup=s,
                               quote=qn or f"Q-{R.randint(30000, 99999)}", price=round(pr, 4 if pr < 5 else 2), lead=lt, moq=mq, est_annual_qty=est, awarded=aw, valid_to=date(2026, 12, 31)))

# ---------------------------------------------------------------- delivery dates: receipts and open orders
PROMISE = {"TRES": (0.85, 1.05), "LONE": (0.95, 1.20), "MVMO": (1.45, 1.70), "EMBR": (1.40, 1.65), "GMFA": (1.40, 1.70), "BUCK": (1.35, 1.60)}      # promise as a multiple of planned lead time
promised = {}
for r in PO:
    if r["bucket"] == "NON_PRODUCT":
        continue
    lead = CP[r["key"]]["lead"] if r["key"] in CP else 10
    lo, hi = PROMISE.get(r["sup"], (1.15, 1.50))
    promised[(r["plant"], r["po"], r["line"])] = r["date"] + timedelta(days=max(2, int(round(lead * R.uniform(lo, hi)))))
po_by = {(r["plant"], r["po"], r["line"]): r for r in PO}
received = defaultdict(float); REC = []; gr_seq = {"A": 5100031000, "B": 81200}
for i in INV:
    if i["type"] != "MAT":
        continue
    k = (i["plant"], i["true_po"], i["true_po_line"]); r = po_by[k]
    rd = max(r["date"] + timedelta(days=1), i["date"] - timedelta(days=R.randint(0, 6)))
    gr_seq[i["plant"]] += R.randint(1, 7)
    REC.append(dict(plant=i["plant"], doc=str(gr_seq["A"]) if i["plant"] == "A" else f"RCV-{gr_seq['B']}", date=rd, po=r["po"], line=r["line"], item=r["item"], qty=i["qty"],
                    uom=r["uom"], promised=promised[k], sup=r["sup"], key=r["key"], po_date=r["date"]))
    received[k] += i["qty"]
REC.sort(key=lambda g: (g["plant"], g["date"], g["doc"]))
OPEN = []
for r in PO:
    k = (r["plant"], r["po"], r["line"])
    if k not in promised:
        continue
    oq = round(r["qty"] - received.get(k, 0), 4)
    if oq <= 0:
        continue
    p = promised[k]
    if r["sup"] == "VIDR" and r["date"] >= SHAKEUP_FROM:
        conf = p + timedelta(days=R.randint(24, 31))             # imported carafes: 4 weeks became 8
    else:
        conf = p + timedelta(days=R.randint(0, 10))
        if conf <= PERIOD_END:
            conf = PERIOD_END + timedelta(days=R.randint(2, 21))
    OPEN.append(dict(r, open_qty=int(oq) if float(oq).is_integer() else oq, promised=p, conf=conf, slip=(conf - p).days))

# ---------------------------------------------------------------- supplier change notices
spend_pks = defaultdict(float); spend_pks_3m = defaultdict(float)
for i in INV:
    if i["key"] in CP:
        spend_pks[(i["plant"], i["key"], i["sup"])] += i["amount"]
        if i["date"] >= date(2026, 8, 1):
            spend_pks_3m[(i["plant"], i["key"], i["sup"])] += i["amount"]
USE_NOW = {(p, m): purchased_requirements(m, p, PERIOD_END) for p, ms in PLANT_MODELS.items() for m in ms}


def models_using(plant, key):
    """(models that buy the part directly today, models where it sits inside a bought assembly or kit)"""
    direct = [m for m in PLANT_MODELS[plant] if any(k == key for (k, t) in USE_NOW[(plant, m)])]
    inbom = [m for m in PLANT_MODELS[plant] if any(b == key for a, b, q, t in bom_edges(m, plant))]
    return direct, [m for m in inbom if m not in direct]


food_plastics = [k for k in CP if CP[k]["comm"] == "PLASTICS" and CP[k]["comp"] and not k.startswith("CLID:5:")]
glass = ["CARAFE:12:GLASS"]
NOTICES = [
    dict(id="PCN-2025-0131", recv=date(2025, 8, 4), plant="A", sup="BUCK", keys=["CORD:0.9M"], part=supp_pn("CORD:0.9M", "BUCK"), type="DESIGN_REVISION",
         text="Plug overmold tooling replaced. Strain relief shape changes slightly. Ratings and UL file unchanged.", eff=date(2026, 2, 1), repl="", last="",
         status=f"CLOSED: item revised {ITEM_OLD[('A', 'CORD:0.9M')][0]} to {ITEM[('A', 'CORD:0.9M')]} on 2026-02-01", actioned="Y",
         truth="Handled properly: the supersession is recorded.", behaviour="Link the notice to the recorded supersession and show it as closed"),
    dict(id="PCN-2025-0156", recv=date(2025, 9, 2), plant="B", sup="GULF", keys=["CHKVALVE"], part=supp_pn("CHKVALVE", "GULF"), type="MATERIAL_CHANGE",
         text="Silicone compound for duckbill valves changes to a new food-grade grade. Dimensions unchanged. Our part number is unchanged.", eff=date(2026, 3, 1), repl="", last="",
         status="FILED: no action recorded", actioned="PARTLY",
         truth="El Paso renumbered this valve in March 2026 and recorded no supersession. This notice is the missing explanation.",
         behaviour="Link the notice to the unrecorded renumbering and propose the old-to-new link for review"),
    dict(id="PCN-2026-0048", recv=date(2026, 5, 12), plant="A", sup="CIRC", keys=["PCB:P1"], part=supp_pn("PCB:P1", "CIRC"), type="FIRMWARE_REVISION",
         text="Control board firmware 2.3 replaces 2.2 (clock drift fix). No hardware change.", eff=date(2026, 8, 1), repl="", last="",
         status="CLOSED: engineering approved 2026-06-03, no item change", actioned="Y", truth="Handled properly. Included so that not every notice is an alarm.",
         behaviour="Show as closed; no alert"),
    dict(id="PCN-2026-0063", recv=date(2026, 6, 15), plant="A", sup="THRM", keys=["TSTAT:105C"], part=CP["TSTAT:105C"]["mpn"], type="DISCONTINUATION",
         text="Thermostat TS-105-NC is discontinued. Replacement is TS-105-NC2 (new terminal plating, same trip point). Last orders accepted until 2026-12-31.",
         eff=date(2027, 1, 1), repl="TS-105-NC2", last="2026-12-31", status="OPEN: no action recorded", actioned="N",
         sups=["THRM", "ALLD"], hidden={"B": "El Paso: since 2026-05-01 the thermostat arrives inside the heater assembly bought complete from Hotwire Components, built to the same drawing"},
         truth="Sent to Dayton only. El Paso bought the same thermostat until April 2026, mostly through a distributor under the distributor's own number and at a higher price, and since May gets it inside a bought heater assembly. El Paso was never told. The thermostat is in every coffee maker both plants build.",
         behaviour="Alert: last order date is close. Show both plants, every model, the spend, and that El Paso was not told"),
    dict(id="PCN-2026-0079", recv=date(2026, 7, 20), plant="B", sup="EMBR", keys=["HEATER:900W"], part=supp_pn("HEATER:900W", "EMBR"), type="DESIGN_CHANGE",
         text="900 W element: terminal tabs rotate 90 degrees to suit automated welding. Wattage, tube shape and mounting unchanged.", eff=date(2027, 1, 15), repl="", last="2026-12-15",
         status="OPEN: forwarded to engineering, no reply", actioned="N",
         truth="Sent to El Paso only, which stopped buying this element in May 2026 when it began buying the heater assembly complete, so nobody there acted. Dayton buys 100% of its 900 W elements from this supplier and was not told. The rotated tabs mean the wire harness routing has to be checked.",
         behaviour="Alert: show that the plant that received the notice no longer buys the part, that Dayton is fully exposed, and that the wire harnesses need an engineering check"),
    dict(id="PCN-2026-0088", recv=date(2026, 8, 25), plant="A", sup="MVMO", keys=food_plastics, part="All food-contact polypropylene parts (tanks, lids, baskets, showerhead, carafe lids)", type="MATERIAL_CHANGE",
         text="Polypropylene resin grade changes for all food-contact parts. New NSF/ANSI 51 letter attached. Customer approval requested within 60 days.", eff=date(2027, 3, 1),
         repl="", last="", status="OPEN: approval overdue since 2026-10-24", actioned="N",
         truth="A notice that names a material family and no part number. It touches every food-contact molded part this supplier makes for Dayton.",
         behaviour="Expand the notice to every matching part and the models that use them"),
    dict(id="PCN-2026-0095", recv=date(2026, 9, 3), plant="B", sup="VIDR", keys=glass, part="All glass carafes", type="LEAD_TIME_CHANGE",
         text="Ocean freight disruption. Lead time for all glass carafes moves from 4 weeks to 8 weeks for orders placed from 2026-09-01 until further notice.", eff=date(2026, 9, 1),
         repl="", last="", status="OPEN: planned lead time still 28 days", actioned="N",
         truth="Open carafe orders at El Paso are confirmed about four weeks later than promised, right in the holiday build. El Paso has already paid for air freight to cover the gap. This supplier is also the cheapest qualified source of the 12-cup carafe, so a price-only comparison would move more volume to it.",
         behaviour="Alert: show open orders that will arrive late, the builds that depend on them, the air freight already spent, and that planning data was not updated"),
    dict(id="PCN-2026-0101", recv=date(2026, 10, 5), plant="A", sup="EMBR", keys=[], part="EH-1500-U (1500 W element)", type="DISCONTINUATION",
         text="1500 W element EH-1500-U is discontinued.", eff=date(2027, 4, 1), repl="", last="2027-02-28", status="OPEN: no action recorded", actioned="N",
         truth="Larkfield does not buy a 1500 W element. No part, BOM or spend is affected.", behaviour="Show zero exposure and suggest closing the notice"),
]

# ---------------------------------------------------------------- write client-facing files
os.makedirs(OUT, exist_ok=True)
DIRS = ("plant_A_dayton_atlas", "plant_B_elpaso_meridian", "shared", "answer_key")
for sub in DIRS:
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
PA, PB, SH, AK = (os.path.join(OUT, s) for s in DIRS)
COUNTS = OrderedDict()


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    COUNTS[os.path.relpath(path, OUT)] = len(rows)
    return len(rows)


def us(d):
    return f"{d.month:02d}/{d.day:02d}/{d.year}"


MISS = random.Random(SEED + 1)
# item masters
rowsA = []
for key in CP:
    if ("A", key) not in ITEM:
        continue
    c = CP[key]
    typ = {"fg": "FG", "make": "MAKE", "buy": "BUY", "kit": "BUY"}[c["kind"]]
    uom = PUOM["A"].get(key, (c["uom"], 1, 1))[0]
    obsolete = key.startswith("CLID:5:")
    dwg = f"D-{ITEM[('A', key)][:7]}" if c["dwg"] else ""
    base = [desc_a(key), typ, c["uom"], uom, COMM_A[c["comm"]], c["mfr"].upper(), c["mpn"], dwg, MISS.choice(["A", "B", "B", "C"]) if dwg else "", c["material"], c["tol"], ""]
    rowsA.append([ITEM[("A", key)]] + base + [round(c["price"], 4) if c["kind"] == "buy" else "", "OBSOLETE" if obsolete else "ACTIVE",
                                               ITEM[("A", "CLID:5")] if obsolete else "", c["rating"], c["comp"], c["dims"]])
    if ("A", key) in ITEM_OLD:
        rowsA.append([ITEM_OLD[("A", key)][0]] + base[:8] + ["A"] + base[9:] + [round(c["price"], 4), "OBSOLETE", ITEM[("A", key)], c["rating"], c["comp"], c["dims"]])
    if ("A", key) in ALIAS:
        rowsA.append([ALIAS[("A", key)], "SCREW, TAPPING, PAN HD, M4 X 12 MM, ZINC", typ, c["uom"], uom, COMM_A[c["comm"]], "", "", "", "", "STEEL, ZINC PLATED", "", "",
                      round(c["price"] * 1.15, 4), "ACTIVE", "", "", "", "M4 X 12"])
for key, sku in SVC.items():
    c = CP[key]
    rowsA.append([sku, "SERVICE PART - " + desc_a(key), "SERVICE", "EA", "EA", "70", "", "", "", "", "", "", "", round(c["price"], 4), "ACTIVE", "", "", "", ""])
write(os.path.join(PA, "A_item_master.csv"),
      ["ITEM_NO", "ITEM_DESC", "ITEM_TYPE", "BASE_UOM", "PURCH_UOM", "COMMODITY_CODE", "MFR_NAME", "MFR_PART_NO", "DRAWING_NO", "DRAWING_REV", "MATERIAL_SPEC", "TOLERANCE_CLASS",
       "GDT_NOTE", "STD_COST", "STATUS", "SUPERSEDED_BY", "RATING", "COMPLIANCE", "DIMENSIONS"], rowsA)
CRIT_B = ("TFUSE:216C:SF", "TFUSE:229C:SF", "SWITCH:16A", "CORD:1.0M", "TUBE:8x1.6", "FOOT:12.5", "SCREW:M3x10", "MC:12:ECT29", "HEATER:900W", "HEATER:1000W", "TSTAT:105C",
          "HARNESS:P", "HARNESS:PT", "CARAFE:12:GLASS")          # parts whose spec fields the near-duplicate cases depend on are never blanked
rowsB = []
for key in CP:
    if ("B", key) not in ITEM:
        continue
    c = CP[key]
    typ = {"fg": "Finished", "make": "Purchased" if key in ("HTR:900", "HTR:1000") else "Manufactured", "buy": "Purchased", "kit": "Purchased"}[c["kind"]]
    uom = PUOM["B"].get(key, (c["uom"], 1, 1))[0]
    miss = lambda v, p: v if key in CRIT_B or MISS.random() >= p else ""
    dwg = f"EP-{ITEM[('B', key)][3:]}" if c["dwg"] else ""
    price = c["price"] * dict((x[0], x[2]) for x in sources("B", key)).get(sources("B", key)[0][0], 1.0) if c["kind"] in ("buy", "kit") or key in ("HTR:900", "HTR:1000") else ""
    rowsB.append([ITEM[("B", key)], desc_b(key), typ, UOM_NAME_B.get(c["uom"], c["uom"]), UOM_NAME_B.get(uom, uom), miss(c["comm"].title(), 0.15), miss(c["mfr"], 0.25),
                  miss(c["mpn"], 0.25), dwg, MISS.choice(["1", "2", "3"]) if dwg else "", miss(c["material"].title(), 0.25), miss(c["tol"], 0.3), "",
                  round(price, 4) if price != "" else "", "Y", miss(c["rating"], 0.2), miss(c["comp"].title().replace("Ul ", "UL ").replace("Nsf", "NSF").replace("Fda", "FDA").replace("Cfr", "CFR").replace("Rohs", "RoHS").replace("Ansi", "ANSI"), 0.25),
                  miss(c["dims"].lower().replace(" mm", " mm"), 0.2)])
    if ("B", key) in ITEM_OLD:
        rowsB.append([ITEM_OLD[("B", key)][0], desc_b(key), typ, "Each", "Each", c["comm"].title(), "", "", "", "", c["material"].title(), "", "", round(c["price"], 4), "N", "", "", ""])
    if ("B", key) in ALIAS:
        rowsB.append([ALIAS[("B", key)], "Carafe glass 12 cup w blk handle 1.8L", typ, "Each", "Each", "Glass", "", "", "", "", "Borosilicate", "", "", round(c["price"], 4), "Y", "", "FDA Food Contact", "1.8 l"])
write(os.path.join(PB, "B_Part_Master.csv"),
      ["Part Number", "Part Description", "Class", "Stock UM", "Buy UM", "Commodity", "Manufacturer", "Mfg Part #", "Dwg", "Rev", "Material", "Tol", "GD&T", "Std Cost", "Active",
       "Rating", "Compliance", "Dimensions"], rowsB)

# BOMs. Dayton: parent/child rows with effectivity dates. El Paso: indented, one block per model.
rowsA = []; seenA = {}
for m in PLANT_MODELS["A"]:
    for a, b, q, tag in bom_edges(m, "A"):
        comp = ALIAS[("A", b)] if tag == "DUP" else ITEM[("A", b)]
        if (a, comp) in seenA:
            continue
        seenA[(a, comp)] = 1
        eff = "2026-04-01" if b == "CLID:5" else ("2026-02-01" if b == "CORD:0.9M" else "2024-01-01")
        rowsA.append([ITEM[("A", a)], comp, q, CP[b]["uom"], eff, "9999-12-31", "PRODUCTION"])
rowsA.append([ITEM[("A", "FG:BL-5")], ITEM[("A", "CLID:5:TOP")], 1, "EA", "2024-01-01", "2026-03-31", "PRODUCTION"])
rowsA.append([ITEM[("A", "FG:BL-5")], ITEM[("A", "CLID:5:HINGE")], 1, "EA", "2024-01-01", "2026-03-31", "PRODUCTION"])
for m in PLANT_MODELS["A"]:
    rowsA.append([ITEM[("A", f"FG:{m}")], ITEM_OLD[("A", "CORD:0.9M")][0], 1, "EA", "2024-01-01", "2026-01-31", "PRODUCTION"])
write(os.path.join(PA, "A_bom_parent_child.csv"), ["PARENT_ITEM", "COMPONENT_ITEM", "QTY_PER", "COMP_UOM", "EFF_FROM", "EFF_TO", "BOM_USAGE"], rowsA)
rowsB = []
for m in PLANT_MODELS["B"]:
    seq = 0
    for a, b, q, tag in bom_edges(m, "B"):
        seq += 10; c = CP[b]; lvl = 1 if a.startswith("FG:") else 2
        src = "Buy" if (c["kind"] == "make" or lvl == 1) else "Reference"            # heater assembly is bought complete since 05/01/2026; its children are reference only
        part = ALIAS[("B", b)] if tag == "DUP" else ITEM[("B", b)]
        rowsB.append([ITEM[("B", f"FG:{m}")], lvl, seq, "." * lvl + part, desc_b(b), q, UOM_NAME_B.get(c["uom"], c["uom"]), src,
                      us(MAKE_TO_BUY_B) if (c["kind"] == "make" or lvl == 2) else us(date(2023, 7, 1))])
write(os.path.join(PB, "B_Indented_BOM.csv"), ["Top Model", "Lvl", "Seq", "Part (indented)", "Description", "Qty Per Parent", "UM", "Source", "Eff Date"], rowsB)
write(os.path.join(PB, "B_Make_Buy_Changes.csv"), ["Part Number", "Description", "Change", "Effective", "Vendor", "Note"],
      [[ITEM[("B", f"HTR:{w}")], desc_b(f"HTR:{w}"), "Make to Buy", us(MAKE_TO_BUY_B), SUPID[("B", "HOTW")],
        "Heater assembly line closed. Assembly now bought complete; element, thermostat, fuses and bracket no longer purchased by El Paso for this assembly."] for w in (900, 1000)])

# suppliers
act = lambda p, s: any(r["sup"] == s and r["plant"] == p for r in PO) or any(q["sup"] == s and q["plant"] == p for q in QUOTES)
write(os.path.join(PA, "A_supplier_master.csv"),
      ["SUPPLIER_ID", "SUPPLIER_NAME", "PARENT_GROUP", "SUPPLIER_TYPE", "STATE", "ISO_9001", "ISO_14001", "OTHER_CERTS", "CAPABILITIES", "APPROVAL_STATUS"],
      [[SUPID[("A", s)], v["name"].upper(), v["group"], v["type"], v["state"], v["iso9001"], v["iso14001"], "; ".join(v["certs"]), v["cap"],
        "APPROVED" if v["iso9001"] == "Y" or v["type"] == "Service" else "NOT QUALIFIED"] for s, v in SUP.items() if act("A", s)])
write(os.path.join(PB, "B_Vendors.csv"), ["Vendor", "Vendor Name", "Type", "St", "Certifications", "Capabilities / Notes", "Status"],
      [[SUPID[("B", s)], NAME_VARIANTS_B.get(s, v["name"]), v["type"], v["state"],
        "; ".join([x for x in (("ISO 9001" if v["iso9001"] == "Y" else ""), ("ISO 14001" if v["iso14001"] == "Y" else "")) if x] + v["certs"]), v["cap"],
        "Approved" if v["iso9001"] == "Y" or v["type"] == "Service" else "Conditional (no ISO 9001)"] for s, v in SUP.items() if act("B", s)])

# item-to-supplier records. Incomplete on purpose.
info = {"A": [], "B": []}; INFO_KEY = {}
pairs = uniq([(r["plant"], r["key"], r["sup"]) for r in PO if r["key"] in CP and r["bucket"] == "PRODUCTION"])
for plant, key, s in pairs:
    if s in DISTRIBUTORS or CP[key]["mpn"] or MISS.random() < 0.35:
        if MISS.random() < 0.78:
            uom = PUOM[plant].get(key, (CP[key]["uom"], 1, 1))[0]
            info[plant].append([ITEM[(plant, key)], SUPID[(plant, s)], supp_pn(key, s), uom, CP[key]["lead"], CP[key]["moq"]]); INFO_KEY[(plant, key, s)] = 1
for r in PO + INV + INV_LATE:
    if "SUPPLIER_PART_NO_ONLY" in r["causes"]:
        r["method"] = "VENDOR_PART_XREF" if (r["plant"], r["key"], r["sup"]) in INFO_KEY else "MFR_PART_NO_OR_DESCRIPTION"
write(os.path.join(PA, "A_purchasing_info_records.csv"), ["ITEM_NO", "SUPPLIER_ID", "SUPPLIER_ITEM", "ORDER_UOM", "PLANNED_LEAD_DAYS", "MIN_ORDER_QTY"], info["A"])
write(os.path.join(PB, "B_Vendor_Part_Xref.csv"), ["Part Number", "Vendor", "Vendor Part", "Buy UM", "Lead Time (days)", "MOQ"],
      [[r[0], r[1], r[2], UOM_NAME_B.get(r[3], r[3]), r[4], r[5]] for r in info["B"]])
write(os.path.join(PA, "A_uom_conversions.csv"), ["ITEM_NO", "ALT_UOM", "BASE_UOM", "BASE_QTY_PER_ALT_UOM"],
      [[ITEM[("A", k)], u, CP[k]["uom"], conv] for k, (u, conv, per) in PUOM["A"].items() if ("A", k) in ITEM and k != "RATINGLABEL"])
write(os.path.join(PB, "B_UM_Conversions.csv"), ["From UM", "To UM", "Factor"], [["Foot", "Meter", 0.3048], ["M", "Each", 1000], ["BX", "Each", 1000]])
write(os.path.join(PA, "A_supersessions.csv"), ["OLD_ITEM", "NEW_ITEM", "EFFECTIVE_DATE", "REASON"],
      [[ITEM_OLD[("A", "CORD:0.9M")][0], ITEM[("A", "CORD:0.9M")], "2026-02-01", "SUPPLIER TOOLING CHANGE - PLUG OVERMOLD"],
       [ITEM[("A", "CLID:5:TOP")], ITEM[("A", "CLID:5")], "2026-04-01", "TWO-PIECE CARAFE LID REPLACED BY ONE-PIECE LID"],
       [ITEM[("A", "CLID:5:HINGE")], ITEM[("A", "CLID:5")], "2026-04-01", "TWO-PIECE CARAFE LID REPLACED BY ONE-PIECE LID"]])
write(os.path.join(PA, "A_rfq_quotes.csv"),
      ["RFQ_NO", "QUOTE_DATE", "ITEM_NO", "SUPPLIER_ID", "QUOTE_NO", "QUOTED_UNIT_PRICE", "CURRENCY", "LEAD_TIME_DAYS", "MOQ", "EST_ANNUAL_QTY", "AWARDED", "VALID_TO"],
      [[q["rfq"], q["date"].isoformat(), q["item"], SUPID[("A", q["sup"])], q["quote"], q["price"], "USD", q["lead"], q["moq"], q["est_annual_qty"], q["awarded"], q["valid_to"].isoformat()]
       for q in QUOTES if q["plant"] == "A"])
write(os.path.join(PB, "B_Quotes.csv"), ["RFQ", "Quoted On", "Part", "Vendor", "Quote #", "Price Each", "Lead Time (wks)", "Min Order", "Annual Usage Est", "Award"],
      [[q["rfq"], us(q["date"]), q["item"], SUPID[("B", q["sup"])], q["quote"], q["price"], round(q["lead"] / 7, 1), q["moq"], q["est_annual_qty"], "Awarded" if q["awarded"] == "Y" else ""]
       for q in QUOTES if q["plant"] == "B"])
write(os.path.join(PA, "A_po_lines.csv"),
      ["PO_NUMBER", "PO_LINE", "PO_DATE", "SUPPLIER_ID", "ITEM_NO", "SUPPLIER_ITEM", "LINE_TEXT", "ORDER_QTY", "ORDER_UOM", "NET_PRICE", "LINE_AMOUNT", "CURRENCY", "COST_CENTER",
       "SHIP_TO_LOC", "RFQ_QUOTE_REF"],
      [[r["po"], r["line"], r["date"].isoformat(), SUPID[("A", r["sup"])], r["item"], r["supp_pn"], r["desc"], r["qty"], r["uom"], r["price"], r["amount"], "USD", r["cost"], r["ship"], r["quote"]]
       for r in PO if r["plant"] == "A"])
write(os.path.join(PB, "B_PO_Detail.csv"),
      ["PO Number", "Ln", "Order Date", "Vendor", "Part Number", "Vendor Part", "Line Description", "Order Qty", "UM", "Unit Price", "Per", "Ext Amount", "GL Account", "Deliver To", "Quote Ref"],
      [[r["po"], r["line"], us(r["date"]), SUPID[("B", r["sup"])], r["item"], r["supp_pn"], r["desc"], r["qty"], UOM_NAME_B.get(r["uom"], r["uom"]), r["price"], r["per"], r["amount"],
        r["cost"], r["ship"], r["quote"]] for r in PO if r["plant"] == "B"])
write(os.path.join(PA, "A_invoice_lines.csv"),
      ["INVOICE_NO", "INV_LINE", "INVOICE_DATE", "SUPPLIER_ID", "PO_NUMBER", "PO_LINE", "ITEM_NO", "LINE_TEXT", "INV_QTY", "UOM", "UNIT_PRICE", "LINE_AMOUNT", "LINE_TYPE", "CURRENCY"],
      [[r["inv"], r["line"], r["date"].isoformat(), SUPID[("A", r["sup"])], r["po"], r["po_line"], r["item"], r["desc"], r["qty"], r["uom"], r["price"], r["amount"], r["type"], "USD"]
       for r in INV if r["plant"] == "A"])
TYPE_B = {"MAT": "Material", "FRT": "Freight", "SVC": "Service", "CRD": "Credit Memo"}
write(os.path.join(PB, "B_AP_Invoice_Lines.csv"), ["Invoice #", "Inv Line", "Inv Date", "Vendor", "PO Ref", "Part", "Description", "Qty", "UM", "Price", "Per", "Amount", "Type"],
      [[r["inv"], r["line"], us(r["date"]), SUPID[("B", r["sup"])], (f"{r['po']}/{r['po_line']}" if r["po"] and r["po_line"] != "" else r["po"]), r["item"], r["desc"], r["qty"],
        UOM_NAME_B.get(r["uom"], r["uom"]), r["price"], r["per"], r["amount"], TYPE_B[r["type"]]] for r in INV if r["plant"] == "B"])
write(os.path.join(PA, "A_goods_receipts.csv"), ["GR_DOC", "GR_DATE", "PO_NUMBER", "PO_LINE", "ITEM_NO", "RECEIVED_QTY", "UOM", "PROMISED_DATE"],
      [[g["doc"], g["date"].isoformat(), g["po"], g["line"], g["item"], g["qty"], g["uom"], g["promised"].isoformat()] for g in REC if g["plant"] == "A"])
write(os.path.join(PB, "B_Receipts.csv"), ["Receiver #", "Recd Date", "PO Number", "Ln", "Part Number", "Qty Recd", "UM", "Due Date"],
      [[g["doc"], us(g["date"]), g["po"], g["line"], g["item"], g["qty"], UOM_NAME_B.get(g["uom"], g["uom"]), us(g["promised"])] for g in REC if g["plant"] == "B"])
write(os.path.join(PA, "A_open_po_lines.csv"), ["PO_NUMBER", "PO_LINE", "PO_DATE", "SUPPLIER_ID", "ITEM_NO", "LINE_TEXT", "OPEN_QTY", "ORDER_UOM", "PROMISED_DATE", "CONFIRMED_DATE"],
      [[o["po"], o["line"], o["date"].isoformat(), SUPID[("A", o["sup"])], o["item"], o["desc"], o["open_qty"], o["uom"], o["promised"].isoformat(), o["conf"].isoformat()]
       for o in OPEN if o["plant"] == "A"])
write(os.path.join(PB, "B_Open_PO_Report.csv"), ["PO Number", "Ln", "Order Date", "Vendor", "Part Number", "Line Description", "Open Qty", "UM", "Due Date", "Vendor Confirmed"],
      [[o["po"], o["line"], us(o["date"]), SUPID[("B", o["sup"])], o["item"], o["desc"], o["open_qty"], UOM_NAME_B.get(o["uom"], o["uom"]), us(o["promised"]), us(o["conf"])]
       for o in OPEN if o["plant"] == "B"])

# shared files
write(os.path.join(SH, "build_volumes.csv"), ["plant", "model", "month", "units_completed"], [[PLANT_NAME[p], m, f"{ym[0]}-{ym[1]:02d}", v] for (p, m, ym), v in BUILD.items()])
PLAN_BIAS = {("B", "BL-12T"): 0.78, ("A", "BL-5"): 1.18, ("B", "BL-12P"): 0.93}       # FY26 plan relative to what was actually built
GROWTH = {("A", "BL-5"): 0.92, ("A", "BL-12"): 1.02, ("A", "BL-12P"): 1.08, ("B", "BL-12"): 1.00, ("B", "BL-12P"): 1.10, ("B", "BL-12T"): 1.40}
fc = []; FCT = OrderedDict()
for (plant, m), base in BASE_BUILDS.items():
    plan = nxt = 0
    for ym in MONTHS:
        u = int(round(base * SEASON[ym[1]] * PLAN_BIAS.get((plant, m), 1.0) / 10.0)) * 10
        fc.append([PLANT_NAME[plant], m, f"{ym[0]}-{ym[1]:02d}", u, "FY26 plan (set October 2025)"]); plan += u
    for ym in NEXT:
        u = int(round(base * GROWTH[(plant, m)] * SEASON[ym[1]] / 10.0)) * 10
        fc.append([PLANT_NAME[plant], m, f"{ym[0]}-{ym[1]:02d}", u, "FY27 plan (set October 2026)"]); nxt += u
    FCT[(plant, m)] = (plan, sum(BUILD[(plant, m, ym)] for ym in MONTHS), nxt)
write(os.path.join(SH, "build_forecast.csv"), ["plant", "model", "month", "forecast_units", "forecast_version"], fc)
LABOR = {"A": (24.0, 1.50), "B": (19.0, 1.40)}       # labor rate per hour, overhead as a multiple of labor
MINUTES = {"BL-5": 4.5, "BL-12": 5.0, "BL-12P": 6.0, "BL-12T": 6.5}; HEATER_MIN = 0.8
lab = []
for plant, models in PLANT_MODELS.items():
    for m in models:
        lab.append([PLANT_NAME[plant], ITEM[(plant, f"FG:{m}")], m, "Final assembly, test and pack", MINUTES[m], LABOR[plant][0], LABOR[plant][1]])
    for w in (650, 900) if plant == "A" else (900, 1000):
        lab.append([PLANT_NAME[plant], ITEM[(plant, f"HTR:{w}")], f"Heater assembly {w} W", "Heater sub-assembly" + ("" if plant == "A" else " (in house until 2026-04-30; bought complete since)"),
                    HEATER_MIN, LABOR[plant][0], LABOR[plant][1]])
write(os.path.join(SH, "labor_and_overhead_standards.csv"), ["plant", "item", "applies_to", "operation", "std_minutes_per_unit", "labor_rate_usd_per_hour", "overhead_multiple_of_labor"], lab)
SVC_GIVEN = {}
svc_rows = []
for key, sku in SVC.items():
    give = MISS.random() < 0.8
    if give:
        SVC_GIVEN[key] = 1
    svc_rows.append([sku, "SERVICE PART - " + desc_a(key), ITEM[("A", key)] if give else "", "; ".join(m for m in MODELS if any(b == key for a, b, q, t in bom_edges(m, "A")) or any(b == key for a, b, q, t in bom_edges(m, "B")))])
write(os.path.join(SH, "service_parts_catalog.csv"), ["service_sku", "description", "production_item_dayton", "applies_to_models"], svc_rows)
write(os.path.join(SH, "warranty_claims.csv"), ["claim_no", "claim_date", "plant", "model", "serial_no", "part_ref", "qty", "parts_cost_usd", "failure_mode", "resolution"],
      [[c["claim"], c["date"].isoformat(), PLANT_NAME[c["plant"]], c["model"], c["serial"], c["part_ref"], c["qty"], c["cost"], c["failure"], c["resolution"]] for c in CLAIMS])
NOTICES.sort(key=lambda n: n["recv"])
write(os.path.join(SH, "supplier_change_notices.csv"),
      ["notice_id", "received_date", "received_by_plant", "supplier_name_on_notice", "supplier_part_no", "notice_type", "notice_text", "effective_date", "replacement_supplier_part_no",
       "last_order_date", "internal_status"],
      [[n["id"], n["recv"].isoformat(), PLANT_NAME[n["plant"]], SUP[n["sup"]]["name"], n["part"], n["type"], n["text"], n["eff"].isoformat(), n["repl"], n["last"], n["status"]] for n in NOTICES])
# legacy cross-reference from the 2023 acquisition: partial, and one row is wrong
dups = [k for k in CP if ("A", k) in ITEM and ("B", k) in ITEM and CP[k]["kind"] == "buy"]
given = R.sample(dups, int(len(dups) * 0.4))
num23 = lambda p, k: ITEM_OLD[(p, k)][0] if (p, k) in ITEM_OLD else ITEM[(p, k)]      # the 2023 workbook carries the numbers that were valid in 2023
xr = [[num23("A", k), num23("B", k), "2023 migration workbook", "Verified" if R.random() < 0.6 else "Unverified"] for k in given]
xr.append([ITEM[("A", "TFUSE:216C:TT")], ITEM[("B", "TFUSE:229C:SF")], "2023 migration workbook", "Unverified"])      # WRONG: 216 C mapped to 229 C
R.shuffle(xr)
write(os.path.join(SH, "legacy_part_crossref_2023.csv"), ["dayton_item", "elpaso_part", "source", "status"], xr)

# ---------------------------------------------------------------- answer key
PRODINV = [i for i in INV if i["bucket"] == "PRODUCTION" and i["key"] in CP]
# near-identical families: (family, standard, [(member, relation, difference)])
SAME, DUPN, CLOSE, NOMERGE = "SAME_PART", "SAME_PART_DUPLICATE_NUMBER", "CLOSE_SPEC_NEEDS_ENGINEERING_REVIEW", "DO_NOT_MERGE"
FAMILIES = [
    ("FAM-01", "Power cord", "CORD:0.9M", [("CORD:1.0M", CLOSE, "0.1 m longer. Same plug, wire gauge and rating")]),
    ("FAM-02", "Housing screw M3", "SCREW:M3x8", [("SCREW:M3x10", CLOSE, "One length step longer (10 mm where the standard is 8 mm). Boss depth must be checked")]),
    ("FAM-03", "Thermal fuse", "TFUSE:216C:TT", [("TFUSE:216C:SF", CLOSE, "Other maker, same 216 C and 10 A rating. The safety file must list the second maker before merging"),
                                                 ("TFUSE:229C:SF", NOMERGE, "Trips at 229 C, not 216 C. Looks identical. Used only on the 1000 W thermal model. A safety-critical difference")]),
    ("FAM-04", "Silicone tube 8 mm", "TUBE:8x1.5", [("TUBE:8x1.6", CLOSE, "Wall 1.6 mm where the standard is 1.5 mm. Same bore, hardness and food-contact grade")]),
    ("FAM-05", "Rubber foot", "FOOT:12", [("FOOT:12.5", CLOSE, "Diameter 12.5 mm where the standard is 12.0 mm")]),
    ("FAM-06", "Rocker switch", "SWITCH:10A", [("SWITCH:16A", CLOSE, "Rated 16 A where 10 A is enough (a 900 W heater draws 7.5 A at 120 V). Same cutout and LED")]),
    ("FAM-07", "Master carton 12-cup", "MC:12:ECT29", [("MC:12:ECT32", CLOSE, "Heavier ECT-32 board where El Paso ships in ECT-29. Same dimensions. Needs a drop test")]),
    ("FAM-08", "Heating element 12-cup", "HEATER:900W", [("HEATER:1000W", NOMERGE, "1000 W, not 900 W. Same tube shape and mounting. Used only on the thermal model")]),
    ("FAM-09", "Wire harness programmable", "HARNESS:P", [("HARNESS:PT", NOMERGE, "7 leads, not 8: no warming plate lead. Descriptions are nearly identical")]),
]
FAM_OF = {}
for fid, name, std, members in FAMILIES:
    FAM_OF[std] = (fid, name, std, "STANDARD", "")
    for k, rel, diff in members:
        FAM_OF[k] = (fid, name, std, rel, diff)

look_ids = defaultdict(list)
for fid, name, std, members in FAMILIES:
    for k, rel, diff in members:
        if rel == NOMERGE:
            look_ids[std].append(CP[k]["cid"]); look_ids[k].append(CP[std]["cid"])
write(os.path.join(AK, "key_canonical_parts.csv"),
      ["canonical_id", "canonical_key", "description", "kind", "commodity", "base_uom", "base_price_usd", "material", "dimensions", "rating", "compliance", "manufacturer", "mfr_part_no",
       "dayton_item", "elpaso_part", "in_both_plants", "near_duplicate_family", "do_not_merge_with", "note"],
      [[c["cid"], k, desc_a(k), c["kind"], c["comm"], c["uom"], c["price"], c["material"], c["dims"], c["rating"], c["comp"], c["mfr"], c["mpn"], ITEM.get(("A", k), ""), ITEM.get(("B", k), ""),
        "Y" if ("A", k) in ITEM and ("B", k) in ITEM else "N", FAM_OF[k][0] if k in FAM_OF else "", "; ".join(look_ids.get(k, [])), c["note"]] for k, c in CP.items()])
rows = []
for (plant, key), it in ITEM.items():
    rows.append([plant, it, CP[key]["cid"], key, "OBSOLETE; superseded many-to-one by " + CP["CLID:5"]["cid"] if key.startswith("CLID:5:") else "CURRENT"])
for (plant, key), (it, until) in ITEM_OLD.items():
    rows.append([plant, it, CP[key]["cid"], key, f"OLD NUMBER valid to {until.isoformat()}; same part as current item {ITEM[(plant, key)]}"])
for (plant, key), it in ALIAS.items():
    rows.append([plant, it, CP[key]["cid"], key, f"DUPLICATE ITEM NUMBER at the same plant; same part as {ITEM[(plant, key)]}"])
for key, sku in SVC.items():
    rows.append(["A", sku, CP[key]["cid"], key, "SERVICE SKU for the same physical part" + ("" if key in SVC_GIVEN else " (cross-reference NOT in the client's service catalogue)")])
write(os.path.join(AK, "key_item_to_canonical.csv"), ["plant", "item_or_sku", "canonical_id", "canonical_key", "relation"], rows)
write(os.path.join(AK, "key_kit_contents.csv"), ["kit", "plant", "component_canonical_id", "component_key", "qty"],
      [["PACKKIT:12T (" + ITEM[("B", "PACKKIT:12T")] + ")", "B", CP[k]["cid"], k, q] for k, q in KIT_CONTENTS["PACKKIT:12T"]])


def truth_row(r, doc, line):
    return [r["plant"], doc, line, CP[r["key"]]["cid"] if r["key"] in CP else "", r["key"], r["bucket"], "|".join(r["causes"]) if r["causes"] else "CLEAN", r["method"], r["resolvable"], r["amount"]]


write(os.path.join(AK, "key_po_line_truth.csv"),
      ["plant", "po_number", "po_line", "canonical_id", "canonical_key", "true_bucket", "mismatch_causes", "expected_match_method", "resolvable", "amount_usd"],
      [truth_row(r, r["po"], r["line"]) for r in PO])
write(os.path.join(AK, "key_invoice_line_truth.csv"),
      ["plant", "invoice_no", "inv_line", "canonical_id", "canonical_key", "true_bucket", "mismatch_causes", "expected_match_method", "resolvable", "amount_usd", "true_po_number", "true_po_line", "base_qty"],
      [truth_row(r, r["inv"], r["line"]) + [r["true_po"], r["true_po_line"], r["base_qty"]] for r in INV])

# price paid per part, plant and supplier (production purchases, per base unit)
ps = defaultdict(lambda: [0.0, 0.0])
for i in PRODINV:
    ps[(i["plant"], i["key"], i["sup"])][0] += i["amount"]; ps[(i["plant"], i["key"], i["sup"])][1] += i["base_qty"]
wprice = defaultdict(lambda: [0.0, 0.0])
for (p, k, s), (a, q) in ps.items():
    wprice[(p, k)][0] += a; wprice[(p, k)][1] += q
price_rows = []
for (p, k, s) in sorted(ps, key=lambda x: (CP[x[1]]["cid"], x[0], x[2])):
    a, q = ps[(p, k, s)]
    price_rows.append([CP[k]["cid"], k, PLANT_NAME[p], ITEM[(p, k)], s, SUP[s]["name"], round(q, 1), round(a, 2), round(a / q, 5) if q else "", "Y" if qualified(s, k) else "N",
                       "" if qualified(s, k) else ("No ISO 9001" if SUP[s]["iso9001"] != "Y" else "Missing required certification"), CP[k]["lead"], CP[k]["moq"]])
write(os.path.join(AK, "key_price_by_part_and_supplier.csv"),
      ["canonical_id", "canonical_key", "plant", "plant_item", "supplier_code", "supplier_name", "invoiced_qty_12m_base_units", "invoiced_spend_12m_usd", "weighted_price_per_base_unit",
       "supplier_qualified_for_this_part", "why_not_qualified", "planned_lead_days", "moq"], price_rows)

# modeled cost per unit: purchased material today, plus labor and overhead from the standards = full cost
ppu = []; cost_rows = []; UNIT_MAT = {}
for plant, models in PLANT_MODELS.items():
    for m in models:
        tot = 0.0
        for (k, tag), q in purchased_requirements(m, plant, PERIOD_END).items():
            a, qq = wprice.get((plant, k), [0, 0])
            wp = a / qq if qq else CP[k]["price"]
            ppu.append([plant, m, CP[k]["cid"], k, ALIAS[(plant, k)] if tag == "DUP" else ITEM[(plant, k)], round(q, 4), CP[k]["uom"], round(wp, 5), round(q * wp, 4)])
            tot += q * wp
        mins = MINUTES[m] + (HEATER_MIN if not heater_bought(plant, PERIOD_END) else 0)
        labor = mins / 60 * LABOR[plant][0]; oh = labor * LABOR[plant][1]
        units = sum(BUILD[(plant, m, ym)] for ym in MONTHS)
        UNIT_MAT[(plant, m)] = tot
        cost_rows.append([PLANT_NAME[plant], m, units, round(tot, 3), round(labor, 3), round(oh, 3), round(tot + labor + oh, 3), round(tot / (tot + labor + oh), 3)])
write(os.path.join(AK, "key_purchased_parts_per_unit.csv"),
      ["plant", "model", "canonical_id", "canonical_key", "plant_item", "qty_per_unit", "base_uom", "weighted_invoice_price_per_base_unit", "cost_per_unit"], ppu)
write(os.path.join(AK, "key_modeled_cost_per_unit.csv"),
      ["plant", "model", "units_built_12m", "purchased_material_usd", "labor_usd", "overhead_usd", "modeled_full_cost_usd", "material_share_of_full_cost"], cost_rows)

# cross-plant: the same part under two numbers, and what each plant pays
same_rows = []
for k in dups:
    a = wprice.get(("A", k)); b = wprice.get(("B", k))
    pa = a[0] / a[1] if a and a[1] else None; pb = b[0] / b[1] if b and b[1] else None
    same_rows.append([CP[k]["cid"], k, ITEM[("A", k)], ITEM[("B", k)], "Y" if k in given else "N", round(pa, 5) if pa else "", round(pb, 5) if pb else "",
                      round(pb / pa - 1, 4) if pa and pb else "", round(a[1], 1) if pa else 0, round(b[1], 1) if pb else 0])
write(os.path.join(AK, "key_cross_plant_same_part.csv"),
      ["canonical_id", "canonical_key", "dayton_item", "elpaso_part", "in_legacy_crossref", "dayton_weighted_price", "elpaso_weighted_price", "gap_pct_elpaso_vs_dayton",
       "dayton_qty_12m", "elpaso_qty_12m"], same_rows)

# near-identical families with the three outcomes
fam_rows = []
for fid, name, std, members in FAMILIES:
    for k, rel, diff in [(std, "STANDARD", "")] + members:
        for p in ("A", "B"):
            if (p, k) not in ITEM:
                continue
            a, q = wprice.get((p, k), [0, 0])
            fam_rows.append([fid, name, PLANT_NAME[p], ITEM[(p, k)], CP[k]["cid"], k, desc_a(k) if p == "A" else desc_b(k), CP[k]["material"], CP[k]["dims"], CP[k]["rating"], CP[k]["comp"],
                             CP[k]["mfr"], CP[k]["mpn"], ", ".join(uniq(models_using(p, k)[0] + models_using(p, k)[1])), "; ".join(SUP[s]["name"] for s in sorted({x[2] for x in ps if x[0] == p and x[1] == k})),
                             round(q, 1), round(a, 2), round(a / q, 5) if q else "", rel, diff,
                             {"STANDARD": "Keep as the family standard", CLOSE: "Replace with the standard after engineering review", NOMERGE: "Keep separate. Never merge"}[rel]])
for (p, k), it in ALIAS.items():
    a = sum(i["amount"] for i in PRODINV if i["plant"] == p and i["key"] == k and i["tag"] == "DUP"); q = sum(i["base_qty"] for i in PRODINV if i["plant"] == p and i["key"] == k and i["tag"] == "DUP")
    fam_rows.append([f"DUP-{p}", "Duplicate item number: " + CP[k]["noun"].lower(), PLANT_NAME[p], it, CP[k]["cid"], k, "", CP[k]["material"], CP[k]["dims"], CP[k]["rating"], CP[k]["comp"], CP[k]["mfr"],
                     CP[k]["mpn"], ", ".join(m for (pp, kk, m) in sorted(DUP_TAG) if pp == p and kk == k), "; ".join(SUP[s]["name"] for s in sorted({i["sup"] for i in PRODINV if i["plant"] == p and i["key"] == k and i["tag"] == "DUP"})),
                     round(q, 1), round(a, 2), round(a / q, 5) if q else "", DUPN, f"The same part as {ITEM[(p, k)]}, created a second time under its own number", "Merge into the existing item number"])
write(os.path.join(AK, "key_near_duplicate_families.csv"),
      ["family_id", "family_name", "plant", "item", "canonical_id", "canonical_key", "description", "material", "dimensions", "rating", "compliance", "manufacturer", "mfr_part_no", "models",
       "suppliers_today", "invoiced_qty_12m", "invoiced_spend_12m_usd", "weighted_price_usd", "relation_to_family_standard", "difference_from_standard", "part_action"], fam_rows)
write(os.path.join(AK, "key_lookalikes_do_not_merge.csv"), ["family_id", "standard_part", "standard_canonical", "lookalike_part", "lookalike_canonical", "why_they_differ", "trap"],
      [[fid, f"{ITEM.get(('A', std), '')} / {ITEM.get(('B', std), '')}", CP[std]["cid"], f"{ITEM.get(('A', k), '')} / {ITEM.get(('B', k), '')}", CP[k]["cid"], diff,
        "The 2023 legacy cross-reference wrongly maps the Dayton 216 C fuse to this part" if k == "TFUSE:229C:SF" else "Descriptions differ by one token"]
       for fid, name, std, members in FAMILIES for k, rel, diff in members if rel == NOMERGE])

# savings opportunities, sized on the last 12 months of production purchases. One row per part or family; each dollar counted once.
def best_qualified(keys):
    """Lowest weighted price among qualified suppliers that already supply at least 10% of the group's volume."""
    tot_q = sum(q for (p, k, s), (a, q) in ps.items() if k in keys)
    cand = defaultdict(lambda: [0.0, 0.0])
    for (p, k, s), (a, q) in ps.items():
        if k in keys and qualified(s, k):
            cand[(p, s)][0] += a; cand[(p, s)][1] += q
    best = None
    for (p, s), (a, q) in sorted(cand.items()):
        if q >= 0.1 * tot_q and (best is None or a / q < best[2]):
            best = (p, s, a / q)
    return best


CAUTION = {"VIDR": "Cheapest qualified source, but its lead time doubled to 8 weeks in September 2026 (PCN-2026-0095). Price alone would pick the wrong supplier."}
opp = []
covered = {}
for fid, name, std, members in FAMILIES:
    close = [k for k, rel, d in members if rel == CLOSE]
    if not close:
        continue
    keys = [std] + close
    best = best_qualified([std]) or best_qualified(keys)
    firm = review = spend = 0.0
    for (p, k, s), (a, q) in ps.items():
        if k in keys:
            spend += a; sv = max(0.0, a - best[2] * q)
            if k == std:
                firm += sv
            else:
                review += sv
            covered[k] = 1
    opp.append([fid, "NEAR_IDENTICAL_FAMILY", name, "; ".join(CP[k]["cid"] for k in keys), len(keys), len({s for (p, k, s) in ps if k in keys}), round(spend, 2),
                f"{CP[std]['cid']} ({desc_a(std)})", SUP[best[1]]["name"], PLANT_NAME[best[0]], round(best[2], 5), round(firm, 2), round(review, 2), round(firm + review, 2),
                "Engineering review needed for the close-spec members before their share counts", CAUTION.get(best[1], "")])
for k in dups + [x for x in CP if x not in dups and CP[x]["kind"] in ("buy", "kit")]:
    if k in covered or not any(kk == k for (p, kk, s) in ps):
        continue
    best = best_qualified([k])
    if not best:
        continue
    spend = sum(a for (p, kk, s), (a, q) in ps.items() if kk == k)
    sv = sum(max(0.0, a - best[2] * q) for (p, kk, s), (a, q) in ps.items() if kk == k)
    nsup = len({s for (p, kk, s) in ps if kk == k})
    if sv < 1 or nsup < 2:
        continue
    opp.append([CP[k]["cid"], "SAME_PART_SEVERAL_SUPPLIERS", desc_a(k), CP[k]["cid"], 1, nsup, round(spend, 2), f"{CP[k]['cid']} ({desc_a(k)})", SUP[best[1]]["name"], PLANT_NAME[best[0]],
                round(best[2], 5), round(sv, 2), 0.0, round(sv, 2), "Same part at both plants or from several suppliers; price alignment to the best qualified supplier", CAUTION.get(best[1], "")])
opp.sort(key=lambda r: -r[13])
write(os.path.join(AK, "key_savings_opportunities.csv"),
      ["opportunity_id", "opportunity_type", "name", "canonical_ids", "part_count", "suppliers_today", "invoiced_spend_12m_usd", "standard_part", "best_qualified_supplier", "at_plant",
       "best_qualified_price_per_base_unit", "saving_same_part_usd", "saving_after_engineering_review_usd", "total_sized_saving_12m_usd", "note", "caution"], opp)
# quote-to-invoice leakage at Dayton
leak = []
for k, f in LEAKAGE_A.items():
    awarded = [q for q in QUOTES if q["plant"] == "A" and q["key"] == k and q["awarded"] == "Y"][0]
    rows_k = [i for i in PRODINV if i["plant"] == "A" and i["key"] == k and i["sup"] == awarded["sup"] and i["po_date"] >= date(2026, 3, 1)]
    q = sum(i["base_qty"] for i in rows_k); a = sum(i["amount"] for i in rows_k)
    surcharge = 1.04 if CP[k]["comm"] == "PLASTICS" else 1.0
    leak.append([CP[k]["cid"], k, ITEM[("A", k)], SUP[awarded["sup"]]["name"], awarded["quote"], awarded["price"], round(a / q, 5) if q else "", round(q, 1),
                 round(a - awarded["price"] * q, 2), "Includes the 4% resin surcharge from May 2026, which is on top of the leakage" if surcharge > 1 else ""])
write(os.path.join(AK, "key_quote_to_invoice_leakage.csv"),
      ["canonical_id", "canonical_key", "dayton_item", "supplier", "awarded_quote_no", "quoted_price", "weighted_invoice_price_since_2026_03", "qty_since_2026_03", "paid_above_quote_usd", "note"], leak)
# tail and unqualified suppliers
tail = []
sup_spend = defaultdict(float)
for i in INV:
    if i["bucket"] in ("PRODUCTION", "SPARE", "WARRANTY"):
        sup_spend[(i["plant"], i["sup"])] += i["amount"]
for (p, s) in sorted(sup_spend, key=lambda x: (x[0], -sup_spend[x])):
    v = SUP[s]
    comms = sorted({CP[i["key"]]["comm"] for i in PRODINV if i["plant"] == p and i["sup"] == s})
    bad = sorted({k for (pp, k, ss) in ps if pp == p and ss == s and not qualified(s, k)})
    tail.append([PLANT_NAME[p], s, SUPID[(p, s)], v["name"], v["type"], v["iso9001"], "; ".join(v["certs"]), "; ".join(comms), round(sup_spend[(p, s)], 2),
                 len(bad), round(sum(ps[(p, k, s)][0] for k in bad), 2), "; ".join(CP[k]["cid"] for k in bad[:12])])
write(os.path.join(AK, "key_supplier_summary.csv"),
      ["plant", "supplier_code", "supplier_id", "supplier_name", "type", "iso_9001", "other_certs", "commodities_supplied", "material_spend_12m_usd", "parts_supplied_without_required_qualification",
       "spend_on_those_parts_usd", "those_parts"], tail)
# make versus buy at El Paso
mvb = []
for w in (900, 1000):
    fz = "TFUSE:229C:SF" if w == 1000 else "TFUSE:216C:SF"
    kids = [(f"HEATER:{w}W", 1), ("TSTAT:105C", 1), (fz, 2), ("HBRACKET", 1)]
    mat = 0.0
    for k, q in kids:
        rows_k = [i for i in PRODINV if i["plant"] == "B" and i["key"] == k and i["po_date"] < MAKE_TO_BUY_B]
        qq = sum(i["base_qty"] for i in rows_k); mat += q * (sum(i["amount"] for i in rows_k) / qq if qq else CP[k]["price"])
    labor = HEATER_MIN / 60 * LABOR["B"][0]; oh = labor * LABOR["B"][1]
    a, q = wprice.get(("B", f"HTR:{w}"), [0, 0]); buy = a / q if q else CP[f"HTR:{w}"]["price"]
    units = sum(BUILD[("B", m, ym)] for m in PLANT_MODELS["B"] if MODELS[m]["watt"] == w for ym in MONTHS if date(ym[0], ym[1], 15) >= MAKE_TO_BUY_B)
    mvb.append([ITEM[("B", f"HTR:{w}")], CP[f"HTR:{w}"]["cid"], f"HTR:{w}", MAKE_TO_BUY_B.isoformat(), round(mat, 4), round(labor, 4), round(oh, 4), round(mat + labor, 4), round(mat + labor + oh, 4),
                round(buy, 4), round(buy - (mat + labor), 4), round(buy - (mat + labor + oh), 4), units, round((buy - (mat + labor)) * units, 2), round((buy - (mat + labor + oh)) * units, 2),
                f"Buying is ${mat + labor + oh - buy:.2f} a unit cheaper than the full standard make cost, but ${buy - mat - labor:.2f} dearer than material plus labor. It saves money only if the overhead really went away."])
write(os.path.join(AK, "key_make_vs_buy.csv"),
      ["elpaso_part", "canonical_id", "canonical_key", "switched_to_buy_on", "make_material_usd", "make_labor_usd", "make_overhead_usd", "make_material_plus_labor_usd", "make_full_cost_usd", "buy_price_usd",
       "buy_minus_material_plus_labor_usd_per_unit", "buy_minus_full_make_cost_usd_per_unit", "units_built_since_switch", "buy_minus_material_plus_labor_usd_since_switch",
       "buy_minus_full_make_cost_usd_since_switch", "reading"], mvb)
# notices
nk = []
for n in NOTICES:
    other = "B" if n["plant"] == "A" else "A"; sups = n.get("sups", [n["sup"]]); hidden = n.get("hidden", {})
    rm = {}; items = {}; sp = {}; sp3 = {}
    for p in ("A", "B"):
        keys_p = [k for k in n["keys"] if any(spend_pks.get((p, k, x), 0) > 0 for x in sups)]
        sp[p] = round(sum(spend_pks.get((p, k, x), 0) for k in n["keys"] for x in sups), 2)
        sp3[p] = round(sum(spend_pks_3m.get((p, k, x), 0) for k in n["keys"] for x in sups), 2)
        rm[p] = uniq([m for k in keys_p for m in PLANT_MODELS[p] if any(b == k for a, b, q, t in bom_edges(m, p))])
        items[p] = [ITEM[(p, k)] for k in keys_p]
    nk.append([n["id"], n["type"], PLANT_NAME[n["plant"]], "; ".join(SUP[x]["name"] for x in sups), "; ".join(CP[k]["cid"] for k in n["keys"]), "; ".join(items["A"]), "; ".join(items["B"]),
               ", ".join(rm["A"]), ", ".join(rm["B"]), " | ".join(hidden[p] for p in ("A", "B") if p in hidden), sp["A"], sp["B"], sp3["A"], sp3["B"],
               "Y" if (sp[other] > 0 or other in hidden) else "N", (n["eff"] - n["recv"]).days, n["actioned"], n["truth"], n["behaviour"]])
write(os.path.join(AK, "key_supplier_change_notices.csv"),
      ["notice_id", "notice_type", "received_by_plant", "suppliers_in_scope", "affected_canonical_ids", "dayton_items", "elpaso_parts", "dayton_models_affected", "elpaso_models_affected", "hidden_use",
       "dayton_spend_12m_usd", "elpaso_spend_12m_usd", "dayton_spend_aug_to_oct_2026_usd", "elpaso_spend_aug_to_oct_2026_usd", "other_plant_also_exposed", "days_from_receipt_to_effective",
       "actioned", "what_is_true", "expected_tool_behaviour"], nk)
# open orders that need attention: on a superseded number, or on a part under an open notice
noticed = {}
for n in NOTICES:
    if n["actioned"] != "Y":
        for k in n["keys"]:
            for x in n.get("sups", [n["sup"]]):
                noticed[(k, x)] = n["id"]
att = []
for o in OPEN:
    if o["key"] not in CP:
        continue
    if "ORDERED_ON_OBSOLETE_NUMBER" in o["causes"]:
        att.append([PLANT_NAME[o["plant"]], o["po"], o["line"], o["sup"], o["item"], CP[o["key"]]["cid"], o["key"], o["open_qty"], round(o["open_qty"] * o["price"] / o["per"], 2),
                    "ORDERED_ON_SUPERSEDED_NUMBER", f"Current number is {ITEM[(o['plant'], o['key'])]}"])
    elif (o["key"], o["sup"]) in noticed:
        att.append([PLANT_NAME[o["plant"]], o["po"], o["line"], o["sup"], o["item"], CP[o["key"]]["cid"], o["key"], o["open_qty"], round(o["open_qty"] * o["price"] / o["per"], 2),
                    "PART_UNDER_OPEN_SUPPLIER_NOTICE", noticed[(o["key"], o["sup"])]])
write(os.path.join(AK, "key_open_orders_needing_attention.csv"),
      ["plant", "po_number", "po_line", "supplier_code", "item_on_po", "canonical_id", "canonical_key", "open_qty", "open_value_usd", "reason", "detail"], att)
# delivery performance
perf = []
for plant in ("A", "B"):
    for s in SUP:
        g = [x for x in REC if x["plant"] == plant and x["sup"] == s]; o = [x for x in OPEN if x["plant"] == plant and x["sup"] == s]
        if not g and not o:
            continue
        late = [(x["date"] - x["promised"]).days for x in g if x["date"] > x["promised"]]
        note = {"TRES": "Planted: promises short and delivers late. Also has no ISO 9001 and no food-contact certification.", "LONE": "Planted: late more often than most. No ISO 9001.",
                "MVMO": "Planted: reliable.", "EMBR": "Planted: reliable.", "GMFA": "Planted: reliable.", "BUCK": "Planted: reliable.",
                "VIDR": "Planted: open orders from September 2026 are confirmed about 4 weeks late (lead time 4 to 8 weeks, notice PCN-2026-0095)."}.get(s, "")
        perf.append([PLANT_NAME[plant], s, SUPID[(plant, s)], SUP[s]["name"], len(g), round(100 * (len(g) - len(late)) / len(g), 1) if g else "", round(sum(late) / len(late), 1) if late else 0,
                     round(sum((x["date"] - x["po_date"]).days for x in g) / len(g), 1) if g else "", len(o), sum(1 for x in o if x["slip"] >= 14), note])
write(os.path.join(AK, "key_supplier_delivery_performance.csv"),
      ["plant", "supplier_code", "supplier_id", "supplier_name", "receipt_lines", "on_time_pct", "avg_days_late_when_late", "avg_actual_lead_days", "open_lines_at_period_end",
       "open_lines_confirmed_14_or_more_days_late", "note"], perf)
write(os.path.join(AK, "key_open_po_slippage.csv"),
      ["plant", "po_number", "po_line", "supplier_code", "canonical_id", "canonical_key", "plant_item", "open_qty", "promised_date", "confirmed_date", "days_late_vs_promise", "models_that_use_the_part"],
      [[PLANT_NAME[o["plant"]], o["po"], o["line"], o["sup"], CP[o["key"]]["cid"], o["key"], o["item"], o["open_qty"], o["promised"].isoformat(), o["conf"].isoformat(), o["slip"],
        ", ".join(uniq(models_using(o["plant"], o["key"])[0] + models_using(o["plant"], o["key"])[1]))] for o in sorted(OPEN, key=lambda o: (-o["slip"], o["plant"], o["po"], o["line"]))
       if o["slip"] >= 14 and o["key"] in CP])
fk = []
for (plant, m), (plan, actual, nxt) in FCT.items():
    fk.append([PLANT_NAME[plant], m, plan, actual, round(actual / plan - 1, 4), nxt, round(nxt / actual - 1, 4), round(UNIT_MAT[(plant, m)], 3), round(nxt * UNIT_MAT[(plant, m)], 2)])
write(os.path.join(AK, "key_forecast_vs_actual.csv"),
      ["plant", "model", "fy26_plan_units", "fy26_actual_units", "actual_vs_plan_pct", "fy27_forecast_units", "fy27_vs_fy26_actual_pct", "purchased_material_usd_per_unit",
       "fy27_forecast_purchased_material_spend_usd"], fk)

# planted cases and summary
tot = sum(r["amount"] for r in INV)
n_cause = lambda c: sum(1 for r in PO if c in r["causes"])
fkd = {(r[0], r[1]): r[4] for r in fk}
tot_opp = lambda t, col: round(sum(r[col] for r in opp if r[1] == t), 2)
air = round(sum(r["amount"] for r in PO if "AIR FREIGHT" in r["desc"].upper()), 2)
planted = [
    ["P01", "CROSS_PLANT_PART_NUMBER", f"{len(dups)} purchased parts exist at both plants under unrelated numbers; the old cross-reference covers {len(given)} of them", "key_cross_plant_same_part.csv", "Propose the remaining links with confidence and evidence"],
    ["P02", "LEGACY_XREF_ERROR", "One row of the 2023 cross-reference links the 216 C thermal fuse to the 229 C fuse", "key_lookalikes_do_not_merge.csv", "Flag the row: the rating field conflicts. Do not inherit it blindly"],
    ["P03", "NEAR_IDENTICAL_CLOSE_SPEC", f"{sum(1 for f in FAMILIES for m in f[3] if m[1] == CLOSE)} parts in near-identical families where the two plants use parts that differ by one small spec step (cord length, screw length, tube wall, foot diameter, switch rating, carton board, fuse maker)", "key_near_duplicate_families.csv", "Group them, show the differing field, and route to engineering review. Do not merge automatically"],
    ["P04", "LOOKALIKE_DO_NOT_MERGE", "3 parts look the same as a family standard and must stay separate (229 C fuse, 1000 W element, thermal-model harness)", "key_lookalikes_do_not_merge.csv", "Keep separate; show the differing rating"],
    ["P05", "DUPLICATE_NUMBER_SAME_PLANT", "The same part was created twice at one plant: the M4 screw at Dayton and the 12-cup glass carafe at El Paso, each bought from a different supplier at a different price", "key_near_duplicate_families.csv (DUP rows)", "Merge the numbers; show the price difference"],
    ["P06", "SUPPLIER_PART_NO_ONLY", f"{n_cause('SUPPLIER_PART_NO_ONLY')} PO lines carry only a distributor's part number", "key_po_line_truth.csv", "Resolve through the vendor part cross-reference, then description"],
    ["P07", "SUPERSESSION_ONE_TO_ONE", "Dayton power cord revised on 2026-02-01; older POs carry the old number", "A_supersessions.csv", "Date-aware link old to new"],
    ["P08", "SUPERSESSION_MANY_TO_ONE", "The two-piece 5-cup carafe lid (top and hinge) was replaced by a one-piece lid on 2026-04-01", "A_supersessions.csv", "Roll both old numbers up to the new part for spend history"],
    ["P09", "RENUMBERED_NO_RECORD", "El Paso check valve renumbered in March 2026 with no supersession record", "key_item_to_canonical.csv", "Suggest from the identical description and the inactive flag; needs review"],
    ["P10", "UOM_AND_PRICE_BASIS", "Screws, clamps, feet and bags: box of 1000 at Dayton, priced per 1000 at El Paso. Silicone tube: 50 m rolls at Dayton, by the foot at El Paso, used by the metre", "A_uom_conversions.csv / B_UM_Conversions.csv", "Normalize to price per base unit before comparing"],
    ["P11", "UOM_CONVERSION_MISSING", f"Dayton rating label {ITEM[('A', 'RATINGLABEL')]} is bought by the roll of 1000 and the conversion is not in the UOM table", "answer here", "Flag for manual conversion; do not compare price per roll with price per label"],
    ["P12", "MAKE_VS_BUY_OVER_TIME", "El Paso assembled the heater assembly in house until 2026-04-30 and has bought it complete since 2026-05-01. Before the switch it bought the element, thermostat, fuses and bracket; after it, one assembly", "B_Make_Buy_Changes.csv, key_make_vs_buy.csv", "Cost the bought assembly at its own level after the switch; never count both parent and children; compare make cost with buy price"],
    ["P13", "SUPPLIER_KIT", "El Paso buys the BL-12T packaging as one kit; the BOM lists box, tray, manual and bag separately", "key_kit_contents.csv", "Match at kit level and show the BOM lines it covers"],
    ["P14", "SPARES_AND_WARRANTY", f"{sum(1 for r in PO if r['bucket'] == 'SPARE')} spare and {sum(1 for r in PO if r['bucket'] == 'WARRANTY')} warranty PO lines: on service SKUs, on production numbers with a service cost centre, and some with no purpose tag", "key_po_line_truth.csv", "Bucket separately from production; lines marked IDENTITY_ONLY can be matched to a part but not to a purpose"],
    ["P15", "SERVICE_XREF_GAPS", f"{len(SVC) - len(SVC_GIVEN)} of {len(SVC)} service SKUs have no production item in the service catalogue", "service_parts_catalog.csv", "Infer from the description, flag for review"],
    ["P16", "FREE_TEXT_RESOLVABLE", f"{sum(1 for r in PO if 'FREE_TEXT' in r['causes'] and r['method'] == 'DESCRIPTION_SIMILARITY')} PO lines have no item number but a usable description, supplier and price", "key_po_line_truth.csv", "Propose candidates with confidence; buyer confirms"],
    ["P17", "FREE_TEXT_QUOTE_REF", "El Paso orders its control boards as free text against a quote number; these are high-value lines", "B_Quotes.csv", "Resolve through the quote reference"],
    ["P18", "FREE_TEXT_UNRESOLVABLE", f"{sum(1 for r in PO if r['bucket'] == 'UNRESOLVED')} PO lines cannot be identified from the data (worth ${sum(r['amount'] for r in PO if r['bucket'] == 'UNRESOLVED'):,.0f})", "key_po_line_truth.csv", "Leave unresolved and report the value; never force a match"],
    ["P19", "NON_PRODUCT_SPEND", "Freight, air freight, safety testing, mold repair, pallets and shop supplies", "key_po_line_truth.csv", "Classify as non-product; do not charge to a BOM"],
    ["P20", "INVOICE_TO_PO", "About a quarter of PO lines are invoiced in two or three parts; about 3% of invoice lines have no PO reference; 12 credit notes; freight lines added at invoice level", "key_invoice_line_truth.csv", "Link many-to-one; recover missing PO references from supplier, item and price"],
    ["P21", "TIMING", f"{len(INV_LATE)} invoice lines fall after 2026-10-31 and are not in the extract, so PO value and invoiced value differ", "computed", "Report as timing difference, not as a mismatch"],
    ["P22", "SEVERAL_SUPPLIERS_SAME_PART", "Most commodities are bought from two suppliers at each plant and from different suppliers across plants, at prices 3% to 20% apart", "key_price_by_part_and_supplier.csv, key_savings_opportunities.csv", "Compare price per base unit by supplier for the same part and size the gap to the best qualified supplier"],
    ["P23", "UNQUALIFIED_TAIL_SUPPLIERS", "Three suppliers have no ISO 9001: a molder that also lacks food-contact certification yet supplies tanks and baskets, a cord maker whose UL file is pending, and a fastener distributor. Two of them are the cheapest source", "key_supplier_summary.csv", "Never pick the cheapest price without the qualification check; show the spend at risk"],
    ["P24", "QUOTE_TO_PO_LEAKAGE", "At Dayton, 4 parts are invoiced 3% to 6% above the awarded quote from March 2026", "key_quote_to_invoice_leakage.csv", "Compare quote, PO and invoice price for the same part"],
    ["P25", "CHEAPER_QUOTE_WITH_A_CATCH", "Some losing quotes are 5% to 12% cheaper but come from an unqualified supplier or carry about double the lead time and 3 to 10 times the MOQ", "quote files", "Show qualification, lead time and MOQ beside price"],
    ["P26", "SUPPLIER_NAME_VARIANTS", "The same supplier appears under different local IDs and spellings at the two plants", "supplier files", "Normalize suppliers before comparing prices"],
    ["P27", "MISSING_MASTER_DATA", "About a quarter of El Paso part master rows lack manufacturer, material, rating or compliance", "B_Part_Master.csv", "Lower confidence where evidence is missing"],
    ["P28", "SUPPLIER_NOTICE_FORGOTTEN", f"{len(NOTICES)} supplier change notices; {sum(1 for n in NOTICES if n['actioned'] != 'Y')} have no completed action", "shared/supplier_change_notices.csv", "Link each notice to parts, BOMs, models and spend; alert on the open ones by effective date"],
    ["P29", "NOTICE_REACHED_ONE_PLANT", "The thermostat discontinuation reached Dayton only, while El Paso uses the same thermostat. The heating element redesign reached El Paso only, which no longer buys that element, while Dayton buys all of its elements from that supplier", "key_supplier_change_notices.csv", "Use the cross-plant part link to show the plant that was not told"],
    ["P30", "NOTICE_EXPLAINS_SUPERSESSION", "One notice explains the recorded Dayton cord revision (P07); another explains the unrecorded El Paso check valve renumbering (P09)", "key_supplier_change_notices.csv", "Tie notices to supersessions, recorded or not"],
    ["P31", "NOTICE_WITHOUT_PART_NUMBER", "Two notices name a material or product group and no part number (food-contact resin, all glass carafes)", "key_supplier_change_notices.csv", "Expand to every matching part"],
    ["P32", "NOTICE_WITH_NO_EXPOSURE", "One notice concerns a 1500 W element the company does not buy", "key_supplier_change_notices.csv", "Show zero exposure; no alert"],
    ["P33", "LEAD_TIME_SHAKE_UP", f"Imported glass carafe lead time doubles from 4 to 8 weeks from September 2026; open carafe orders at El Paso are confirmed about 4 weeks late; ${air:,.0f} of air freight was already spent", "open PO files, key_open_po_slippage.csv", "Flag open orders at risk, the models they hold up and the freight already spent"],
    ["P34", "SUPPLIER_DELIVERY_PERFORMANCE", "Promised versus actual receipt dates differ by supplier; the two unqualified tail suppliers are also the late ones", "receipt files, key_supplier_delivery_performance.csv", "Show on-time rate and actual lead time beside price when comparing suppliers"],
    ["P35", "FORECAST_VS_ACTUAL", f"El Paso BL-12T ran {fkd[('El Paso', 'BL-12T')]:+.0%} against its FY26 plan and Dayton BL-5 {fkd[('Dayton', 'BL-5')]:+.0%}; the FY27 plan grows the thermal model 40% and shrinks the 5-cup", "shared/build_forecast.csv, key_forecast_vs_actual.csv", "Compare actual with plan, and project next year's purchased-material spend from the forecast"],
    ["P37", "SUPERSEDED_PART_STILL_ON_ORDER", "Two open orders placed in late October 2026 use superseded numbers: the old Dayton power cord number and the old El Paso check valve number", "open PO files, key_open_orders_needing_attention.csv", "Flag open orders on superseded numbers, and open orders on parts under an open supplier notice"],
    ["P36", "FULL_COST", "Labor minutes, labor rates and overhead multiples per plant are given, so a full cost per unit can be modeled on top of purchased material", "shared/labor_and_overhead_standards.csv, key_modeled_cost_per_unit.csv", "Show material, labor and overhead as separate, labeled parts of the unit cost"],
]
write(os.path.join(AK, "key_planted_cases.csv"), ["case_id", "type", "what_is_planted", "where_to_look", "expected_tool_behaviour"], planted)
spend = defaultdict(float)
for r in INV:
    spend[(r["plant"], r["bucket"])] += r["amount"]
ok_id = sum(r["amount"] for r in INV if r["bucket"] in ("PRODUCTION", "SPARE", "WARRANTY"))
ontime = sum(1 for g in REC if g["date"] <= g["promised"])
summary = OrderedDict(
    seed=SEED, period="2025-11-01 to 2026-10-31", units_built_12m=sum(BUILD.values()),
    canonical_parts=len(CP), purchased_canonical_parts=sum(1 for c in CP.values() if c["kind"] in ("buy", "kit")), suppliers=len(SUP),
    cross_plant_same_parts=len(dups), cross_plant_links_in_legacy_xref=len(given),
    near_identical_families=len(FAMILIES), close_spec_members=sum(1 for f in FAMILIES for m in f[3] if m[1] == CLOSE), do_not_merge_lookalikes=sum(1 for f in FAMILIES for m in f[3] if m[1] == NOMERGE),
    duplicate_item_numbers_same_plant=len(ALIAS),
    po_lines=len(PO), invoice_lines_in_extract=len(INV), invoice_lines_after_period_end=len(INV_LATE),
    invoiced_spend_total_usd=round(tot, 2), invoiced_spend_by_plant_and_bucket={f"{p}:{b}": round(v, 2) for (p, b), v in sorted(spend.items())},
    share_of_spend_linkable_to_a_part=round(ok_id / tot, 4),
    share_of_spend_matched_by_exact_item_number_only=round(sum(r["amount"] for r in INV if r["item"] and r["bucket"] in ("PRODUCTION", "SPARE", "WARRANTY") and r["method"] in ("EXACT_ITEM", "KIT_CONTENTS")) / tot, 4),
    share_of_spend_unresolvable=round(sum(r["amount"] for r in INV if r["bucket"] == "UNRESOLVED") / tot, 4),
    share_of_spend_non_product=round(sum(r["amount"] for r in INV if r["bucket"] == "NON_PRODUCT") / tot, 4),
    po_lines_by_cause={c: n_cause(c) for c in sorted({c for r in PO for c in r["causes"]})},
    true_savings_by_opportunity_type_usd=OrderedDict([
        ("same_part_price_alignment_across_suppliers_and_plants", tot_opp("SAME_PART_SEVERAL_SUPPLIERS", 11)),
        ("near_identical_family_standard_part_price_alignment", tot_opp("NEAR_IDENTICAL_FAMILY", 11)),
        ("near_identical_family_after_engineering_review", tot_opp("NEAR_IDENTICAL_FAMILY", 12)),
        ("quote_to_invoice_leakage_at_dayton", round(sum(r[8] for r in leak), 2)),
        ("air_freight_spent_on_late_carafes", air)]),
    sized_supplier_and_part_savings_total_usd=round(sum(r[13] for r in opp), 2),
    of_which_depends_on_a_supplier_with_a_caution_usd=round(sum(r[13] for r in opp if r[15]), 2),
    open_orders_on_superseded_numbers=sum(1 for r in att if r[9] == "ORDERED_ON_SUPERSEDED_NUMBER"), open_orders_on_parts_under_open_notice=sum(1 for r in att if r[9] != "ORDERED_ON_SUPERSEDED_NUMBER"),
    sized_savings_pct_of_invoiced_spend=round(sum(r[13] for r in opp) / tot, 4),
    spend_with_suppliers_lacking_required_qualification_usd=round(sum(r[10] for r in tail), 2),
    supplier_change_notices=len(NOTICES), notices_without_completed_action=sum(1 for n in NOTICES if n["actioned"] != "Y"),
    receipt_lines=len(REC), receipts_on_time_pct=round(100 * ontime / len(REC), 1),
    open_po_lines_at_period_end=len(OPEN), open_po_lines_confirmed_14_or_more_days_late=sum(1 for o in OPEN if o["slip"] >= 14),
    fy27_forecast_units=sum(v[2] for v in FCT.values()), fy27_forecast_purchased_material_spend_usd=round(sum(r[8] for r in fk), 2),
    file_row_counts=COUNTS,
)
with open(os.path.join(AK, "key_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
