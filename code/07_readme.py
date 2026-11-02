"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, g, t, d, a, sh, w, wo = R["source"], R["geo"], R["towns"], R["dist"], R["abroad"], R["shape"], R["winners"], R["women"]
N = lambda v: f"{round(v):,}"
readme = f"""# Every Tour de France, mapped

Every stage of the men's Tour de France from {s['first_year']} to {s['last_year']} ({N(s['men_stages'])} stages in {s['men_years']} Tours) and of the Tour de France Femmes since {s['women_first']} ({s['women_stages']} stages), geocoded with GeoNames and drawn as straight lines from start town to finish town: how the route wandered, the most visited stage towns, how far the race goes abroad, and how it got shorter and faster.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Geocoding: {N(g['matched'])} of {N(g['ends'])} starts and finishes ({g['rate']:.1f}%) located at {N(t['n'])} places; {g['names_matched']} of {g['names']} distinct names. Unmatched: mostly summit finishes and ski stations with no village in their name (Puy de Dôme {g['unmatched_top'][0][2]}, Mont Ventoux {g['unmatched_top'][1][2]}), venues and villages missing from the gazetteer. List in `data/unmatched_names.csv`.
- The loop: in the 1920s, {sh['edge50_1920s']:.0f}% of French stage towns lay within 50 km of the coast or a land border (against {sh['area_edge50_pct']:.0f}% of France's area); in the 2020s, {sh['edge50_2020s']:.0f}%. No stage in the 1910s, 1920s or 1930s started away from the previous finish; in the 2020s {sh['transfer_pct_2020s']:.0f}% do, about {N(sh['transfer_km_2020s'])} km of transfers a Tour in straight lines.
- Towns: Paris {t['paris']['visits']} starts and finishes in {t['paris']['tours']} Tours, Bordeaux {t['top_visits'][1]['n']}, Pau {t['top_visits'][2]['n']} (the most common start, {t['top_starts'][0]['n']}), Luchon {t['top_visits'][3]['n']}. Every Tour finished in Paris except {t['final_elsewhere'][0][0]} ({t['final_elsewhere'][0][1]}). All {R['deps']['n']} départements of metropolitan France hosted at least one start or finish.
- Distance and speed: longest Tour {N(d['longest_km'])} km in {d['longest_year']}; {s['last_year']}: {N(d['y2026'])} km. Mean stage {d['avg_stage_1920s']:.0f} km in the 1920s, {d['avg_stage_2020s']:.0f} km in the 2020s. Winner's average speed {d['speed_1903']:.1f} km/h in 1903, {d['speed_max']:.2f} km/h in {d['speed_max_year']} (the fastest).
- Abroad: {a['gd_abroad']} Grand Départs abroad, the first in {a['gd_first_abroad_town']} in {a['gd_first_abroad']}; {a['gd_since2000']} of {a['tours_since2000']} since 2000. {a['stages_abroad']} stages ({a['stages_abroad_pct']:.1f}%) touched one of {a['n_countries']} other countries; {a['cross']} crossed a border. Belgium leads with {a['stages_by_country']['Belgium']} stages.
- Winners: France {w['france']} (last {w['france_last']}), Belgium {w['belgium']}, Spain {w['spain']}, Italy {w['italy']}, United Kingdom {w['uk']}. The official record has no winner for {w['no_winner'][0]} to {w['no_winner'][-1]} (titles stripped, not reawarded).
- Tour de France Femmes: {s['women_years']} editions, {wo['stages']} stages, {N(wo['dist_total'])} km, {wo['towns']} places.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; all page data embedded). |
| `header.png` | Social card, 1200 x 630. |
| `img/map_static.png` | Static map shown if the interactive map cannot start. |
| `data/stages.csv` | Every stage (men and women): year, stage, start and finish as given, matched place, country, département, coordinates, how it was matched, straight-line length, transfer from the previous finish, stage winner, Tour total distance. |
| `data/stage_towns.csv` | Every place used by the men's Tour: starts, finishes, Tours, first and last year. |
| `data/tours_by_year.csv` | Per Tour: stages, total and mean stage distance, winner, nation and speed, stages abroad and crossing borders, transfers. |
| `data/departements.csv` | Starts and finishes per département of metropolitan France. |
| `data/unmatched_names.csv` | Stage names left without a place, with the reason. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/europe.json`, `data/departements_geo.json` | Page data and outlines. |
| `code/` | Scripts, run in order (below), the geocoding table (`aliases.py`), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Stages: LeTourDataSet rows; {s['joint']} stages listed twice for shared wins merged; {s['dropped_2022']} rows from 2022 (a repeated time trial and two transfer rows) dropped. Half stages and prologues count as stages.
- Places: GeoNames cities1000, searching only the thirteen countries the Tour visited. Names compared without accents, case, hyphens or apostrophes, St spelt out; a hand-made table (`code/aliases.py`) of {g['alias_n']} names for French exonyms, variants, venues and ski stations named after their village. Ambiguous names: the candidate nearest the stage's other end (or neighbouring stages), preferring France within 400 km. Summits and passes with no village in the name are left unmatched.
- Lines are straight from start to finish: not roads, not distances. Transfers are measured the same way. Abroad = a stage town outside France (Monaco and Andorra included). Edge of France = within 50 km of the outline of metropolitan France (Natural Earth 1:10m, Lambert 93).
- Winners' nationalities are hand-coded (the rider file has none) and checked against the team column in national team years.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read in place: `raw/` (LeTourDataSet CSVs and GeoNames cities1000) and Natural Earth in `/home/claude/newdata/raw/geo/` (set `TDF_GEO` to change). Intermediate files go to `/dev/shm/tourdefrance/work` (set `TDFTMP`).

```
python3 code/01_clean.py        # read and tidy stages and winners
python3 code/02_geo.py          # geocode stage towns, outlines
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures, static map
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Thomas Camminady, LeTourDataSet, {LTD_URL} (commit {LTD_COMMIT[:7]}), MIT licence; compiled from the official letour.fr and letourfemmes.fr historical pages.
- GeoNames cities1000 (https://www.geonames.org/), CC BY 4.0, as packaged by lutangar/cities.json (commit {GN_COMMIT[:7]}).
- Natural Earth countries and départements (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri; optional labels © OpenFreeMap, OpenMapTiles, OpenStreetMap contributors.

## Citation

Hotham, T. (2026) {CITE_TITLE[0].upper() + CITE_TITLE[1:]}. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The stage and rider data are
derived from Thomas Camminady's LeTourDataSet
(github.com/thomascamminady/LeTourDataSet), MIT licence, which compiles the
official letour.fr pages. Place coordinates and codes come from GeoNames
(geonames.org), CC BY 4.0: please credit GeoNames. Natural Earth is public
domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] Every Tour de France stage since 1903, start to finish. For 30 years it was one unbroken lap of France's edges; now {sh['transfer_pct_2020s']:.0f}% of stages start somewhere other than the last finish

## Body

I mapped all {N(s['men_stages'])} stages of the men's Tour de France ({s['first_year']} to {s['last_year']}) as straight lines from start town to finish town, coloured by decade. The early Tours really were a tour: in the 1920s, {sh['edge50_1920s']:.0f}% of the French towns the race stopped in were within 50 km of the coast or a border, and every stage started where the last one ended. The longest Tour was {N(d['longest_km'])} km in {d['longest_year']}; the {s['last_year']} race was {N(d['y2026'])} km and won at a record {d['speed_max']:.1f} km/h. Paris ({t['paris']['visits']} starts and finishes), Bordeaux ({t['top_visits'][1]['n']}) and Pau ({t['top_visits'][2]['n']}) are the most used towns, and {a['gd_abroad']} Tours have started abroad, {a['gd_since2000']} of the {a['tours_since2000']} since 2000. Caveats: lines are not roads; summit finishes with no village in their name (Puy de Dôme, Mont Ventoux) are left off; {g['rate']:.1f}% of starts and finishes are located. Interactive map with a play button that draws each Tour in order: {PAGE}

## Source comment

Source: LeTourDataSet by Thomas Camminady (MIT licence, github.com/thomascamminady/LeTourDataSet), compiled from the official letour.fr pages: every stage's start and finish town, every Tour's distance and the winners' times. Town locations: GeoNames cities1000 (CC BY 4.0), matched by name with a hand-checked table for French exonyms (Londres, Gand), venues and ski stations. Outlines: Natural Earth. Winners' nationalities added by hand.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for tx in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in tx.replace("```", "").replace("|---|---|", ""), bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
