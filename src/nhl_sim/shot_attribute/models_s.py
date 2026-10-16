"""SL-R4 arms (docs/models/shot_attribute/experiments.md SL-R4; D26, L33): the state-stratified baseline L0s and the
booster L3c started from it, with EN rows on the baseline only.

Strata: the 7 team-view pre-event states (st 0 5v5, 1 PP-for, 2 PK, 3 4v4, 4 3v3, 5 EN-for, 6 EN-against) x period
type (regulation / OT) = 14 rows, indexed s0 = st * 2 + ptype.

  L0s (unlevelled table, (14, 78)):
    PP-for, PK, EN-for, EN-against: the SL-R1 L0 row of the same (strength group x period type) (Dirichlet joint,
        ALPHA0 pseudo-attempts on the pooled joint frequency), unchanged.
    5v5:      cell shares = Dirichlet posterior mean of the 5v5 cell counts with ALPHA0 pseudo-attempts on the pooled
              (all rows) cell frequency, the same smoothing as L0;
    4v4, 3v3: cell shares = (n_cell + K s_5v5,cell) / (N + K), K = 500 unblocked attempts, shrunk to the 5v5 cell
              shares OF THE SAME PERIOD TYPE (labelled reading of "the 5v5 cell shares");
    ES states: P(type | cell) = the pooled-ES conditional of the same period type, i.e. the SL-R1 L0 ES row
              (5v5 + 4v4 + 3v3 pooled) normalised within each cell.
  The level E enters per row as the cell offset of the row's level group (mix_level.row_offset: ES ratio for 5v5 /
  4v4 / 3v3 and, as before, EN pooled with ES), with coefficient 1: L0s levelled = L0s[s0] x exp(off), renormalised.

  L3c: LightGBM multiclass on the joint, init_score = log L0s levelled (so the trees model deviations only), the
  SL-R3 L3b features and frozen booster params. EN-for / EN-against rows are EXCLUDED from the booster's training
  rows and are served L0s levelled with no tree output (L33).

Because softmax is invariant to a per-row constant, the levelled prediction is the unlevelled one x exp(off),
renormalised: the engine serves the unlevelled per-state table and applies the level from GameState.rec_era.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attribute import models as M
from nhl_sim.shot_attribute.mix_level import apply_cell_offset
from nhl_sim.shot_attribute.tables import N_CELL, N_CLASS, N_TYPE

K_SHRINK = 500.0
N_ST = 7
N_L0S = N_ST * 2
ES_STATES = (0, 3, 4)
EN_STATES = (5, 6)
GROUP_OF_ST = np.array([0, 1, 2, 0, 0, 3, 4], np.int64)
STATE_NAMES = ("5v5", "PP", "PK", "4v4", "3v3", "ENF", "ENA")


def s0_index(r: pd.DataFrame) -> np.ndarray:
    st = r.st.to_numpy().astype(np.int64)
    if (GROUP_OF_ST[st] != r.grp.to_numpy()).any():
        raise ValueError("st and grp disagree")
    return st * 2 + r.ptype.to_numpy().astype(np.int64)


def fit_l0s(r: pd.DataFrame) -> dict:
    """(14, 78) unlevelled L0s table from the fold's training rows (unblocked, with st / grp / ptype / cls / cell)."""
    l0 = np.asarray(M.fit_l0(r)["p"])                                  # (10, 78) SL-R1 L0 rows (group x ptype)
    cls = r.cls.to_numpy().astype(np.int64)
    cell = cls // N_TYPE
    st = r.st.to_numpy().astype(np.int64)
    pt = r.ptype.to_numpy().astype(np.int64)
    nc = np.zeros((N_ST, 2, N_CELL))
    np.add.at(nc, (st, pt, cell), 1.0)
    pooled_cell = (np.bincount(cell, minlength=N_CELL) + 0.5) / (len(cell) + 0.5 * N_CELL)
    p = np.zeros((N_L0S, N_CLASS))
    info = {}
    for ptype in (0, 1):
        es_joint = l0[0 * 2 + ptype].reshape(N_CELL, N_TYPE)
        type_given_cell = es_joint / es_joint.sum(1, keepdims=True)   # pooled ES (5v5 + 4v4 + 3v3), same ptype
        n5 = nc[0, ptype]
        s5 = (n5 + M.ALPHA0 * pooled_cell) / (n5.sum() + M.ALPHA0)
        cells = {0: s5}
        for s_ in (3, 4):
            n_ = nc[s_, ptype]
            cells[s_] = (n_ + K_SHRINK * s5) / (n_.sum() + K_SHRINK)
        for s_ in ES_STATES:
            p[s_ * 2 + ptype] = (cells[s_][:, None] * type_given_cell).reshape(-1)
            info[f"{STATE_NAMES[s_]}_pt{ptype}_n"] = int(nc[s_, ptype].sum())
        for s_ in (1, 2, 5, 6):
            p[s_ * 2 + ptype] = l0[GROUP_OF_ST[s_] * 2 + ptype]
    if not np.allclose(p.sum(1), 1.0, atol=1e-12) or (p <= 0).any():
        raise ValueError("L0s rows must be positive probability vectors")
    return dict(arm="L0s", p=p.tolist(), k_shrink=K_SHRINK, n=info)


def predict_l0s(m: dict, r: pd.DataFrame) -> np.ndarray:
    return np.asarray(m["p"])[s0_index(r)]


def l0s_levelled(m: dict, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    return apply_cell_offset(predict_l0s(m, r), off)


def _softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def booster_rows(r: pd.DataFrame) -> np.ndarray:
    """Rows the L3c booster sees (training) / applies to (prediction): every non-EN row."""
    return ~np.isin(r.st.to_numpy(), EN_STATES)


def lgb_dataset_c(r: pd.DataFrame, off: np.ndarray, l0s: dict, ref=None):
    """Booster training set: non-EN rows only, init_score = log L0s levelled."""
    import lightgbm as lgb
    m = booster_rows(r)
    rr = r[m]
    return lgb.Dataset(rr[M.LGB_FEATURES].astype(float), label=rr.cls.to_numpy(), categorical_feature=["grp"],
                       free_raw_data=False, reference=ref, init_score=np.log(l0s_levelled(l0s, rr, off[m])))


def predict_l3c(booster, l0s: dict, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    """Non-EN rows: softmax(raw trees + log L0s levelled); EN rows: L0s levelled (no tree output)."""
    P = l0s_levelled(l0s, r, off)
    m = booster_rows(r)
    if m.any():
        rr = r[m]
        raw = booster.predict(rr[M.LGB_FEATURES].astype(float), raw_score=True)
        P[m] = _softmax(raw + np.log(P[m]))
    return P
