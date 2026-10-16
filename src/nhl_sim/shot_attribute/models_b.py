"""SL-R3 arm L3b (docs/models/shot_attribute/experiments.md SL-R3; D24, L32): LightGBM multiclass on the joint (cell x
type, 78 classes) whose init_score is the log of the L0m (levelled) class probabilities of each row's (strength group x
period type), so the trees model only the deviations (ratings, score, home, rest, clock, period). Same feature list as
L3m (models.LGB_FEATURES).

  init(row) = log L0m(row) = log( L0[l0] x exp(off[cell]) / Z(row) ),  L0 = models.fit_l0 on the fold's training rows,
  off = the SL-R2 level-E cell offset log(s_E / s_train) of the row's level group (mix_level.row_offset).
  P(row)    = softmax(raw_trees(row) + init(row)).

Because softmax is invariant to a per-row constant, P = softmax(raw + log L0[l0]) x exp(off) renormalised: the engine can
serve the unlevelled table and apply the level from GameState.rec_era (engine/sim.py levelled path) exactly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attribute import models as M
from nhl_sim.shot_attribute.mix_level import apply_cell_offset


def _softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def l3b_init(l0: dict, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    """(n, 78) init_score = log of the levelled L0 (L0m) class probabilities of each row."""
    return np.log(apply_cell_offset(M.predict_l0(l0, r), off))


def lgb_dataset_b(r: pd.DataFrame, off: np.ndarray, l0: dict, ref=None):
    import lightgbm as lgb
    return lgb.Dataset(r[M.LGB_FEATURES].astype(float), label=r.cls.to_numpy(), categorical_feature=["grp"],
                       free_raw_data=False, reference=ref, init_score=l3b_init(l0, r, off))


def predict_l3b(booster, l0: dict, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    raw = booster.predict(r[M.LGB_FEATURES].astype(float), raw_score=True)
    return _softmax(raw + l3b_init(l0, r, off))
