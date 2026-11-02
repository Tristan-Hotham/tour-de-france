"""r/dataisbeautiful collage for tour-de-france: 2400 x 3200 px, light background. Numbers from data/results.json.
Map notes sit on open sea or on the paper around the map, never over land or stage lines (checked); no leader lines."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from shapely.geometry import shape as _shape, box as _box, LineString as _LS, Polygon as _Poly

R = jload(f"{DATA}/results.json")
BGc = "#F8F6F1"; SEAc = "#E8EFF2"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
s, d, t, a, sh, w = R["source"], R["dist"], R["towns"], R["abroad"], R["shape"], R["winners"]
Y = pd.DataFrame(R["years"]).set_index("y")
DS = pd.read_csv(f"{DATA}/stages.csv")

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, .985, "Every Tour de France stage since 1903", fontproperties=DISP, fontsize=40, color=FG, va="top")
fig.text(.045, .942, f"All {s['men_stages']:,} stages of the men's race, {s['first_year']} to {s['last_year']}, drawn as straight lines from start town to finish town.\n"
         f"For thirty years it was one unbroken lap round the edge of France. Now {sh['transfer_pct_2020s']:.0f}% of stages start somewhere new.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.45)

# ---- main map
EXT = ext_ll(-6.2, 10.4, 41.0, 51.6)
ax = fig.add_axes([.03, .435, .94, .455]); basemap(ax, ext=EXT, sea=SEAc, ec=BGc, lw=.6)
S, seg = stages_xy("men")
order = np.argsort(S.year.values)
ax.add_collection(LineCollection(seg[order], colors=[DCOL[decade_of(y)] for y in S.year.values[order]], linewidths=.7, alpha=.55, zorder=3, capstyle="round"))
TW = pd.read_csv(f"{DATA}/stage_towns.csv")
pts = pd.concat([DS[["start_place", "start_lat", "start_lon"]].set_axis(["name", "lat", "lon"], axis=1), DS[["finish_place", "finish_lat", "finish_lon"]].set_axis(["name", "lat", "lon"], axis=1)]).dropna().drop_duplicates("name")
TW = TW.merge(pts, on="name")
x, y = proj(TW.lon.values, TW.lat.values)
ax.scatter(x, y, s=2 + 4 * np.sqrt(TW.visits.values), c=FG, alpha=.6, lw=.3, edgecolor="#fff", zorder=4)

# obstacles: land (with a margin) and every stage line
from shapely.strtree import STRtree
REG = _box(-7, 40, 11.5, 53)
_land = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = _shape(f["geometry"]); gs = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for q in gs:
        if not q.intersects(REG): continue
        q = q.intersection(REG).simplify(.01)
        for qq in (q.geoms if q.geom_type == "MultiPolygon" else [q]):
            if qq.geom_type != "Polygon" or qq.is_empty: continue
            xy = np.array(qq.exterior.coords); px, py = proj(xy[:, 0], xy[:, 1]); _land.append(_Poly(np.column_stack([px, py])).buffer(0))
LANDT = STRtree(_land); SEGT = STRtree([_LS(sg) for sg in seg])
MARGIN_LAND, MARGIN_LINE = 12e3, 4e3


class _Hit:
    def __init__(self, tree, m): self.t, self.m = tree, m
    def intersects(self, b): return len(self.t.query(b.buffer(self.m), predicate="intersects")) > 0


LANDP, LINES = _Hit(LANDT, MARGIN_LAND), _Hit(SEGT, MARGIN_LINE)
fig.canvas.draw(); REN = fig.canvas.get_renderer(); PLACED = []


def tbox(tx):
    bb = tx.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 5, bb.y0 - 4], [bb.x1 + 5, bb.y1 + 4]])
    return _box(x0, y0, x1, y1)


def note(name, txt, anchors, ha="left", size=10.5, col=FG, wgt="medium"):
    """Put a note at the first clean spot near (lon, lat): open sea, clear of lines and other notes, inside the map."""
    tx = ax.text(0, 0, txt, ha=ha, va="center", fontsize=size, color=col, fontweight=wgt, linespacing=1.3, zorder=10, path_effects=HALO)
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim(); frame = _box(x0 + 2e4, y0 + 2e4, x1 - 2e4, y1 - 2e4)
    for lon, lat in anchors:
     for r in range(0, 10):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r: continue
                px, py = proj(lon + dx * .25, lat + dy * .2); tx.set_position((float(px), float(py))); b = tbox(tx)
                if frame.contains(b) and not LANDP.intersects(b) and not LINES.intersects(b) and not any(b.intersects(o) for _, o in PLACED):
                    PLACED.append((name, b)); return
    raise RuntimeError("no clean spot for " + name)


TV = t["top_visits"]
note("biscay", f"The Pyrenean gateways:\nBordeaux {TV[1]['n']}, Pau {TV[2]['n']}\nand Luchon {TV[3]['n']} starts\nand finishes", [(-4.8, 45.4), (-5.5, 44.6)])
note("paris", f"Paris: {t['paris']['visits']} starts\nand finishes in\n{t['paris']['tours']} Tours", [(-5.6, 47.4), (-5.8, 48.6), (-1.0, 50.3), (-5.0, 50.0)])
note("med", f"{a['gd_abroad']} Grand Départs abroad,\nfrom Amsterdam ({a['gd_first_abroad']})\nto Barcelona ({s['last_year']})", [(4.6, 42.1), (6.5, 41.6), (3.6, 41.5)])
for nm, b in PLACED:
    assert not LANDP.intersects(b) and not LINES.intersects(b), nm
    assert not any(b.intersects(o) for n2, o in PLACED if n2 != nm), nm
print("map notes ok:", [n for n, _ in PLACED])

# decade legend, full, on the paper under the map
h = [Line2D([], [], color=DCOL[dd], lw=3.6, label=f"{dd}s") for dd in DECADES]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(.035, .432), ncol=7, frameon=False, fontsize=10.5, handlelength=1.6, columnspacing=1.3, title="Line colour: decade of the stage. Circles: stage towns, sized by starts and finishes.", title_fontsize=9.6, alignment="left")

# ---- 1926 against the latest Tour
last = s["last_year"]


def mini(rect, year, title):
    a_ = fig.add_axes(rect); basemap(a_, ext=ext_ll(-5.3, 9.6, 41.2, 51.3), sea=SEAc, ec=BGc, lw=.4)
    X = DS[(DS.race == "men") & (DS.year == year)].sort_values("order_in_tour"); prev = None
    for r in X.itertuples():
        if pd.notna(r.start_lat) and prev is not None and prev != (r.start_lon, r.start_lat):
            px, py = proj([prev[0], r.start_lon], [prev[1], r.start_lat]); a_.plot(px, py, color=MUT, lw=1, ls=(0, (2.5, 2.5)), zorder=4)
        if pd.notna(r.start_lat) and pd.notna(r.finish_lat):
            px, py = proj([r.start_lon, r.finish_lon], [r.start_lat, r.finish_lat]); a_.plot(px, py, color=FG, lw=4, solid_capstyle="round", zorder=5); a_.plot(px, py, color=YELLOW, lw=2.4, solid_capstyle="round", zorder=6)
        prev = (r.finish_lon, r.finish_lat) if pd.notna(r.finish_lat) else None
    a_.set_title(title, loc="left", fontsize=11.5, color=FG, pad=6, fontweight="medium")


yl = Y.loc[last]
mini([.045, .135, .29, .195], 1926, f"1926: {int(Y.loc[1926].n)} stages, {int(Y.loc[1926].dist):,} km,\none unbroken loop")
mini([.36, .135, .29, .195], last, f"{last}: {int(yl.n)} stages, {int(yl.dist):,} km,\nhops joined by transfers")
fig.text(.045, .123, "Yellow: stages. Dashed: transfers to the next start.", fontsize=9.2, color=MUT)

# ---- numbers column
nums = [(f"{d['longest_km']:,} km", NAVY, f"the longest Tour, {d['longest_year']}.\n{last}: {d['y2026']:,} km"),
        (f"{d['speed_max']:.1f} km/h", RED, f"the winner's average in {d['speed_max_year']},\na record ({d['speed_1903']:.1f} in 1903)"),
        (f"{sh['edge50_1920s']:.0f}%", "#2E7D9A", f"of French stage towns in the 1920s\nwere within 50 km of the coast or a\nborder ({sh['edge50_2020s']:.0f}% in the 2020s)")]
for i, (big, col, small) in enumerate(nums):
    yy = .335 - i * .072
    fig.text(.69, yy, big, fontproperties=DISP, fontsize=30, color=col, va="top")
    fig.text(.69, yy - .033, small, family=MONO, fontsize=9.6, color=FG, va="top", linespacing=1.35)

# ---- distance and speed strip
b = fig.add_axes([.075, .064, .86, .036]); b.set_facecolor(BGc)
b.bar(Y.index, Y.dist, color=[DCOL[decade_of(yy)] for yy in Y.index], width=.8); spines(b); b.set_xlim(1901, 2028); b.set_ylim(0, 6300); b.tick_params(labelsize=9)
b.set_yticks([0, 3000, 6000], ["0", "3,000", "6,000 km"])
b.set_title("Total distance of every Tour", family=MONO, fontsize=11, color=FG, loc="left", pad=5)

fig.text(.045, .006, "Source: LeTourDataSet by Thomas Camminady (MIT), compiled from letour.fr; places: GeoNames cities1000 (CC BY 4.0); outlines: Natural Earth.\n"
         f"{R['geo']['rate']:.1f}% of starts and finishes located; summit finishes with no village name (Puy de Dôme, Mont Ventoux) are not drawn. Lines are not roads.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/tour-de-france", family=MONO, fontsize=8.4, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "every_tour_de_france.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
