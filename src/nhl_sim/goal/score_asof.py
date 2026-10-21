"""G-R4 score-state terms of the goal model (docs/models/goal/experiments.md G-R4; D48, INV-74, INV-71).

Score buckets (shooting team's view, BEFORE the shot): sc 0..6 = shooter lead -3+..+3+ ->
    b 0 trail 2+ (sc 0, 1) | b 1 trail 1 (sc 2) | b 2 tied (sc 3, reference) | b 3 lead 1 (sc 4) | b 4 lead 2+ (sc 5, 6)
EAF rows (shooting team's own goalie pulled) carry no score term (L33 / D26, as in C1s).

C1s non-score logit (frozen, per fold): the fold's C1s linear predictor without its score dummies:
    C0 logit (M1 K500) + C1s sg intercepts + home + b2b own / opp + arena factor + team finishing (fixed scale)
    + goalie offset s_t x z (as-of scale H90 P2000)
C1s-sa  : non-score logit + d_t[bucket], d_t (4,) = the four bucket log-odds deviations relative to tied, as-of:
    window   every in-scope SOG dated strictly before d, weight 0.5^((d - date_i) / H)
    fit      four-parameter logistic with the offset fixed, maximising
                 sum_i w_i ll_i(d) - 0.5 (d - d_prev)' (P x Ibar) (d - d_prev),
             Ibar = sum_i w_i p_i (1 - p_i) x_i x_i' / sum_i w_i (per-SOG Fisher information, diagonal since the dummies
             are disjoint; the prior counts as P SOG over all buckets), re-read at every Newton iterate; the SL-R7 / SB-R5
             solver `_newton2` (eigen-restricted step, decrement-halving safeguard), max |step| < 1e-8
    floor    AS-1 (f = 0.5): prior precision P x (Ibar + f I_ref) while lambda_min(Ibar) < f lambda_min(I_ref);
             I_ref = Ibar at d = 0 over the fold's 2021-22 in-scope rows, unweighted
    start    d = 0; 2021-22 is burn-in, never judged or served
    snapshot created_at = the previous date's last puck drop + 6 h, asserted < puck_drop of every game on d
C1s-sp  : C1s with the score dummies replaced by bucket x period (P1 / P2 / P3) dummies, tied-P1 reference (14), fitted
          on the training seasons; OT rows (period >= 4) and EAF rows carry no score term (labelled).
C1s-sap : C1s-sa + pooled period-interaction deviations: per bucket b, P2 / P3 dummies centred by the bucket's training
          period shares, so each bucket's training-weighted mean interaction is 0 ("bucket x period minus bucket main
          effect"); fitted on the training seasons with the C1s-sa logit as offset; OT / EAF rows carry none.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.block.models import fit_logit_offset  # read-only reuse
from nhl_sim.goal.data import N_SG, sigmoid
from nhl_sim.goal.models import EAF, design_base
from nhl_sim.shot_attribute.scale import _days, _frame, _newton2, _snap_rows, floor_binds  # template (read-only)

BUCKET_OF_SC = np.array([0, 0, 1, 2, 3, 4, 4], np.int64)
B_NAMES = ("trail2+", "trail1", "tied", "lead1", "lead2+")
TIED = 2
DEV_B = (0, 1, 3, 4)
N_DEV = 4
H_GRID = (90, 180, 365)
P_GRID = (2000, 10000)
GRID_ORDER = [(H, P) for H in sorted(H_GRID, reverse=True) for P in sorted(P_GRID, reverse=True)]   # simplest first
F_FLOOR = 0.5
SCORE_COLS = list(range(N_SG, N_SG + 6))                 # design_base columns of the C1s score dummies
NONSCORE_COLS = [c for c in range(N_SG + 6 + 4) if c not in SCORE_COLS]


def skey(H, P):
    return f"H{int(H)}_P{int(P)}"


def bucket(r: pd.DataFrame) -> np.ndarray:
    return BUCKET_OF_SC[r.sc.to_numpy().astype(np.int64)]


def dev_design(r: pd.DataFrame) -> np.ndarray:
    """(n, 4) one-hots of the non-tied buckets (trail2+, trail1, lead1, lead2+); zero on EAF rows."""
    b = bucket(r)
    X = (b[:, None] == np.asarray(DEV_B)[None, :]).astype(float)
    X[(r.sg == EAF).to_numpy()] = 0.0
    return X


def nonscore_logit(coef, r: pd.DataFrame, fixed_off: np.ndarray) -> np.ndarray:
    """C1s linear predictor without its score dummies. fixed_off = C0 logit + team offset + goalie offset."""
    c = np.asarray(coef, float)
    X = design_base(r)
    return X[:, NONSCORE_COLS] @ c[NONSCORE_COLS] + fixed_off


def c1s_score_term(coef, r: pd.DataFrame) -> np.ndarray:
    c = np.asarray(coef, float)
    return design_base(r)[:, SCORE_COLS] @ c[SCORE_COLS]


# ------------------------------------------------------------------------------------------------ as-of estimator
def info_ref(off, X):
    """AS-1 I_ref (K x K): per-SOG Fisher information at d = 0, unweighted, over the given rows."""
    p = sigmoid(np.asarray(off, float))
    v = p * (1 - p)
    X = np.asarray(X, float)
    return (X * v[:, None]).T @ X / len(v)


def _stats(off, y, X, w):
    sw = float(w.sum())

    def stats(dv):
        p = sigmoid(off + X @ dv)
        v = w * p * (1 - p)
        return X.T @ (w * (y - p)), (X * v[:, None]).T @ X, sw
    return stats


def fit_once(off, y, X, w=None, d0=None):
    """Unshrunk weighted MLE of the deviations (P = 0; per-season diagnostic)."""
    X = np.asarray(X, float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    d0 = np.zeros(X.shape[1]) if d0 is None else np.asarray(d0, float)
    return _newton2(d0, _stats(np.asarray(off, float), np.asarray(y, float), X, w), 0.0)[0]


def asof_dev(date, drop, off, y, X, H, P, d0=None, floor=None):
    """Per-date as-of deviation vector (columns d_0..d_{K-1}, in DEV_B order). Rows dated < d only.
    floor = (f, I_ref) (AS-1) or None."""
    order, ds, days, start, end = _days(date)
    off = np.asarray(off, float)[order]
    y = np.asarray(y, float)[order]
    X = np.asarray(X, float)[order]
    K = X.shape[1]
    dr = pd.to_datetime(pd.Series(drop), utc=True).iloc[order].reset_index(drop=True)
    meta = _snap_rows(days, start, end, dr)
    dnum = ds.astype(np.int64)
    d = np.zeros(K) if d0 is None else np.asarray(d0, float)
    out = []
    for k, day in enumerate(days):
        nb = int(start[k])
        bnd = False
        if nb > 0:
            w = 0.5 ** ((day.astype(np.int64) - dnum[:nb]) / H)
            st = _stats(off[:nb], y[:nb], X[:nb], w)
            d, neff = _newton2(d, st, P, floor=floor)
            if floor is not None:
                _, I_, sw_ = st(d)
                bnd = bool(sw_ > 0 and np.trace(I_) > 0 and floor_binds(I_ / sw_, floor))
        else:
            neff = 0.0
        rec = dict(meta[k])
        rec.update({f"d_{j}": float(d[j]) for j in range(K)})
        rec.update(n_eff=neff, n_before=nb)
        if floor is not None:
            rec["floor_binds"] = bnd
        out.append(rec)
    return _frame(out)


def attach_dev(dates, sc: pd.DataFrame, K: int = N_DEV) -> np.ndarray:
    """(n, K) per-row deviations from a per-date snapshot frame (one cell), keyed by game date."""
    idx = pd.to_datetime(sc.date).to_numpy("datetime64[D]")
    k = pd.to_datetime(pd.Series(dates)).to_numpy("datetime64[D]")
    D = np.column_stack([pd.Series(sc[f"d_{j}"].to_numpy(), index=idx).reindex(k).to_numpy() for j in range(K)])
    if np.isnan(D).any():
        raise ValueError("rows without a deviation snapshot")
    return D


def sa_logit(nonscore, r, Dv):
    """C1s-sa logit: non-score logit + the row's bucket deviation (EAF rows none)."""
    return nonscore + (dev_design(r) * Dv).sum(1)


# --------------------------------------------------------------------------------------------- pooled period arms
def period3(r: pd.DataFrame) -> np.ndarray:
    """0 / 1 / 2 for P1 / P2 / P3, -1 for OT (period >= 4)."""
    p = r.period.to_numpy().astype(np.int64)
    return np.where(p <= 3, p - 1, -1)


def sp_design_score(r: pd.DataFrame) -> np.ndarray:
    """(n, 14) bucket x period dummies, tied-P1 reference; zero on OT and EAF rows."""
    b, p = bucket(r), period3(r)
    cell = b * 3 + p
    ref = TIED * 3 + 0
    cols = [c for c in range(15) if c != ref]
    X = (cell[:, None] == np.asarray(cols)[None, :]).astype(float)
    X[(p < 0) | (r.sg == EAF).to_numpy()] = 0.0
    return X


SP_COLS = [c for c in range(15) if c != TIED * 3]       # bucket * 3 + period index of each sp score column


def sp_design(r):
    """sg one-hots (6) | bucket x period (14) | is_home, b2b_own, b2b_opp, arena_f."""
    X = design_base(r)
    return np.hstack([X[:, :N_SG], sp_design_score(r), X[:, N_SG + 6:]])


def fit_sp(r, fixed_off):
    w, nit = fit_logit_offset(sp_design(r), r.y.to_numpy(), fixed_off, n_free=N_SG)
    return dict(arm="C1s-sp", coef=w.tolist(), n_iter=nit)


def predict_sp(m, r, fixed_off):
    return sigmoid(sp_design(r) @ np.asarray(m["coef"]) + fixed_off)


def sp_score_table(m) -> np.ndarray:
    """(5, 3) bucket x period log-odds of C1s-sp (tied-P1 = 0)."""
    c = np.asarray(m["coef"])[N_SG:N_SG + 14]
    T = np.zeros(15)
    T[SP_COLS] = c
    return T.reshape(5, 3)


def sap_shares(tr: pd.DataFrame) -> np.ndarray:
    """(5, 3) training period shares within each bucket (regulation, non-EAF rows)."""
    b, p = bucket(tr), period3(tr)
    m = (p >= 0) & (tr.sg != EAF).to_numpy()
    n = np.zeros((5, 3))
    np.add.at(n, (b[m], p[m]), 1.0)
    return n / n.sum(1, keepdims=True)


def sap_design(r: pd.DataFrame, shares: np.ndarray) -> np.ndarray:
    """(n, 10) centred interactions: column (b, q), q in P2 / P3: 1[b, q] - shares[b, q] 1[b]; zero on OT / EAF."""
    b, p = bucket(r), period3(r)
    cols = []
    for bb in range(5):
        inb = (b == bb).astype(float)
        for q in (1, 2):
            cols.append(((b == bb) & (p == q)).astype(float) - shares[bb, q] * inb)
    X = np.column_stack(cols)
    X[(p < 0) | (r.sg == EAF).to_numpy()] = 0.0
    return X


def fit_sap(r, sa_off, shares):
    w, nit = fit_logit_offset(sap_design(r, shares), r.y.to_numpy(), sa_off, n_free=0)
    return dict(arm="C1s-sap", coef=w.tolist(), shares=np.asarray(shares).tolist(), n_iter=nit)


def predict_sap(m, r, sa_off):
    return sigmoid(sap_design(r, np.asarray(m["shares"])) @ np.asarray(m["coef"]) + sa_off)


def sap_term_table(m) -> np.ndarray:
    """(5, 3) interaction log-odds per bucket x period implied by the C1s-sap coefficients (each row's
    training-share-weighted mean is 0)."""
    sh, c = np.asarray(m["shares"]), np.asarray(m["coef"]).reshape(5, 2)
    T = np.zeros((5, 3))
    for b in range(5):
        raw = np.array([0.0, c[b, 0], c[b, 1]])
        T[b] = raw - (sh[b] * raw).sum()
    return T


# ------------------------------------------------------------------------------------------------ bucket check
def bucket_ratio(p, y, b, gp=None, G=None, W=None):
    """served / actual conversion per bucket relative to tied: (sum p_b / sum y_b) / (sum p_tied / sum y_tied).
    Optional game-block bootstrap SE (gp = game position per row, W = (B, G) resample counts)."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    P_ = np.bincount(b, weights=p, minlength=5)
    Y_ = np.bincount(b, weights=y, minlength=5)
    rat = (P_ / Y_) / (P_[TIED] / Y_[TIED])
    se = None
    if W is not None:
        PG = np.zeros((G, 5))
        YG = np.zeros((G, 5))
        np.add.at(PG, (gp, b), p)
        np.add.at(YG, (gp, b), y)
        Pb, Yb = W @ PG, W @ YG
        Rb = (Pb / Yb) / (Pb[:, [TIED]] / Yb[:, [TIED]])
        se = Rb.std(0)
    return rat, se
