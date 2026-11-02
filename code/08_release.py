"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23873013, https://doi.org/10.5281/zenodo.23873013 and https://blog.tristanhotham.com/2026/10/31/tour-de-france/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Shape_of_the_Tour"

# the page build checks the shared facts; these are numbers written in words or alt text in the blog and collage
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
T, C = R["towns"], {c["dec"]: c for c in R["centre"]}
assert [x["n"] for x in T["top_visits"][:4]] == [161, 137, 133, 113]
assert (round(C[1900]["edge50_pct"]), round(C[1920]["edge50_pct"]), round(R["decades"][-1]["transfer_pct"])) == (63, 92, 88)
assert R["dist"]["longest_km"] == 5745 and round(R["dist"]["speed_max"], 1) == 45.1 and R["abroad"]["gd_abroad"] == 27
assert [v for _, v in R["winners"]["by_nation"][:7]] == [36, 18, 12, 10, 6, 5, 5]
assert all(3250 < y["dist"] < 3700 for y in R["years"] if y["y"] >= 2000)
gl = R["abroad"]["gd_list"]; assert gl[-1]["town"] == "Barcelona" and R["source"]["last_year"] == 2026

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23873013", "https://blog.tristanhotham.com/2026/10/31/tour-de-france/"}, set(re.findall(r"\{\{[^|}]+\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s, d, a, sh = R["source"], R["dist"], R["abroad"], R["shape"]
meta = {"title": "Every Tour de France, mapped: from a lap of France to a race that hops",
        "slug": "tour-de-france",
        "excerpt": f"I mapped all {s['men_stages']:,} stages of the Tour de France since {s['first_year']}, start to finish. For thirty years it was one unbroken loop round the edge of France; now {sh['transfer_pct_2020s']:.0f}% of stages start somewhere new, the race is {d['dist_drop_pct']}% shorter than in {d['longest_year']} and faster than ever.",
        "seo_description": f"Every Tour de France stage since {s['first_year']} on one map: the giant loop, {a['gd_abroad']} Grand Départs abroad, Paris, Bordeaux and Pau, and a shorter, faster race.",
        "tags": ["Tour de France", "cycling", "maps", "data visualisation", "sport history", "France", "GeoNames", "open data"],
        "header_alt": f"Title card reading 'Every Tour de France, mapped' in black and red, with 'Tour de' on a yellow band, beside a map of France covered in thin coloured lines for every stage since {s['first_year']}, with the 1926 route drawn in thick yellow as a loop round the edge of the country. Text: {s['men_stages']:,} stages, {s['first_year']} to {s['last_year']}, start to finish; the 1926 loop in yellow, {d['longest_km']:,} km, the longest Tour."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/tour-de-france_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dd in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, dd))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, dd, fn), f"tour-de-france/{dd}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"tour-de-france/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "tour-de-france/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": PAPER_TITLE,
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Stage and rider data: LeTourDataSet by Thomas Camminady (MIT licence), from letour.fr. Places: GeoNames (CC BY 4.0).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Tour de France", "cycling", "sport geography", "historical GIS", "geocoding", "GeoNames", "route maps", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": LTD_URL, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.geonames.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj and "DSIT" not in sj and "DCMS" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
