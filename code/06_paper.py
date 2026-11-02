"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23873013 placeholder."""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Shape_of_the_Tour"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
Y = {y["y"]: y for y in R["years"]}
DEC = {d["dec"]: d for d in R["decades"]}; CEN = {c["dec"]: c for c in R["centre"]}
assert all(Y[y]["dist"] > 5000 for y in Y if 1911 <= y <= 1929) and Y[1910]["dist"] < 5000 and Y[1930]["dist"] < 5000   # "every Tour from 1911 to 1929"
assert R["dist"]["shortest_years"] == [1903, 1904]                                                                      # "the shortest the first two"
assert all(45 < CEN[d]["edge50_pct"] < 52 for d in range(1980, 2030, 10)) and CEN[2020]["edge50_pct"] > R["shape"]["area_edge50_pct"]   # "near half since the 1980s"
assert DEC[1900]["transfer_pct"] < 6 and DEC[1940]["transfer_pct"] < 2 and DEC[1950]["transfer_pct"] < 5                 # "rare until the 1950s"
assert all(DEC[a]["transfer_pct"] < DEC[b]["transfer_pct"] for a, b in ((1950, 1960), (1960, 1970), (1970, 1980), (1980, 1990), (1990, 2000), (2000, 2010), (2010, 2020)))   # "grew steadily"
assert 35 < R["dist"]["dist_drop_pct"] < 45 and R["dist"]["speed_max"] / R["dist"]["speed_1926"] > 1.8                    # "two fifths", "almost twice as fast"
assert R["winners"]["belgium_last"] == 1976 and R["dist"]["n1926"] == 17
S = pd.read_csv(f"{DATA}/stages.csv")
pyr = S[(S.race == "men") & (S.year.between(1910, 1939))]
pyr_dep = pyr[pyr.start_departement.isin(["64", "65", "31", "09", "66"]) | pyr.finish_departement.isin(["64", "65", "31", "09", "66"])]
assert pyr_dep.year.nunique() == pyr.year.nunique()                                                                       # "crossed every year in its early decades"
L26 = S[(S.race == "men") & (S.year == 1926)].sort_values("order_in_tour")
assert list(L26.start_place)[:1] == ["Évian-les-Bains"] and list(L26.finish_place)[-1] == "Paris" and "Dunkirk" in set(L26.finish_place)
assert R["geo"]["unmatched_reasons"]["summit"] + R["geo"]["unmatched_reasons"]["ski station"] > R["geo"]["unmatched_ends"] / 2   # "mostly mountain finishes"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{d['dec']}s & {d['tours']} & {d['stages']:,} & {d['dist']:,} & {d['avg_stage']:.0f} & {('%.1f' % d['speed']) if d['speed'] else ''} & {d['abroad_pct']:.1f} & {d['transfer_pct']:.1f} & {CEN[d['dec']]['edge50_pct']:.1f}\\\\\n" for d in R["decades"])
TD = ("\\begin{table}[tbp]\\centering\\small\\setlength{\\tabcolsep}{5pt}\\caption{The men's Tour by decade: Tours, stages, mean total distance (km), mean stage (km), mean winning speed (km/h), stages abroad (\\%), stages starting away from the previous finish (\\%), and French stage towns within 50 km of the edge of France (\\%).}\\label{tab:decades}"
      "\\begin{tabular}{lrrrrrrrr}\\toprule Decade & Tours & Stages & km & Stage & km/h & Abroad & Transfer & Edge\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
TT = pd.read_csv(f"{DATA}/stage_towns.csv").sort_values(["visits", "tours"], ascending=False).head(20)
rows = "".join(f"{tex(r.name)} & {tex(COUNTRIES[r.cc])} & {r.starts} & {r.finishes} & {r.visits} & {r.tours} & {r.first} & {r.last}\\\\\n" for r in TT.itertuples())
TW = ("\\begin{table}[tbp]\\centering\\small\\caption{The twenty most visited stage towns of the men's Tour.}\\label{tab:towns}"
      "\\begin{tabular}{llrrrrrr}\\toprule Town & Country & Starts & Finishes & Total & Tours & First & Last\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
g = R["abroad"]["gd_list"]; half = (len(g) + 1) // 2
rows = "".join(f"{a['year']} & {tex(a['town'])} & {tex(a['cc'])} & " + (f"{b['year']} & {tex(b['town'])} & {tex(b['cc'])}" if b else " & & ") + "\\\\\n" for a, b in zip(g[:half], g[half:] + [None]))
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Grand Départs outside France: the start town of the first stage or prologue.}\\label{tab:gd}"
      "\\begin{tabular}{rllrll}\\toprule Year & Town & Country & Year & Town & Country\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("DECADES", TD), ("TOWNS", TW), ("GD", TG)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
