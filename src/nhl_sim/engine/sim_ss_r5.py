"""SUPERSEDED (SA-R3, INV-32, 2026-10-16): merged into `engine/sim.py` as `simulate(..., per_team_types=True)`; kept
in place only as the parity reference of `tests/engine/test_sim_t2_merge.py`. Do not use for new runs.

Closed-loop strength-state sim (cascade stage 1) over (games x seeds), one second per step, lookup tables only.

Per second, for every alive sim: (1) expire due penalties (`settle`), (2) read the PRE-event state (strength,
score bucket, penalty-differential bucket, minute), (3) draw goals from the goal table, (4) draw coincidental
stoppages and each team's own penalty-taking events from the hazard and type tables, (5) draw OT whistles,
(6) record the second, (7) advance the clock.

Coincidental events: the hazard target counts one coincidental event for EACH team at a coincidental stoppage,
so a coincidental stoppage occurs at rate (lam_h p_c,h + lam_a p_c,a) / 2 (each team's count of the same events,
averaged); each team's own non-coincidental events occur at lam (1 - p_c). This is a consequence of the target
definition, not a tuning constant.
"""
from __future__ import annotations

import numpy as np

from nhl_sim.engine import rng
from nhl_sim.engine.box import DOUBLE, MAJOR, MINOR
from nhl_sim.engine.rules import RuleEra
from nhl_sim.engine.state import GameState

TOI_COLS = ("toi_5v5_s", "toi_pp_home_s", "toi_pp_away_s", "toi_4v4_s", "toi_3v3_s", "toi_5v3_s")
KINDS = (MINOR, DOUBLE, MAJOR)
UNIT_PIM = np.array([2, 4, 5])
SWAP = np.array([0, 2, 1, 3, 4], np.int64)
EQ_ST = {5: 0, 4: 3, 3: 4}


def team_view_state(sk: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sh, sa = sk[:, 0].astype(np.int64), sk[:, 1].astype(np.int64)
    st = np.where(sh > sa, 1, np.where(sh < sa, 2, np.where(sh == 5, 0, np.where(sh == 4, 3, 4))))
    return st, SWAP[st]


class Recorder:
    def __init__(self, n):
        self.toi = np.zeros((n, len(TOI_COLS)), np.int32)
        self.ppo = np.zeros((n, 2), np.int16)
        self.adv = np.zeros((n, 2), bool)
        self.played = np.zeros(n, np.int32)

    def record(self, idx, sk):
        sh, sa = sk[:, 0], sk[:, 1]
        eq = sh == sa
        np.add.at(self.toi[:, 0], idx[eq & (sh == 5)], 1)
        np.add.at(self.toi[:, 1], idx[sh > sa], 1)
        np.add.at(self.toi[:, 2], idx[sh < sa], 1)
        np.add.at(self.toi[:, 3], idx[eq & (sh == 4)], 1)
        np.add.at(self.toi[:, 4], idx[eq & (sh == 3)], 1)
        np.add.at(self.toi[:, 5], idx[((sh == 5) & (sa == 3)) | ((sh == 3) & (sa == 5))], 1)
        adv = np.stack([sh > sa, sa > sh], 1)
        new = adv & ~self.adv[idx]
        self.ppo[idx] += new
        self.adv[idx] = adv
        self.played[idx] += 1


def simulate(tables: dict, game_ids: np.ndarray, game_types: np.ndarray, n_seeds: int, era: RuleEra,
             seed0: int = 0, max_t: int = 3600 + 6 * 1200) -> dict:
    """SS-R5 VARIANT of engine.sim.simulate at HEAD c6fb0a5 (versioned sibling; engine.sim untouched). Only change:
    tables["types"] has shape (G, 2, 6, 5, 4, 4), a per-game per-team penalty-type table (team terms, T2/T3).
    tables: lam (G, 2, M, 5, 5, 5) per hour (games in game_ids order), types (G, 2, 6, 5, 4, 4),
    coinc_smp / coinc_pim arrays, goal_rate (3, 3) per hour, stop_rate_ot per second."""
    G, S = len(game_ids), n_seeds
    N = G * S
    gi = np.repeat(np.arange(G), S)
    seeds = np.tile(np.arange(seed0, seed0 + S), G)
    gid = np.asarray(game_ids, np.int64)[gi]
    gs = GameState(np.asarray(game_types)[gi], era, auto_end=True)
    K = {f: rng.stream_keys(seeds, gid, f) for f in ("goal", "penalty", "penalty_type", "coincidental",
                                                     "stoppage", "shootout_stub")}
    lam = tables["lam"]
    M = lam.shape[2]
    lam_flat = lam.reshape(-1)
    ptyp = tables["types"]
    c_smp, c_pim = tables["coinc_smp"], tables["coinc_pim"]
    goal_rate = np.asarray(tables["goal_rate"]) / 3600.0
    stop_p = 1.0 - np.exp(-tables["stop_rate_ot"])
    rec = Recorder(N)
    pim = np.zeros(N, np.int32)
    n_type = np.zeros((N, 2, 4), np.int16)
    n_coinc_4v4 = np.zeros(N, np.int16)
    while gs.alive.any() and gs.t < max_t:
        t = gs.t
        gs.settle()
        a = np.nonzero(gs.alive)[0]
        sk = gs.skaters()[a]
        sh, sa = sk[:, 0].astype(np.int64), sk[:, 1].astype(np.int64)
        st_h, st_a = team_view_state(sk)
        diff = gs.score[a, 0].astype(np.int64) - gs.score[a, 1]
        sc_h = np.clip(diff, -2, 2) + 2
        pdd = gs.pen_count[a, 0].astype(np.int64) - gs.pen_count[a, 1]
        pd_h = np.clip(pdd, -2, 2) + 2
        minute = min(t // 60, M - 1)
        per = min(gs.period()[0] if t < 3600 else 4, 4) - 1
        g_a = gi[a]

        def lam_of(team, st, sc, pd_):
            return lam_flat[((((g_a * 2 + team) * M + minute) * 5 + st) * 5 + sc) * 5 + pd_].astype(np.float64)

        lh = lam_of(0, st_h, sc_h, pd_h) / 3600.0
        la = lam_of(1, st_a, 4 - sc_h, 4 - pd_h) / 3600.0
        Ph, Pa = ptyp[g_a, 0, st_h, sc_h, per], ptyp[g_a, 1, st_a, 4 - sc_h, per]   # SS-R5: per-game per-team type table
        # goals (stub)
        gh = rng.uniform(K["goal"][a], t, 0) < 1.0 - np.exp(-goal_rate[sh - 3, sa - 3])
        ga = rng.uniform(K["goal"][a], t, 1) < 1.0 - np.exp(-goal_rate[sa - 3, sh - 3])
        gs.goal(a[gh], 0)
        ga &= gs.alive[a]
        gs.goal(a[ga], 1)
        live = gs.alive[a]
        # coincidental stoppages
        r_pair = 0.5 * (lh * Ph[:, 3] + la * Pa[:, 3])
        cp = (rng.uniform(K["coincidental"][a], t, 0) < 1.0 - np.exp(-r_pair)) & live
        # own penalty-taking events
        uh = rng.uniform(K["penalty"][a], t, 0) < 1.0 - np.exp(-lh * (1.0 - Ph[:, 3]))
        ua = rng.uniform(K["penalty"][a], t, 1) < 1.0 - np.exp(-la * (1.0 - Pa[:, 3]))
        uh &= live
        ua &= live
        whistle = cp | uh | ua
        if gs.in_ot():
            whistle |= (rng.uniform(K["stoppage"][a], t, 0) < stop_p) & live
        gs.stoppage(a[whistle])
        if cp.any():
            j = np.nonzero(cp)[0]
            pick = np.minimum((rng.uniform(K["coincidental"][a[j]], t, 1) * len(c_smp)).astype(np.int64),
                              len(c_smp) - 1)
            ex = gs.coincidental(a[j], c_smp[pick])
            n_coinc_4v4[a[j[ex]]] += 1
            pim[a[j]] += c_pim[pick]
            n_type[a[j], 0, 3] += 1
            n_type[a[j], 1, 3] += 1
        for team, hit, P in ((0, uh, Ph), (1, ua, Pa)):
            if not hit.any():
                continue
            j = np.nonzero(hit)[0]
            q = P[j, :3] / P[j, :3].sum(1, keepdims=True)
            u = rng.uniform(K["penalty_type"][a[j]], t, team)
            cls = (u[:, None] > np.cumsum(q, 1)).sum(1)
            cls = np.minimum(cls, 2)
            for c, kind in enumerate(KINDS):
                m = cls == c
                if m.any():
                    gs.penalty(a[j[m]], team, kind)
                    n_type[a[j[m]], team, c] += 1
                    pim[a[j[m]]] += UNIT_PIM[c]
        a2 = a[gs.alive[a]]
        rec.record(a2, gs.skaters()[a2])
        gs.end_second()
    so = gs.end_state == 3
    so_home = rng.uniform(K["shootout_stub"], 0, 0) < 0.5
    return dict(game_idx=gi, seed=seeds, score=gs.score.copy(), end_state=gs.end_state.copy(), so_home_win=so & so_home,
                toi=rec.toi, ppo=rec.ppo, played_s=rec.played, pim=pim, n_type=n_type, pen_count=gs.pen_count.copy(),
                n_minor=gs.box.n_minor.copy(), n_minor_pp_ended=gs.box.n_minor_pp_ended.copy(),
                coinc_4v4=n_coinc_4v4, unfinished=int(gs.alive.sum()))
