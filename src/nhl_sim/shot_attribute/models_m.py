"""SL-R2 arms with the as-of league location-mix level (docs/models/shot_attribute/experiments.md SL-R2; D23).

The level enters every arm as a per-cell offset off = log(s_asof / s_train) with coefficient 1 (mix_level.row_offset),
in training AND prediction; type is not levelled (P(type | cell) carries no offset).
  L0m   L0 (SL-R1) x exp(off) on the cell, renormalised. L0 is a saturated frequency table; it is fit without the
        offset and levelled at prediction (s_train is its own pooled training share, so its baseline is s_train).
  L1m   L1 with the offset inside the cell softmax: an offset-aware multinomial logit, same objective as SL-R1's
        sklearn fit (C * sum NLL + 0.5 ||coef||^2 on standardised features, intercepts unpenalised); P(type | cell)
        is SL-R1's sklearn type model unchanged.
  L3m   L3 (SL-R1 LightGBM multiclass on the joint, same features) with init_score = base + off on each class's
        cell, where base = log of the training rows' class frequency (exactly what LightGBM's boost_from_average starts
        from when no init_score is given; supplying init_score switches that off, so it is restored explicitly and
        stored with the model as `<model>.base.json`). With a zero offset L3m is L3.
  L0o   diagnostic only: L0 x the ORACLE level (never selectable).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from nhl_sim.shot_attribute import models as M
from nhl_sim.shot_attribute.mix_level import apply_cell_offset
from nhl_sim.shot_attribute.tables import N_CELL, N_CLASS, N_TYPE


def _softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def fit_mnl_offset(X: np.ndarray, y: np.ndarray, off: np.ndarray, C: float = M.C_REG, K: int = N_CELL,
                   tol: float = 1e-9) -> tuple[np.ndarray, np.ndarray, int]:
    """Multinomial logit with a fixed per-class offset. Returns (coef (K, p) on the raw X scale, intercept (K,), nit)."""
    sx = M._scale(X)
    Z = X / sx
    n, p = Z.shape
    Y = np.zeros((n, K))
    Y[np.arange(n), y] = 1.0

    def f(theta):
        W = theta[:K * p].reshape(K, p)
        b = theta[K * p:]
        eta = Z @ W.T + b + off
        m = eta.max(1, keepdims=True)
        lse = m[:, 0] + np.log(np.exp(eta - m).sum(1))
        nll = (lse - eta[np.arange(n), y]).sum()
        P = np.exp(eta - lse[:, None])
        R = P - Y
        s = 1.0 / (C * n)                       # objective scaled by 1 / (C n): same optimum, O(1) gradients
        gW = (C * (R.T @ Z) + W) * s
        gb = C * R.sum(0) * s
        return (C * nll + 0.5 * (W ** 2).sum()) * s, np.concatenate([gW.ravel(), gb])

    res = minimize(f, np.zeros(K * p + K), jac=True, method="L-BFGS-B",
                   options=dict(maxiter=20000, maxfun=40000, ftol=1e-15, gtol=tol, maxcor=30))
    W = res.x[:K * p].reshape(K, p)
    return W / sx, res.x[K * p:], int(res.nit)


def fit_l1m(r: pd.DataFrame, off: np.ndarray) -> dict:
    from sklearn.linear_model import LogisticRegression
    X = M.base_design(r, False)
    cw, ci, nit = fit_mnl_offset(X, r.cell.to_numpy().astype(np.int64), off)
    Xt = np.hstack([np.eye(N_CELL)[r.cell.to_numpy()], X])
    st = M._scale(Xt)
    mt = LogisticRegression(C=M.C_REG, max_iter=5000, tol=1e-8)
    mt.fit(Xt / st, r.type6.to_numpy())
    if list(mt.classes_) != list(range(N_TYPE)):
        raise ValueError("a type class is absent from training")
    return dict(arm="L1m", arena=False, cell_coef=cw.tolist(), cell_int=ci.tolist(), type_coef=(mt.coef_ / st).tolist(),
                type_int=mt.intercept_.tolist(), n_iter=[nit, int(mt.n_iter_[0])])


def predict_l1m(m: dict, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    X = M.base_design(r, m["arena"])
    pc = _softmax(X @ np.asarray(m["cell_coef"]).T + np.asarray(m["cell_int"]) + off)
    Wt = np.asarray(m["type_coef"])
    base = X @ Wt[:, N_CELL:].T + np.asarray(m["type_int"])
    out = np.empty((len(r), N_CLASS))
    for c in range(N_CELL):
        out[:, c * N_TYPE:(c + 1) * N_TYPE] = pc[:, [c]] * _softmax(base + Wt[:, c][None, :])
    return out


def class_base(cls: np.ndarray) -> np.ndarray:
    """(78,) log class frequency of the training rows (LightGBM's multiclass boost_from_average, kEpsilon 1e-15)."""
    p = np.bincount(cls, minlength=N_CLASS) / len(cls)
    return np.log(np.maximum(p, 1e-15))


def class_init(off: np.ndarray, base: np.ndarray) -> np.ndarray:
    """(n, 13) cell offset -> (n, 78) init_score = base + the class's cell offset."""
    return np.repeat(off, N_TYPE, axis=1) + base[None, :]


def lgb_dataset_m(r: pd.DataFrame, off: np.ndarray, base: np.ndarray, ref=None):
    import lightgbm as lgb
    return lgb.Dataset(r[M.LGB_FEATURES].astype(float), label=r.cls.to_numpy(), categorical_feature=["grp"],
                       free_raw_data=False, reference=ref, init_score=class_init(off, base))


def predict_l3m(model, r: pd.DataFrame, off: np.ndarray, base: np.ndarray) -> np.ndarray:
    raw = model.predict(r[M.LGB_FEATURES].astype(float), raw_score=True)
    return _softmax(raw + class_init(off, base))


def predict_arm_m(arm: str, model, r: pd.DataFrame, off: np.ndarray) -> np.ndarray:
    if arm in ("L0m", "L0o"):
        return apply_cell_offset(M.predict_l0(model, r), off)
    if arm == "L0":
        return M.predict_l0(model, r)
    if arm == "L1m":
        return predict_l1m(model, r, off)
    if arm.startswith("L3m"):
        booster, base = model
        return predict_l3m(booster, r, off, np.asarray(base))
    raise ValueError(arm)
