"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, and Natural Earth outlines of France and its neighbours in the ETRS89 Lambert
azimuthal equal-area projection (EPSG:3035)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72"})
BG, FG, MUT, LAND, RULE, SEA = "#F7F5EF", "#1C1E22", "#626870", "#ECE6D8", "#DDD7CA", "#E6EDF0"
RED, NAVY, GOLD = "#C8322B", "#1B2A4A", "#E0A800"
DCOL = dict(zip(DECADES, DEC_COL))

LAEA = Transformer.from_crs(4326, 3035, always_xy=True)
EUR = jload(f"{DATA}/europe.json")
DEPS = jload(f"{DATA}/departements_geo.json")


def proj(lon, lat):
    return LAEA.transform(np.asarray(lon, float), np.asarray(lat, float))


def polys(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in EUR["features"]:
    for ring in polys(f["geometry"]):
        x, y = proj(ring[:, 0], ring[:, 1]); SHAPES.append((f["properties"]["iso"], np.column_stack([x, y])))
DSHAPES = []
for f in DEPS["features"]:
    for ring in polys(f["geometry"]):
        x, y = proj(ring[:, 0], ring[:, 1]); DSHAPES.append((f["properties"]["code"], np.column_stack([x, y])))


def ext_ll(lon0, lon1, lat0, lat1):
    """Map extent in projected metres for a lon/lat box (taken from its corners and edge midpoints)."""
    lo = [lon0, lon1, lon0, lon1, (lon0 + lon1) / 2, (lon0 + lon1) / 2]; la = [lat0, lat0, lat1, lat1, lat0, lat1]
    x, y = proj(lo, la); return (min(x), max(x), min(y), max(y))


FRANCE = ext_ll(-5.6, 9.9, 41.2, 51.4)


def basemap(ax, ext=FRANCE, land=LAND, sea=SEA, ec="#FFFFFF", lw=.5, z=1, deps=False, dec=None):
    ax.set_facecolor(sea)
    for iso, p in SHAPES:
        ax.add_patch(MPoly(p, closed=True, fc=land if iso == "FRA" else "#F1EDE4", ec=ec, lw=lw, zorder=z))
    if deps:
        for c, p in DSHAPES:
            ax.add_patch(MPoly(p, closed=True, fc="none", ec="#D9D1BF", lw=.35, zorder=z + .1))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def stages_xy(race="men", years=None):
    """Stage lines (start and finish both located, different towns) as projected segments with year."""
    S = pd.read_csv(f"{DATA}/stages.csv")
    S = S[(S.race == race) & S.start_lat.notna() & S.finish_lat.notna() & ((S.start_lat != S.finish_lat) | (S.start_lon != S.finish_lon))]
    if years is not None: S = S[S.year.isin(years)]
    x0, y0 = proj(S.start_lon.values, S.start_lat.values); x1, y1 = proj(S.finish_lon.values, S.finish_lat.values)
    return S, np.stack([np.column_stack([x0, y0]), np.column_stack([x1, y1])], axis=1)
