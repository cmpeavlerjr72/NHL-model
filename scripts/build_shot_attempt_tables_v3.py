"""SA-R3 (INV-32) tables: the thin-state LC-1 levels for arm A3g-s (docs/models/shot_attempt/experiments.md SA-R3).
`_v2` tables are untouched; PP-for / PK levels stay `_v2`.

    build_shot_attempt_tables_v3.py level   -> league_level_v3_f{1,2}.parquet, profile_v3_f{1,2}.json

Five-group scheme of A3g-s: ES-5v5 (st 0), PP-for, PK, 4v4 (st 3), 3v3 (st 4). This builds the three new group levels
(5v5, 4v4, 3v3), each with its own training-only season-phase profile, by the LC-1 method (D16,
`league_level_lc1.lc1_level`) at the frozen k = 5, K = 2k x the group's previous-season share of team-hours (as SA-R2).

Labelled choices:
  - Profile bins with under 1 team-hour of pooled training exposure (3v3 in the playoffs: regular-season OT only;
    2021-22 has 1 playoff 3v3 attempt in under a minute) get p = 0; otherwise a bin empty in some but not all
    training seasons averages over the seasons that have it.
  - The per-team-game group counts are aggregated from the `_v1` attempt rows (same rows as team_game_v1).
created_at < puck_drop asserted on every level row.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_shot_attempt_tables import FOLDS, OUT, SEASONS, long_frame  # noqa: E402
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.league_level_lc1 import lc1_level  # noqa: E402
from nhl_sim.strength_state.seasonality import BINS, game_bins  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

V3 = "v3"
K_FROZEN = (5,)
MIN_BIN_H = 1.0                             # a profile bin needs >= 1 pooled training team-hour, else p = 0
THIN = {"s5v5": 0, "s44": 3, "s33": 4}      # group name -> team-view strength state


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def thin_long():
    long = long_frame()
    rows = pd.concat([pd.read_parquet(OUT / f"attempt_rows_v1_{s}.parquet",
                                      columns=["game_id", "team", "st", "y", "exposure_s"]) for s in SEASONS])
    for g, st in THIN.items():
        a = rows[rows.st == st].groupby(["game_id", "team"]).agg(**{f"for_{g}": ("y", "sum"),
                                                                    f"min_{g}": ("exposure_s", "sum")})
        a[f"min_{g}"] = a[f"min_{g}"] / 60.0
        long = long.merge(a.reset_index(), on=["game_id", "team"], how="left")
        long[[f"for_{g}", f"min_{g}"]] = long[[f"for_{g}", f"min_{g}"]].fillna(0.0)
    return long


def profile_allow_empty(long, cnt, mins, gbin, train):
    """estimate_profile with empty bins allowed (labelled): mean over the training seasons with exposure in the bin;
    0 where no training season has any."""
    L = long[long.season.isin(train)].assign(bin=lambda d: d.game_id.map(gbin).to_numpy())
    ps = []
    for _, d in L.groupby("season"):
        full = d[cnt].sum() / (d[mins].sum() / 60.0)
        gb = d.groupby("bin").agg(e=(cnt, "sum"), m=(mins, "sum")).reindex(range(len(BINS)))
        x = np.log((gb.e / (gb.m / 60.0)) / full).to_numpy().copy()
        x[~(gb.m.fillna(0).to_numpy() > 0)] = np.nan
        if np.isinf(x).any():
            raise ValueError(f"{cnt}: a bin with exposure but no events")
        ps.append(x)
    P = np.vstack(ps)
    pooled_h = L.groupby("bin")[mins].sum().reindex(range(len(BINS))).fillna(0).to_numpy() / 60.0
    return np.array([np.nanmean(P[:, j]) if pooled_h[j] >= MIN_BIN_H else 0.0 for j in range(P.shape[1])])


def level():
    long = thin_long()
    games = load_games(SEASONS, columns=["game_id", "game_type", "game_date_local"])
    gbin = game_bins(long, games)
    for f, tr in FOLDS.items():
        prof, lv = {}, None
        for g in THIN:
            p = profile_allow_empty(long, f"for_{g}", f"min_{g}", gbin, tr)
            prof[f"level_{g}"] = [float(x) for x in p]
            r = lc1_level(long, gbin, p, K_FROZEN, count_col=f"for_{g}", minutes_col=f"min_{g}",
                          prefix=f"level_{g}", total_minutes_col="minutes")
            assert_pregame(r)
            r = r.rename(columns={"p": f"p_level_{g}", "r_prev": f"r_prev_level_{g}"})
            keep = ["game_id", f"p_level_{g}", f"r_prev_level_{g}"] + [f"level_{g}_k{k}" for k in K_FROZEN]
            lv = r if lv is None else lv.merge(r[keep], on="game_id", validate="one_to_one")
        lv.to_parquet(OUT / f"league_level_{V3}_f{f}.parquet", index=False)
        (OUT / f"profile_{V3}_f{f}.json").write_text(json.dumps(
            {"fold": f, "train_seasons": tr, "bins": BINS, "p": prof,
             "levels": "SA-R3 A3g-s thin-state LC-1 levels (D16 method, k=5): level_<g> = the team's attempts in state "
                       "g / team-hours in g (goalies in), g in s5v5 (st 0), s44 (st 3), s33 (st 4); empty profile "
                       "bins -> 0 (labelled)"}, indent=1))
        print(now(), "fold", f, {k: [round(x, 3) for x in v] for k, v in prof.items()}, flush=True)
        for s in sorted(lv.season.unique()):
            m = lv[lv.season == s]
            print("  ", s, {c: round(float(np.exp(m[c]).mean()), 2) for c in lv.columns if c.endswith("_k5")},
                  {c: round(float(m[c].iloc[0]), 2) for c in lv.columns if c.startswith("r_prev")}, flush=True)


if __name__ == "__main__":
    print(now(), "start level", flush=True)
    level()
    print(now(), "done level", flush=True)
