"""Shared paths, palettes and helpers for the tour-de-france project.

Raw inputs (read in place, never modified), all in raw/ inside the study:
  raw/men/TDF_Stages_History.csv      one row per stage of the men's Tour, 1903 to 2026: year, total distance of that
                                      Tour, stage number, start town, finish town, stage winner and jersey holders
  raw/men/TDF_Riders_History.csv      one row per rider and edition: final general classification rank, time, distance
  raw/women/TDFF_Stages_History.csv   the same for the Tour de France Femmes, 2022 to 2026
  raw/women/TDFF_Riders_History.csv
      All four from Thomas Camminady's LeTourDataSet (https://github.com/thomascamminady/LeTourDataSet, MIT licence,
      commit in raw/LeTourDataSet_commit.txt; README and licence in raw/), which compiles the official historical
      pages of letour.fr and letourfemmes.fr.
  raw/geonames_cities1000.json        GeoNames cities1000 gazetteer (every place with at least 1,000 people), as packaged
                                      by lutangar/cities.json (commit in raw/cities_json_commit.txt). CC BY 4.0, GeoNames.
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_10m_admin_0_countries.geojson,
      ne_10m_admin_1_states_provinces.geojson (French departements), ne_50m_land.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("TDF_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("TDF_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("TDF_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("TDFTMP", "/dev/shm/tourdefrance"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "tour-de-france"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23873013"                # filled in by the publisher
DOI_URL = "https://doi.org/10.5281/zenodo.23873013"        # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/tour-de-france/"          # filled in by the publisher
LTD_URL = "https://github.com/thomascamminady/LeTourDataSet"
LTD_COMMIT = open(os.path.join(RAW, "LeTourDataSet_commit.txt")).read().strip()
GN_COMMIT = open(os.path.join(RAW, "cities_json_commit.txt")).read().strip()
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
TITLE = "Every Tour de France, mapped"
PAPER_TITLE = "The Shape of the Tour: Every Stage of the Tour de France, 1903 to 2026, Mapped from Start to Finish"
CITE_TITLE = "The shape of the Tour: every stage of the Tour de France, 1903 to 2026, mapped from start to finish"

# Decades and their colours (a dark to warm ramp; yellow is kept for the highlighted Tour on the map)
DECADES = list(range(1900, 2030, 10))
DEC_COL = ["#1B2A4A", "#22417A", "#2F5FA7", "#2F7FB0", "#2E9A8C", "#4FA66A", "#8FAE45", "#C3A23A", "#DE8A2C",
           "#D9662A", "#C8432B", "#A4283A", "#7A1F45"]
assert len(DECADES) == len(DEC_COL)
WOMEN_COL = "#8E44AD"
YELLOW = "#F5C400"

# Countries that hosted stage towns: ISO2 -> English name (only these are searched in the gazetteer)
COUNTRIES = {"FR": "France", "BE": "Belgium", "LU": "Luxembourg", "DE": "Germany", "CH": "Switzerland", "IT": "Italy",
             "ES": "Spain", "AD": "Andorra", "MC": "Monaco", "NL": "Netherlands", "GB": "United Kingdom", "IE": "Ireland",
             "DK": "Denmark"}
NEIGHBOURS = {"FR", "BE", "LU", "DE", "CH", "IT", "ES", "AD", "MC"}

# Nationality of every overall winner in the riders file. LeTourDataSet has no nationality column, so this is a
# hand-made table (one line per rider, as the riders file spells the name). In the national team years (1930 to 1961,
# 1967, 1968) the team column names the nation and 03_results.py checks it against this table.
WINNER_NAT = {
    "MAURICE GARIN": "France", "HENRI CORNET (GEBOREN JARDY)": "France", "LOUIS TROUSSELIER": "France", "RENÉ POTTIER": "France",
    "LUCIEN MAZAN DIT PETIT-BRETON": "France", "FRANÇOIS FABER": "Luxembourg", "OCTAVE LAPIZE": "France", "GUSTAVE GARRIGOU": "France",
    "ODIEL DEFRAEYE": "Belgium", "PHILIPPE THYS": "Belgium", "FIRMIN LAMBOT": "Belgium", "LÉON SCIEUR": "Belgium",
    "HENRI PELISSIER": "France", "OTTAVIO BOTTECCHIA": "Italy", "LUCIEN BUYSSE": "Belgium", "NICOLAS FRANTZ": "Luxembourg",
    "MAURICE DE WAELE": "Belgium", "ANDRÉ LEDUCQ": "France", "ANTONIN MAGNE": "France", "GEORGES SPEICHER": "France",
    "ROMAIN MAES": "Belgium", "SYLVÈRE MAES": "Belgium", "ROGER LAPEBIE": "France", "GINO BARTALI": "Italy", "JEAN ROBIC": "France",
    "FAUSTO COPPI": "Italy", "FERDI KUBLER": "Switzerland", "HUGO KOBLET": "Switzerland", "LOUISON BOBET": "France",
    "ROGER WALKOWIAK": "France", "JACQUES ANQUETIL": "France", "CHARLY GAUL": "Luxembourg", "FEDERICO BAHAMONTES": "Spain",
    "GASTONE NENCINI": "Italy", "FELICE GIMONDI": "Italy", "LUCIEN AIMAR": "France", "ROGER PINGEON": "France",
    "JAN JANSSEN": "Netherlands", "EDDY MERCKX": "Belgium", "LUIS OCANA": "Spain", "BERNARD THEVENET": "France",
    "LUCIEN VAN IMPE": "Belgium", "BERNARD HINAULT": "France", "JOOP ZOETEMELK": "Netherlands", "LAURENT FIGNON": "France",
    "GREG LEMOND": "United States", "STEPHEN ROCHE": "Ireland", "PEDRO DELGADO": "Spain", "MIGUEL INDURAIN": "Spain",
    "BJARNE RIIS": "Denmark", "JAN ULLRICH": "Germany", "MARCO PANTANI": "Italy", "OSCAR PEREIRO SIO": "Spain",
    "ALBERTO CONTADOR": "Spain", "CARLOS SASTRE": "Spain", "ANDY SCHLECK": "Luxembourg", "CADEL EVANS": "Australia",
    "BRADLEY WIGGINS": "United Kingdom", "CHRIS FROOME": "United Kingdom", "VINCENZO NIBALI": "Italy", "GERAINT THOMAS": "United Kingdom",
    "EGAN BERNAL GOMEZ": "Colombia", "TADEJ POGACAR": "Slovenia", "JONAS VINGEGAARD HANSEN": "Denmark",
    # women
    "ANNEMIEK VAN VLEUTEN": "Netherlands", "DEMI VOLLERING": "Netherlands", "KATARZYNA NIEWIADOMA-PHINNEY": "Poland",
    "PAULINE FERRAND PREVOT": "France"}
# names of national teams in the riders file (1930 to 1961, 1967, 1968) -> nation
TEAM_NATION = {"FRANCE": "France", "BELGIQUE": "Belgium", "ITALIE": "Italy", "SUISSE": "Switzerland", "ESPAGNE": "Spain",
               "NEDERLAND": "Netherlands", "PAYS BAS-LUXEMBOURG": "Luxembourg"}
NAT_COL = {"France": "#2F5FA7", "Belgium": "#C8432B", "Spain": "#DE8A2C", "Italy": "#2E9A8C", "Luxembourg": "#7FB2D9",
           "United Kingdom": "#1B2A4A", "Netherlands": "#F2B701", "Denmark": "#A4283A", "Slovenia": "#4FA66A",
           "Switzerland": "#B05A7A", "United States": "#6B6B9A", "Others": "#A79F94"}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def strip_acc(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(ch for ch in s if not unicodedata.combining(ch))


ARTICLES = ("le ", "la ", "les ", "l ")


def norm(s):
    """Lower case, no accents, St/Ste spelt out, hyphens, apostrophes and underscores as spaces."""
    s = strip_acc(s).lower().replace("_", " ").replace("’", "'").replace("œ", "oe").replace("æ", "ae").replace("ß", "ss")
    s = re.sub(r"[\W]+", " ", s).strip()
    s = re.sub(r"\bste\b", "sainte", s); s = re.sub(r"\bst\b", "saint", s)
    return re.sub(r"\s+", " ", s)


def norm_noart(s):
    n = norm(s)
    for a in ARTICLES:
        if n.startswith(a):
            return n[len(a):]
    return n


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


def hav_km(lat1, lon1, lat2, lon2):
    """Great circle distance in km (works on numbers or numpy arrays)."""
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


def decade_of(y):
    return int(y) // 10 * 10
