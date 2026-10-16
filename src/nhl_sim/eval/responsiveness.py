"""D32 slope-based responsiveness gate.

Rows are bucketed by decile of the as-of rating. b = n-weighted least-squares slope of the ACTUAL bucket means on the
PREDICTED (sim) bucket means. R = 1 / b = predicted spread per unit of actual. Band [0.8, 1.2] on R. The CI is a
game-block bootstrap (games, not rows, are resampled; buckets are held fixed at the point-estimate deciles, so the
bootstrap varies the data not the bucketing). CI wider than the band -> UNDERPOWERED (the point estimate still gates, D18).
The old Q5-Q1 endpoint ratio (quintiles) is reported but does not gate.

Bucket mean = sum(w * y) / sum(w). For rate quantities pass y = per-row rate and w = exposure (pred_weights for the
predicted side if its exposure differs); the regression weight is the number of rows in the bucket.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BAND = (0.8, 1.2)


def _buckets(rating, n):
    r = pd.Series(np.asarray(rating, float)).rank(method="first")
    return pd.qcut(r, n, labels=False).to_numpy()


def _stats(counts_g, gp, q, nb, pred, actual, wa, wp):
    """counts_g: per-game resample multiplicity (G,). Returns (R, b, bucket pred means, bucket actual means, n)."""
    c = counts_g[gp]
    n = np.bincount(q, weights=c, minlength=nb)
    sa = np.bincount(q, weights=c * wa, minlength=nb)
    sp = np.bincount(q, weights=c * wp, minlength=nb)
    ya = np.bincount(q, weights=c * wa * actual, minlength=nb) / np.maximum(sa, 1e-12)
    yp = np.bincount(q, weights=c * wp * pred, minlength=nb) / np.maximum(sp, 1e-12)
    ok = n > 0
    x, y, w = yp[ok], ya[ok], n[ok]
    xm, ym = np.average(x, weights=w), np.average(y, weights=w)
    b = np.sum(w * (x - xm) * (y - ym)) / np.sum(w * (x - xm) ** 2)
    return (1.0 / b if b != 0 else np.inf), b, yp, ya, n


def slope_ratio(pred, actual, rating, weights, game_ids, n_buckets=10, n_boot=1000, seed=0, pred_weights=None):
    pred, actual, rating = (np.asarray(v, float) for v in (pred, actual, rating))
    wa = np.asarray(weights, float)
    wp = wa if pred_weights is None else np.asarray(pred_weights, float)
    games, gp = np.unique(np.asarray(game_ids), return_inverse=True)
    G = len(games)
    q = _buckets(rating, n_buckets)
    R, b, yp, ya, n = _stats(np.ones(G), gp, q, n_buckets, pred, actual, wa, wp)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        boots[i] = _stats(rng.multinomial(G, np.full(G, 1.0 / G)).astype(float), gp, q, n_buckets,
                          pred, actual, wa, wp)[0]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    # old Q5-Q1 endpoint ratio on quintiles (reported only)
    q5 = _buckets(rating, 5)
    c1 = np.ones(G)[gp]
    def qm(v, w):
        return np.bincount(q5, weights=c1 * w * v, minlength=5) / np.bincount(q5, weights=c1 * w, minlength=5)
    pm, am = qm(pred, wp), qm(actual, wa)
    old = float((pm[4] - pm[0]) / (am[4] - am[0])) if am[4] != am[0] else float("nan")
    table = pd.DataFrame({"n": n, "pred": yp, "actual": ya}, index=range(1, n_buckets + 1))
    return dict(R=float(R), b=float(b), ci=(float(lo), float(hi)), underpowered=bool((hi - lo) > (BAND[1] - BAND[0])),
                status="PASS" if BAND[0] <= R <= BAND[1] else "FAIL", old_q5q1=old, table=table, n_games=int(G))
