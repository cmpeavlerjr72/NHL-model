"""SL-R1 step 2: build the shot-attribute tables (versioned, data/processed/shot_attribute/).

    build_shot_attribute_tables.py rows      per-attempt rows per season (2021-22..2024-25), all target attempts with
                                             the blocked flag, pre-event stage-1 state, cell / type / class, segments
    build_shot_attribute_tables.py xg        xG_ref per fold (fold-train seasons only, frozen) -> xg_ref_v1_f{1,2}.npy
    build_shot_attribute_tables.py ratings   as-of shot-quality ratings, per fold, grid w {0.5, 0.7, 0.85, 1.0} x
                                             b {300, 1000, 3000} attempts, groups ES / PP / PK -> sq_ratings_v1_f{1,2}
    build_shot_attribute_tables.py arena     as-of arena distance-recording factor (c = ARENA_C pseudo-attempts)
    build_shot_attribute_tables.py all
created_at < puck_drop asserted on every ratings and arena row. The 2025-26 season is sealed (loader).
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
from nhl_sim.shot_attribute.tables import (ATTR_EV_COLS, N_CLASS, asof_arena_distance, asof_sq_ratings,  # noqa: E402
                                           season_attempts, xg_ref_table)
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

OUT = PROCESSED / "shot_attribute"
V = "v1"
SEASONS = [20212022, 20222023, 20232024, 20242025]
FOLDS = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}
FOLD_SEASONS = {1: [20212022, 20222023, 20232024], 2: SEASONS}
GRID_W = (0.5, 0.7, 0.85, 1.0)
GRID_B = (300, 1000, 3000)
ARENA_C = 1200.0     # prior pseudo-attempts on the arena factor (SA-R1 ARENA_C precedent; labelled, not tuned)
RG = ("es", "pp", "pk")
OPP_RG = {0: 0, 1: 2, 2: 1}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def wkey(w, b):
    return f"w{float(w)}_b{int(b)}"


def load_rows(seasons):
    return pd.concat([pd.read_parquet(OUT / f"attempt_attr_{V}_{s}.parquet") for s in seasons], ignore_index=True)


def rows():
    OUT.mkdir(parents=True, exist_ok=True)
    info = {}
    for s in SEASONS:
        t0 = time.time()
        ev = load_events([s], columns=ATTR_EV_COLS)
        r = season_attempts(ev)
        r.to_parquet(OUT / f"attempt_attr_{V}_{s}.parquet", index=False)
        # parity with the stage-3 attempt rows: same attempt count per (game, team, st)
        sa = pd.read_parquet(PROCESSED / "shot_attempt" / f"attempt_rows_v1_{s}.parquet", columns=["game_id", "team", "st", "y"])
        a1 = sa.groupby(["game_id", "team", "st"]).y.sum()
        a1 = a1[a1 > 0]
        a2 = r.groupby(["game_id", "team", "st"]).size()
        j = pd.concat([a1.rename("rows"), a2.rename("attr")], axis=1).fillna(0)
        mism = int((j["rows"] != j["attr"]).sum())
        info[s] = dict(n=len(r), unblocked=int((~r.blocked).sum()), goals=int(r.is_goal.sum()),
                       rebound=float(r.rebound.mean()), rush=float(r.rush.mean()), st_parity_mismatch_cells=mism,
                       secs=round(time.time() - t0, 1))
        print(now(), s, info[s], flush=True)
        if mism:
            raise AssertionError(f"{s}: {mism} (game, team, st) cells differ from the stage-3 attempt rows")
    (OUT / f"rows_info_{V}.json").write_text(json.dumps(info, indent=1))


def xg():
    for f, tr in FOLDS.items():
        r = load_rows(tr)
        x = xg_ref_table(r)
        np.save(OUT / f"xg_ref_{V}_f{f}.npy", x)
        u = r[~r.blocked]
        print(now(), f"fold {f}: train {tr} unblocked {len(u)} goals {int(u.is_goal.sum())}; "
              f"in-sample mean xG {x[u.cls, u.grp].mean():.5f} vs goal rate {u.is_goal.mean():.5f}", flush=True)


def team_games(seasons):
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet",
                         columns=["game_id", "season", "date", "drop", "team_id", "opp_id", "is_home"])
    return tg[tg.season.isin(seasons)].reset_index(drop=True)


def attach_ids(r):
    g = load_games(sorted(r.season.unique()), columns=["game_id", "home_id", "away_id"])
    r = r.merge(g.drop(columns="season"), on="game_id", how="left", validate="many_to_one")
    r["team_id"] = np.where(r.team == 0, r.home_id, r.away_id)
    r["opp_id"] = np.where(r.team == 0, r.away_id, r.home_id)
    return r


def ratings():
    for f, seas in FOLD_SEASONS.items():
        x = np.load(OUT / f"xg_ref_{V}_f{f}.npy")
        r = attach_ids(load_rows(seas))
        u = r[~r.blocked & (r.grp <= 2)].copy()
        u["xg"] = x[u.cls.to_numpy(), u.grp.to_numpy()]
        tg = team_games(seas)
        grid = tg[["game_id", "team_id"]].copy()
        longs = {}
        for gi_, g in enumerate(RG):
            fo = u[u.grp == gi_].groupby(["game_id", "team_id"]).agg(xf=("xg", "sum"), nf=("xg", "size"))
            ag = u[u.grp == OPP_RG[gi_]].groupby(["game_id", "opp_id"]).agg(xa=("xg", "sum"), na=("xg", "size"))
            ag.index = ag.index.set_names(["game_id", "team_id"])
            L = tg.join(fo, on=["game_id", "team_id"]).join(ag, on=["game_id", "team_id"])
            longs[g] = L.fillna({"xf": 0.0, "nf": 0, "xa": 0.0, "na": 0}).sort_values(["date", "game_id"])
        for w, b in itertools.product(GRID_W, GRID_B):
            for g in RG:
                rr = asof_sq_ratings(longs[g], w, b)
                assert_pregame(rr)
                rr = rr.rename(columns={"rf": f"rf_{g}_{wkey(w, b)}", "ra": f"ra_{g}_{wkey(w, b)}"})
                keep = ["game_id", "team_id", f"rf_{g}_{wkey(w, b)}", f"ra_{g}_{wkey(w, b)}"]
                if "created_at" not in grid.columns:
                    keep += ["created_at", "puck_drop"]
                grid = grid.merge(rr[keep], on=["game_id", "team_id"], how="left", validate="one_to_one")
        if grid.drop(columns=["created_at"]).isna().any().any():
            raise ValueError("missing ratings")
        grid.to_parquet(OUT / f"sq_ratings_{V}_f{f}.parquet", index=False)
        k = wkey(0.85, 1000)
        print(now(), f"fold {f}: ratings rows {len(grid)}; SD rf_es {grid[f'rf_es_{k}'].std():.4f} "
              f"ra_es {grid[f'ra_es_{k}'].std():.4f} rf_pp {grid[f'rf_pp_{k}'].std():.4f}", flush=True)


def arena():
    r = attach_ids(load_rows(SEASONS))
    g = load_games(SEASONS, columns=["game_id", "neutral_site", "venue", "game_date_local", "puck_drop_utc"])
    u = r[~r.blocked & (r.grp <= 2)].merge(g.drop(columns="season"), on="game_id", how="left", validate="many_to_one")
    ns = u.neutral_site.astype(bool)
    u["arena"] = np.where(ns, "venue:" + u.venue.astype(str), "team:" + u.home_id.astype(str))
    u["shoot_id"], u["def_id"] = u.team_id, u.opp_id
    u["shooter_road"] = (u.team == 1) | ns
    u["defender_road"] = (u.team == 0) | ns
    u["date"], u["drop"] = u.game_date_local, u.puck_drop_utc
    af = asof_arena_distance(u[["game_id", "season", "date", "drop", "arena", "shoot_id", "def_id", "shooter_road",
                                "defender_road", "d"]], ARENA_C)
    assert_pregame(af)
    af["c"] = ARENA_C
    # games with no unblocked goalies-in attempt (none expected) would be missing: check against the game list
    allg = load_games(SEASONS, columns=["game_id"])
    tgids = set(pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id"]).game_id)
    miss = set(allg.game_id) & tgids - set(af.game_id)
    if miss:
        raise ValueError(f"{len(miss)} games without an arena factor")
    af.to_parquet(OUT / f"arena_dist_{V}.parquet", index=False)
    print(now(), af.groupby(af.game_id // 1000000).arena_f.describe().round(4).to_string(), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["rows", "xg", "ratings", "arena", "all"])
    a = ap.parse_args()
    print(now(), "start", a.stage, flush=True)
    for st in (["rows", "xg", "ratings", "arena"] if a.stage == "all" else [a.stage]):
        {"rows": rows, "xg": xg, "ratings": ratings, "arena": arena}[st]()
    print(now(), "done", a.stage, flush=True)
