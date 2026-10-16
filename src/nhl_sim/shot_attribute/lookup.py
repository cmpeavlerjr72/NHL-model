"""Engine lookup for the stage-4 shot-attribute arm (no live model calls in the sim loop; L4).

attr_table -> (cdf float32 (G, 2, NI, 3, 7, 78), interval_of_minute int64 (100,)): the cumulative joint (cell x type)
distribution for every (game, team, clock interval, rating group ES / PP-for / PK, team-view pre-event score bucket).
It is built by evaluating the fitted arm on synthetic rows that carry the game's real as-of features through the SAME
`models.attach_features` used in training (ratings, b2b, arena factor), so the served distribution is the trained one
by construction. EN groups are unreachable in the sim until the stage-8 goalie-pull model exists.

Clock intervals: L0-L2 depend on the clock only through the period type, so NI = 2 (regulation minutes 0-59, OT
60+). L3 also uses the game minute and the period: its intervals are cut at every split threshold the booster uses
on `clock` and at the period boundaries (20, 40, 60), so every minute in an interval gets the identical prediction.
Minutes >= 100 (long playoff OT) reuse minute 99, as the engine clamps (stage-3 convention).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attribute import models as M
from nhl_sim.shot_attribute.tables import N_CLASS

N_MIN = 100


def clock_intervals(arm: str, model) -> tuple[np.ndarray, np.ndarray]:
    """-> (interval_of_minute (N_MIN,), representative minute per interval)."""
    cuts = {59.5}
    if arm.startswith("L3"):
        cuts |= {19.5, 39.5}
        fi = M.LGB_FEATURES.index("clock")
        dump = model.dump_model()

        def walk(nd):
            if "split_index" in nd:
                if nd["split_feature"] == fi:
                    cuts.add(float(nd["threshold"]))
                walk(nd["left_child"])
                walk(nd["right_child"])
        for tr in dump["tree_info"]:
            walk(tr["tree_structure"])
    c = np.array(sorted(cuts))
    minutes = np.arange(N_MIN)
    iv = np.searchsorted(c, minutes, side="left")       # LightGBM: value <= threshold goes left
    _, rep_idx = np.unique(iv, return_index=True)
    iv = np.unique(iv, return_inverse=True)[1]
    return iv.astype(np.int64), minutes[rep_idx]


def attr_table(arm: str, model, games: pd.DataFrame, fold: int, w: float, b: int, chunk: int = 64, predict=None):
    """games: game_id, season (sorted by game_id). Returns (cdf, interval_of_minute). predict: optional callable(rows)
    -> P (n, 78) replacing models.predict_arm (SL-R2 levelled arms; default None keeps SL-R1 behaviour)."""
    games = games.sort_values("game_id").reset_index(drop=True)
    iv, rep = clock_intervals(arm, model)
    NI = len(rep)
    mm, gg, ss = np.meshgrid(rep, np.arange(3), np.arange(7), indexing="ij")
    base = pd.DataFrame({"minute": mm.ravel(), "grp": gg.ravel().astype(np.int8), "sc": ss.ravel().astype(np.int8)})
    B = len(base)
    out = np.zeros((len(games), 2, B, N_CLASS), np.float32)
    for a0 in range(0, len(games), chunk):
        part = games.iloc[a0:a0 + chunk]
        n = len(part) * 2
        big = base.loc[np.tile(np.arange(B), n)].reset_index(drop=True)
        big["game_id"] = np.repeat(np.repeat(part.game_id.to_numpy(), 2), B)
        big["season"] = np.repeat(np.repeat(part.season.to_numpy(), 2), B)
        big["team"] = np.tile(np.repeat(np.array([0, 1], np.int8), B), len(part))
        big["is_home"] = (1 - big.team).astype(np.int8)
        big["t"] = (big.minute * 60).astype(np.int32)
        big["period"] = np.where(big.minute < 60, big.minute // 20 + 1, 4).astype(np.int8)
        big["ptype"] = (big.period == 4).astype(np.int8)
        big["blocked"] = False
        big["cls"] = 0
        big["st"] = np.array([0, 1, 2], np.int8)[big.grp.to_numpy()]
        r = M.attach_features(big, fold, w, b)
        if len(r) != len(big) or not (r.game_id.to_numpy() == big.game_id.to_numpy()).all():
            raise ValueError("feature attach changed the rows")
        P = predict(r) if predict is not None else M.predict_arm("L3" if arm.startswith("L3") else arm, model, r)
        out[a0:a0 + len(part)] = P.reshape(len(part), 2, B, N_CLASS).astype(np.float32)
    cdf = np.cumsum(out.reshape(len(games), 2, NI, 3, 7, N_CLASS).astype(np.float64), -1)
    cdf /= cdf[..., -1:]
    return cdf.astype(np.float32), iv
