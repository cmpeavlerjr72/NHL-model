"""SM-R1 arms S0 / S1 / S2 (docs/models/miss/experiments.md SM-R1). Target: missed (1) vs on goal (0) per unblocked attempt.

  S0  level + recorded cell x type x strength-group frequency. The base table is the training-row miss rate per (joint class,
      strength group), shrunk (K_BASE pseudo-attempts, labelled) toward the additive-in-logit expectation from the class rate
      pooled over groups and the group rate; the offset is the as-of level logit(s_asof) - logit(s_train) per level group, and
      ten (strength group x period type) intercepts are fitted under it, so that the arm matches the level.
  S1  logistic: S0's logit as offset + 10 intercept corrections + score bucket (6) + home + b2b own / opp + as-of arena miss
      factor + the shooting team's road-only miss rating at a FIXED offset scale s x c (c = the fold-1-train-fitted coefficient,
      raw units; s chosen on fold 1). Fit on gated rows (ES / PP / PK); EN rows take S0 (labelled; L33).
  S2  LightGBM binary on gated rows, init_score = logit of S0 (L32), features S1's minus the rating (no rating in the trees,
      D31): grp, ptype, sc, is_home, b2b_own, b2b_opp, arena_f. EN rows take S0 only (L33).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.block.models import fit_logit_offset  # read only
from nhl_sim.miss.data import logit, sigmoid
from nhl_sim.shot_attribute.tables import N_CELL, N_CLASS, N_TYPE

K_BASE = 20.0
N_L0 = 10
NUM = ["is_home", "b2b_own", "b2b_opp", "arena_f"]
I_RATE = 20                          # column of own_r in the S1 design with the rating
LGB_FEATURES = ["grp", "ptype", "sc", "is_home", "b2b_own", "b2b_opp", "arena_f"]


def fit_base(tr: pd.DataFrame) -> np.ndarray:
    """(N_CLASS, 5) logit of the shrunk training miss rate per (joint class, strength group)."""
    n = np.zeros((N_CLASS, 5))
    m = np.zeros((N_CLASS, 5))
    np.add.at(n, (tr.cls.to_numpy(), tr.grp.to_numpy()), 1.0)
    np.add.at(m, (tr.cls.to_numpy(), tr.grp.to_numpy()), tr.y.to_numpy().astype(float))
    p_all = m.sum() / n.sum()
    ng = n.sum(0)
    p_g = (m.sum(0) + 1.0 * p_all) / (ng + 1.0)
    nc, mc = n.sum(1), m.sum(1)
    cell_n = nc.reshape(N_CELL, N_TYPE).sum(1)
    cell_m = mc.reshape(N_CELL, N_TYPE).sum(1)
    p_cell = (cell_m + K_BASE * p_all) / (cell_n + K_BASE)
    p_c = (mc + K_BASE * np.repeat(p_cell, N_TYPE)) / (nc + K_BASE)
    q = sigmoid(logit(p_c)[:, None] + (logit(p_g) - logit(p_all))[None, :])
    p = (m + K_BASE * q) / (n + K_BASE)
    return logit(p)


def base_offset(base: np.ndarray, r: pd.DataFrame, level_off: np.ndarray) -> np.ndarray:
    return base[r.cls.to_numpy(), r.grp.to_numpy()] + level_off


def fit_s0(tr: pd.DataFrame, level_off: np.ndarray) -> dict:
    base = fit_base(tr)
    off = base_offset(base, tr, level_off)
    X = np.eye(N_L0)[tr.l0.to_numpy()]
    w, nit = fit_logit_offset(X, tr.y.to_numpy(), off, n_free=N_L0)
    return dict(arm="S0", base=base.tolist(), coef=w.tolist(), n_iter=nit)


def s0_logit(m: dict, r: pd.DataFrame, level_off: np.ndarray) -> np.ndarray:
    return base_offset(np.asarray(m["base"]), r, level_off) + np.eye(N_L0)[r.l0.to_numpy()] @ np.asarray(m["coef"])


def predict_s0(m, r, level_off):
    return sigmoid(s0_logit(m, r, level_off))


def design_s1(r: pd.DataFrame, rating: bool) -> np.ndarray:
    sc = np.eye(7)[r.sc.to_numpy()][:, [0, 1, 2, 4, 5, 6]]
    cols = [np.eye(N_L0)[r.l0.to_numpy()], sc, r[NUM].to_numpy(float)]
    if rating:
        cols.append(r[["own_r"]].to_numpy(float))
    return np.hstack(cols)


def fit_s1_free(tr, off):
    """Rating coefficient free (used only to obtain c on fold-1 train)."""
    w, nit = fit_logit_offset(design_s1(tr, True), tr.y.to_numpy(), off)
    return dict(coef=w.tolist(), n_iter=nit)


def rating_off(r, c, s):
    return s * c * r.own_r.to_numpy(float)


def fit_s1(tr, off_s0, c, s) -> dict:
    w, nit = fit_logit_offset(design_s1(tr, False), tr.y.to_numpy(), off_s0 + rating_off(tr, c, s))
    return dict(arm="S1", coef=w.tolist(), s=s, c=c, n_iter=nit)


def predict_s1(m, r, off_s0):
    return sigmoid(design_s1(r, False) @ np.asarray(m["coef"]) + off_s0 + rating_off(r, m["c"], m["s"]))


def lgb_params(num_leaves, min_data, seed, threads=2):
    return dict(objective="binary", learning_rate=0.05, num_leaves=num_leaves, min_data_in_leaf=min_data, seed=seed,
                num_threads=threads, deterministic=True, force_row_wise=True, verbose=-1)


def lgb_dataset(r, init_logit, ref=None):
    import lightgbm as lgb
    return lgb.Dataset(r[LGB_FEATURES].astype(float), label=r.y.to_numpy(), categorical_feature=["grp"],
                       free_raw_data=False, reference=ref, init_score=init_logit)


def predict_s2(bst, r, init_logit):
    return sigmoid(bst.predict(r[LGB_FEATURES].astype(float), raw_score=True) + init_logit)
