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

INV-60 / INV-57 / INV-54 (Lane E2, 2026-10-21; every flag default off, flag-off bit-identical to 7fac157,
tests/engine/test_sim_c1s.py):
  - per-game stage-4 level (INV-57; on when attr holds "game_mult" instead of "era_mult"): game_mult[g, rating group,
    class] = s_asof[g, level group, cell] / s_train[level group, cell] (the M1 K500 as-of mix level of SL-R6 D35), applied
    to the L0s state_pdf row (or the pdf row) exactly as era_mult: multiply, cumsum, renormalise. No rec_era needed.
  - block B0 with own 4v4 / 3v3 groups (INV-54; on when p_block_game has shape (G, 5, 2)): indexed by the team-view
    state st 0..4 directly (5v5 / PP / PK as before; 4v4 and 3v3 their own M1 K500 level and intercept). A (G, 3, 2)
    table is served as before (rating group of st).
  - miss S0t STAND-IN (stage 5b; on when attr holds "p_miss_game" (G, 3, 2, C) = [game, rating group, period type,
    class]): after the class draw an unblocked attempt is a miss with that probability (stream "attempt_miss"), else a
    shot on goal. Needs the label attr["stand_in"]["miss"].
  - goal C1s (stage 6, CONFIRMED-INCUMBENT provisional, D40; on when attr holds "goal", which requires the miss flag and
    vice versa): a shot on goal is a goal with sigmoid(cls_logit[class, st] + game_logit[g, team, st] + sc_logit[sc7])
    (stream "attempt_goal"), replacing the xG_ref stub draw. game_logit bakes in the level M1 K500, the C1s strength-group
    / home / rest / arena coefficients, team finishing at its fixed scale and s_t(date) x z(goalie) for the game's starting
    goalie (attr["goal"]["goalie_id"][g, team] = the goalie facing `team`'s shots): ORACLE GOALIE (box-score starter,
    D8); no in-game goalie change (stage 8). The output carries "goal_model", "oracle_goalie", "goalie_against" and
    attr_sog / attr_gprob (shots on goal and summed C1s probability by (team, team-view state)); xG_ref is still summed
    per unblocked attempt (attr_xg) for G3.

SL-R7 L1x-as (Lane A7, 2026-10-21; default off, on when attr holds "l1x", which requires the L0s state_pdf and the
per-game level game_mult; replaces the L0s STAND-IN, so attr["stand_in"] must NOT label "attr"): the unblocked
attempt's class row is softmax(log state_pdf[st, ptype] + log game_mult[g, rating group] + l1x["game_logit"][g, team,
rating group] + l1x["sc_logit"][ptype, sc7]) (cumsum / last). game_logit bakes in the frozen SL-R6 L1x-ot0 home and
rest terms and the as-of rating tilt (s_for,t(date) zf + s_against,t(date) za) x c of the game's teams; sc_logit holds
the centred score terms, zero on OT rows (ptype 1, D38). Tables: shot_attribute.serve_l1xas. The output carries
"attr_model". Flag off: bit-identical (tests/engine/test_sim_l1xas.py).

DEFAULT TABLE SET (INV-63, Lane E3, 2026-10-21, D40-D43): simulate() itself is unchanged (every variant above is still a
default-off flag keyed on tables / tables["attr"], so absent keys give the old paths bit for bit). What changed is the
table builder the closed-loop runners call with no flags: nhl_sim.engine.defaults.default_attr(games) serves stage 4
L1x-as (attr["l1x"]), block B0 and miss S0t as labelled STAND-INS, goal C1s with the ORACLE GOALIE; stage 1 H3''-LC2 + T2
and stage 3 A3g-c are the other tables keys. Its output carries stand_in = [block, miss] (no "attr" label), attr_model,
goal_model, oracle_goalie. The L0s stand-in (defaults.l0s_attr) and the xG_ref goal stub (attr["xg"] without
attr["goal"]) stay behind their explicit flags. tests/engine/test_sim_defaults.py.

BLOCK B1a-as (SB-R5, INV-64, Lane B5, 2026-10-21; default off, on when attr holds "block_b1aas" = dict(game_logit
(G, 2, 5), sc_logit (7,), label)): replaces the B0 STAND-IN. The block probability per attempt is
sigmoid(logit p_block_game[g, st, period type] + game_logit[g, shooting team, st] + sc_logit[sc7]) on the (G, 5, 2) B0'
table (INV-54), so attr still carries p_block_game (the B0' base) but attr["stand_in"] must NOT label "block". The
tables are built by nhl_sim.block.serve_b1aas.b1aas_tables from the committed snapshot (block_scale_v1_f2.parquet,
never recomputed). EN states (pull on) keep B0's own EN groups. Output carries "block_model". Flag off: bit-identical
(tests/engine/test_sim_b1aas.py).

GOALIE PULL + EN CASCADE (EG-R1 part A, INV-66, Lane H8a, 2026-10-21; default off, on when `tables` holds "pull", which
needs the stage-3 attempt table, the L0s state_pdf baseline, block B0 (p_block_game), miss S0t and goal C1s): at the
start of each second t in the last 600 s of regulation, before the second's draws, each team trailing before the
second whose goalie is in draws a pull (stream "pull", counter (t, team)) with the served hazard: P1 =
table[deficit 1 / 2 / 3+, (3600 - t - 1) // 10, penalty state none / pk / pp from the penalty-derived skaters,
pulled_before, home] (pull["hazard"]["kind"] == "P1"), or P0's h_first[deficit, penalty-on, t - 3000] / h_repull[t -
last return]. Returns (GameState, deterministic): at a goal against and at the team's own tying goal. While a team's
goalie is out the cascade runs at the team-view states 5 EN-for (pulled team) / 6 EN-against (its opponent): attempts at
pull["en_lam"][g, st - 5] per hour (STAND-IN as-of M1 K500 levels; A3g-c has no EN state), block = B0's own ENF / ENA
groups with the ES level (pull["p_block_en"][g, st - 5, ptype]), class = L0s baseline row 5 / 6 x the ES-group level (L33;
the L1x-as terms are not applied on EN rows, as offline), miss = S0t's own ENF / ENA groups with the ES level group
(pull["p_miss_en"][g, st - 5, ptype, class]), goal: EN-for = C1s EAF (pull["eaf_cls"][class] + pull["eaf_game"][g, team];
no score dummies on EAF rows, L33), EN-against =
pull["p_en_goal"][g] (STAND-IN level, no goalie). Stage 1 keeps reading the penalty-derived strength. No delayed-penalty
state (INV-70). Recording arrays by team-view state have 7 states when the flag is on (5 otherwise); outputs add
pull_s / n_pulls / n_repulls / first_pull_t / first_pull_def / pull_at_trail1 / trail1_seen / n_ret_ga / n_ret_tie /
n_repull_after_ga and the pull_model / pull_stand_in markers. Flag off: bit-identical (tests/engine/test_sim_pull.py).

SHOOTOUT S1 (EG-R1 part C, INV-67, Lane H8b, 2026-10-21; default off, on when `tables` holds "shootout" = dict(p_home,
p_away, home_first, label), per game): replaces the 50 / 50 winner stub for the sims that end level after the 5-minute
regular-season OT (end_state SO). The shootout is played attempt by attempt with the rules mechanics of
`end_game.shootout` on its own stream "shootout"; outputs add so_n_att / so_goals_home / so_goals_away / so_home_first and
the shootout_model marker, and `so_home_win` is the S1 winner. Flag off: bit-identical (tests/engine/test_sim_otso.py).
The 3v3 OT attempt level (EG-R1 part B) is a stage-3 table builder (`end_game.ot_level.served_att_lam`, which re-levels
only the st = 3v3 entries of the A3g-c table; `defaults.att_table(games, ot3v3=True)`), not an engine branch: sudden death
and the 4v3 / 3v4 / 4v4 OT states are the regulation cascade with the OT period type (tests/test_end_game_otso.py).
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
ST_RGRP7 = np.array([0, 1, 2, 0, 0, 0, 0], np.int64)  # with the EN states 5 / 6 (ES group); equal on 0..4
BLK_ST = np.array([0, 1, 2, 3, 4, 0, 0], np.int64)    # team-view state -> (G, 5, 2) block table index (EN: ES group)
PULL_WIN = 600                                         # pulls are drawn in the last 600 s of regulation


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
    pull = tables.get("pull")
    n_st = 7 if pull is not None else 5
    if att is not None:
        K["attempt"] = rng.stream_keys(seeds, gid, "attempt")
        K["attempt_goal"] = rng.stream_keys(seeds, gid, "attempt_goal")
        Ma = att.shape[2]
        att_flat = att.reshape(-1)
        p_goal = np.asarray(tables["p_goal"], np.float64)
        att_st = np.zeros((N, 2, n_st), np.int32)
        att_sc = np.zeros((N, 2, 7), np.int32)
        toi_st_sc = np.zeros((N, n_st, 7), np.int32)
    attr = tables.get("attr")
    AS = None
    if attr is not None:
        if att is None:
            raise ValueError("the shot-attribute variant needs the stage-3 attempt table (att_lam)")
        if "era_mult" in attr and "game_mult" in attr:
            raise ValueError("attr carries both era_mult and game_mult: one stage-4 level only")
        levelled = "era_mult" in attr or "game_mult" in attr
        labels = dict(attr.get("stand_in", {}))
        state_pdf = attr.get("state_pdf")
        if state_pdf is not None:                       # D32 stand-in: stage-4 L0s by (team-view state, period type)
            state_pdf = np.asarray(state_pdf, np.float64)
            if state_pdf.ndim != 3 or state_pdf.shape[:2] != (7, 2) or not (state_pdf > 0).all():
                raise ValueError(f"attr state_pdf must be a positive (7, 2, C) table, got {state_pdf.shape}")
            if not levelled:
                raise ValueError("the L0s stand-in is served levelled: attr needs era_mult or game_mult")
            if "l1x" in attr:
                if "attr" in labels:
                    raise ValueError("attr l1x replaces the L0s STAND-IN: do not label 'attr' as a stand-in")
            elif "attr" not in labels:
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
                  fen=np.zeros((N, 2, n_st), np.int32), xg_sum=np.zeros((N, 2, n_st)), goals=np.zeros((N, 2, n_st), np.int32))
        if state_pdf is not None:
            AS["state_pdf"] = state_pdf
        if "p_block_game" in attr:                      # D32 stand-in: block B0 per (game, rating group / st, period type)
            pbg = np.asarray(attr["p_block_game"], np.float64)
            if pbg.shape not in ((G, 3, 2), (G, 5, 2)) or not ((pbg >= 0) & (pbg <= 1)).all():
                raise ValueError(f"attr p_block_game must be (G, 3, 2) or (G, 5, 2) probabilities, got {pbg.shape}")
            if "block_b1aas" in attr:                   # SB-R5 B1a-as on the B0' base (INV-64)
                bx = attr["block_b1aas"]
                if "block" in labels:
                    raise ValueError("attr block_b1aas replaces the B0 STAND-IN: do not label 'block' as a stand-in")
                if pbg.shape != (G, 5, 2) or not ((pbg > 0) & (pbg < 1)).all():
                    raise ValueError("attr block_b1aas needs the (G, 5, 2) B0' base table with 0 < p < 1")
                bg, bs = np.asarray(bx["game_logit"], np.float64), np.asarray(bx["sc_logit"], np.float64)
                if bg.shape != (G, 2, 5) or bs.shape != (7,) or not (np.isfinite(bg).all() and np.isfinite(bs).all()):
                    raise ValueError("attr block_b1aas needs finite game_logit (G, 2, 5) and sc_logit (7,)")
                if not bx.get("label"):
                    raise ValueError("attr block_b1aas needs a model label")
                AS.update(b1aas_base=np.log(pbg) - np.log1p(-pbg), b1aas_game=bg, b1aas_sc=bs,
                          block_model=str(bx["label"]))
            elif "block" not in labels:
                raise ValueError("attr p_block_game is a STAND-IN: attr['stand_in'] must label it ('block')")
            AS["p_block_game"] = pbg
        elif AS["p_block"] is None:
            raise ValueError("attr needs p_block (empirical stub) or p_block_game (B0 stand-in)")
        if "p_miss_game" in attr:                       # INV-60: miss S0t STAND-IN per (game, rating group, ptype, class)
            pmg = np.asarray(attr["p_miss_game"], np.float64)
            if pmg.shape != (G, 3, 2, nc) or not ((pmg >= 0) & (pmg <= 1)).all():
                raise ValueError(f"attr p_miss_game must be (G, 3, 2, {nc}) probabilities, got {pmg.shape}")
            if "miss" not in labels:
                raise ValueError("attr p_miss_game is a STAND-IN: attr['stand_in'] must label it ('miss')")
            AS["p_miss"] = pmg
            K["attempt_miss"] = rng.stream_keys(seeds, gid, "attempt_miss")
        if "goal" in attr:                              # INV-60: goal C1s per shot on goal
            if "p_miss" not in AS:
                raise ValueError("the C1s goal model is per shot on goal: attr needs the miss model (p_miss_game)")
            gm_ = attr["goal"]
            cl, gl_, sl = (np.asarray(gm_[k], np.float64) for k in ("cls_logit", "game_logit", "sc_logit"))
            gid_ = np.asarray(gm_["goalie_id"], np.int64)
            if cl.shape != (nc, 5) or gl_.shape != (G, 2, 5) or sl.shape != (7,) or gid_.shape != (G, 2):
                raise ValueError("attr goal needs cls_logit (C, 5), game_logit (G, 2, 5), sc_logit (7,), goalie_id (G, 2)")
            if not (np.isfinite(cl).all() and np.isfinite(gl_).all() and np.isfinite(sl).all()):
                raise ValueError("attr goal logits must be finite")
            if not gm_.get("label") or "oracle" not in str(gm_.get("oracle_goalie", "")).lower():
                raise ValueError("attr goal needs a model label and an oracle_goalie label (the box-score starter, D8)")
            AS.update(goal_cls=cl, goal_game=gl_, goal_sc=sl, goalie_id=gid_, goal_label=str(gm_["label"]),
                      oracle_goalie=str(gm_["oracle_goalie"]), sog=np.zeros((N, 2, n_st), np.int32),
                      gprob=np.zeros((N, 2, n_st)))
        elif "p_miss" in AS:
            raise ValueError("the miss stand-in needs the C1s goal model (attr['goal']): xG_ref is per unblocked attempt")
        if labels:
            AS["stand_in"] = np.array([f"{k}: {labels[k]}" for k in sorted(labels)])
        if "game_mult" in attr:                         # INV-57: per-game stage-4 level (M1 K500 as-of mix level)
            gmu = np.asarray(attr["game_mult"], np.float64)
            if gmu.shape != (G, 3, nc) or not (np.isfinite(gmu).all() and (gmu > 0).all()):
                raise ValueError(f"game_mult must be a positive finite (G, 3, {nc}) table, got {gmu.shape}")
            AS["game_mult"] = gmu
        elif levelled:
            em = np.asarray(attr["era_mult"], np.float64)
            if gs.rec_era is None:
                raise ValueError("the levelled stage-4 lookup reads GameState.rec_era: pass seasons= to simulate")
            if em.shape != (max(RECORDING_ERAS) + 1, 3, nc) or not np.isfinite(em[list(RECORDING_ERAS)]).all():
                raise ValueError(f"era_mult must be ({max(RECORDING_ERAS) + 1}, 3, {nc}) finite on eras {RECORDING_ERAS}")
            AS.update(era_mult=em, rec_era=gs.rec_era.astype(np.int64))
        if "l1x" in attr:                               # SL-R7 L1x-as on the levelled L0s baseline
            lx = attr["l1x"]
            if state_pdf is None or "game_mult" not in AS:
                raise ValueError("attr l1x needs the L0s state_pdf and the per-game level game_mult")
            glx, slx = np.asarray(lx["game_logit"], np.float64), np.asarray(lx["sc_logit"], np.float64)
            if glx.shape != (G, 2, 3, nc) or slx.shape != (2, 7, nc):
                raise ValueError(f"attr l1x needs game_logit (G, 2, 3, {nc}) and sc_logit (2, 7, {nc})")
            if not (np.isfinite(glx).all() and np.isfinite(slx).all()) or not lx.get("label"):
                raise ValueError("attr l1x logits must be finite and carry a model label")
            AS.update(l1x_game=glx, l1x_sc=slx, l1x_base=np.log(state_pdf), l1x_lgm=np.log(AS["game_mult"]),
                      attr_model=str(lx["label"]))
        AS["cell"] = np.zeros((N, 2, n_st, AS["n_cell"]), np.int32)
        AS["type"] = np.zeros((N, 2, n_st, AS["n_type"]), np.int32)
    PS = None
    if pull is not None:                                # EG-R1 part A goalie pull + EN cascade
        if att is None:
            raise ValueError("the goalie pull needs the stage-3 attempt table (att_lam)")
        PS = _pull_setup(pull, AS, G, N, gs)
        AS["en"] = PS
        K["pull"] = rng.stream_keys(seeds, gid, "pull")
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
    late_goals = np.zeros((N, 2, 4), np.int16)            # [sim, scoring team, lead / tied / trail 1 / trail 2+] (pull flag only)
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
        if PS is not None:
            ast_h, ast_a = _pull_second(gs, PS, K, a, t, sk, diff, st_h, st_a)
        else:
            ast_h, ast_a = st_h, st_a
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
            late = PS is not None and gs.reg_end - 120 <= t < gs.reg_end
            if late:                                    # EG-R1 recording: goals in the last 2 min by the scorer's deficit
                sc0 = gs.score[a].astype(np.int64)
            _attempts_second(gs, a, t, g_a, ast_h, ast_a, diff, K, att_flat, Ma, p_goal, att_st, att_sc, toi_st_sc, AS)
            if late:
                dg = gs.score[a].astype(np.int64) - sc0
                for team in (0, 1):
                    m = dg[:, team] > 0
                    if m.any():
                        lead = sc0[m, team] - sc0[m, 1 - team]
                        cat = np.where(lead > 0, 0, np.where(lead == 0, 1, np.where(lead == -1, 2, 3)))
                        np.add.at(late_goals, (a[m], team, cat), dg[m, team])
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
    so_home_win = so & so_home
    so_extra = {}
    shoot = tables.get("shootout")
    if shoot is not None:                                # EG-R1 part C: S1 replaces the 50 / 50 stub
        so_home_win, so_extra = _shootout_s1(shoot, so, gi, seeds, gid, N)
    extra = {} if att is None else dict(att_st=att_st, att_sc=att_sc, toi_st_sc=toi_st_sc)
    if AS is not None:
        extra.update(attr_fen=AS["fen"], attr_xg=AS["xg_sum"], attr_goals=AS["goals"], attr_cell=AS["cell"],
                     attr_type=AS["type"])
        if "stand_in" in AS:
            extra["stand_in"] = AS["stand_in"]
        if "attr_model" in AS:
            extra["attr_model"] = np.array([AS["attr_model"]])
        if "block_model" in AS:
            extra["block_model"] = np.array([AS["block_model"]])
        if "goal_cls" in AS:
            extra.update(attr_sog=AS["sog"], attr_gprob=AS["gprob"], goal_model=np.array([AS["goal_label"]]),
                         oracle_goalie=np.array([AS["oracle_goalie"]]), goalie_against=AS["goalie_id"])
    if PS is not None:
        extra.update(pull_s=PS["pull_s"], n_pulls=PS["n_pulls"], n_repulls=PS["n_repulls"], first_pull_t=PS["first_t"],
                     first_pull_def=PS["first_d"], pull_at_trail1=PS["at_t1"], trail1_seen=PS["t1_seen"],
                     n_ret_ga=gs.n_ret_ga.copy(), n_ret_tie=gs.n_ret_tie.copy(), n_repull_after_ga=PS["rep_ga"],
                     pull_model=np.array([PS["label"]]), pull_stand_in=np.array(PS["stand_in"]), late_goals=late_goals)
    return dict(**extra, game_idx=gi, seed=seeds, score=gs.score.copy(), end_state=gs.end_state.copy(), so_home_win=so_home_win, **so_extra,
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
        if AS is not None and "en" in AS and (st > 4).any():   # EN states: STAND-IN levels (A3g-c has no EN state)
            en = st > 4
            v = att_flat[(((g_a * 2 + team) * Ma + m) * 5 + np.where(en, 0, st)) * 7 + sc].astype(np.float64) / 3600.0
            v[en] = AS["en"]["en_lam"][g_a[en], st[en] - 5] / 3600.0
            return v
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
    unb = rng.uniform(K["attempt_block"][ai], t, kk) >= (block_prob(AS, gi, st, t, team, sc) if "b1aas_game" in AS
                                                         else block_prob(AS, gi, st, t))
    if not unb.any():
        return np.zeros(len(ai), np.int64)
    ai, gi, st, sc = ai[unb], gi[unb], st[unb], sc[unb]
    rg = ST_RGRP7[st]
    row = class_cdf(AS, ai, gi, team, st, sc, m, t)
    u = rng.uniform(K["attempt_attr"][ai], t, kk)
    cls = np.minimum((row <= u[:, None]).sum(1), row.shape[1] - 1)
    x = AS["xg"][cls, rg]
    if "p_miss" in AS:                                  # INV-60: miss S0t -> shot on goal -> goal C1s
        sog = rng.uniform(K["attempt_miss"][ai], t, kk) >= miss_prob(AS, gi, st, t, cls)
        pg = goal_prob(AS, gi, team, st, sc, cls)
        goal = sog & (rng.uniform(K["attempt_goal"][ai], t, kk) < pg)
        np.add.at(AS["sog"], (ai, team, st), sog.astype(np.int32))
        np.add.at(AS["gprob"], (ai, team, st), np.where(sog, pg, 0.0))
    else:
        goal = rng.uniform(K["attempt_goal"][ai], t, kk) < x
    np.add.at(AS["fen"], (ai, team, st), 1)
    np.add.at(AS["xg_sum"], (ai, team, st), x)
    np.add.at(AS["goals"], (ai, team, st), goal.astype(np.int32))
    np.add.at(AS["cell"], (ai, team, st, cls // AS["n_type"]), 1)
    np.add.at(AS["type"], (ai, team, st, cls % AS["n_type"]), 1)
    out = np.zeros(len(unb), np.int64)
    out[np.nonzero(unb)[0]] = goal
    return out


def block_prob(AS, gi, st, t, team=None, sc=None):
    """Served block probability per attempt (game index gi, team-view state st, game second t): the B0 stand-in
    p_block_game[g, rating group, period type] when on, else the empirical stub p_block[st]. With the SB-R5 flag
    (AS["b1aas_game"]): sigmoid(logit B0'[g, st, ptype] + game_logit[g, team, st] + sc_logit[sc]); team = shooting team
    (0 home), sc = its score bucket sc7 (both required)."""
    if "b1aas_game" in AS:
        if team is None or sc is None:
            raise ValueError("block B1a-as needs the shooting team and score bucket")
        st = np.asarray(st)
        en = st > 4
        if en.any() and "en" not in AS:
            raise ValueError("EN state without the pull tables")
        b = BLK_ST[st]
        z = AS["b1aas_base"][gi, b, int(t >= 3600)] + AS["b1aas_game"][gi, team, b] + AS["b1aas_sc"][np.asarray(sc)]
        v = 1.0 / (1.0 + np.exp(-z))
        if en.any():
            v[en] = AS["en"]["p_block_en"][gi[en], st[en] - 5, int(t >= 3600)]
        return v
    if "en" in AS and (np.asarray(st) > 4).any():      # EG-R1 part A: B0's own ENF / ENA groups (ES level)
        st = np.asarray(st)
        en = st > 4
        v = block_prob({k: x for k, x in AS.items() if k != "en"}, gi, np.where(en, 0, st), t)
        v = np.array(v, np.float64, copy=True)
        v[en] = AS["en"]["p_block_en"][gi[en], st[en] - 5, int(t >= 3600)]
        return v
    if "p_block_game" in AS:
        pbg = AS["p_block_game"]
        return pbg[gi, BLK_ST[st] if pbg.shape[1] == 5 else ST_RGRP7[st], int(t >= 3600)]
    return AS["p_block"][st]


def miss_prob(AS, gi, st, t, cls):
    """Served miss probability per unblocked attempt (INV-60 S0t STAND-IN): p_miss_game[g, rating group, ptype, class]."""
    if "en" in AS and (np.asarray(st) > 4).any():      # EG-R1 part A: S0t's own ENF / ENA groups (ES level group)
        st = np.asarray(st)
        en = st > 4
        v = np.array(AS["p_miss"][gi, ST_RGRP7[np.where(en, 0, st)], int(t >= 3600), cls], np.float64, copy=True)
        v[en] = AS["en"]["p_miss_en"][gi[en], st[en] - 5, int(t >= 3600), cls[en]]
        return v
    return AS["p_miss"][gi, ST_RGRP7[st], int(t >= 3600), cls]


def goal_prob(AS, gi, team, st, sc, cls):
    """Served C1s goal probability per shot on goal (INV-60): sigmoid(cls_logit[class, st] + game_logit[g, team, st] +
    sc_logit[sc7]); team = shooting team (0 home), st = its team-view state 0..4, sc = its score bucket 0..6."""
    st = np.asarray(st)
    if "en" in AS and (st > 4).any():                   # EG-R1 part A: EN-for = C1s EAF, EN-against = the EN level
        PS = AS["en"]
        ef, ea = st == 5, st == 6
        s4 = np.minimum(st, 4)
        z = AS["goal_cls"][cls, s4] + AS["goal_game"][gi, team, s4] + AS["goal_sc"][sc]
        z[ef] = PS["eaf_cls"][cls[ef]] + PS["eaf_game"][gi[ef], team]       # C1s EAF: no score dummies (L33)
        p = 1.0 / (1.0 + np.exp(-z))
        p[ea] = PS["p_en_goal"][gi[ea]]
        return p
    z = AS["goal_cls"][cls, st] + AS["goal_game"][gi, team, st] + AS["goal_sc"][sc]
    return 1.0 / (1.0 + np.exp(-z))


def class_cdf(AS, ai, gi, team, st, sc, m, t):
    """Served cumulative class row per unblocked attempt (the row the engine draws the class from): the L0s stand-in
    state_pdf[st, period type] or the arm lookup cdf / pdf[g, team, interval, rating group, sc]; levelled by
    era_mult[rec_era, rating group] and renormalised when era_mult is present."""
    rg = ST_RGRP7[st]
    if "l1x_game" in AS and (np.asarray(st) > 4).any():  # EG-R1 part A: EN rows on the L0s baseline x ES-group level
        en = np.asarray(st) > 4
        out = np.empty((len(st), AS["l1x_base"].shape[2]))
        if (~en).any():
            out[~en] = class_cdf(AS, None, gi[~en], team, st[~en], sc[~en], m, t)
        row = np.cumsum(AS["state_pdf"][st[en], int(t >= 3600)] * AS["game_mult"][gi[en], 0], 1)
        out[en] = row / row[:, -1:]
        return out
    if "l1x_game" in AS:                                # SL-R7 L1x-as
        pt = int(t >= 3600)
        z = AS["l1x_base"][st, pt] + AS["l1x_lgm"][gi, rg] + AS["l1x_game"][gi, team, rg] + AS["l1x_sc"][pt, sc]
        z = np.exp(z - z.max(1, keepdims=True))
        row = np.cumsum(z, 1)
        return row / row[:, -1:]
    if "state_pdf" in AS:
        row = AS["state_pdf"][st, int(t >= 3600)]
    else:
        row = AS["cdf"][gi, team, AS["imap"][m], rg, sc]
    if "game_mult" in AS:
        row = np.cumsum(row.astype(np.float64) * AS["game_mult"][gi, rg], 1)
        row /= row[:, -1:]
    elif "era_mult" in AS:
        row = np.cumsum(row.astype(np.float64) * AS["era_mult"][AS["rec_era"][ai], rg], 1)
        row /= row[:, -1:]
    return row


def _pull_setup(pull: dict, AS, G: int, N: int, gs) -> dict:
    """Validate tables["pull"] and allocate the pull counters."""
    if AS is None or "goal_cls" not in AS or "p_miss" not in AS or "state_pdf" not in AS or "p_block_game" not in AS:
        raise ValueError("the goalie pull needs the default cascade: L0s state_pdf, block B0, miss S0t, goal C1s")
    hz = pull["hazard"]
    if hz["kind"] == "P1":
        tab = np.asarray(hz["table"], np.float64)
        if tab.shape != (3, PULL_WIN // 10, 3, 2, 2):
            raise ValueError(f"P1 hazard table must be (3, 60, 3, 2, 2), got {tab.shape}")
        h0 = h1 = None
    elif hz["kind"] == "P0":
        tab = None
        h0, h1 = np.asarray(hz["h_first"], np.float64), np.asarray(hz["h_repull"], np.float64)
        if h0.shape != (3, 2, PULL_WIN) or h1.shape != (PULL_WIN + 1,):
            raise ValueError("P0 needs h_first (3, 2, 600) and h_repull (601,)")
    else:
        raise ValueError(hz["kind"])
    pbe, pme = np.asarray(pull["p_block_en"], np.float64), np.asarray(pull["p_miss_en"], np.float64)
    if pbe.shape != (G, 2, 2) or pme.shape != (G, 2, 2, AS["goal_cls"].shape[0]):
        raise ValueError("pull needs p_block_en (G, 2, 2) and p_miss_en (G, 2, 2, C) [game, ENF / ENA, period type]")
    lam, pe = np.asarray(pull["en_lam"], np.float64), np.asarray(pull["p_en_goal"], np.float64)
    ec, eg = np.asarray(pull["eaf_cls"], np.float64), np.asarray(pull["eaf_game"], np.float64)
    if lam.shape != (G, 2) or pe.shape != (G,) or eg.shape != (G, 2) or ec.shape != (AS["goal_cls"].shape[0],):
        raise ValueError("pull needs en_lam (G, 2), p_en_goal (G,), eaf_cls (C,), eaf_game (G, 2)")
    if not pull.get("label") or not pull.get("stand_in"):
        raise ValueError("pull needs a model label and its stand_in labels")
    gs.track_pull = True
    return dict(kind=hz["kind"], table=tab, h_first=h0, h_repull=h1, en_lam=lam, p_en_goal=pe, eaf_cls=ec, eaf_game=eg,
                p_block_en=pbe, p_miss_en=pme,
                label=str(pull["label"]), stand_in=[f"{k}: {v}" for k, v in sorted(pull["stand_in"].items())],
                reg_end=gs.reg_end, pull_s=np.zeros((N, 2), np.int32), n_pulls=np.zeros((N, 2), np.int16),
                n_repulls=np.zeros((N, 2), np.int16), first_t=np.full((N, 2), -1, np.int32), first_d=np.zeros((N, 2), np.int8),
                at_t1=np.zeros((N, 2), bool), t1_seen=np.zeros((N, 2), bool), rep_ga=np.zeros((N, 2), np.int16))


def _shootout_s1(shoot: dict, so: np.ndarray, gi: np.ndarray, seeds: np.ndarray, gid: np.ndarray, N: int):
    """EG-R1 part C, S1 (default off; on when `tables` holds "shootout"): the shootout of every sim that ends level
    after the 5-minute OT is played with the rules mechanics of `end_game.shootout` (three rounds, early termination,
    sudden death, alternating shooters), a constant per-attempt success p for both sides and the as-of home-shoots-first
    share, per game. Stream "shootout" (counter (0, 0): who shoots first; (1, j): attempt j). Returns (home_win (N,)
    bool, outputs: so_n_att / so_goals_home / so_goals_away / so_home_first (N,), shootout_model marker)."""
    from nhl_sim.end_game import shootout as SOF
    G = len(shoot["p_home"])
    p_h, p_a, hf = (np.asarray(shoot[k], np.float64) for k in ("p_home", "p_away", "home_first"))
    if p_h.shape != (G,) or p_a.shape != (G,) or hf.shape != (G,) or not ((p_h > 0) & (p_h < 1) & (p_a > 0) & (p_a < 1)).all()             or not ((hf >= 0) & (hf <= 1)).all():
        raise ValueError("tables['shootout'] needs per-game p_home / p_away in (0, 1) and home_first in [0, 1]")
    if not shoot.get("label"):
        raise ValueError("tables['shootout'] needs a model label")
    hw = np.zeros(N, bool)
    n_att = np.zeros(N, np.int16)
    gh = np.zeros(N, np.int16)
    ga = np.zeros(N, np.int16)
    first = np.zeros(N, bool)
    idx = np.nonzero(so)[0]
    if idx.size:
        keys = rng.stream_keys(seeds[idx], gid[idx], "shootout")
        u_att = np.stack([rng.uniform(keys, 1, j) for j in range(SOF.MAX_ATTEMPTS)], 1)
        g = gi[idx]
        w, n, h_, a_, f = SOF.shootout_home_win(rng.uniform(keys, 0, 0), u_att, p_h[g], p_a[g], hf[g])
        hw[idx], n_att[idx], gh[idx], ga[idx], first[idx] = w, n, h_, a_, f
    return hw, dict(so_n_att=n_att, so_goals_home=gh, so_goals_away=ga, so_home_first=first,
                    shootout_model=np.array([str(shoot["label"])]))


def pull_hazard(PS: dict, dcat, t, pen, pb, home, lag) -> np.ndarray:
    """Served per-second pull probability: dcat 0..2 (deficit 1 / 2 / 3+), game second t, pen 0 none / 1 pk / 2 pp,
    pulled_before 0 / 1, home 0 / 1, lag = seconds since the last return (P0 re-pull)."""
    dcat, pen, pb, home, lag = (np.asarray(x, np.int64) for x in (dcat, pen, pb, home, lag))
    re = PS.get("reg_end", 3600)
    if PS["kind"] == "P1":
        return PS["table"][dcat, (re - int(t) - 1) // 10, pen, pb, home]
    a = PS["h_first"][dcat, (pen > 0).astype(np.int64), int(t) - (re - PULL_WIN)]
    b = PS["h_repull"][np.clip(lag, 0, PULL_WIN)]
    return np.where(pb == 1, b, a)


def _pull_second(gs, PS, K, a, t, sk, diff, st_h, st_a):
    """Pull draws at the start of second t (pre-event state), pulled-second counters, and the team-view states of the
    second's attempts (5 EN-for / 6 EN-against while a goalie is out)."""
    if gs.reg_end - PULL_WIN <= t < gs.reg_end:
        for team in (0, 1):
            d = -diff if team == 0 else diff                  # own deficit before the second
            own, opp = sk[:, team].astype(np.int64), sk[:, 1 - team].astype(np.int64)
            PS["t1_seen"][a[d == 1], team] = True
            j = np.nonzero((d >= 1) & ~gs.pulled[a, team])[0]
            if not j.size:
                continue
            aj = a[j]
            pen = np.where(own[j] < opp[j], 1, np.where(own[j] > opp[j], 2, 0))
            pb = gs.pulled_before[aj, team].astype(np.int64)
            lr = gs.last_return[aj, team]
            lag = np.where(lr >= 0, t - lr, -1)
            h = pull_hazard(PS, np.minimum(d[j], 3) - 1, t, pen, pb, np.full(j.size, 1 - team), lag)
            k = rng.uniform(K["pull"][aj], t, team) < h
            if k.any():
                hit, dh = aj[k], d[j][k]
                gs.pulled[hit, team] = True
                PS["n_pulls"][hit, team] += 1
                PS["n_repulls"][hit, team] += gs.pulled_before[hit, team]
                PS["rep_ga"][hit, team] += gs.ga_open[hit, team]
                gs.ga_open[hit, team] = False
                nf = PS["first_t"][hit, team] < 0
                PS["first_t"][hit[nf], team] = t
                PS["first_d"][hit[nf], team] = np.minimum(dh[nf], 3)
                PS["at_t1"][hit[dh == 1], team] = True
    pu = gs.pulled[a]
    if not pu.any():
        return st_h, st_a
    PS["pull_s"][a] += pu
    sh, sa = st_h.copy(), st_a.copy()
    sh[pu[:, 0]], sa[pu[:, 0]] = 5, 6
    sh[pu[:, 1]], sa[pu[:, 1]] = 6, 5
    return sh, sa
