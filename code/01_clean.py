"""Read LeTourDataSet's stage and rider files for the men's Tour (1903 to 2026) and the Tour de France Femmes (2022 to
2026) and clean them.

Stages. One row per stage in the source, in race order. Three kinds of row are tidied:
  * shared stage wins: four stages (1924 stage 3, 1934 stage 5, 1937 stage 17.2, 1938 stage 21) appear twice with the
    same start and finish and two different winners. They are joint wins, so each becomes one stage with both winners.
  * 2022: the opening time trial in Copenhagen appears twice, followed by two rows whose start and finish are both
    "Transfert" (the transfer day after the Danish stages). The repeat and the two transfer rows are dropped.
  * stage numbers are kept as the source gives them (0 = prologue; 1.1, 1.2 = a day split into two half stages), and
    each half stage counts as a stage.
Riders. The final general classification of every edition: the winner (rank 1), time, distance and result type
('time', 'points' for 1905 to 1912 when the Tour was decided on points, 'no-results'). The source has no winner for
1999 to 2005: those seven titles were stripped in 2012 and not given to anyone else, and the file follows that
official record. Average winning speed is distance divided by the winner's time, only where the result is a time."""
import pandas as pd, numpy as np
from common import *

chk = {}


def stages(path, race):
    s = pd.read_csv(path, dtype={"Stages": str})
    chk[f"{race}_rows"] = len(s)
    s["order"] = range(len(s))
    s["Winner of stage"] = s["Winner of stage"].fillna("")
    # joint winners: same year, stage, start and finish
    key = ["Year", "Stages", "Start", "End"]
    tr = (s.Start == "Transfert") | (s.End == "Transfert")
    chk[f"{race}_transfer_rows"] = int(tr.sum())
    s = s[~tr]
    dup = s[s.duplicated(key, keep=False)]
    joint, repeat = [], []
    for k, g in dup.groupby(key, sort=False):
        if g["Winner of stage"].nunique() > 1: joint.append(list(map(str, k)))
        else: repeat.append(list(map(str, k)))
    chk[f"{race}_joint"] = joint; chk[f"{race}_repeat"] = repeat
    agg = {c: "first" for c in s.columns if c not in key}
    agg["Winner of stage"] = lambda v: " and ".join(dict.fromkeys(v))
    s = s.groupby(key, sort=False, as_index=False).agg(agg).sort_values("order").reset_index(drop=True)
    s["race"] = race
    s["stage"] = s.Stages.astype(str).str.replace(r"\.0$", "", regex=True)
    s["winner"] = s["Winner of stage"].str.replace(r"\s+", " ", regex=True).str.replace(r" \((Tdf \d{4} \*\*\*)\)", "", regex=True).str.strip()
    s["Start"] = s.Start.str.strip(); s["End"] = s.End.str.strip()
    s["dist_total"] = s.TotalTDFDistance.astype(int)
    s["k"] = s.groupby("Year").cumcount()          # order of the stage within its Tour
    return s[["race", "Year", "stage", "k", "Start", "End", "winner", "dist_total"] + (["Yellow Jersey"] if "Yellow Jersey" in s else [])] \
        .rename(columns={"Year": "year", "Start": "start", "End": "end", "Yellow Jersey": "yellow"})


M = stages(f"{RAW}/men/TDF_Stages_History.csv", "men")
W = stages(f"{RAW}/women/TDFF_Stages_History.csv", "women")
assert chk["men_joint"] == [["1924", "3", "Cherbourg-en-Cotentin", "Brest"], ["1934", "5", "Belfort", "Évian-les-Bains"],
                            ["1937", "17.2", "Royan", "Saintes"], ["1938", "21", "Lille", "Paris"]], chk["men_joint"]
assert chk["men_repeat"] == [["2022", "1", "Copenhague", "Copenhague"]] and chk["men_transfer_rows"] == 2
assert len(M[M.year == 2022]) == 21 and M.year.nunique() == 113 and W.year.nunique() == 5
ST = pd.concat([M, W], ignore_index=True)
chk["men_stages"] = len(M); chk["women_stages"] = len(W)


def riders(path, race):
    r = pd.read_csv(path)
    w = r[r.Rank.astype(str) == "1"].copy()
    w["race"] = race
    w["speed"] = np.where((w.ResultType == "time") & (w.TotalSeconds > 0), w["Distance (km)"] / (w.TotalSeconds / 3600), np.nan)
    chk[f"{race}_rider_rows"] = len(r); chk[f"{race}_rider_years"] = int(r.Year.nunique())
    chk[f"{race}_finishers"] = {int(y): int(n) for y, n in r.groupby("Year").size().items()}
    return w.rename(columns={"Year": "year", "Rider": "rider", "Team": "team", "Times": "time", "Distance (km)": "dist", "ResultType": "rtype"})[
        ["race", "year", "rider", "team", "time", "dist", "rtype", "TotalSeconds", "speed"]]


WM = riders(f"{RAW}/men/TDF_Riders_History.csv", "men")
WW = riders(f"{RAW}/women/TDFF_Riders_History.csv", "women")
miss = sorted(set(range(1903, 2027)) - set(M.year))
assert miss == [1915, 1916, 1917, 1918, 1940, 1941, 1942, 1943, 1944, 1945, 1946], miss
nowin = sorted(set(M.year) - set(WM.year))
assert nowin == list(range(1999, 2006)), nowin
chk["no_winner_years"] = nowin
WIN = pd.concat([WM, WW], ignore_index=True)
unk = sorted(set(WIN.rider) - set(WINNER_NAT))
assert not unk, unk
WIN["nation"] = WIN.rider.map(WINNER_NAT)
# national team years: the team column names the nation, check it against the table
nt = WIN[WIN.team.str.upper().isin(TEAM_NATION)]
bad = nt[nt.team.str.upper().map(TEAM_NATION) != nt.nation]
assert bad.empty, bad
chk["nation_checked_by_team"] = len(nt)
ST.to_pickle(f"{WORK}/stages.pkl"); WIN.to_pickle(f"{WORK}/winners.pkl")
jsave(chk, f"{WORK}/checks.json", indent=1)
print("stages", len(M), "men,", len(W), "women; winners", len(WIN), "; nation checked by team", len(nt))
