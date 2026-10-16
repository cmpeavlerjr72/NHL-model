"""SA-R2 (INV-31) tables, `_v2` siblings of the SA-R1 tables (v1 untouched). Attempt rows and team-game aggregates
are unchanged and stay `_v1` (identical content; not re-versioned, labelled).

    build_shot_attempt_tables_v2.py ratings     ratings grid w {0.7, 0.85, 1.0} x b {200, 600, 1800} -> ratings_grid_v2
    build_shot_attempt_tables_v2.py level       LC-1 (D16) per fold: all-state level + ES / PP-for / PK group levels,
                                                k in {5, 15, 50}, each with its own training-only profile
                                                -> league_level_v2_f{1,2}.parquet, profile_v2_f{1,2}.json
    build_shot_attempt_tables_v2.py arena --w W --b B                       -> arena_v2.parquet
created_at < puck_drop asserted on every ratings, level and arena row.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_shot_attempt_tables import ARENA_C, FOLDS, OUT, SEASONS, long_frame, wkey  # noqa: E402
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.league_level_lc1 import lc1_level  # noqa: E402
from nhl_sim.shot_attempt.tables import GROUPS, asof_arena_factor  # noqa: E402
from nhl_sim.strength_state.seasonality import BINS, estimate_profile, game_bins  # noqa: E402
from nhl_sim.strength_state.tables import asof_ratings, assert_pregame  # noqa: E402

V2 = "v2"
GRID_W = (0.7, 0.85, 1.0)
GRID_B = (200, 600, 1800)
KS = (5, 15, 50)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


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
    if grid.drop(columns=["created_at"]).isna().any().any():
        raise ValueError("missing ratings")
    grid.to_parquet(OUT / f"ratings_grid_{V2}.parquet", index=False)


def level():
    long = long_frame()
    games = load_games(SEASONS, columns=["game_id", "game_type", "game_date_local"])
    gbin = game_bins(long, games)
    for f, tr in FOLDS.items():
        prof = {}
        specs = [("level", "att", "minutes", None)] + [(f"level_{g}", f"for_{g}", f"min_{g}", "minutes") for g in GROUPS]
        lv = None
        for prefix, cnt, mins, totc in specs:
            p = estimate_profile(long.assign(taken=long[cnt], minutes=long[mins]), gbin, tr)
            prof[prefix] = [float(x) for x in p]
            r = lc1_level(long, gbin, p, KS, count_col=cnt, minutes_col=mins, prefix=prefix, total_minutes_col=totc)
            assert_pregame(r)
            r = r.rename(columns={"p": f"p_{prefix}", "r_prev": f"r_prev_{prefix}"})
            keep = ["game_id", f"p_{prefix}", f"r_prev_{prefix}"] + [f"{prefix}_k{k}" for k in KS]
            lv = r if lv is None else lv.merge(r[keep], on="game_id", validate="one_to_one")
        lv.to_parquet(OUT / f"league_level_{V2}_f{f}.parquet", index=False)
        (OUT / f"profile_{V2}_f{f}.json").write_text(json.dumps(
            {"fold": f, "train_seasons": tr, "bins": BINS, "p": prof,
             "levels": "LC-1 absolute as-of de-seasonalised log rate per team-hour (D16); level = all attempts / all "
                       "team-hours; level_<g> = the team's attempts in group g / team-hours in g (goalies in)"},
            indent=1))
        print("fold", f, {k: [round(x, 4) for x in v] for k, v in prof.items()})
        for s in sorted(lv.season.unique()):
            m = lv[lv.season == s]
            print("  ", s, {c: round(float(np.exp(m[c]).mean()), 3) for c in lv.columns if c.endswith("_k15")})


def arena(w, b):
    long = long_frame()
    rt = pd.read_parquet(OUT / f"ratings_grid_{V2}.parquet")
    k = wkey(w, b)
    cols = {f"{p}_{g}_{k}": f"{p}_{g}" for p in ("rf", "ra") for g in GROUPS}
    rt = rt[["game_id", "team_id", *cols]].rename(columns=cols)
    games = load_games(SEASONS, columns=["game_id", "home_id", "neutral_site", "venue"])
    af = asof_arena_factor(long, rt, games, ARENA_C)
    assert_pregame(af)
    af["w"], af["b"], af["c"] = w, b, ARENA_C
    af.to_parquet(OUT / f"arena_{V2}.parquet", index=False)
    print(af.arena_f.describe().round(4).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["ratings", "level", "arena"])
    ap.add_argument("--w", type=float)
    ap.add_argument("--b", type=int)
    a = ap.parse_args()
    print(now(), "start", a.stage, flush=True)
    if a.stage == "arena":
        arena(a.w, a.b)
    else:
        {"ratings": ratings, "level": level}[a.stage]()
    print(now(), "done", a.stage, flush=True)
