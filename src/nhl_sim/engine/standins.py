"""D32 engine STAND-INS: the flat baselines the engine serves until SB-R4 (block decision) and SL-R6 (stage 4) pass.

  block B0   SB-R1 arm B0 (fold-2 fit, results/block_sb_r1/models/B0.json): one-hot (strength group x period type)
             + the M1 K500 as-of league block-share level (D27) as a logit offset with coefficient 1. Engine table
             p_block_game (G, 3, 2) = [game, rating group ES / PP / PK, period type]; 4v4 / 3v3 are ES rows.
  stage-4 L0s  SL-R4 L0s (fold-2 fit, results/shot_attribute_r4/models/L0s.json): (7 states x 2 period types, 78)
             unlevelled; the level E enters in the engine as era_mult[rec_era, rating group, class] (SL-R3 form).
             EN rows (states 5 / 6) are the baseline (L33) and unreachable until stage 8.

Both are FLAT and NOT adoptable (D24, D32). They exist so stage 5 can be built and closed-loop tested. No offline fit
may use stand-in sim output: every fit uses recorded data (D32). The labels below travel with the engine tables
(attr["stand_in"]) and into the sim output ("stand_in") and every gate report header.

The parity helpers evaluate the ENGINE's own served values (engine.sim.block_prob / class_cdf) on the offline fold-2
rows and compare them with the offline B0 / L0s predictions.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nhl_sim.engine import sim as SIM
from nhl_sim.engine.rules import RECORDING_ERAS, recording_era

BLOCK_LABEL = ("STAND-IN (D32): block B0 = SB-R1 B0 (one-hot strength group x period type) + M1 K500 as-of league "
               "block-share level; flat, not adoptable")
ATTR_LABEL = ("STAND-IN (D32): stage-4 L0s (SL-R4) levelled by E from GameState.rec_era; EN rows on the baseline; "
              "flat, not adoptable")
STAND_IN = {"block": BLOCK_LABEL, "attr": ATTR_LABEL}

B_RES = Path("results/block_sb_r1")
L_RES = Path("results/shot_attribute_r4")
F2_TRAIN = [20212022, 20222023, 20232024]
LEVEL_NAME = "M1_K500"


# ------------------------------------------------------------------------------------------------ block B0
def block_b0_table(games: np.ndarray, res: Path = B_RES) -> tuple[np.ndarray, dict]:
    """games: sorted fold-2 game ids (the engine's game order). -> (p_block_game (G, 3, 2), info)."""
    from nhl_sim.block import data as D
    from nhl_sim.block.data import logit, sigmoid
    sel = json.loads((res / "step0.json").read_text())["selected"]
    if sel != LEVEL_NAME:
        raise ValueError(f"B0 stand-in uses the M1 K500 level (D27); SB-R1 selected {sel}")
    coef = np.asarray(json.loads((res / "models" / "B0.json").read_text())["coef"], np.float64)
    if coef.shape != (10,):
        raise ValueError("B0 coef must be (strength group 5 x period type 2)")
    gl = pd.read_parquet(D.OUT / "games_v1.parquet", columns=["game_id"])
    a = D.load_attempts(F2_TRAIN).merge(gl, on="game_id")
    s_train = D.share_table(a)                                     # (3,) pooled block share per level group
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    L = L[L.construction == LEVEL_NAME].set_index("game_id")[["s_0", "s_1", "s_2"]].reindex(np.asarray(games))
    if L.isna().any().any():
        raise ValueError("games without an M1 K500 level")
    S = L.to_numpy()                                               # (G, 3) as-of share per level group
    off = logit(S) - logit(s_train)[None]                          # rating group == level group for ES / PP / PK
    pbg = np.zeros((len(games), 3, 2))
    for rg in range(3):
        for pt in range(2):
            pbg[:, rg, pt] = sigmoid(coef[rg * 2 + pt] + off[:, rg])
    return pbg, dict(level=LEVEL_NAME, s_train=s_train.tolist(), coef=coef.tolist())


def b0_parity(games: np.ndarray, pbg: np.ndarray, res: Path = B_RES) -> dict:
    """Engine-served block probability (sim.block_prob) vs the offline fold-2 B0 prediction on every goalie-in row."""
    lab = json.loads((res / "labels_sealed.json").read_text())["B0"]
    rows = pd.read_parquet(res / "fold2_rows.parquet", columns=["game_id", "grp", "st", "ptype"])
    pred = np.load(res / f"fold2_pred_{lab}.npy").astype(np.float64)
    m = (rows.grp <= 2).to_numpy()
    r, p = rows[m], pred[m]
    gpos = np.searchsorted(games, r.game_id.to_numpy())
    if not (np.asarray(games)[np.minimum(gpos, len(games) - 1)] == r.game_id.to_numpy()).all():
        raise ValueError("offline rows outside the engine game list")
    AS = dict(p_block_game=pbg)
    served = np.zeros(len(r))
    st5 = np.minimum(r.st.to_numpy().astype(np.int64), 4)          # goalie-in team-view state 0..4
    for pt in (0, 1):
        k = (r.ptype.to_numpy() == pt)
        served[k] = SIM.block_prob(AS, gpos[k], st5[k], 3600 * pt)
    d = np.abs(served - p)
    return dict(n_rows=int(len(r)), max_abs_diff=float(d.max()), mean_served=float(served.mean()),
                mean_offline=float(p.mean()), n_en_rows_not_served=int((~m).sum()))


# --------------------------------------------------------------------------------------------- stage-4 L0s
def l0s_tables(res: Path = L_RES) -> tuple[np.ndarray, np.ndarray, dict]:
    """-> (state_pdf (7, 2, 78) unlevelled L0s, era_mult (3, 3, 78), info). era_mult[e, lg, class] =
    s_E[e, lg, cell] / s_train[lg, cell] on the fold-2 unblocked training rows (SL-R2 level E, SL-R3 engine form)."""
    from nhl_sim.shot_attribute import mix_level as ML
    from nhl_sim.shot_attribute import models as M
    from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE
    m = json.loads((res / "models" / "L0s.json").read_text())
    if m.get("arm") != "L0s":
        raise ValueError("not an L0s model file")
    state_pdf = np.asarray(m["p"], np.float64).reshape(7, 2, N_CELL * N_TYPE)   # row s0 = st * 2 + ptype
    tr = M.load_rows(F2_TRAIN)
    u = tr[~tr.blocked]
    s_train = ML.share_table(u)
    era_tr = recording_era(u.season.to_numpy())
    em = np.full((max(RECORDING_ERAS) + 1, 3, N_CELL * N_TYPE), np.nan)
    for e in RECORDING_ERAS:
        em[e] = np.repeat(ML.share_table(u[era_tr == e]) / s_train, N_TYPE, axis=1)
    return state_pdf, em, dict(s_train=s_train.tolist())


def l0s_parity(state_pdf: np.ndarray, em: np.ndarray, res: Path = L_RES) -> dict:
    """Engine-served class probabilities (increments of sim.class_cdf) vs the offline fold-2 L0s levelled prediction,
    every unblocked row incl. EN-for / EN-against (the baseline rows the engine will serve at stage 8)."""
    lab = json.loads((res / "labels_sealed.json").read_text())["L0s"]
    rows = pd.read_parquet(res / "fold2_rows.parquet", columns=["game_id", "season", "st", "ptype"])
    pred = np.load(res / f"fold2_pred_{lab}.npy").astype(np.float64)
    st = rows.st.to_numpy().astype(np.int64)
    rg = np.array([0, 1, 2, 0, 0, 0, 0])[st]                      # EN rows: ES level group (mix_level.LEVEL_GROUP)
    AS = dict(state_pdf=state_pdf, era_mult=em, rec_era=recording_era(rows.season.to_numpy()).astype(np.int64))
    served = np.zeros_like(pred)
    ai = np.arange(len(rows))
    for pt in (0, 1):
        k = rows.ptype.to_numpy() == pt
        # class_cdf indexes era_mult by the rating group of st 0..4; EN states take the ES group, as in the offline offset
        stk = st[k]
        cdf = _class_cdf_any_state(AS, ai[k], stk, rg[k], 3600 * pt)
        served[k] = np.diff(cdf, axis=1, prepend=0.0)
    d = np.abs(served - pred).max(1)
    out = dict(n_rows=int(len(rows)), max_abs_diff=float(d.max()))
    for s_ in range(7):
        k = st == s_
        out[f"max_abs_diff_st{s_}"] = float(d[k].max()) if k.any() else None
        out[f"n_st{s_}"] = int(k.sum())
    return out


def _class_cdf_any_state(AS, ai, st, rg, t):
    """sim.class_cdf for states 0..4 (the engine path); states 5 / 6 (EN, unreachable) evaluated with the same
    formula and the ES rating group, so the parity also covers the EN baseline rows."""
    reach = st <= 4
    out = np.zeros((len(st), AS["state_pdf"].shape[2]))
    if reach.any():
        out[reach] = SIM.class_cdf(AS, ai[reach], None, None, st[reach], None, None, t)
    if (~reach).any():
        row = AS["state_pdf"][st[~reach], int(t >= 3600)]
        row = np.cumsum(row * AS["era_mult"][AS["rec_era"][ai[~reach]], rg[~reach]], 1)
        out[~reach] = row / row[:, -1:]
    return out
