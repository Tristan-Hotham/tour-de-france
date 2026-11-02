"""Geocode every stage start and finish with the GeoNames cities1000 gazetteer, and prepare outlines.

Matching, in this order, for each stage name exactly as LeTourDataSet spells it:
  1. names deliberately left without a place (aliases.NOPLACE: summits, ski stations and venues with no village in
     their name, regions, and a few places missing from the gazetteer);
  2. the hand-made table aliases.ALIAS (French names of foreign towns, variants, districts and venues, and ski
     stations named after their village), each pointing at exactly one GeoNames place;
  3. the name itself, compared after normalising (accents, case, hyphens, apostrophes, St and Ste spelt out); a name
     without its article may match a GeoNames name with one (Bourg-d'Oisans = Le Bourg-d'Oisans), not the reverse;
  4. otherwise the name is unmatched (it is not in the gazetteer: mostly villages under 1,000 people).
     Les Angles (Pyrenees, 2026) is left unmatched by hand because only its namesake near Avignon is in the gazetteer.
Only places in the thirteen countries the Tour has visited are searched (common.COUNTRIES). When a name fits several
places (Pau in France, Spain and Italy; two Revels; three Saint-Nazaires; Fribourg, which the source uses for both
Fribourg in Switzerland and Freiburg in Germany), I keep an exact spelling match if there is one, and otherwise the
candidate nearest to the stage's other end; if that end is itself ambiguous, the candidate with the smallest mean
distance to up to two unambiguous towns before and after it in race order. A French candidate within 400 km of that
context is preferred. With no context, France wins. cities1000 has no population field, so size cannot be used.
Every place in France gets its departement from the GeoNames admin2 code, checked against the Natural Earth polygon
that contains it.
Outlines: Natural Earth 1:50m countries (cut to Europe) for the page and figures, and the 96 departements of
metropolitan France (Natural Earth 1:10m admin 1) for the departement map."""
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping, Point, box
from shapely.prepared import prep
from common import *
from aliases import ALIAS, ALIAS_ANY, NOPLACE

ST = pd.read_pickle(f"{WORK}/stages.pkl")
G = jload(f"{RAW}/geonames_cities1000.json")
for g in G:
    g["lat"] = float(g["lat"]); g["lng"] = float(g["lng"])
idx, idx_art = {}, {}
for i, g in enumerate(G):
    if g["country"] not in COUNTRIES:
        continue
    idx.setdefault(norm(g["name"]), []).append(i)
    if norm(g["name"]) != norm_noart(g["name"]):
        idx_art.setdefault(norm_noart(g["name"]), []).append(i)
chk = {"gazetteer_rows": len(G), "gazetteer_searched": sum(len(v) for v in idx.values())}

# alias targets must exist exactly once
AL = {}
for raw, (nm, cc, a2, kind) in ALIAS.items():
    hit = [i for i in idx.get(norm(nm), []) if G[i]["country"] == cc and G[i]["name"] == nm and (a2 is None or G[i]["admin2"] == a2)]
    assert len(hit) == 1, (raw, nm, cc, a2, [(G[i]["name"], G[i]["admin2"]) for i in hit])
    AL[raw] = (hit[0], kind)
ANY = {}
for raw, ts in ALIAS_ANY.items():
    ANY[raw] = []
    for nm, cc, a2 in ts:
        hit = [i for i in idx.get(norm(nm), []) if G[i]["country"] == cc and G[i]["name"] == nm and G[i]["admin2"] == a2]
        assert len(hit) == 1, (raw, nm); ANY[raw].append(hit[0])


def candidates(raw):
    if raw in NOPLACE: return [], "none:" + NOPLACE[raw]
    if raw in AL: return [AL[raw][0]], AL[raw][1]
    if raw in ANY: return ANY[raw], "exonym"
    k = norm(raw)
    if k in idx: return idx[k], "name"
    if k in idx_art: return idx_art[k], "name"
    return [], "none:not in gazetteer"


names = sorted(set(ST.start) | set(ST.end))
CAND = {n: candidates(n) for n in names}
ll = lambda i: (G[i]["lat"], G[i]["lng"])


def pick(raw, ctx):
    cs, how = CAND[raw]
    if len(cs) <= 1: return (cs[0] if cs else None), how, 1 if cs else 0
    ex = [i for i in cs if G[i]["name"] == raw]
    if len(ex) == 1 and raw not in ANY: return ex[0], how, len(cs)
    if ctx:
        d = {i: sum(hav_km(G[i]["lat"], G[i]["lng"], la, lo) for la, lo in ctx) / len(ctx) for i in cs}
        fr = [i for i in cs if G[i]["country"] == "FR" and d[i] <= 400]
        return min(fr or cs, key=d.get), how + " (nearest)", len(cs)
    fr = [i for i in cs if G[i]["country"] == "FR"]
    return (fr or cs)[0], how + " (France first)", len(cs)


ST = ST.sort_values(["race", "year", "k"]).reset_index(drop=True)
res = {}
for (race, year), g in ST.groupby(["race", "year"], sort=False):
    # the Tour as a sequence of town names: start 1, end 1, start 2, end 2, ...
    seq = [(r.Index, e, getattr(r, e)) for r in g.itertuples() for e in ("start", "end")]
    for j, (ix, e, raw) in enumerate(seq):
        if len(CAND[raw][0]) <= 1:
            res[(ix, e)] = pick(raw, [])
            continue
        # context: the stage's other end if it has exactly one place; otherwise the nearest names in race order
        # (before and after) that have exactly one place, up to two on each side
        oth = seq[j + 1 if e == "start" else j - 1][2]
        if oth != raw and len(CAND[oth][0]) == 1:
            ctx = [ll(CAND[oth][0][0])]
        else:
            ctx = []
            for step in (-1, 1):
                k, n = j + step, 0
                while 0 <= k < len(seq) and n < 2:
                    c = CAND[seq[k][2]][0]
                    if len(c) == 1: ctx.append(ll(c[0])); n += 1
                    k += step
        res[(ix, e)] = pick(raw, ctx)
for end in ("start", "end"):
    ST[end + "_gid"] = [res[(i, end)][0] for i in ST.index]
    ST[end + "_how"] = [res[(i, end)][1] for i in ST.index]
    ST[end + "_ncand"] = [res[(i, end)][2] for i in ST.index]

# departements: GeoNames admin2, checked against Natural Earth polygons
NE1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")
DEP = {}
for f in NE1["features"]:
    p = f["properties"]
    if p["adm0_a3"] == "FRA" and p["type_en"] == "Metropolitan department":
        code = p["iso_3166_2"].split("-")[1]
        nm = {"Seien-et-Marne": "Seine-et-Marne", "Haute-Rhin": "Haut-Rhin"}.get(p["name"], p["name"])
        DEP[code] = {"name": nm, "geom": shape(f["geometry"])}
assert len(DEP) == 96, len(DEP)
DEPP = {c: prep(d["geom"]) for c, d in DEP.items()}
used = sorted({int(x) for x in pd.concat([ST.start_gid, ST.end_gid]).dropna()})
places = {}
for i in used:
    g = G[i]; d = {"gid": i, "name": g["name"], "cc": g["country"], "lat": round(g["lat"], 5), "lon": round(g["lng"], 5), "admin1": g["admin1"], "admin2": g["admin2"]}
    if g["country"] == "FR":
        pt = Point(g["lng"], g["lat"]); inside = [c for c, pp in DEPP.items() if pp.contains(pt)]
        if not inside:   # on the coast: the nearest polygon
            inside = [min(DEP, key=lambda c: DEP[c]["geom"].distance(pt))]
        d["dep"] = g["admin2"] if g["admin2"] in DEP else inside[0]
        d["dep_poly"] = inside[0]
    places[i] = d
mism = [(p["name"], p["admin2"], p["dep_poly"]) for p in places.values() if p["cc"] == "FR" and p["admin2"] != p["dep_poly"]]
chk["dep_mismatch"] = mism
print("departement code vs polygon mismatches:", mism)

# review lists
st = ST.copy()
for e in ("start", "end"):
    st[e + "_lat"] = st[e + "_gid"].map(lambda i: places[int(i)]["lat"] if pd.notna(i) else np.nan)
    st[e + "_lon"] = st[e + "_gid"].map(lambda i: places[int(i)]["lon"] if pd.notna(i) else np.nan)
st["crow_km"] = hav_km(st.start_lat, st.start_lon, st.end_lat, st.end_lon)
rev = st.sort_values("crow_km", ascending=False).head(25)
print(rev[["year", "stage", "start", "end", "crow_km"]].to_string())
amb = st[(st.start_ncand > 1) | (st.end_ncand > 1)]
for r in amb.itertuples():
    for e in ("start", "end"):
        if getattr(r, e + "_ncand") > 1:
            p = places[int(getattr(r, e + "_gid"))]
            chk.setdefault("ambiguous", []).append([int(r.year), r.stage, getattr(r, e), p["name"], p["cc"], p["admin2"], getattr(r, e + "_how")])
ST.to_pickle(f"{WORK}/stages_geo.pkl")
pd.DataFrame(places.values()).to_pickle(f"{WORK}/places.pkl")
jsave({c: d["name"] for c, d in DEP.items()}, f"{WORK}/departements.json")

# ---------- outlines ----------
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]


def rnd(c, k=3):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


EU = box(-26, 26, 42, 72)
feats = []
for f in jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]:
    p = f["properties"]; g = shape(f["geometry"])
    if not g.intersects(EU): continue
    g = g.intersection(EU).simplify(0.01, preserve_topology=True)
    if g.is_empty: continue
    gm = mapping(g)
    feats.append({"type": "Feature", "properties": {"iso": iso_of(p), "name": p.get("NAME_EN") or p["NAME"]}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/europe.json")
dfe = []
for c, d in sorted(DEP.items()):
    gm = mapping(d["geom"].simplify(0.006, preserve_topology=True))
    dfe.append({"type": "Feature", "properties": {"code": c, "name": d["name"]}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
jsave({"type": "FeatureCollection", "features": dfe}, f"{DATA}/departements_geo.json")
jsave(chk, f"{WORK}/checks_geo.json", indent=1)
print("names", len(names), "places used", len(places), "europe.json", os.path.getsize(f"{DATA}/europe.json") // 1024, "KB")
