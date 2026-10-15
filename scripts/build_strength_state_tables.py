"""SS-R1 step 3: build the strength-state tables (versioned, data/processed/strength_state/).

    build_strength_state_tables.py [--seasons 20212022 20222023 20232024 20242025] [--version v1]
    build_strength_state_tables.py --version v2 --delayed-fix --grid-w 0.7 0.85 1.0 --grid-b 1800 5400 --level-k 50 150 450
                                   (SS-R2: delayed-penalty state, extended ratings grid, as-of league level)

Writes:
  hazard_rows_<v>_<season>.parquet  game x team x interval rows (exposure_s, y = penalty-taking events)
  type_rows_<v>.parquet             one row per penalty-taking event (cls in minor/double/major/coincidental)
  team_game_<v>.parquet             per team-game taken / drawn / minutes / rest
  ratings_grid_<v>.parquet          as-of taken/drawn ratings for every (w, prior strength) grid point
  nontarget_tally_<v>.parquet       misconducts / game misconducts / penalty shots per season (not targets)
  coinc_bundles_<v>.parquet         coincidental stoppages (smp flag, PIM) for the engine's composition lookup
  league_level_<v>.parquet          (with --level-k) as-of in-season league level per game for every k
  delayed_windows_<v>.parquet       (with --delayed-fix) one row per delayed-penalty signal window
The created_at < puck_drop check is enforced on every ratings and league-level row before writing.
"""
import argparse
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import PROCESSED, load_events, load_games  # noqa: E402
from nhl_sim.strength_state.league_level import asof_league_level  # noqa: E402
from nhl_sim.strength_state.tables import asof_ratings, assert_pregame, season_rows, team_game_long  # noqa: E402
from nhl_sim.strength_state.timeline import EV_COLS  # noqa: E402

GRID_W = (0.3, 0.5, 0.7)
GRID_B = (200, 600, 1800)
OUT = PROCESSED / "strength_state"


def rest_days(long: pd.DataFrame) -> pd.DataFrame:
    d = long[["game_id", "team_id", "date"]].copy()
    d["date"] = pd.to_datetime(d.date)
    d = d.sort_values(["team_id", "date"])
    d["rest"] = d.groupby("team_id").date.diff().dt.days
    d["b2b"] = (d.rest == 1).astype(np.int8)
    return d[["game_id", "team_id", "rest", "b2b"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=[20212022, 20222023, 20232024, 20242025])
    ap.add_argument("--version", default="v1")
    ap.add_argument("--delayed-fix", action="store_true")
    ap.add_argument("--grid-w", nargs="+", type=float, default=list(GRID_W))
    ap.add_argument("--grid-b", nargs="+", type=int, default=list(GRID_B))
    ap.add_argument("--level-k", nargs="+", type=int, default=[])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    v = a.version
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "start", flush=True)
    games = load_games(a.seasons)
    types, tgms, tallies, coincs, wins = [], [], [], [], []
    for s in a.seasons:
        t0 = time.time()
        ev = load_events([s], columns=EV_COLS)
        rows, ty, tgm, tl = season_rows(ev, delayed_fix=a.delayed_fix)
        if a.delayed_fix:
            wn = tl["delayed_windows"].assign(season=s, game_id=lambda d: tl["games"].game_id.to_numpy()[d.g])
            wins.append(wn)
            print(f"  delayed windows {len(wn)}, goalie-state seconds changed {tl['delayed_changed_s']}", flush=True)
        rows.to_parquet(OUT / f"hazard_rows_{v}_{s}.parquet", index=False)
        types.append(ty)
        tgms.append(tgm)
        tallies.append(tl["tally"])
        c = tl["targets"]
        coincs.append(c[(c.cls == "coincidental") & (c.team == 0)][["game_id", "season", "t", "smp", "pim"]])
        print(time.strftime("%H:%M:%S"), s, f"rows={len(rows)} events={int(rows.y.sum())} "
              f"exposure_h={rows.exposure_s.sum() / 3600 / 2:.0f} ({time.time() - t0:.1f}s)", flush=True)
    ty = pd.concat(types, ignore_index=True)
    ty.to_parquet(OUT / f"type_rows_{v}.parquet", index=False)
    pd.concat(tallies, ignore_index=True).to_parquet(OUT / f"nontarget_tally_{v}.parquet", index=False)
    pd.concat(coincs, ignore_index=True).to_parquet(OUT / f"coinc_bundles_{v}.parquet", index=False)
    tgm = pd.concat(tgms, ignore_index=True)
    long = team_game_long(tgm, games)
    long = long.merge(rest_days(long), on=["game_id", "team_id"], how="left")
    long.to_parquet(OUT / f"team_game_{v}.parquet", index=False)
    grid = None
    if wins:
        pd.concat(wins, ignore_index=True).to_parquet(OUT / f"delayed_windows_{v}.parquet", index=False)
    if a.level_k:
        lv = None
        for k in a.level_k:
            r = asof_league_level(long, k)
            assert_pregame(r)
            r = r.rename(columns={"level": f"level_k{k}"})
            lv = r if lv is None else lv.merge(r[["game_id", f"level_k{k}"]], on="game_id")
        lv.to_parquet(OUT / f"league_level_{v}.parquet", index=False)
    for w, b in itertools.product(a.grid_w, a.grid_b):
        r = asof_ratings(long, w, b)
        assert_pregame(r)
        r = r.rename(columns={"taken_rel": f"taken_w{w}_b{b}", "drawn_rel": f"drawn_w{w}_b{b}"})
        if grid is None:
            grid = r
        else:
            grid = grid.merge(r[["game_id", "team_id", f"taken_w{w}_b{b}", f"drawn_w{w}_b{b}"]],
                              on=["game_id", "team_id"])
    grid.to_parquet(OUT / f"ratings_grid_{v}.parquet", index=False)
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "done; type rows", len(ty), ty.cls.value_counts().to_dict(), flush=True)


if __name__ == "__main__":
    main()
