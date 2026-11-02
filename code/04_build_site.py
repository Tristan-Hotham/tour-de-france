"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, europe.json, departements_geo.json) is embedded. Facts stated in
words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before </body>.
10.5281/zenodo.23873013 and https://blog.tristanhotham.com/2026/10/31/tour-de-france/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
T, D, A, SH, W, DP, WO, G = R["towns"], R["dist"], R["abroad"], R["shape"], R["winners"], R["deps"], R["women"], R["geo"]
WY = {y: (r, n) for y, r, n in W["years"]}
DEC = {d["dec"]: d for d in R["decades"]}

# facts stated in words (page, blog, paper, collage)
assert [t["name"] for t in T["top_visits"][:4]] == ["Paris", "Bordeaux", "Pau", "Luchon"]
assert T["top_starts"][0]["name"] == "Pau" and T["top_finishes"][0]["name"] == "Paris"
assert T["final_elsewhere"] == [[2024, "Nice"]] and T["paris_final"] == R["source"]["men_years"] - 1
assert T["gd_paris_until_first_other"] and T["gd_not_paris_first"] == 1926 and T["edition_2013"] == 100
assert WY[1903][0] == "Maurice Garin" and WY[1926][0] == "Lucien Buysse" and WY[D["speed_max_year"]][0] == "Tadej Pogacar"
assert WY[1909] == ("François Faber", "Luxembourg") and WY[1986] == ("Greg Lemond", "United States") and WY[1985][0] == "Bernard Hinault"
assert W["france_last"] == 1985 and W["first_non_fr"] == 1909 and W["first_outside_europe"] == 1986
assert [m[1] for m in W["most"][:5]] == [5] * 5 and W["most"][5][1] < 5
assert {m[0] for m in W["most"][:5]} == {"Jacques Anquetil", "Eddy Merckx", "Bernard Hinault", "Miguel Indurain", "Tadej Pogacar"}
assert WY[2006][0] == "Oscar Pereiro Sio" and WY[2010][0] == "Andy Schleck" and W["no_winner"] == list(range(1999, 2006))
assert W["lux"] == W["slovenia"] == 5 and [n for n, _ in W["by_nation"][:4]] == ["France", "Belgium", "Spain", "Italy"]
assert [x[2] for x in W["women"]] == ["Netherlands", "Netherlands", "Poland", "France", "Netherlands"]
assert all(DEC[d]["transfer_pct"] == 0 for d in (1910, 1920, 1930))
assert SH["edge50_1920s"] > 90 and SH["edge50_2020s"] < 50 < SH["edge50_1920s"]
assert SH["transfer_top"][0]["from"] == "Espelette" and SH["transfer_top"][0]["to"] == "Houilles" and SH["transfer_top"][0]["year"] == 2018
assert {(c["year"], c["start"], c["end"]) for c in D["crow_top"][:2]} == {(1903, "Paris", "Lyon"), (1904, "Paris", "Lyon")}
assert [t["name"] for t in T["top_abroad"][:2]] == ["Brussels", "Liège"]
assert list(A["stages_by_country"])[:4] == ["Belgium", "Switzerland", "Spain", "Italy"]
gdc = {g["cc"] for g in A["gd_list"]}
assert gdc == {"Netherlands", "Belgium", "Germany", "Spain", "Luxembourg", "Switzerland", "Monaco", "Ireland", "Denmark", "Italy", "United Kingdom"}
assert [g["town"] for g in A["gd_list"] if g["cc"] == "United Kingdom"] == ["London", "Leeds"]
assert {"Dublin", "Florence", "Copenhagen"} <= {g["town"] for g in A["gd_list"]}
assert A["first_abroad"] == {"year": 1913, "start": "Grenoble", "end": "Geneva", "stage": "11"}
assert DP["n_never"] == 0 and DP["top"][0][0] == "64" and DP["top"][1][0] == "31"
dl = sorted(jload(f"{DATA}/site.json")["dep_visits"].items(), key=lambda kv: kv[1])
assert dl[0][0] == "79" and {c for c, _ in dl[:4]} == {"79", "2A", "2B", "23"}
assert [d for d in DP["one_tour"] if d[0] in ("2A", "2B")] == [["2A", "Corse-du-Sud", 1], ["2B", "Haute-Corse", 1]]
assert all(y["n"] in (8, 9) for y in WO["years"]) and WO["years"][0]["start"] == "Paris" and WO["years"][2]["start"] == "Rotterdam" and WO["years"][4]["start"] == "Lausanne"
assert WO["gd_abroad"] == [2024, 2026]
assert G["unmatched_top"][0][0] == "Puy de Dôme" and G["unmatched_top"][1][0] == "Mont Ventoux" and G["mtn_since1970_pct"] > 75   # "especially since the 1970s"
assert R["source"]["men_years"] == 113 and R["dist"]["n1903"] == 6


def fill(text):
    return re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\}|DOI_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), text)


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23873013", "https://blog.tristanhotham.com/2026/10/31/tour-de-france/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*EUROPE*/", open(f"{DATA}/europe.json", encoding="utf-8").read())
    html = html.replace("/*DEPS*/", open(f"{DATA}/departements_geo.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
