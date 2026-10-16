"""SL-R6 arm L1x (docs/models/shot_attribute/experiments.md SL-R6; D32): a multinomial-logit deviation layer on top of
the L0s baseline (levelled by E), with the team shot-quality ratings entering as FIXED-SCALE offsets along one
"quality" direction.

  logit_k = log L0s_lev_k + s_f * own_r * c_k,g + s_a * opp_r * c_k,g + (x - x_bar_train) . W_k      (non-EN rows)
  EN-for / EN-against rows: L0s levelled only (no deviation layer; L33, SL-R4).

  c_k,g  = log xG_ref of class k in the row's strength group g, centred over the 78 classes (the centring is a per-row
           constant, so it cancels in the softmax; cosmetic). Classes with xG_ref = 0 (no training goals; about 0.1%
           of ES attempts) take log(XG_FLOOR) (labelled).
  x      = home, score bucket (6 dummies, reference tied), back-to-back own / opp: the fitted terms (no ratings),
           centred on the training means (so a mean row is served L0s; labelled: there are no free class intercepts,
           L0s carries them).
  s_f, s_a: fitted freely on fold 1 (the "fold-1-fitted s"); in the arm they are FIXED at m x the fold-1 fit, the
           common multiplier m chosen on fold 1 (D27 / D29 fixed-scale form), and only W is refit per fold.
Fit: penalised (ridge RIDGE on W only, per row-mean loss) maximum likelihood, scipy L-BFGS-B; deterministic given
the start point (the seed arm starts from a seeded random W).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from nhl_sim.shot_attribute import models_s as MS
from nhl_sim.shot_attribute.tables import N_CLASS

XG_FLOOR = 0.005
RIDGE = 1e-5                       # on the per-row mean loss (= 1e-5 x n in sum form; prior SD on W about 1 / sqrt(1e-5 n))
REF_CLASS = 4 * 6 + 0               # gauge: W column of the reference class (20-30 ft, <= 30 deg, wrist+snap) is pinned at 0
FEATS = ["is_home", "sc0", "sc1", "sc2", "sc4", "sc5", "sc6", "b2b_own", "b2b_opp"]


def qdir(xg: np.ndarray) -> np.ndarray:
    c = np.log(np.maximum(xg, XG_FLOOR))
    return c - c.mean(0, keepdims=True)


def feat_matrix(r: pd.DataFrame) -> np.ndarray:
    sc = r.sc.to_numpy().astype(np.int64)
    cols = [r.is_home.to_numpy(float)] + [(sc == k).astype(float) for k in (0, 1, 2, 4, 5, 6)] + \
           [r.b2b_own.to_numpy(float), r.b2b_opp.to_numpy(float)]
    return np.column_stack(cols)


def _softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


class Fitter:
    """Holds the fixed per-row inputs of one training set (non-EN rows only)."""

    def __init__(self, base_logp, C, own, opp, X, y, xbar=None):
        self.B, self.C, self.own, self.opp, self.y = base_logp, C, own, opp, y
        self.xbar = X.mean(0) if xbar is None else xbar
        self.X = X - self.xbar
        self.n = len(y)

    def logits(self, W, sf, sa):
        return self.B + (sf * self.own + sa * self.opp)[:, None] * self.C + self.X @ W

    def fit(self, s_fixed=None, seed=None, maxiter=3000):
        F = self.X.shape[1]
        rng = np.random.default_rng(seed) if seed is not None else None
        w0 = rng.normal(0, 0.05, (F, N_CLASS)) if rng is not None else np.zeros((F, N_CLASS))
        w0[:, REF_CLASS] = 0.0
        w0 = w0.ravel()
        free_s = s_fixed is None
        x0 = np.concatenate([w0, [0.0, 0.0]]) if free_s else w0
        idx = np.arange(self.n)

        def f(theta):
            W = theta[:F * N_CLASS].reshape(F, N_CLASS)
            sf, sa = (theta[-2], theta[-1]) if free_s else s_fixed
            Z = self.logits(W, sf, sa)
            zy = Z[idx, self.y]
            mx = Z.max(1)
            Z -= mx[:, None]
            np.exp(Z, out=Z)
            se = Z.sum(1)
            loss = (np.log(se) + mx - zy).mean() + 0.5 * RIDGE * (W ** 2).sum()
            P = Z
            P /= se[:, None]
            P[idx, self.y] -= 1.0
            P /= self.n
            gW = self.X.T @ P + RIDGE * W
            gW[:, REF_CLASS] = 0.0
            g = [gW.ravel()]
            if free_s:
                gc = (P * self.C).sum(1)
                g.append([float(gc @ self.own), float(gc @ self.opp)])
            return loss, np.concatenate([g[0], np.asarray(g[1], float)]) if free_s else g[0]

        res = minimize(f, x0, jac=True, method="L-BFGS-B", options=dict(maxiter=maxiter, gtol=1e-8, ftol=1e-13,
                                                                       maxcor=30))
        th = res.x
        W = th[:F * N_CLASS].reshape(F, N_CLASS)
        sf, sa = (float(th[-2]), float(th[-1])) if free_s else (float(s_fixed[0]), float(s_fixed[1]))
        return dict(W=W.tolist(), s_f=sf, s_a=sa, xbar=self.xbar.tolist(), loss=float(res.fun), nit=int(res.nit),
                    converged=bool(res.success), msg=str(res.message), s_free=free_s)

    def s_se(self, m, game_ids):
        """SEs of (s_f, s_a) conditional on W (model-based and game-cluster sandwich); labelled conditional."""
        Z = self.logits(np.asarray(m["W"]), m["s_f"], m["s_a"])
        P = _softmax(Z)
        idx = np.arange(self.n)
        Ec = (P * self.C).sum(1)
        Vc = (P * self.C ** 2).sum(1) - Ec ** 2
        R = np.column_stack([self.own, self.opp])
        H = (R * Vc[:, None]).T @ R
        sc = R * (self.C[idx, self.y] - Ec)[:, None]
        gi = pd.factorize(np.asarray(game_ids))[0]
        S = np.zeros((gi.max() + 1, 2))
        np.add.at(S, gi, sc)
        Hi = np.linalg.inv(H)
        V = Hi @ (S.T @ S) @ Hi
        return dict(se_model=np.sqrt(np.diag(Hi)).tolist(), se_cluster=np.sqrt(np.diag(V)).tolist())


def inputs(r: pd.DataFrame, l0s: dict, off: np.ndarray, xg: np.ndarray, own_col="own_r", opp_col="opp_r"):
    """Per-row inputs: log L0s levelled, quality direction C (n, 78), ratings, features, labels."""
    B = np.log(MS.l0s_levelled(l0s, r, off))
    C = qdir(xg)[:, r.grp.to_numpy()].T
    return B, C, r[own_col].to_numpy(float), r[opp_col].to_numpy(float), feat_matrix(r), r.cls.to_numpy().astype(np.int64)


def fitter_for(r, l0s, off, xg, own_col="own_r", opp_col="opp_r", xbar=None):
    m = MS.booster_rows(r)
    rr = r[m]
    B, C, own, opp, X, y = inputs(rr, l0s, off[m], xg, own_col, opp_col)
    return Fitter(B, C, own, opp, X, y, xbar), rr


def predict_l1x(m: dict, l0s: dict, r: pd.DataFrame, off: np.ndarray, xg: np.ndarray, own_col="own_r",
                opp_col="opp_r") -> np.ndarray:
    """Non-EN rows: softmax(log L0s levelled + fixed-scale rating tilt + fitted terms); EN rows: L0s levelled."""
    P = MS.l0s_levelled(l0s, r, off)
    msk = MS.booster_rows(r)
    if msk.any():
        rr = r[msk]
        B, C, own, opp, X, _ = inputs(rr, l0s, off[msk], xg, own_col, opp_col)
        Z = B + (m["s_f"] * own + m["s_a"] * opp)[:, None] * C + (X - np.asarray(m["xbar"])) @ np.asarray(m["W"])
        P[msk] = _softmax(Z)
    return P
