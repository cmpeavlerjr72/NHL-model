"""SA-R1 step 1: build the shot-attempt tables (versioned, data/processed/shot_attempt/).

    build_shot_attempt_tables.py rows        attempt rows per season + team-game aggregates + exclusion tally
    build_shot_attempt_tables.py ratings     as-of ratings for the 12-point (w, prior strength) grid, all 3 groups
    build_shot_attempt_tables.py level       training-only season-phase profile + de-seasonalised as-of level, per fold
    build_shot_attempt_tables.py arena --w W --b B   as-of arena recording factor at the frozen ratings grid point

Writes (v1):
  attempt_rows_v1_<season>.parquet   game x team x interval rows (exposure_s, y = attempts, y_goal, y_opp)
  team_game_v1.parquet               per team-game attempts for / against / minutes per group (ES, PP, PK)
  exclusions_v1.json                 penalty-shot and shootout attempts (excluded, tallied), delayed-state seconds
  ratings_grid_v1.parquet            rf_/ra_<group>_w<w>_b<b>: as-of log attempt rates for / against, relative to the
                                     snapshot league mean; created_at < puck_drop asserted
  profile_v1_f{1,2}.json, league_level_v1_f{1,2}.parquet   (SS-R3 method on total attempts per team-hour)
  arena_v1.parquet                   as-of arena factor (c = ARENA_C pseudo-attempts); created_at < puck_drop asserted
"""
import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import PROCESSED, load_events, load_games  # noqa: E402
from nhl_sim.shot_attempt.tables import GROUPS, SA_EV_COLS, asof_arena_factor, season_rows  # noqa: E402
from nhl_sim.strength_state.seasonality import BINS, asof_level_adj, estimate_profile, game_bins  # noqa: E402
from nhl_sim.strength_state.tables import asof_ratings, assert_pregame  # noqa: E402

OUT = PROCESSED / "shot_attempt"
V = "v1"
SEASONS = [20212022, 20222023, 20232024, 20242025]
GRID_W = (0.5, 0.7, 0.85, 1.0)
GRID_B = (600, 1800, 5400)
KS = (15, 50, 150)
FOLDS = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}
ARENA_C = 1200.0   # prior pseudo-attempts (about 10 games of both teams' attempts); labelled, not tuned


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def wkey(w, b):
    return f"w{float(w)}_b{int(b)}"


def long_frame():
    tgm = pd.read_parquet(OUT / f"team_game_{V}.parquet")
    g = load_games(SEASONS, columns=["game_id", "game_date_local", "puck_drop_utc", "home_id", "away_id"])
    d = tgm.merge(g.drop(columns="season"), on="game_id", how="left", validate="many_to_one")
    d["team_id"] = np.where(d.team == 0, d.home_id, d.away_id)
    d["opp_id"] = np.where(d.team == 0, d.away_id, d.home_id)
    d["date"], d["drop"] = d.game_date_local, d.puck_drop_utc
    return d.sort_values(["date", "game_id", "team"]).reset_index(drop=True)


def rows():
    OUT.mkdir(parents=True, exist_ok=True)
    games = load_games(SEASONS)
    tgms, tally = [], {}
    for s in SEASONS:
        t0 = time.time()
        ev = load_events([s], columns=SA_EV_COLS)
        r, tgm, tl, info = season_rows(ev, delayed_fix=True)
        r.to_parquet(OUT / f"attempt_rows_{V}_{s}.parquet", index=False)
        tgms.append(tgm)
        tally[s] = {**tl, **info}
        print(now(), s, f"rows={len(r)} attempts={int(r.y.sum())} goals={int(r.y_goal.sum())} "
              f"expo_h={r.exposure_s.sum() / 7200:.0f} {tally[s]} ({time.time() - t0:.0f}s)", flush=True)
    pd.concat(tgms, ignore_index=True).to_parquet(OUT / f"team_game_{V}.parquet", index=False)
    (OUT / f"exclusions_{V}.json").write_text(json.dumps(tally, indent=1))
    del games


def ratings():
    long = long_frame()
    grid = long[["game_id", "team_id"]].copy()
    for w, b in itertools.product(GRID_W, GRID_B):
        for g in GROUPS:
            lg = long.assign(taken=long[f"for_{g}"], drawn=long[f"against_{g}"], minutes=long[f"min_{g}"])
            r = asof_ratings(lg, w, b)
            assert_pregame(r)
            r = r.rename(columns={"taken_rel": f"rf_{g}_{wkey(w, b)}", "drawn_rel": f"ra_{g}_{wkey(w, b)}"})
            keep = ["game_id", "team_id", f"rf_{g}_{wkey(w, b)}", f"ra_{g}_{wkey(w, b)}"]
            if "created_at" not in grid.columns:
                keep += ["created_at", "puck_drop"]
            grid = grid.merge(r[keep], on=["game_id", "team_id"], how="left", validate="one_to_one")
        print(now(), "ratings", wkey(w, b), flush=True)
    if grid.isna().drop(columns=["created_at"]).any().any():
        raise ValueError("missing ratings")
    grid.to_parquet(OUT / f"ratings_grid_{V}.parquet", index=False)


def level():
    long = long_frame().assign(taken=lambda d: d.att)
    games = load_games(SEASONS, columns=["game_id", "game_type", "game_date_local"])
    gbin = game_bins(long, games)
    for f, tr in FOLDS.items():
        p = estimate_profile(long, gbin, tr)
        lv = asof_level_adj(long, gbin, p, KS)
        assert_pregame(lv)
        lv.to_parquet(OUT / f"league_level_{V}_f{f}.parquet", index=False)
        (OUT / f"profile_{V}_f{f}.json").write_text(json.dumps(
            {"fold": f, "train_seasons": tr, "bins": BINS, "p": [float(x) for x in p],
             "rate": "all shot attempts (target definition) per team-hour, all strength states"}, indent=1))
        print("fold", f, {b: round(float(x), 4) for b, x in zip(BINS, p)})
        for s in sorted(lv.season.unique()):
            m = lv[lv.season == s]
            print("  ", s, {k: round(float(m[f"level_k{k}"].mean()), 4) for k in KS})


def arena(w, b):
    long = long_frame()
    rt = pd.read_parquet(OUT / f"ratings_grid_{V}.parquet")
    k = wkey(w, b)
    cols = {f"{p}_{g}_{k}": f"{p}_{g}" for p in ("rf", "ra") for g in GROUPS}
    rt = rt[["game_id", "team_id", *cols]].rename(columns=cols)
    games = load_games(SEASONS, columns=["game_id", "home_id", "neutral_site", "venue"])
    af = asof_arena_factor(long, rt, games, ARENA_C)
    assert_pregame(af)
    af["w"], af["b"], af["c"] = w, b, ARENA_C
    af.to_parquet(OUT / f"arena_{V}.parquet", index=False)
    s = af.merge(load_games(SEASONS, columns=["game_id", "season"]), on="game_id")
    print(s.groupby("season").arena_f.describe().round(4).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["rows", "ratings", "level", "arena"])
    ap.add_argument("--w", type=float)
    ap.add_argument("--b", type=int)
    a = ap.parse_args()
    print(now(), "start", a.stage, flush=True)
    if a.stage == "arena":
        arena(a.w, a.b)
    else:
        {"rows": rows, "ratings": ratings, "level": level}[a.stage]()
    print(now(), "done", a.stage, flush=True)
