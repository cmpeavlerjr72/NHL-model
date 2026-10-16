"""G-R1 rating tables (docs/models/goal/experiments.md G-R1): as-of goalie save ratings and team finishing ratings, every
grid cell, per fold (the expectation is the fold's C0: training cell table + the selected level, step 1).

  goalie   saves above C0 expectation per SOG: sign -1 x shrunk log(goals / C0 expected), b in {1000, 3000, 10000, 30000},
           w in {0.5, 0.7, 0.85}; centre weighted by (season-to-date + last season's) SOG
  team     shooting team's goals above C0 expectation per SOG (home and road pooled), b in {1000, 3000, 10000},
           w in {0.5, 0.7, 0.85}; unweighted centre over teams
created_at < puck_drop asserted (data.asof_oe_ratings). Rows of the fold's seasons only; 2025-26 never read.
-> data/processed/goal/ratings_goalie_v1_f{1,2}.parquet, ratings_team_v1_f{1,2}.parquet
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.goal import data as D  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

RES = Path("results/goal_g_r1")
GRID_G = [(b, w) for b in (1000, 3000, 10000, 30000) for w in (0.5, 0.7, 0.85)]
GRID_T = [(b, w) for b in (1000, 3000, 10000) for w in (0.5, 0.7, 0.85)]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def fold_c0(rows, fold, level_name):
    tr_s, te_s = D.F[fold]
    r = rows[rows.season.isin(tr_s + [te_s])].reset_index(drop=True)
    T = np.load(D.OUT / f"cell_table_f{fold}.npy")
    lv = pd.read_parquet(D.OUT / f"level_v1_f{fold}.parquet")
    lv = lv[lv.construction == level_name]
    return r, D.sigmoid(D.c0_logit(r, T, lv))


def build(rows, fold, level_name):
    r, p = fold_c0(rows, fold, level_name)
    out = {}
    for key, grid, sign, wc, nm in (("goalie_id", GRID_G, -1.0, True, "goalie"), ("team_id", GRID_T, 1.0, False, "team")):
        base = None
        for b, w in grid:
            rt = D.asof_oe_ratings(r, p, key, b, w, sign, wc)
            if base is None:
                base = rt[["game_id", key, "created_at", "puck_drop"]].copy()
            else:
                assert (base.game_id.to_numpy() == rt.game_id.to_numpy()).all()
            base[D.rkey(b, w)] = rt.r.to_numpy()
        assert_pregame(base)
        base.to_parquet(D.OUT / f"ratings_{nm}_v1_f{fold}.parquet", index=False)
        out[nm] = base
        print(now(), f"fold {fold} {nm} ratings {base.shape}", flush=True)
    return out


if __name__ == "__main__":
    print(now(), "start", flush=True)
    rows = pd.read_parquet(RES / "rows_v1.parquet")
    sel = json.loads((RES / "step1.json").read_text())["selected"]
    for fold in (1, 2):
        build(rows, fold, sel)
    print(now(), "done", flush=True)
