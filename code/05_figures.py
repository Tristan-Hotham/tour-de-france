"""Header card, blog figures (release/blog/b_*.png, 1800 px wide), paper figures (release/paper/f_*.png) and the
static map shown when the interactive one cannot start (img/map_static.png). Numbers from data/results.json."""
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper"); IMG = os.path.join(ROOT, "img")
for d in (BL, PA, IMG): os.makedirs(d, exist_ok=True)
HALO = [pe.withStroke(linewidth=3.2, foreground="#FFFFFF")]
Y = pd.DataFrame(R["years"]).set_index("y")
DS = pd.read_csv(f"{DATA}/stages.csv")
TOWNS = pd.read_csv(f"{DATA}/stage_towns.csv")
PLC = {}
for r in DS.itertuples():
    for e, nm, la, lo in (("s", r.start_place, r.start_lat, r.start_lon), ("f", r.finish_place, r.finish_lat, r.finish_lon)):
        if isinstance(nm, str): PLC[nm] = (lo, la)


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def label(ax, name, dx=0, dy=0, ha="left", size=10, w="medium", col=FG):
    x, y = proj(*PLC[name]); ax.text(x + dx, y + dy, name, ha=ha, va="center", fontsize=size, color=col, fontweight=w, path_effects=HALO, zorder=9)


def draw_all(ax, lw=.55, alpha=.5, dots=True):
    S, seg = stages_xy("men")
    order = np.argsort(S.year.values)
    cols = [DCOL[decade_of(y)] for y in S.year.values[order]]
    ax.add_collection(LineCollection(seg[order], colors=cols, linewidths=lw, alpha=alpha, zorder=3, capstyle="round"))
    if dots:
        t = TOWNS[TOWNS.visits > 0].merge(pd.DataFrame([(k, v[0], v[1]) for k, v in PLC.items()], columns=["name", "lon", "lat"]), on="name", how="left")
        x, y = proj(t.lon.values, t.lat.values)
        ax.scatter(x, y, s=1.5 + 3.2 * np.sqrt(t.visits.values), c=FG, alpha=.55, lw=.3, edgecolor="#fff", zorder=4)


def decade_legend(fig, x, y, ncol=13, size=9.5):
    h = [Line2D([], [], color=DCOL[d], lw=3.2, label=f"{d}s") for d in DECADES]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(x, y), ncol=ncol, frameon=False, fontsize=size, handlelength=1.4, columnspacing=1.0)


# ---------- the map of every stage ----------
fig = plt.figure(figsize=(12, 13.2), facecolor=BG)
ax = fig.add_axes([0.02, 0.075, 0.96, 0.87]); basemap(ax); draw_all(ax)
for nm, dx, dy, ha in (("Paris", 22e3, 18e3, "left"), ("Bordeaux", -22e3, 0, "right"), ("Pau", -18e3, -14e3, "right"), ("Luchon", 14e3, -22e3, "left"),
                       ("Nice", 18e3, 0, "left"), ("Metz", 18e3, 10e3, "left"), ("Brest", 0, 30e3, "center"), ("Grenoble", 20e3, -6e3, "left")):
    label(ax, nm, dx, dy, ha, size=11, w="bold")
fig.text(.03, .975, f"Every stage of the Tour de France, {R['source']['first_year']} to {R['source']['last_year']}", fontproperties=DISPB, fontsize=21, color=FG, va="top")
fig.text(.03, .944, f"{R['source']['men_stages']:,} stages as straight lines from start town to finish town, coloured by decade. Circles: stage towns, by starts and finishes.", fontsize=10.5, color=MUT, va="top")
decade_legend(fig, .03, .068, ncol=13, size=9.2)
fig.text(.03, .018, "Data: LeTourDataSet (T. Camminady, from letour.fr); places: GeoNames; outlines: Natural Earth. Summit finishes without a village name are not drawn.", fontsize=8.8, color=MUT)
fig.savefig(os.path.join(IMG, "map_static.png"), dpi=110, facecolor=BG)
both(fig, "map")

# ---------- 1926 against the latest Tour ----------
last = R["source"]["last_year"]


def one_tour(ax, year, title, sub):
    basemap(ax, ext=FRANCE)
    S = DS[(DS.race == "men") & (DS.year == year)].sort_values("order_in_tour")
    prev = None
    for r in S.itertuples():
        if pd.notna(r.start_lat) and prev is not None and (prev[0] != r.start_lon or prev[1] != r.start_lat):
            x, y = proj([prev[0], r.start_lon], [prev[1], r.start_lat]); ax.plot(x, y, color=MUT, lw=1.2, ls=(0, (3, 3)), zorder=4)
        if pd.notna(r.start_lat) and pd.notna(r.finish_lat):
            x, y = proj([r.start_lon, r.finish_lon], [r.start_lat, r.finish_lat])
            ax.plot(x, y, color=FG, lw=5.2, solid_capstyle="round", zorder=5); ax.plot(x, y, color=YELLOW, lw=3.2, solid_capstyle="round", zorder=6)
        prev = (r.finish_lon, r.finish_lat) if pd.notna(r.finish_lat) else None
    pts = pd.concat([S[["start_lon", "start_lat"]].set_axis(["lon", "lat"], axis=1), S[["finish_lon", "finish_lat"]].set_axis(["lon", "lat"], axis=1)]).dropna()
    x, y = proj(pts.lon.values, pts.lat.values); ax.scatter(x, y, s=22, c=YELLOW, ec=FG, lw=1.1, zorder=7)
    f = S.iloc[0]; x, y = proj(f.start_lon, f.start_lat); ax.scatter([x], [y], s=110, c="#2E8A57", ec=FG, lw=1.3, zorder=8)
    l = S.iloc[-1]; x, y = proj(l.finish_lon, l.finish_lat); ax.scatter([x], [y], s=110, c=RED, ec=FG, lw=1.3, zorder=8)
    ax.set_title(title, loc="left", fontproperties=DISPB, fontsize=17, color=FG, pad=26)
    ax.text(0, 1.012, sub, transform=ax.transAxes, fontsize=10, color=MUT, va="bottom")


y26, yl = Y.loc[1926], Y.loc[last]
fig, axs = plt.subplots(1, 2, figsize=(12, 7.4), facecolor=BG); fig.subplots_adjust(left=.02, right=.98, top=.86, bottom=.1, wspace=.05)
one_tour(axs[0], 1926, "1926: one unbroken loop", f"{int(y26.n)} stages, {int(y26.dist):,} km, every stage from the last finish")
one_tour(axs[1], last, f"{last}: hops and transfers", f"{int(yl.n)} stages, {int(yl.dist):,} km, from {R['abroad']['gd_list'][-1]['town']}; transfers about {int(yl.tkm):,} km")
fig.legend(handles=[Line2D([], [], color=YELLOW, lw=4, path_effects=[pe.Stroke(linewidth=6, foreground=FG), pe.Normal()], label="stage, start to finish"),
                    Line2D([], [], color=MUT, lw=1.2, ls=(0, (3, 3)), label="transfer to the next start"),
                    Line2D([], [], ls="", marker="o", ms=9, mfc="#2E8A57", mec=FG, label="first start"), Line2D([], [], ls="", marker="o", ms=9, mfc=RED, mec=FG, label="final finish")],
           loc="lower center", ncol=4, frameon=False, fontsize=10, bbox_to_anchor=(.5, .005))
assert R["abroad"]["gd_list"][-1]["year"] == last
both(fig, "loop")

# ---------- distance and speed ----------
fig = plt.figure(figsize=(12, 5.6), facecolor=BG); ax = fig.add_axes([.07, .11, .86, .72]); ax.set_facecolor(BG)
ax.bar(Y.index, Y.dist, color=[DCOL[decade_of(y)] for y in Y.index], width=.8, alpha=.9)
ax.set_xlim(1901, 2028); ax.set_ylim(0, 6500); spines(ax); ax.set_ylabel("total distance, km"); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{int(v):,}"))
a2 = ax.twinx(); sp = Y.speed.dropna()
a2.scatter(sp.index, sp.values, s=16, c=FG, ec="#fff", lw=.5, zorder=5); a2.set_ylim(15, 48); a2.set_ylabel("winner's average speed, km/h"); a2.spines["top"].set_visible(False)
D = R["dist"]
ax.text(D["longest_year"] - 1, D["longest_km"] + 120, f"{D['longest_year']}: {D['longest_km']:,} km", ha="center", fontsize=10, color=FG, fontweight="medium")
a2.text(D["speed_max_year"] - 1.5, D["speed_max"] + .4, f"{D['speed_max_year']}: {D['speed_max']:.1f} km/h", ha="right", fontsize=10, color=FG, fontweight="medium")
fig.text(.07, .93, "Bars: total distance of each Tour, coloured by decade.   Dots: the winner's average speed (Tours decided on time).", fontsize=10, color=MUT)
both(fig, "distance")

# ---------- stage towns ----------
top = R["towns"]["top_visits"][:15]
tt = TOWNS.set_index("name")
fig = plt.figure(figsize=(12, 6.8), facecolor=BG); ax = fig.add_axes([.17, .11, .78, .77]); ax.set_facecolor(BG)
nm = [t["name"] for t in top][::-1]; s = [int(tt.loc[n, "starts"]) for n in nm]; f = [int(tt.loc[n, "finishes"]) for n in nm]
ax.barh(nm, s, color=NAVY, height=.7, label="starts"); ax.barh(nm, f, left=s, color=GOLD, height=.7, label="finishes")
for i, n in enumerate(nm): ax.text(s[i] + f[i] + 1.5, i, f"{s[i] + f[i]}   ({int(tt.loc[n, 'tours'])} Tours)", va="center", fontsize=9.5, color=FG)
ax.set_xlim(0, 195); spines(ax); ax.tick_params(axis="y", length=0, labelsize=10.5); ax.set_xlabel("starts and finishes, men's Tour")
ax.legend(loc="lower right", frameon=False, fontsize=10)
fig.text(.17, .93, f"The most visited stage towns, {R['source']['first_year']} to {R['source']['last_year']}", fontproperties=DISPB, fontsize=17, color=FG)
both(fig, "towns")

# ---------- the edge of France and transfers, by decade ----------
dec = pd.DataFrame(R["decades"]).set_index("dec"); cen = pd.DataFrame(R["centre"]).set_index("dec")
fig = plt.figure(figsize=(12, 5.2), facecolor=BG); ax = fig.add_axes([.07, .12, .9, .7]); ax.set_facecolor(BG)
x = np.arange(len(dec))
ax.bar(x, cen.loc[dec.index, "edge50_pct"], color=[DCOL[d] for d in dec.index], width=.7, label="French stage towns within 50 km of the coast or a border")
ax.plot(x, dec.transfer_pct, "-o", color=RED, lw=2.4, ms=6, mec="#fff", label="stages starting away from the previous finish", zorder=5)
ax.axhline(R["shape"]["area_edge50_pct"], color=FG, lw=1.1, ls=(0, (5, 4)), label=f"share of France's area within 50 km of its edge ({R['shape']['area_edge50_pct']:.0f}%)")
ax.set_xticks(x, [f"{d}s" for d in dec.index], fontsize=10); ax.set_ylim(0, 100); spines(ax); ax.set_ylabel("%"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
fig.legend(loc="upper left", bbox_to_anchor=(.07, .99), ncol=2, frameon=False, fontsize=9.6)
both(fig, "edge")

# ---------- abroad ----------
CC = {"Belgium": "#C8432B", "Switzerland": "#B05A7A", "Spain": "#DE8A2C", "Italy": "#2E9A8C", "Germany": "#1B2A4A", "Netherlands": "#F2B701", "Luxembourg": "#7FB2D9",
      "United Kingdom": "#2F5FA7", "Ireland": "#4FA66A", "Monaco": "#A79F94", "Andorra": "#8C8478", "Denmark": "#A4283A"}
byc = pd.DataFrame(R["abroad"]["by_year_country"], columns=["y", "c", "n"]).pivot(index="y", columns="c", values="n").fillna(0)
order = list(R["abroad"]["stages_by_country"])
fig = plt.figure(figsize=(12, 5.4), facecolor=BG); ax = fig.add_axes([.06, .2, .92, .66]); ax.set_facecolor(BG)
base = np.zeros(len(byc))
for c in order:
    v = byc[c].values if c in byc else np.zeros(len(byc)); ax.bar(byc.index, v, bottom=base, color=CC[c], width=.82, label=f"{c} ({R['abroad']['stages_by_country'][c]})"); base += v
for g in R["abroad"]["gd_list"]: ax.plot(g["year"], 11.6, marker="v", color=FG, ms=6)
ax.set_xlim(1901, 2028); ax.set_ylim(0, 12.2); spines(ax); ax.set_ylabel("stages abroad"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.legend(loc="upper center", bbox_to_anchor=(.5, -.09), ncol=6, frameon=False, fontsize=9.4)
fig.text(.06, .93, f"Stages starting or finishing outside France, by country. Triangles: the {R['abroad']['gd_abroad']} Grand Départs abroad.", fontsize=10.5, color=MUT)
both(fig, "abroad")

# ---------- winners ----------
NC = dict(NAT_COL); NC.update({"Ireland": "#8FAE45", "Germany": "#555555", "Australia": "#8C564B", "Colombia": "#17BECF"})
W = {y: n for y, r, n in R["winners"]["years"]}; raced = set(Y.index); nw = set(R["winners"]["no_winner"])
fig = plt.figure(figsize=(12, 6.8), facecolor=BG)
a1 = fig.add_axes([.03, .67, .94, .22]); a1.set_xlim(0, 62); a1.set_ylim(-.15, 2.15); a1.axis("off")
for k, y in enumerate(range(1903, last + 1)):
    row, col = divmod(k, 62); yy = 1.1 - row * 1.15
    if y in W: a1.add_patch(Rectangle((col + .04, yy), .92, .8, fc=NC.get(W[y], "#999")))
    elif y in nw: a1.add_patch(Rectangle((col + .04, yy), .92, .8, fc="#ECE8DE", ec=MUT, hatch="////", lw=.4))
    else: a1.add_patch(Rectangle((col + .04, yy), .92, .8, fc="none", ec=RULE, lw=.6))
    if y % 10 == 0 or col == 0: a1.text(col + .05, yy - .1, str(y), fontsize=8.5, color=MUT, va="top")
a2 = fig.add_axes([.17, .05, .78, .52]); a2.set_facecolor(BG)
nat = R["winners"]["by_nation"][::-1]
a2.barh([n for n, _ in nat], [v for _, v in nat], color=[NC.get(n, "#999") for n, _ in nat], height=.72)
for i, (n, v) in enumerate(nat): a2.text(v + .4, i, str(v), va="center", fontsize=9.5)
spines(a2); a2.set_xticks([]); a2.spines["bottom"].set_visible(False); a2.tick_params(axis="y", length=0, labelsize=10)
fig.text(.03, .955, "Who won, year by year, and titles by nation", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.03, .915, f"Blank: no Tour. Hatched: no winner in the official record ({R['winners']['no_winner'][0]} to {R['winners']['no_winner'][-1]}, titles stripped).", fontsize=10, color=MUT)
both(fig, "winners")

# ---------- departements (paper only) ----------
dv = SITE_DV = jload(f"{DATA}/site.json")["dep_visits"]
fig = plt.figure(figsize=(9, 9.2), facecolor=BG); ax = fig.add_axes([.02, .1, .96, .84]); basemap(ax, ext=ext_ll(-5.3, 9.7, 41.3, 51.2))
cmap = matplotlib.colormaps["YlOrBr"]; mx = max(dv.values())
for c, p in DSHAPES:
    ax.add_patch(MPoly(p, closed=True, fc=cmap(.08 + .85 * np.sqrt(dv[c] / mx)), ec="#FFFFFF", lw=.5, zorder=2))
sm = plt.cm.ScalarMappable(cmap=cmap, norm=matplotlib.colors.Normalize(0, mx)); cax = fig.add_axes([.25, .06, .5, .018])
cb = fig.colorbar(sm, cax=cax, orientation="horizontal"); cb.set_ticks([]); cax.text(0, -1.4, "few", transform=cax.transAxes, fontsize=9); cax.text(1, -1.4, f"{mx} starts and finishes", transform=cax.transAxes, fontsize=9, ha="right")
both(fig, "deps", blog=False)

# ---------- the women's Tour (paper only) ----------
fig = plt.figure(figsize=(9, 9.2), facecolor=BG); ax = fig.add_axes([.02, .1, .96, .84]); basemap(ax, ext=ext_ll(-5.3, 9.7, 41.3, 52.3))
WC = ["#8E44AD", "#2F7FB0", "#2E9A8C", "#DE8A2C", "#C8322B"]
for k, wy in enumerate(R["women"]["years"]):
    S, seg = stages_xy("women", [wy["year"]]); ax.add_collection(LineCollection(seg, colors=WC[k], linewidths=2.4, zorder=3 + k, label=f"{wy['year']}: {wy['start']} to {wy['end']}"))
ax.legend(loc="upper center", bbox_to_anchor=(.5, -.01), ncol=2, frameon=False, fontsize=9)
both(fig, "women", blog=False)

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.5, .02, .48, .96]); basemap(ax, ext=ext_ll(-5.0, 9.6, 41.6, 51.3)); draw_all(ax, lw=.45, alpha=.45, dots=False)
S, seg = stages_xy("men", [1926]); ax.add_collection(LineCollection(seg, colors=FG, linewidths=4.2, zorder=6)); ax.add_collection(LineCollection(seg, colors=YELLOW, linewidths=2.6, zorder=7))
fig.text(.04, .88, "Every", fontproperties=DISP, fontsize=50, color=FG, va="top")
t = fig.text(.04, .72, "Tour de", fontproperties=DISP, fontsize=50, color=FG, va="top", bbox=dict(boxstyle="square,pad=0.08", fc=YELLOW, ec="none"))
fig.text(.04, .56, "France, mapped", fontproperties=DISP, fontsize=50, color=RED, va="top")
fig.text(.04, .36, f"{R['source']['men_stages']:,} stages, {R['source']['first_year']} to {R['source']['last_year']}, start to finish.\nThe 1926 loop in yellow: {R['dist']['longest_km']:,} km, the longest Tour.", fontproperties=SERP, fontsize=15, color=FG, va="top", linespacing=1.4)
fig.text(.04, .05, "maps.tristanhotham.com/tour-de-france", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
