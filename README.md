# Every Tour de France, mapped

Every stage of the men's Tour de France from 1903 to 2026 (2,427 stages in 113 Tours) and of the Tour de France Femmes since 2022 (42 stages), geocoded with GeoNames and drawn as straight lines from start town to finish town: how the route wandered, the most visited stage towns, how far the race goes abroad, and how it got shorter and faster.

Interactive page: https://maps.tristanhotham.com/tour-de-france/
Paper: https://doi.org/10.5281/zenodo.23873013
Blog post: https://blog.tristanhotham.com/2026/10/31/tour-de-france/

## Headline results

- Geocoding: 4,731 of 4,938 starts and finishes (95.8%) located at 701 places; 766 of 863 distinct names. Unmatched: mostly summit finishes and ski stations with no village in their name (Puy de Dôme 15, Mont Ventoux 13), venues and villages missing from the gazetteer. List in `data/unmatched_names.csv`.
- The loop: in the 1920s, 92% of French stage towns lay within 50 km of the coast or a land border (against 37% of France's area); in the 2020s, 49%. No stage in the 1910s, 1920s or 1930s started away from the previous finish; in the 2020s 88% do, about 1,152 km of transfers a Tour in straight lines.
- Towns: Paris 161 starts and finishes in 112 Tours, Bordeaux 137, Pau 133 (the most common start, 69), Luchon 113. Every Tour finished in Paris except 2024 (Nice). All 96 départements of metropolitan France hosted at least one start or finish.
- Distance and speed: longest Tour 5,745 km in 1926; 2026: 3,333 km. Mean stage 306 km in the 1920s, 162 km in the 2020s. Winner's average speed 25.7 km/h in 1903, 45.08 km/h in 2026 (the fastest).
- Abroad: 27 Grand Départs abroad, the first in Amsterdam in 1954; 14 of 27 since 2000. 304 stages (12.5%) touched one of 12 other countries; 209 crossed a border. Belgium leads with 118 stages.
- Winners: France 36 (last 1985), Belgium 18, Spain 12, Italy 10, United Kingdom 6. The official record has no winner for 1999 to 2005 (titles stripped, not reawarded).
- Tour de France Femmes: 5 editions, 42 stages, 5,275 km, 63 places.

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

- Stages: LeTourDataSet rows; 4 stages listed twice for shared wins merged; 3 rows from 2022 (a repeated time trial and two transfer rows) dropped. Half stages and prologues count as stages.
- Places: GeoNames cities1000, searching only the thirteen countries the Tour visited. Names compared without accents, case, hyphens or apostrophes, St spelt out; a hand-made table (`code/aliases.py`) of 150 names for French exonyms, variants, venues and ski stations named after their village. Ambiguous names: the candidate nearest the stage's other end (or neighbouring stages), preferring France within 400 km. Summits and passes with no village in the name are left unmatched.
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

- Thomas Camminady, LeTourDataSet, https://github.com/thomascamminady/LeTourDataSet (commit c377920), MIT licence; compiled from the official letour.fr and letourfemmes.fr historical pages.
- GeoNames cities1000 (https://www.geonames.org/), CC BY 4.0, as packaged by lutangar/cities.json (commit e5e759c).
- Natural Earth countries and départements (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri; optional labels © OpenFreeMap, OpenMapTiles, OpenStreetMap contributors.

## Citation

Hotham, T. (2026) The shape of the Tour: every stage of the Tour de France, 1903 to 2026, mapped from start to finish. Zenodo. https://doi.org/10.5281/zenodo.23873013

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
