"""Replay real mechanics events (penalties, goals, stoppages) through GameState, one sim per game.

This is the same GameState/PenaltyBox code the closed-loop sim uses; only the event source differs. Output is
the penalty-derived skater timeline per second (post-event state of each second), plus box counters.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.engine.box import DOUBLE, MAJOR, MINOR
from nhl_sim.engine.rules import RuleEra
from nhl_sim.engine.state import GameState

CLS_KIND = {"minor": MINOR, "double": DOUBLE, "major": MAJOR}


def replay(game_ids: np.ndarray, game_types: np.ndarray, end_t: np.ndarray, mech: pd.DataFrame, era: RuleEra,
           expire_first: bool = True):
    """mech: columns game_id, t, so, kind, team, cls, smp (from strength_state.events.mech_events).
    Returns dict(sk=(N, T, 2) int8 skaters per second, n_minor, n_minor_pp_ended, coinc_4v4 count per game)."""
    gidx = {g: i for i, g in enumerate(game_ids)}
    m = mech[mech.game_id.isin(gidx)].copy()
    m["gi"] = m.game_id.map(gidx).astype(np.int64)
    m = m.sort_values(["t", "gi", "so"]).reset_index(drop=True)
    m["rk"] = m.groupby(["t", "gi"]).cumcount()
    T = int(end_t.max())
    N = len(game_ids)
    gs = GameState(game_types, era, auto_end=False)
    sk = np.zeros((N, T, 2), np.int8)
    tt = m.t.to_numpy()
    starts = np.searchsorted(tt, np.arange(T + 1))
    gi_all, kind_all, team_all = m.gi.to_numpy(), m.kind.to_numpy(), m.team.to_numpy()
    cls_all, smp_all, rank_all = m.cls.to_numpy(), m.smp.to_numpy(), m["rk"].to_numpy()
    who_all = m.who.to_numpy().astype(np.int64)
    c44 = np.zeros(N, np.int32)
    for t in range(T):
        a, b = starts[t], starts[t + 1]
        gs.alive = t < end_t
        if expire_first:
            gs.settle()
        if b > a:
            for r in range(int(rank_all[a:b].max()) + 1):
                sel = np.arange(a, b)[rank_all[a:b] == r]
                kd = kind_all[sel]
                for kname in ("goal", "pen", "coinc", "stop"):
                    s2 = sel[kd == kname]
                    if s2.size == 0:
                        continue
                    idx = gi_all[s2]
                    if kname == "goal":
                        gs.goal(idx, team_all[s2])
                    elif kname == "stop":
                        gs.stoppage(idx)
                    elif kname == "coinc":
                        ex = gs.coincidental(idx, smp_all[s2].astype(bool))
                        np.add.at(c44, idx[ex], 1)
                    else:
                        for c, k in CLS_KIND.items():
                            s3 = s2[cls_all[s2] == c]
                            if s3.size:
                                gs.penalty(gi_all[s3], team_all[s3], k, who=who_all[s3])
        gs.settle()
        sk[:, t] = gs.skaters()
        gs.end_second()
    return dict(sk=sk, n_minor=gs.box.n_minor.copy(), n_minor_pp_ended=gs.box.n_minor_pp_ended.copy(), coinc_4v4=c44)
