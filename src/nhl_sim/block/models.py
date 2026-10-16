"""SB-R1 arms B0 / B1 / B2 (docs/models/block/experiments.md SB-R1). Target: blocked (1) vs not (0) per attempt.

  B0  level only: one-hot (strength group x period type) + level offset logit(s_asof) - logit(s_train), coefficient 1
  B1  logistic: B0 + score bucket (6 dummies, tied is the reference) + home + b2b own / opp + shooting team's
      blocked-against rating + defending team's blocks-for rating + as-of arena block-recording factor
  B2  LightGBM binary on the B1 features + clock + period, init_score = logit of B0's prediction (L32)
Fits are offset logistic regressions (L-BFGS, features standardised, intercepts / one-hots unpenalised via a tiny ridge).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from nhl_sim.block.data import logit, sigmoid

N_L0 = 10
C_REG = 1e4
B1_NUM = ["is_home", "b2b_own", "b2b_opp", "own_r", "opp_r", "arena_f"]
LGB_FEATURES = ["grp", "ptype", "sc", "is_home", "b2b_own", "b2b_opp", "own_r", "opp_r", "arena_f", "clock", "period"]


def design_b0(r: pd.DataFrame) -> np.ndarray:
    return np.eye(N_L0)[r.l0.to_numpy()]


def design_b1(r: pd.DataFrame) -> np.ndarray:
    sc = np.eye(7)[r.sc.to_numpy()][:, [0, 1, 2, 4, 5, 6]]
    return np.hstack([design_b0(r), sc, r[B1_NUM].to_numpy(float)])


def fit_logit_offset(X: np.ndarray, y: np.ndarray, off: np.ndarray, n_free: int = N_L0, C: float = C_REG):
    """Binary logistic with a fixed offset. The first n_free columns (one-hots) are unpenalised; the rest are
    standardised with ridge 1/C. Returns (coef on the raw X scale, nit)."""
    sx = X.std(0)
    sx[:n_free] = 1.0
    sx[sx == 0] = 1.0
    Z = X / sx
    n, p = Z.shape
    pen = np.ones(p)
    pen[:n_free] = 0.0
    y = y.astype(float)

    def f(w):
        eta = Z @ w + off
        ll = np.logaddexp(0.0, eta) - y * eta
        pr = sigmoid(eta)
        g = Z.T @ (pr - y) + (pen * w) / C
        return (ll.sum() + 0.5 * (pen * w ** 2).sum() / C) / n, g / n

    w0 = np.zeros(p)
    res = minimize(f, w0, jac=True, method="L-BFGS-B", options=dict(maxiter=5000, maxfun=10000, ftol=1e-15, gtol=1e-9))
    return res.x / sx, int(res.nit)


def fit_b0(r: pd.DataFrame, off: np.ndarray) -> dict:
    w, nit = fit_logit_offset(design_b0(r), r.y.to_numpy(), off)
    return dict(arm="B0", coef=w.tolist(), n_iter=nit)


def predict_b0(m: dict, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    return sigmoid(design_b0(r) @ np.asarray(m["coef"]) + off)


def fit_b1(r: pd.DataFrame, off: np.ndarray) -> dict:
    w, nit = fit_logit_offset(design_b1(r), r.y.to_numpy(), off)
    return dict(arm="B1", coef=w.tolist(), n_iter=nit)


def predict_b1(m: dict, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    return sigmoid(design_b1(r) @ np.asarray(m["coef"]) + off)


def lgb_params(num_leaves, min_data, seed, threads=4):
    return dict(objective="binary", learning_rate=0.05, num_leaves=num_leaves, min_data_in_leaf=min_data, seed=seed,
                num_threads=threads, deterministic=True, force_row_wise=True, verbose=-1)


def lgb_dataset(r: pd.DataFrame, init_logit: np.ndarray, ref=None):
    import lightgbm as lgb
    return lgb.Dataset(r[LGB_FEATURES].astype(float), label=r.y.to_numpy(), categorical_feature=["grp"],
                       free_raw_data=False, reference=ref, init_score=init_logit)


def predict_b2(booster, r: pd.DataFrame, init_logit: np.ndarray) -> np.ndarray:
    return sigmoid(booster.predict(r[LGB_FEATURES].astype(float), raw_score=True) + init_logit)
