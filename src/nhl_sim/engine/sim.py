"""Closed-loop strength-state sim (cascade stage 1) over (games x seeds), one second per step, lookup tables only.

Per second, for every alive sim: (1) expire due penalties (`settle`), (2) read the PRE-event state (strength,
score bucket, penalty-differential bucket, minute), (3) draw goals from the goal table, (4) draw coincidental
stoppages and each team's own penalty-taking events from the hazard and type tables, (5) draw OT whistles,
(6) record the second, (7) advance the clock.

Coincidental events: the hazard target counts one coincidental event for EACH team at a coincidental stoppage,
so a coincidental stoppage occurs at rate (lam_h p_c,h + lam_a p_c,a) / 2 (each team's count of the same events,
averaged); each team's own non-coincidental events occur at lam (1 - p_c). This is a consequence of the target
definition, not a tuning constant.

Stage-3 variant (default off; on when `tables` holds "att_lam", SA-R1): goals are no longer drawn from the stub goal
table. Each second each team draws its shot-attempt count from att_lam[g, team, minute, st, sc7] (attempts per hour;
st = team-view strength 0..4, sc7 = team-view pre-event score bucket <=-3..>=+3), k in {0, 1, 2} by the Poisson
inverse CDF (P(k >= 3) ~ lam^3 / 6 per second, about 1e-6, is folded into k = 2), and each attempt is a goal with
probability p_goal[st] (a LABELLED STUB goal model until stage 6). Attempt counts by state / score bucket and the
pre-event exposure by (home-view st, sc7) are recorded.

Per-team penalty-type variant (default off; `per_team_types=True`, SA-R3 merge of the SS-R5 T2 engine sibling
`sim_ss_r5.py`, which is superseded): tables["types"] has shape (G, 2, 6, 5, 4, 4), a per-game per-team type table
(team terms, T2), indexed [game, team, st, sc, period]. Off: the shared (6, 5, 4, 4) table, as before. Parity tests
`tests/engine/test_sim_t2_merge.py`: off is bit-identical to the pre-merge engine, on to `sim_ss_r5.simulate`.

Stage-4 shot-attribute variant (default off; on when `tables` holds "attr", SL-R1, step-0 blocks rule (b)): each
attempt of the stage-3 draw is first blocked with probability attr["p_block"][st] (a LABELLED STUB for the stage-5
block model: the empirical block rate by strength group); an unblocked attempt draws its joint (location cell x
type) class from attr["cdf"][g, team, interval_of_minute[minute], rating group, sc7] (78 classes, the stage-4 arm's
lookup), and is a goal with probability attr["xg"][class, rating group] (xG_ref, a LABELLED STUB goal model replacing
p_goal; stage 5 / 6 do not exist yet, so SOG / miss / goal is one draw). Records unblocked attempts, summed xG_ref,
goals, and cell / type counts by (team, team-view state). Parity test `tests/engine/test_sim_attr_flag.py`: with the
variant off the engine is bit-identical to the pre-change file (b024504).

Levelled stage-4 lookup (SL-R3, D24; on when attr holds "pdf" and "era_mult" instead of "cdf"): the arm's UNLEVELLED
joint probabilities pdf[g, team, interval, rating group, sc7] are multiplied by era_mult[rec_era, rating group, class]
= exp(log(s_E[era, level group, cell] / s_train[level group, cell])) (the SL-R2 level E as a per-cell factor), the
row is renormalised (cumsum / last) and the class drawn as before. rec_era is read from GameState (`season=` passed to
simulate; rules.recording_era, boundary 2023-24 fixed, not fitted). Exact for L0m and for an init_score booster (L3b),
whose levelled softmax is the unlevelled one times exp(offset), renormalised. With a unit era_mult and pdf = the
increments of a float64 cdf it reproduces the cdf path bit for bit (tests/engine/test_sim_era_flag.py).

D32 STAND-INS (two default-off flags inside tables["attr"]; flat baselines, NOT adoptable, labelled STAND-IN):
  - block B0 (on when attr holds "p_block_game"): the block probability is p_block_game[g, rating group of the
    team-view state, period type] (G, 3, 2) instead of the empirical p_block[st] stub: the SB-R1 B0 fit (one-hot
    strength group x period type) with the M1 K500 as-of league block-share level as a logit offset (D27), evaluated
    per game by engine.standins.block_b0_table. 4v4 / 3v3 take the ES group, as in B0's training rows.
  - stage-4 L0s (on when attr holds "state_pdf"): the unblocked attempt's class row is state_pdf[st, period type]
    (7 team-view states x 2 x 78: the SL-R4 L0s table; EN rows 5 / 6 carry the baseline and are unreachable until the
    stage-8 goalie pull), levelled by era_mult[rec_era, rating group] exactly as the SL-R3 pdf path (L0s is served
    levelled only; era_mult is required). No game / team / score / clock dependence: flat by construction (D24).
  Period type = (t >= 3600), the attempt tables' ptype (period 4+). Each flag requires a label in attr["stand_in"]
  ({"block": ..., "attr": ...}); whenever attr carries stand_in labels the output carries "stand_in" (an array of
  "component: label" strings), so no consumer can mistake stand-in output for an adopted model's. With both flags off
  and no labels, the output is bit-identical to 3ce7112 (tests/engine/test_sim_standins.py).
"""
from __future__ import annotations

import numpy as np

from nhl_sim.engine import rng
from nhl_sim.engine.box import DOUBLE, MAJOR, MINOR
from nhl_sim.engine.rules import RECORDING_ERAS, RuleEra
from nhl_sim.engine.state import GameState

TOI_COLS = ("toi_5v5_s", "toi_pp_home_s", "toi_pp_away_s", "toi_4v4_s", "toi_3v3_s", "toi_5v3_s")
KINDS = (MINOR, DOUBLE, MAJOR)
UNIT_PIM = np.array([2, 4, 5])
SWAP = np.array([0, 2, 1, 3, 4], np.int64)
EQ_ST = {5: 0, 4: 3, 3: 4}
ST_RGRP = np.array([0, 1, 2, 0, 0], np.int64)      # team-view state 0..4 -> rating group ES / PP-for / PK


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
             seed0: int = 0, max_t: int = 3600 + 6 * 1200, per_team_types: bool = False, seasons=None) -> dict:
    """tables: lam (G, 2, M, 5, 5, 5) per hour (games in game_ids order), types (6, 5, 4, 4) or, with
    per_team_types=True, (G, 2, 6, 5, 4, 4), coinc_smp / coinc_pim arrays, goal_rate (3, 3) per hour, stop_rate_ot per
    second. seasons: optional (G,) season ids; sets GameState.rec_era (needed by the levelled stage-4 lookup only)."""
    G, S = len(game_ids), n_seeds
    N = G * S
    gi = np.repeat(np.arange(G), S)
    seeds = np.tile(np.arange(seed0, seed0 + S), G)
    gid = np.asarray(game_ids, np.int64)[gi]
    gs = GameState(np.asarray(game_types)[gi], era, auto_end=True,
                   season=None if seasons is None else np.asarray(seasons, np.int64)[gi])
    K = {f: rng.stream_keys(seeds, gid, f) for f in ("goal", "penalty", "penalty_type", "coincidental",
                                                     "stoppage", "shootout_stub")}
    att = tables.get("att_lam")
    if att is not None:
        K["attempt"] = rng.stream_keys(seeds, gid, "attempt")
        K["attempt_goal"] = rng.stream_keys(seeds, gid, "attempt_goal")
        Ma = att.shape[2]
        att_flat = att.reshape(-1)
        p_goal = np.asarray(tables["p_goal"], np.float64)
        att_st = np.zeros((N, 2, 5), np.int32)
        att_sc = np.zeros((N, 2, 7), np.int32)
        toi_st_sc = np.zeros((N, 5, 7), np.int32)
    attr = tables.get("attr")
    AS = None
    if attr is not None:
        if att is None:
            raise ValueError("the shot-attribute variant needs the stage-3 attempt table (att_lam)")
        levelled = "era_mult" in attr
        labels = dict(attr.get("stand_in", {}))
        state_pdf = attr.get("state_pdf")
        if state_pdf is not None:                       # D32 stand-in: stage-4 L0s by (team-view state, period type)
            state_pdf = np.asarray(state_pdf, np.float64)
            if state_pdf.ndim != 3 or state_pdf.shape[:2] != (7, 2) or not (state_pdf > 0).all():
                raise ValueError(f"attr state_pdf must be a positive (7, 2, C) table, got {state_pdf.shape}")
            if not levelled:
                raise ValueError("the L0s stand-in is served levelled: attr needs era_mult")
            if "attr" not in labels:
                raise ValueError("attr state_pdf is a STAND-IN: attr['stand_in'] must label it ('attr')")
            cdf = None
            nc = state_pdf.shape[2]
        else:
            cdf = attr["pdf"] if levelled else attr["cdf"]
            if cdf.ndim != 6 or cdf.shape[:2] != (G, 2) or cdf.shape[3:] != (3, 7, cdf.shape[5]):
                raise ValueError(f"attr cdf / pdf must be (G, 2, NI, 3, 7, C), got {cdf.shape}")
            nc = cdf.shape[5]
        K["attempt_block"] = rng.stream_keys(seeds, gid, "attempt_block")
        K["attempt_attr"] = rng.stream_keys(seeds, gid, "attempt_attr")
        AS = dict(cdf=cdf, imap=np.asarray(attr.get("interval_of_minute", np.zeros(100)), np.int64),
                  p_block=np.asarray(attr["p_block"], float) if "p_block" in attr else None,
                  xg=np.asarray(attr["xg"], float), n_type=int(attr["n_type"]), n_cell=nc // int(attr["n_type"]),
                  fen=np.zeros((N, 2, 5), np.int32), xg_sum=np.zeros((N, 2, 5)), goals=np.zeros((N, 2, 5), np.int32))
        if state_pdf is not None:
            AS["state_pdf"] = state_pdf
        if "p_block_game" in attr:                      # D32 stand-in: block B0 per (game, rating group, period type)
            pbg = np.asarray(attr["p_block_game"], np.float64)
            if pbg.shape != (G, 3, 2) or not ((pbg >= 0) & (pbg <= 1)).all():
                raise ValueError(f"attr p_block_game must be (G, 3, 2) probabilities, got {pbg.shape}")
            if "block" not in labels:
                raise ValueError("attr p_block_game is a STAND-IN: attr['stand_in'] must label it ('block')")
            AS["p_block_game"] = pbg
        elif AS["p_block"] is None:
            raise ValueError("attr needs p_block (empirical stub) or p_block_game (B0 stand-in)")
        if labels:
            AS["stand_in"] = np.array([f"{k}: {labels[k]}" for k in sorted(labels)])
        if levelled:
            em = np.asarray(attr["era_mult"], np.float64)
            if gs.rec_era is None:
                raise ValueError("the levelled stage-4 lookup reads GameState.rec_era: pass seasons= to simulate")
            if em.shape != (max(RECORDING_ERAS) + 1, 3, nc) or not np.isfinite(em[list(RECORDING_ERAS)]).all():
                raise ValueError(f"era_mult must be ({max(RECORDING_ERAS) + 1}, 3, {nc}) finite on eras {RECORDING_ERAS}")
            AS.update(era_mult=em, rec_era=gs.rec_era.astype(np.int64))
        AS["cell"] = np.zeros((N, 2, 5, AS["n_cell"]), np.int32)
        AS["type"] = np.zeros((N, 2, 5, AS["n_type"]), np.int32)
    lam = tables["lam"]
    M = lam.shape[2]
    lam_flat = lam.reshape(-1)
    ptyp = tables["types"]
    if per_team_types and (ptyp.ndim != 6 or ptyp.shape[:2] != (G, 2)):
        raise ValueError(f"per_team_types needs a (G, 2, 6, 5, 4, 4) type table, got {ptyp.shape}")
    if not per_team_types and ptyp.ndim != 4:
        raise ValueError(f"shared type table must be (6, 5, 4, 4), got {ptyp.shape} (per_team_types is off)")
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
        if per_team_types:
            Ph, Pa = ptyp[g_a, 0, st_h, sc_h, per], ptyp[g_a, 1, st_a, 4 - sc_h, per]
        else:
            Ph, Pa = ptyp[st_h, sc_h, per], ptyp[st_a, 4 - sc_h, per]
        if att is None:
            # goals (stub)
            gh = rng.uniform(K["goal"][a], t, 0) < 1.0 - np.exp(-goal_rate[sh - 3, sa - 3])
            ga = rng.uniform(K["goal"][a], t, 1) < 1.0 - np.exp(-goal_rate[sa - 3, sh - 3])
            gs.goal(a[gh], 0)
            ga &= gs.alive[a]
            gs.goal(a[ga], 1)
        else:
            _attempts_second(gs, a, t, g_a, st_h, st_a, diff, K, att_flat, Ma, p_goal, att_st, att_sc, toi_st_sc, AS)
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
    extra = {} if att is None else dict(att_st=att_st, att_sc=att_sc, toi_st_sc=toi_st_sc)
    if AS is not None:
        extra.update(attr_fen=AS["fen"], attr_xg=AS["xg_sum"], attr_goals=AS["goals"], attr_cell=AS["cell"],
                     attr_type=AS["type"])
        if "stand_in" in AS:
            extra["stand_in"] = AS["stand_in"]
    return dict(**extra, game_idx=gi, seed=seeds, score=gs.score.copy(), end_state=gs.end_state.copy(), so_home_win=so & so_home,
                toi=rec.toi, ppo=rec.ppo, played_s=rec.played, pim=pim, n_type=n_type, pen_count=gs.pen_count.copy(),
                n_minor=gs.box.n_minor.copy(), n_minor_pp_ended=gs.box.n_minor_pp_ended.copy(),
                coinc_4v4=n_coinc_4v4, unfinished=int(gs.alive.sum()))


def poisson_k(u: np.ndarray, lam: np.ndarray) -> np.ndarray:
    """Poisson(lam) count in {0, 1, 2} from one uniform by the inverse CDF (k >= 3 folded into 2)."""
    p0 = np.exp(-lam)
    return (u >= p0).astype(np.int64) + (u >= p0 * (1.0 + lam)).astype(np.int64)


def _attempts_second(gs, a, t, g_a, st_h, st_a, diff, K, att_flat, Ma, p_goal, att_st, att_sc, toi_st_sc, AS=None):
    """Stage-3 attempt draws for the alive sims `a` at second t (pre-event state), then the goals they produce
    (stub p_goal by state; or, with the stage-4 variant AS, block stub -> attribute class -> xG_ref goal draw)."""
    sc_h = np.clip(diff, -3, 3) + 3
    sc_a = 6 - sc_h
    m = min(t // 60, Ma - 1)

    def lam_of(team, st, sc):
        return att_flat[(((g_a * 2 + team) * Ma + m) * 5 + st) * 7 + sc].astype(np.float64) / 3600.0

    kh = poisson_k(rng.uniform(K["attempt"][a], t, 0), lam_of(0, st_h, sc_h))
    ka = poisson_k(rng.uniform(K["attempt"][a], t, 1), lam_of(1, st_a, sc_a))
    np.add.at(toi_st_sc, (a, st_h, sc_h), 1)
    np.add.at(att_st, (a, 0, st_h), kh)
    np.add.at(att_st, (a, 1, st_a), ka)
    np.add.at(att_sc, (a, 0, sc_h), kh)
    np.add.at(att_sc, (a, 1, sc_a), ka)
    ng = []
    for team, k, st, sc in ((0, kh, st_h, sc_h), (1, ka, st_a, sc_a)):
        g = np.zeros(len(a), np.int64)
        if AS is None:
            for j in range(2):
                g += (k > j) & (rng.uniform(K["attempt_goal"][a], t, 2 * team + j) < p_goal[st])
        else:
            for j in range(2):
                i = np.nonzero(k > j)[0]
                if i.size:
                    g[i] += _attribute_draw(AS, a[i], t, g_a[i], team, j, st[i], sc[i], m, K)
        ng.append(g)
    for team in (0, 1):
        for j in (1, 2):
            hit = (ng[team] >= j) & gs.alive[a]
            gs.goal(a[hit], team)


def _attribute_draw(AS, ai, t, gi, team, j, st, sc, m, K):
    """Stage-4 variant, for attempt j of `team` in sims ai: block stub, then joint class, then the xG_ref goal draw.
    Returns goals (0/1) per sim; records unblocked counts, xG_ref, goals, cell and type by team-view state."""
    kk = 2 * team + j
    unb = rng.uniform(K["attempt_block"][ai], t, kk) >= block_prob(AS, gi, st, t)
    if not unb.any():
        return np.zeros(len(ai), np.int64)
    ai, gi, st, sc = ai[unb], gi[unb], st[unb], sc[unb]
    rg = ST_RGRP[st]
    row = class_cdf(AS, ai, gi, team, st, sc, m, t)
    u = rng.uniform(K["attempt_attr"][ai], t, kk)
    cls = np.minimum((row <= u[:, None]).sum(1), row.shape[1] - 1)
    x = AS["xg"][cls, rg]
    goal = rng.uniform(K["attempt_goal"][ai], t, kk) < x
    np.add.at(AS["fen"], (ai, team, st), 1)
    np.add.at(AS["xg_sum"], (ai, team, st), x)
    np.add.at(AS["goals"], (ai, team, st), goal.astype(np.int32))
    np.add.at(AS["cell"], (ai, team, st, cls // AS["n_type"]), 1)
    np.add.at(AS["type"], (ai, team, st, cls % AS["n_type"]), 1)
    out = np.zeros(len(unb), np.int64)
    out[np.nonzero(unb)[0]] = goal
    return out


def block_prob(AS, gi, st, t):
    """Served block probability per attempt (game index gi, team-view state st, game second t): the B0 stand-in
    p_block_game[g, rating group, period type] when on, else the empirical stub p_block[st]."""
    if "p_block_game" in AS:
        return AS["p_block_game"][gi, ST_RGRP[st], int(t >= 3600)]
    return AS["p_block"][st]


def class_cdf(AS, ai, gi, team, st, sc, m, t):
    """Served cumulative class row per unblocked attempt (the row the engine draws the class from): the L0s stand-in
    state_pdf[st, period type] or the arm lookup cdf / pdf[g, team, interval, rating group, sc]; levelled by
    era_mult[rec_era, rating group] and renormalised when era_mult is present."""
    rg = ST_RGRP[st]
    if "state_pdf" in AS:
        row = AS["state_pdf"][st, int(t >= 3600)]
    else:
        row = AS["cdf"][gi, team, AS["imap"][m], rg, sc]
    if "era_mult" in AS:
        row = np.cumsum(row.astype(np.float64) * AS["era_mult"][AS["rec_era"][ai], rg], 1)
        row /= row[:, -1:]
    return row
