"""Text helpers: turn a messy part description into comparable tokens.

Two plants describe the same part differently ("HOUSING, BL-12, PP, BLACK" and
"BL12 PP Black hsg"). These helpers expand abbreviations, drop buyer noise
("re-order", "- urgent") and pull out the numbers that matter (216 C, 900 W,
M3 x 8) so the rest of the tool can compare like with like.

The abbreviation list is plain data. On a real client it would be extended in
the first days of the engagement.
"""
import re

ABBREVIATIONS = {
    "HSG": "HOUSING", "PLT": "PLATE", "BSKT": "BASKET", "WARM": "WARMING", "HTG": "HEATING",
    "T-STAT": "THERMOSTAT", "TSTAT": "THERMOSTAT", "HTR": "HEATER", "BRKT": "BRACKET",
    "CHK": "CHECK", "PWR": "POWER", "SW": "SWITCH", "CTRL": "CONTROL", "CTN": "CARTON",
    "PKG": "PACKAGING", "ASSY": "ASSEMBLY", "ZP": "ZN", "ZINC": "ZN", "PH": "PAN HEAD",
    "HD": "HEAD", "TUBING": "TUBE", "POLYBAG": "POLY BAG", "BLK": "BLACK", "BL12": "BL-12",
    "BL5": "BL-5", "BL12P": "BL-12P", "BL12T": "BL-12T", "SELF-TAPPING": "TAPPING",
    "CLOCK/TIMER": "CLOCK TIMER", "EN/ES/FR": "EN ES FR", "BOARDS": "BOARD", "IND": "INDUSTRIAL",
}
# Phrases buyers type into free-text lines that say nothing about the part.
NOISE = [r"\bRE-?ORDER\b", r"\bURGENT\b", r"\bPER BUYER\b", r"\(STOCK OUT\)", r"\bSTOCK OUT\b",
         r"\bFOR BL-?\d+[PT]? LINE\b", r"\bSERVICE PART\b", r"\bPLATED\b"]
STOP = {"WITH", "W", "AND", "X", "MM", "-", "", "NO", "ID", "THE", "OF"}
# Material, colour and finish words: useful evidence, but not what a part *is*.
GENERIC = {"PP", "BLACK", "CLEAR", "STEEL", "ZN", "TRANSLUCENT", "SILICONE", "GLASS", "ADHESIVE",
           "RED", "LED", "LDPE", "PET", "SILVER", "ALUMINUM"}


def clean(text):
    t = (text or "").upper()
    for pat in NOISE:
        t = re.sub(pat, " ", t)
    t = re.sub(r"(\d+)\s+CUP\b", r"\1-CUP", t)            # "12 cup" -> "12-CUP"
    t = re.sub(r"\bM(\d+)\s*X\s*(\d+)\b", r"M\1X\2", t)   # "M4 X 12" -> "M4X12"
    t = re.sub(r"(\d)\s+(MM|M|L|W|V|A|C)\b", r"\1\2", t)   # "12 MM" -> "12MM"
    t = re.sub(r"[,;()+]", " ", t)
    t = re.sub(r"\s-\s", " ", t)
    return t


def tokens(text):
    out = []
    for tok in clean(text).split():
        tok = tok.strip(".:")
        for part in ABBREVIATIONS.get(tok, tok).split():
            if part not in STOP:
                out.append(part)
    return out


def token_set(text):
    return set(tokens(text))


def norm(text):
    """Canonical text form: sorted unique tokens."""
    return " ".join(sorted(token_set(text)))


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def similarity(text_a, text_b):
    return round(jaccard(token_set(text_a), token_set(text_b)), 3)


def core_words(text):
    """Words that say what the part is: no numbers, no material or colour words."""
    return {t for t in token_set(text) if not re.search(r"\d", t) and t not in GENERIC}


# --- attributes: the numbers that decide whether two parts are interchangeable ----
ATTRIBUTE_PATTERNS = [
    ("model", r"\bBL-?(\d+[PT]?)\b"),
    ("cup size", r"\b(\d+)-CUP\b"),
    ("holds", r"\bHOLDS (\d+)\b"),
    ("thread", r"\bM(\d+)X\d+\b"),
    ("thread length mm", r"\bM\d+X(\d+)\b"),
    ("temperature C", r"\b(\d{2,3})\s?C\b"),
    ("power W", r"\b(\d{3,4})\s?W\b"),
    ("voltage V", r"\b(\d{2,3})\s?V\b"),
    ("current A", r"\b(\d{1,2})\s?A\b"),
    ("wires", r"\b(\d+)[- ](?:WIRE|LEADS)\b"),
    ("board grade ECT", r"\bECT-?(\d+)\b"),
    ("wall mm", r"\b([\d.]+)MM WALL\b|\bWALL ([\d.]+)"),
    ("diameter mm", r"\bDIA ([\d.]+)"),
    ("length m", r"\b(\d\.\d)M\b"),
    ("volume L", r"\b([\d.]+)\s?L\b"),
    ("wire gauge AWG", r"\b(\d+)AWG\b"),
    ("size mm", r"\b(\d+(?:\.\d+)?)MM\b"),
]


def attributes(*texts):
    """Pull comparable numbers out of description, rating and dimension fields."""
    found = {}
    for text in texts:
        t = clean(text)
        for name, pat in ATTRIBUTE_PATTERNS:
            if name in found:
                continue
            m = re.search(pat, t)
            if m:
                val = next(g for g in m.groups() if g is not None)
                found[name] = val
    # "12MM" foot vs "DIA 12.0 MM": treat a lone size as the diameter when both exist
    if "diameter mm" in found and "size mm" in found:
        found.pop("size mm")
    return found


def norm_supplier(name):
    t = (name or "").upper()
    t = t.replace("&", " AND ").replace("E.M.S.", "EMS")
    t = re.sub(r"[.,]", " ", t)
    words = []
    for w in t.split():
        w = {"IND": "INDUSTRIAL", "CTRLS": "CONTROLS", "PROD": "PRODUCTS", "CO": "", "INC": "",
             "LLC": "", "CORP": ""}.get(w, w)
        if w:
            words.append(w)
    return " ".join(words).replace("GLASS WORKS", "GLASSWORKS")
