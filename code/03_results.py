"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json).

Definitions:
  * stage: one row of LeTourDataSet after 01_clean.py (joint wins merged, the 2022 repeat and transfer rows dropped).
    Half stages (1.1, 1.2) count as stages; the prologue (0) counts as a stage.
  * a stage's line: a straight line from its start town to its finish town. LeTourDataSet gives no route and no
    distance for single stages, only each Tour's total distance, so 'as the crow flies' figures are lower bounds and
    the line is a sketch of the stage, not its road.
  * stage town: a GeoNames place that hosted a start or finish. A visit = one start or one finish.
  * abroad: the place's GeoNames country is not France (Monaco and Andorra count as abroad).
  * crosses a border: start and finish both located and in different countries.
  * transfer: the start of a stage is a different place from the finish of the stage before (both located).
  * near the edge of France: a French stage town within 50 km of the outline of metropolitan France (coast or land
    border; Natural Earth 1:10m, measured in the Lambert 93 projection).
  * departement: from the GeoNames admin2 code of every French stage town; 'visited' means it hosted a start or a
    finish of the men's or women's Tour. Stages that only passed through are not in the data.
  * winning speed: the winner's distance divided by his or her time, for editions decided on time.
  * Grand Départ: the start town of the first stage (or prologue) of each Tour."""
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.ops import unary_union, transform as stf
from pyproj import Transformer
from common import *

ST = pd.read_pickle(f"{WORK}/stages_geo.pkl").sort_values(["race", "year", "k"]).reset_index(drop=True)
PL = pd.read_pickle(f"{WORK}/places.pkl").set_index("gid")
WIN = pd.read_pickle(f"{WORK}/winners.pkl")
CHK = jload(f"{WORK}/checks.json"); CG = jload(f"{WORK}/checks_geo.json")
DEPN = jload(f"{WORK}/departements.json")
pc = lambda a, b: round(100 * a / b, 2) if b else None
R = {}

# display name of each place: English names for foreign towns matched through a French exonym, otherwise the stage
# name the source uses most often for it (Luchon, L'Alpe-d'Huez, Futuroscope), or the GeoNames name where the two differ
# only in accents or case
EN = {"Köln": "Cologne", "Donostia / San Sebastián": "San Sebastián", "Gasteiz / Vitoria": "Vitoria-Gasteiz", "Martigny-Ville": "Martigny",
      "les Escaldes": "Escaldes-Engordany", "Freiburg": "Freiburg im Breisgau"}
raws = pd.concat([ST[["start", "start_gid", "start_how"]].set_axis(["raw", "gid", "how"], axis=1), ST[["end", "end_gid", "end_how"]].set_axis(["raw", "gid", "how"], axis=1)])
raws = raws[raws.gid.notna()]
tidy = lambda t: re.sub(r"\s+", " ", t.replace("_", " ")).strip()
disp = {}
for gid, x in raws.groupby("gid"):
    gn = PL.loc[int(gid), "name"]; topraw = tidy(x.raw.value_counts().index[0])
    if gn in EN: disp[int(gid)] = EN[gn]
    elif x.how.str.startswith("exonym").any() or norm(gn) == norm(topraw) or topraw.isupper(): disp[int(gid)] = gn
    else: disp[int(gid)] = topraw
PL["gname"] = PL.name; PL["name"] = PL.index.map(disp)

for e in ("start", "end"):
    for c in ("name", "cc", "lat", "lon", "dep"):
        ST[f"{e}_{c}"] = ST[f"{e}_gid"].map(lambda i: PL.loc[int(i), c] if pd.notna(i) else None)
    ST[f"{e}_ok"] = ST[f"{e}_gid"].notna()
both = ST.start_ok & ST.end_ok
ST["crow_km"] = np.where(both, hav_km(ST.start_lat.astype(float), ST.start_lon.astype(float), ST.end_lat.astype(float), ST.end_lon.astype(float)), np.nan)
ST["dec"] = ST.year.map(decade_of)
ST["abroad_s"] = ST.start_ok & (ST.start_cc != "FR"); ST["abroad_e"] = ST.end_ok & (ST.end_cc != "FR")
ST["abroad"] = ST.abroad_s | ST.abroad_e
ST["cross"] = both & (ST.start_cc != ST.end_cc)
ST["loop"] = both & (ST.start_gid == ST.end_gid)
g = ST.groupby(["race", "year"])
ST["prev_gid"] = g.end_gid.shift(); ST["prev_lat"] = g.end_lat.shift(); ST["prev_lon"] = g.end_lon.shift()
has_prev = ST.prev_gid.notna() & ST.start_ok
ST["same_as_prev"] = has_prev & (ST.prev_gid == ST.start_gid)
ST["transfer"] = has_prev & (ST.prev_gid != ST.start_gid)
ST["transfer_km"] = np.where(ST.transfer, hav_km(ST.prev_lat.astype(float), ST.prev_lon.astype(float), ST.start_lat.astype(float), ST.start_lon.astype(float)), 0.0)
M = ST[ST.race == "men"].copy(); WO = ST[ST.race == "women"].copy()
YEARS = sorted(M.year.unique())

# ---------- source and geocoding ----------
ends = pd.concat([ST[["race", "start", "start_gid", "start_how"]].set_axis(["race", "raw", "gid", "how"], axis=1),
                  ST[["race", "end", "end_gid", "end_how"]].set_axis(["race", "raw", "gid", "how"], axis=1)], ignore_index=True)
ends["kind"] = ends.how.str.split(" ").str[0].str.replace(r":.*", "", regex=True)
names = ends.drop_duplicates("raw")
um = ends[ends.gid.isna()]
umv = um.groupby(["raw", "how"]).size().reset_index(name="n").sort_values(["n", "raw"], ascending=[False, True])
R["source"] = {"men_rows": CHK["men_rows"], "women_rows": CHK["women_rows"], "men_stages": len(M), "women_stages": len(WO),
               "stages": len(ST), "men_years": len(YEARS), "first_year": int(min(YEARS)), "last_year": int(max(YEARS)),
               "women_years": int(WO.year.nunique()), "women_first": int(WO.year.min()), "women_last": int(WO.year.max()),
               "joint": len(CHK["men_joint"]), "dropped_2022": 3, "commit": LTD_COMMIT[:7], "gn_commit": GN_COMMIT[:7],
               "gazetteer_rows": CG["gazetteer_rows"], "gazetteer_searched": CG["gazetteer_searched"],
               "war_gaps": "1915 to 1918 and 1940 to 1946", "half_stages": int(M.stage.str.contains(r"\.").sum()),
               "prologues": int((M.stage == "0").sum())}
assert R["source"]["men_years"] == 113 and R["source"]["first_year"] == 1903 and R["source"]["last_year"] == 2026
gc = {"ends": len(ends), "matched": int(ends.gid.notna().sum()), "names": len(names), "names_matched": int(names.gid.notna().sum()),
      "places": int(PL.shape[0]), "unmatched_ends": len(um), "unmatched_names": int(umv.raw.nunique()),
      "by_kind": {k: int(v) for k, v in ends[ends.gid.notna()].kind.value_counts().items()},
      "unmatched_reasons": {k.replace("none:", ""): int(v) for k, v in um.how.value_counts().items()},
      "ambiguous_ends": len(CG.get("ambiguous", [])), "dep_mismatch": len(CG["dep_mismatch"])}
gc["rate"] = pc(gc["matched"], gc["ends"]); gc["names_rate"] = pc(gc["names_matched"], gc["names"])
gc["both_located"] = int(both.sum()); gc["both_pct"] = pc(both.sum(), len(ST))
gc["unmatched_top"] = [[r.raw, r.how.replace("none:", ""), int(r.n)] for r in umv.head(12).itertuples()]
gc["alias_n"] = int(names.kind.isin(["exonym", "variant", "part", "station"]).sum())
ends["year"] = pd.concat([ST.year, ST.year], ignore_index=True)
mtn = ends[ends.how.isin(["none:summit", "none:ski station"])]
gc["mtn_unmatched"] = len(mtn); gc["mtn_since1970"] = int((mtn.year >= 1970).sum()); gc["mtn_since1970_pct"] = pc(gc["mtn_since1970"], len(mtn))
R["geo"] = gc
assert gc["rate"] > 95, gc["rate"]
umv.assign(reason=umv.how.str.replace("none:", "")).drop(columns="how").rename(columns={"raw": "stage_name", "n": "appearances"}) \
    .to_csv(f"{DATA}/unmatched_names.csv", index=False)

# ---------- towns ----------
vis = pd.concat([ST[ST.start_ok][["race", "year", "start_gid"]].assign(role="start").rename(columns={"start_gid": "gid"}),
                 ST[ST.end_ok][["race", "year", "end_gid"]].assign(role="end").rename(columns={"end_gid": "gid"})])
vis["gid"] = vis.gid.astype(int)
vm = vis[vis.race == "men"]
cnt = pd.DataFrame({"starts": vm[vm.role == "start"].groupby("gid").size(), "finishes": vm[vm.role == "end"].groupby("gid").size()}).fillna(0).astype(int)
cnt["visits"] = cnt.starts + cnt.finishes; cnt["tours"] = vm.groupby("gid").year.nunique()
cnt["first"] = vm.groupby("gid").year.min(); cnt["last"] = vm.groupby("gid").year.max()
cnt = cnt.join(PL[["name", "cc", "dep"]])
top = lambda col, n=15: [{"name": PL.loc[i, "name"], "cc": PL.loc[i, "cc"], "n": int(cnt.loc[i, col]), "tours": int(cnt.loc[i, "tours"])}
                         for i in cnt.sort_values([col, "tours"], ascending=False).index[:n]]
R["towns"] = {"n": int(PL.shape[0]), "men_n": int(cnt.shape[0]), "top_visits": top("visits"), "top_starts": top("starts"), "top_finishes": top("finishes"),
              "top_abroad": [{"name": PL.loc[i, "name"], "cc": COUNTRIES[PL.loc[i, "cc"]], "n": int(cnt.loc[i, "visits"]), "tours": int(cnt.loc[i, "tours"])}
                             for i in cnt[cnt.cc != "FR"].sort_values(["visits", "tours"], ascending=False).index[:10]],
              "top_tours": top("tours"), "once": int((cnt.visits == 1).sum()), "fr": int((PL.cc == "FR").sum()), "abroad": int((PL.cc != "FR").sum())}
T = R["towns"]
assert [t["name"] for t in T["top_visits"][:3]] == ["Paris", "Bordeaux", "Pau"], T["top_visits"][:3]
T["once_pct"] = pc(T["once"], T["men_n"])
byname = {PL.loc[i, "name"]: i for i in cnt.index}
T["paris"] = {k: int(cnt.loc[byname["Paris"], k]) for k in ("starts", "finishes", "visits", "tours")}
# where each Tour finished
last = M.groupby("year").tail(1)
T["paris_final"] = int((last.end_name == "Paris").sum()); T["final_elsewhere"] = [[int(r.year), r.end_name or r.end] for r in last[last.end_name != "Paris"].itertuples()]
assert T["final_elsewhere"] == [[2024, "Nice"]], T["final_elsewhere"]
first = M.groupby("year").head(1)
T["paris_gd"] = int((first.start_name == "Paris").sum())
T["gd_not_paris_first"] = int(first[first.start_name != "Paris"].year.min())
T["gd_paris_until_first_other"] = bool((first[first.year < T["gd_not_paris_first"]].start_name == "Paris").all())
T["edition_2013"] = YEARS.index(2013) + 1
cnt.reset_index().rename(columns={"gid": "geonames_row"}).sort_values("visits", ascending=False).to_csv(f"{DATA}/stage_towns.csv", index=False)

# ---------- distance and speed ----------
Y = M.groupby("year").agg(n=("stage", "size"), dist=("dist_total", "first"), abroad=("abroad", "sum"), cross=("cross", "sum"),
                          crow=("crow_km", "sum"), transfer_km=("transfer_km", "sum"), transfers=("transfer", "sum"),
                          same=("same_as_prev", "sum"), has_prev=("prev_gid", lambda s: int(s.notna().sum())))
Y["avg_stage"] = Y.dist / Y.n
wm = WIN[WIN.race == "men"].set_index("year")
Y["speed"] = wm.speed; Y["winner"] = wm.rider; Y["nation"] = wm.nation
dmax, dmin = Y.dist.idxmax(), Y.dist.idxmin()
D = {"longest_year": int(dmax), "longest_km": int(Y.dist.max()), "shortest_year": int(dmin), "shortest_km": int(Y.dist.min()),
     "shortest_years": [int(y) for y in Y.index[Y.dist == Y.dist.min()]],
     "y1903": int(Y.loc[1903, "dist"]), "y2026": int(Y.loc[2026, "dist"]), "y2026_n": int(Y.loc[2026, "n"]),
     "most_stages_year": int(Y.n.idxmax()), "most_stages": int(Y.n.max()), "total_km": int(Y.dist.sum()),
     "avg_stage_all": round(float(Y.dist.sum() / Y.n.sum()), 1), "n1903": int(Y.loc[1903, "n"]), "n1926": int(Y.loc[1926, "n"])}
dec = []
for d in sorted(M.dec.unique()):
    y = Y[(Y.index >= d) & (Y.index < d + 10)]; s = M[M.dec == d]
    fr = s.assign(x=1)
    dec.append({"dec": int(d), "tours": len(y), "stages": int(y.n.sum()), "dist": round(float(y.dist.mean())), "avg_stage": round(float(y.dist.sum() / y.n.sum()), 1),
                "speed": round(float(y.speed.mean()), 1) if y.speed.notna().any() else None, "abroad_pct": pc(s.abroad.sum(), len(s)),
                "cross_pct": pc(s.cross.sum(), len(s)), "transfer_pct": pc(s.transfer.sum(), (s.transfer | s.same_as_prev).sum()),
                "transfer_km": round(float(y.transfer_km.mean())), "stages_per_tour": round(float(y.n.mean()), 1)})
R["decades"] = dec
DD = {d["dec"]: d for d in dec}
D["avg_stage_1920s"] = DD[1920]["avg_stage"]; D["avg_stage_2020s"] = DD[2020]["avg_stage"]
D["dist_1920s"] = DD[1920]["dist"]; D["dist_2020s"] = DD[2020]["dist"]
D["avg_stage_max_year"] = int(Y.avg_stage.idxmax()); D["avg_stage_max"] = round(float(Y.avg_stage.max()))
D["avg_stage_2026"] = round(float(Y.loc[2026, "avg_stage"]), 1)
D["dist_drop_pct"] = round(100 * (1 - D["y2026"] / D["longest_km"]))
sp = Y.speed.dropna()
D["speed_1903"] = round(float(sp.loc[1903]), 1); D["speed_max_year"] = int(sp.idxmax()); D["speed_max"] = round(float(sp.max()), 2)
D["speed_2026"] = round(float(sp.loc[2026]), 2); D["speed_1926"] = round(float(sp.loc[1926]), 1)
D["speed_years"] = len(sp); D["speed_min_year"] = int(sp.idxmin()); D["speed_min"] = round(float(sp.min()), 1)
D["speed_1950s"] = DD[1950]["speed"]; D["speed_2020s"] = DD[2020]["speed"]
D["speed_over40"] = [int(y) for y in sp.index[sp >= 40]]
D["time_2026_h"] = round(float(wm.loc[2026, "TotalSeconds"]) / 3600, 1); D["time_1926_h"] = round(float(wm.loc[1926, "TotalSeconds"]) / 3600, 1)
assert D["longest_year"] == 1926 and D["longest_km"] == 5745 and D["shortest_km"] == 2428 and D["speed_max_year"] == 2026
cr = M[M.crow_km.notna() & ~M.loop].sort_values("crow_km", ascending=False)
D["crow_top"] = [{"year": int(r.year), "stage": r.stage, "start": r.start_name, "end": r.end_name, "km": round(float(r.crow_km))} for r in cr.head(8).itertuples()]
D["crow_mean"] = round(float(M[M.crow_km.notna()].crow_km.mean()), 1)
D["loops"] = int(M.loop.sum()); D["loops_pct"] = pc(M.loop.sum(), both[M.index].sum())
R["dist"] = D

# ---------- abroad, Grand Départs, borders ----------
gd = first.copy()
gd_ab = gd[gd.start_ok & (gd.start_cc != "FR")]
A = {"gd_abroad": len(gd_ab), "gd_first_abroad": int(gd_ab.year.min()), "gd_first_abroad_town": gd_ab.sort_values("year").iloc[0].start_name,
     "gd_list": [{"year": int(r.year), "town": r.start_name, "cc": COUNTRIES[r.start_cc]} for r in gd_ab.sort_values("year").itertuples()],
     "gd_by_country": {COUNTRIES[k]: int(v) for k, v in gd_ab.start_cc.value_counts().items()},
     "gd_since2000": int((gd_ab.year >= 2000).sum()), "tours_since2000": int((first.year >= 2000).sum())}
A["gd_since2000_pct"] = pc(A["gd_since2000"], A["tours_since2000"])
ab = M[M.abroad]
A["stages_abroad"] = len(ab); A["stages_abroad_pct"] = pc(len(ab), len(M)); A["cross"] = int(M.cross.sum()); A["cross_pct"] = pc(M.cross.sum(), int(both[M.index].sum()))
A["both_abroad"] = int((M.abroad_s & M.abroad_e).sum())
evc = pd.concat([M[M.abroad_s].start_cc, M[M.abroad_e].end_cc]).value_counts()
A["ends_by_country"] = {COUNTRIES[k]: int(v) for k, v in evc.items()}
stc = {}
for cc in evc.index:
    stc[COUNTRIES[cc]] = int(((M.start_cc == cc) | (M.end_cc == cc)).sum())
A["stages_by_country"] = dict(sorted(stc.items(), key=lambda kv: -kv[1]))
A["n_countries"] = len(evc)
A["tours_abroad"] = int(M.groupby("year").abroad.any().sum()); A["tours_all_france"] = len(YEARS) - A["tours_abroad"]
A["first_abroad_year"] = int(ab.year.min()); A["first_abroad"] = [ab.sort_values("k").iloc[0].start_name, ab.sort_values("k").iloc[0].end_name]
fa = ab[ab.year == ab.year.min()].iloc[0]; A["first_abroad"] = {"year": int(fa.year), "start": fa.start_name, "end": fa.end_name, "stage": fa.stage}
yab = Y.abroad
A["most_abroad_year"] = int(yab.idxmax()); A["most_abroad_n"] = int(yab.max())
A["years_list"] = [[int(y), int(v)] for y, v in yab.items()]
gcnt = M[M.abroad].assign(cc=lambda d: np.where(d.abroad_s, d.start_cc, d.end_cc)).groupby(["year", "cc"]).size()
A["by_year_country"] = [[int(y), COUNTRIES[c], int(n)] for (y, c), n in gcnt.items()]
assert A["gd_first_abroad"] == 1954 and A["gd_first_abroad_town"] == "Amsterdam", (A["gd_first_abroad"], A["gd_first_abroad_town"])
R["abroad"] = A

# ---------- shape of the route: centre, extent, edge ----------
FR10 = [f for f in jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"] if f["properties"]["ADM0_A3"] == "FRA"][0]
frg = shape(FR10["geometry"])
metro = unary_union([p for p in frg.geoms if -6 < p.centroid.x < 10 and 41 < p.centroid.y < 52])
L93 = Transformer.from_crs(4326, 2154, always_xy=True)
import shapely
metro93 = shapely.transform(metro, lambda a: np.column_stack(L93.transform(a[:, 0], a[:, 1])))
edge = metro93.boundary
pts = vis[vis.race == "men"].join(PL[["lat", "lon", "cc"]], on="gid")
pts["dec"] = pts.year.map(decade_of)
frp = pts[pts.cc == "FR"].copy()
xy = L93.transform(frp.lon.values, frp.lat.values)
EDGE = {}
for i, (x, y) in zip(frp.gid, zip(*xy)):
    if i not in EDGE: EDGE[i] = edge.distance(Point(x, y)) / 1000
frp["edge_km"] = frp.gid.map(EDGE)
cen = []
for d in sorted(pts.dec.unique()):
    p = pts[pts.dec == d]; f = frp[frp.dec == d]
    cen.append({"dec": int(d), "lat": round(float(p.lat.mean()), 3), "lon": round(float(p.lon.mean()), 3), "n": len(p),
                "lat_min": round(float(p.lat.min()), 2), "lat_max": round(float(p.lat.max()), 2), "lon_min": round(float(p.lon.min()), 2), "lon_max": round(float(p.lon.max()), 2),
                "edge50_pct": pc((f.edge_km <= 50).sum(), len(f)), "edge_median": round(float(f.edge_km.median()), 1),
                "fr_towns": int(f.gid.nunique())})
R["centre"] = cen
C = {c["dec"]: c for c in cen}
R["shape"] = {"edge50_1900s": C[1900]["edge50_pct"], "edge50_1920s": C[1920]["edge50_pct"], "edge50_2020s": C[2020]["edge50_pct"],
              "edge_med_1900s": C[1900]["edge_median"], "edge_med_1920s": C[1920]["edge_median"], "edge_med_2020s": C[2020]["edge_median"],
              "edge50_min_dec": int(min(cen, key=lambda c: c["edge50_pct"])["dec"]), "edge50_min": min(c["edge50_pct"] for c in cen),
              "edge50_max_dec": int(max(cen, key=lambda c: c["edge50_pct"])["dec"]), "edge50_max": max(c["edge50_pct"] for c in cen),
              "edge50_all": pc((frp.edge_km <= 50).sum(), len(frp)),
              "transfer_pct_1920s": DD[1920]["transfer_pct"], "transfer_pct_2020s": DD[2020]["transfer_pct"], "transfer_pct_1960s": DD[1960]["transfer_pct"],
              "transfer_km_1920s": DD[1920]["transfer_km"], "transfer_km_2020s": DD[2020]["transfer_km"],
              "transfer_km_1950s": DD[1950]["transfer_km"]}
# share of France's area within 50 km of its outline, for comparison
R["shape"]["area_edge50_pct"] = round(100 * metro93.intersection(edge.buffer(50000)).area / metro93.area, 1)
# first decade with transfers in most Tours
nt = M.groupby("year").transfer.sum()
R["shape"]["no_transfer_tours"] = int((nt == 0).sum()); R["shape"]["last_no_transfer"] = int(nt[nt == 0].index.max())
R["shape"]["first_transfer_year"] = int(nt[nt > 0].index.min())
big = M[M.transfer].sort_values("transfer_km", ascending=False)
R["shape"]["transfer_top"] = [{"year": int(r.year), "from": PL.loc[int(r.prev_gid), "name"], "to": r.start_name, "km": round(float(r.transfer_km))} for r in big.head(6).itertuples()]
R["shape"]["transfer_km_max_year"] = int(Y.transfer_km.idxmax()); R["shape"]["transfer_km_max"] = round(float(Y.transfer_km.max()))
assert R["shape"]["edge50_1900s"] > R["shape"]["edge50_2020s"] and R["shape"]["transfer_pct_1920s"] < 5

# ---------- departements ----------
fv = vis.join(PL[["cc", "dep"]], on="gid")
fv = fv[fv.cc == "FR"]
dv = fv.groupby("dep").size(); dt = fv.groupby("dep").year.nunique()
never = sorted(set(DEPN) - set(dv.index))
R["deps"] = {"n": len(DEPN), "visited": int(len(set(dv.index) & set(DEPN))), "never": [[c, DEPN[c]] for c in never], "n_never": len(never),
             "top": [[c, DEPN[c], int(dv[c]), int(dt[c])] for c in dv.sort_values(ascending=False).index[:12]],
             "one_tour": [[c, DEPN[c], int(dt[c])] for c in dt[dt <= 2].sort_values().index]}
assert set(dv.index) <= set(DEPN), set(dv.index) - set(DEPN)
dep_rows = [{"code": c, "name": DEPN[c], "visits": int(dv.get(c, 0)), "tours": int(dt.get(c, 0)),
             "first": int(fv[fv.dep == c].year.min()) if c in dv.index else None, "last": int(fv[fv.dep == c].year.max()) if c in dv.index else None} for c in sorted(DEPN)]
pd.DataFrame(dep_rows).to_csv(f"{DATA}/departements.csv", index=False)

# ---------- winners ----------
w = WIN[WIN.race == "men"].copy()
nat = w.nation.value_counts()
R["winners"] = {"n_editions_with_winner": len(w), "no_winner": CHK["no_winner_years"], "n_no_winner": len(CHK["no_winner_years"]),
                "by_nation": [[k, int(v)] for k, v in nat.items()], "n_nations": int(nat.shape[0]),
                "france": int(nat["France"]), "belgium": int(nat["Belgium"]), "spain": int(nat["Spain"]), "italy": int(nat["Italy"]),
                "uk": int(nat["United Kingdom"]), "slovenia": int(nat["Slovenia"]), "denmark": int(nat["Denmark"]), "lux": int(nat["Luxembourg"]),
                "france_last": int(w[w.nation == "France"].year.max()), "belgium_last": int(w[w.nation == "Belgium"].year.max()),
                "first_non_fr": int(w[w.nation != "France"].year.min()), "first_non_fr_name": w[w.nation != "France"].sort_values("year").iloc[0].rider.title(),
                "first_outside_europe": int(w[w.nation.isin(["United States", "Australia", "Colombia"])].year.min()),
                "since1986_fr": int(((w.year >= 1986) & (w.nation == "France")).sum()), "checked_by_team": CHK["nation_checked_by_team"],
                "years": [[int(r.year), r.rider.title(), r.nation] for r in w.sort_values("year").itertuples()]}
riders_n = w.rider.value_counts()
R["winners"]["most"] = [[k.title(), int(v)] for k, v in riders_n.head(8).items()]
R["winners"]["n_riders"] = int(riders_n.shape[0])
wd = []
for d in sorted(M.dec.unique()):
    x = w[(w.year >= d) & (w.year < d + 10)]
    wd.append({"dec": int(d), **{k: int(v) for k, v in x.nation.value_counts().items()}})
R["winners"]["by_decade"] = wd
assert R["winners"]["france_last"] == 1985 and R["winners"]["n_no_winner"] == 7 and R["winners"]["france"] == 36
WW = WIN[WIN.race == "women"].sort_values("year")
R["winners"]["women"] = [[int(r.year), r.rider.title(), r.nation, round(float(r.speed), 2)] for r in WW.itertuples()]

# ---------- women ----------
wy = []
for y, s in WO.groupby("year"):
    nm = lambda r, e: r[e + "_name"] if isinstance(r[e + "_name"], str) else r[e]
    wy.append({"year": int(y), "n": len(s), "dist": int(s.dist_total.iloc[0]), "start": nm(s.iloc[0], "start"),
               "start_cc": COUNTRIES.get(s.iloc[0].start_cc, ""), "end": nm(s.iloc[-1], "end"), "abroad": int(s.abroad.sum()),
               "winner": WW[WW.year == y].rider.iloc[0].title(), "nation": WW[WW.year == y].nation.iloc[0],
               "speed": round(float(WW[WW.year == y].speed.iloc[0]), 2)})
R["women"] = {"years": wy, "stages": len(WO), "dist_total": int(sum(x["dist"] for x in wy)), "towns": int(vis[vis.race == "women"].gid.nunique()),
              "abroad": int(WO.abroad.sum()), "gd_abroad": [x["year"] for x in wy if x["start_cc"] not in ("France", "")],
              "shared_towns": int(len(set(vis[vis.race == "women"].gid) & set(vm.gid))),
              "deps": int(fv[fv.race == "women"].dep.nunique())}
assert [x["year"] for x in wy] == [2022, 2023, 2024, 2025, 2026]

# ---------- tables out ----------
out = ST.copy()
out["start_country"] = out.start_cc.map(COUNTRIES); out["end_country"] = out.end_cc.map(COUNTRIES)
out[["race", "year", "stage", "k", "start", "end", "start_name", "start_country", "start_dep", "start_lat", "start_lon", "start_how",
     "end_name", "end_country", "end_dep", "end_lat", "end_lon", "end_how", "crow_km", "transfer_km", "winner", "dist_total"]] \
    .rename(columns={"start": "start_as_given", "end": "finish_as_given", "start_name": "start_place", "end_name": "finish_place", "start_how": "start_match",
                     "end_how": "finish_match", "end_country": "finish_country", "end_dep": "finish_departement", "start_dep": "start_departement",
                     "end_lat": "finish_lat", "end_lon": "finish_lon", "k": "order_in_tour", "winner": "stage_winner", "dist_total": "tour_total_km",
                     "crow_km": "straight_line_km", "transfer_km": "transfer_from_previous_finish_km"}).round(3).to_csv(f"{DATA}/stages.csv", index=False)
yo = Y.reset_index()[["year", "n", "dist", "avg_stage", "speed", "winner", "nation", "abroad", "cross", "transfers", "transfer_km"]]
yo.rename(columns={"n": "stages", "dist": "total_km", "avg_stage": "mean_stage_km", "speed": "winner_speed_kmh", "abroad": "stages_abroad",
                   "cross": "stages_crossing_border"}).round(2).to_csv(f"{DATA}/tours_by_year.csv", index=False)
R["years"] = [{"y": int(y), "n": int(r.n), "dist": int(r.dist), "avg": round(float(r.avg_stage), 1), "speed": None if pd.isna(r.speed) else round(float(r.speed), 2),
               "abroad": int(r.abroad), "winner": None if pd.isna(r.winner) else r.winner.title(), "nation": None if pd.isna(r.nation) else r.nation,
               "tkm": round(float(r.transfer_km))} for y, r in Y.iterrows()]

# ---------- page data ----------
PI = {int(g): k for k, g in enumerate(PL.index)}
dname = lambda r, e: getattr(r, e + "_name") or getattr(r, e)
srow = []
for r in ST.itertuples():
    srow.append([0 if r.race == "men" else 1, int(r.year), r.stage, PI[int(r.start_gid)] if r.start_ok else -1, PI[int(r.end_gid)] if r.end_ok else -1,
                 r.start, r.end, r.winner])
allc = pd.DataFrame({"s": vis[vis.race == "men"].groupby("gid").size(), "w": vis[vis.race == "women"].groupby("gid").size()}).fillna(0).astype(int)
prow = [[PL.loc[g, "name"], PL.loc[g, "cc"], round(float(PL.loc[g, "lat"]), 4), round(float(PL.loc[g, "lon"]), 4),
         PL.loc[g, "dep"] if isinstance(PL.loc[g, "dep"], str) else "", int(allc.loc[g, "s"]), int(allc.loc[g, "w"])] for g in PL.index]
site = {"cols": ["race", "year", "stage", "sp", "ep", "start", "end", "winner"], "stages": srow, "places": prow, "pcols": ["name", "cc", "lat", "lon", "dep", "men", "women"],
        "decades": DECADES, "dcol": DEC_COL, "women_col": WOMEN_COL, "yellow": YELLOW, "countries": COUNTRIES, "deps": DEPN,
        "dep_visits": {c: int(dv.get(c, 0)) for c in DEPN}}
jsave(site, f"{DATA}/site.json")
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "ltd": LTD_URL}
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "results.json", "stages.csv")})
print(R["geo"]); print(T["top_visits"][:6]); print(T["top_starts"][:4]); print(T["top_finishes"][:4]); print(D); print({k: v for k, v in A.items() if k not in ("years_list", "by_year_country")})
print(R["shape"]); print(R["deps"]["never"], R["deps"]["n_never"]); print(R["winners"]["by_nation"], R["winners"]["most"]); print(R["women"])
for c in cen: print(c)
for d in dec: print(d)
