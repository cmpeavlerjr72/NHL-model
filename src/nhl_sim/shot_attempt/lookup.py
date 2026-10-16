"""Engine lookup for the stage-3 attempt hazard (no live model calls in the sim loop).

attempt_table -> float32 (G, 2, N_MIN, 5, 7): attempts per hour for every (game, team, game minute, team-view
strength 0..4, team-view pre-event score bucket 0..6). EN states (5, 6) are unreachable until the stage-8
goalie-pull model exists. The table is built by evaluating the fitted arm on synthetic one-hour rows carrying the
game's real as-of features (ratings, b2b, level + profile offset, arena), so the served rate is the trained rate
by construction (L4); `tests/test_shot_attempt_lookup.py` checks it against the offline fold-2 predictions.
Playoff OT minutes >= N_MIN reuse the last minute (the engine clamps the same way).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attempt import models as S
from nhl_sim.shot_attempt.tables import N_SC

N_MIN = 100
N_ST_ENGINE = 5


def _grid():
    m, st, sc = np.meshgrid(np.arange(N_MIN), np.arange(N_ST_ENGINE), np.arange(N_SC), indexing="ij")
    b = pd.DataFrame({"minute": m.ravel(), "st": st.ravel().astype(np.int8), "sc": sc.ravel().astype(np.int8)})
    b["period"] = np.where(b.minute < 60, b.minute // 20 + 1, 4).astype(np.int8)
    b["ptype"] = (b.period == 4).astype(np.int8)
    b["last5"] = ((b.minute >= 55) & (b.minute < 60)).astype(np.int8)
    b["t0"] = (b.minute * 60).astype(np.int32)
    b["exposure_s"] = 3600
    b["y"] = 0
    return b


def attempt_table(arm: str, model, games: pd.DataFrame, fz: dict, fold: int, chunk: int = 48, tv: str = "v1",
                  level: str = "r3") -> np.ndarray:
    """games: game_id, season (sorted by game_id). fz: frozen params (k, w, prior_strength_min). tv / level: as
    `models.attach_features` (SA-R1 defaults; SA-R2 tv="v2", level "lc1" or "lc1g" for the g arms)."""
    games = games.sort_values("game_id").reset_index(drop=True)
    base = _grid()
    B = len(base)
    out = np.zeros((len(games), 2, B), np.float32)
    for a0 in range(0, len(games), chunk):
        part = games.iloc[a0:a0 + chunk]
        n = len(part) * 2
        big = base.loc[np.tile(np.arange(B), n)].reset_index(drop=True)
        big["game_id"] = np.repeat(np.repeat(part.game_id.to_numpy(), 2), B)
        big["season"] = np.repeat(np.repeat(part.season.to_numpy(), 2), B)
        big["team"] = np.tile(np.repeat(np.array([0, 1], np.int8), B), len(part))
        big["is_home"] = (1 - big.team).astype(np.int8)
        r = S.attach_features(big, fz["w"], fz["prior_strength_min"], fz["k"], fold, tv=tv, level=level)
        if len(r) != len(big):
            raise ValueError("feature attach changed the row count")
        mu = S.predict_lgb(model, r) if arm.startswith("A3") else S.predict_glm(model, r)
        out[a0:a0 + len(part)] = np.asarray(mu, np.float32).reshape(len(part), 2, B)
    return out.reshape(len(games), 2, N_MIN, N_ST_ENGINE, N_SC)


def goal_stub(season: int) -> np.ndarray:
    """LABELLED STUB goal model: league goals per attempt by team-view strength 0..4 in one training season."""
    r = S.load_rows([season])
    g = r[r.st <= 4].groupby("st")[["y_goal", "y"]].sum().reindex(range(N_ST_ENGINE))
    if g.isna().any().any() or (g.y == 0).any():
        raise ValueError("goal stub: a reachable state has no attempts")
    return (g.y_goal / g.y).to_numpy(float)
