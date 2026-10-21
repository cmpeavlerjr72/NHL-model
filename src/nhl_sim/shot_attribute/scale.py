"""SL-R7 as-of response scale on Qa (docs/models/shot_attribute/experiments.md SL-R7; INV-59 / INV-53; the G-R3
template `src/nhl_sim/goal/scale.py`, two slopes).

L1x-as (non-EN rows):
  logit_k = A_k + (s_for,t x zf + s_against,t x za) x c_k
  A       = log L0s levelled (M1 K500) + (x - x_bar) . W, the FROZEN home / score / rest terms of the fold's SL-R6
            L1x-ot0 fit (score terms zero on OT rows, D38); fixed offset
  c       = the frozen quality direction (centred log xG_ref of the class in the row's strength group, models_x.qdir)
  zf, za  = own Qa "for" / opponent Qa "against" divided by their SD over the fold's 2021-22 in-scope rows (unit only)
  (s_for,t, s_against,t): an as-of estimate per game date d:
    window   every in-scope (non-EN) attempt dated strictly before d, across seasons, weight 0.5^((d - date_i) / H)
    fit      two-parameter multinomial-logit slope with the offset fixed, maximising
                 sum_i w_i ll_i(s) - 0.5 (s - s_prev)' (P x Ibar) (s - s_prev)
             Ibar = sum_i w_i Var_i(c) z_i z_i' / sum_i w_i (the per-attempt Fisher information matrix at the current
             iterate; the prior counts as P attempts); s_prev = the previous game date's pair; Newton from s_prev to
             max |step| < 1e-8 (the G-R3 iteration, Ibar re-read at every iterate)
    carry    a direction with no Fisher information in the window (season-opening all-zero ratings, or the
             collinear near-zero ratings of the first days) keeps s_prev: the Newton step is restricted to the
             eigen-directions of the information with eigenvalue > EIG_REL x the largest (the G-R3 0/0 fix, in 2-D)
    start    s = (0, 0) before any data (2021-22 burn-in, never judged)
    snapshot created_at = the previous game date's last puck drop + 6 h, asserted < puck_drop of every game on d

Evaluation (labelled numerical method, not a model choice): the window sums are maintained by exact exponential-decay
recursion over per-day moment sums, and each row's score / information is evaluated through the Taylor series of its
cumulant function in t = s . z, K_i'(t) = sum_n kappa_{n+1,i} t^n / n!, truncated at order ORDER. The series is used
for a Newton iterate only while the exact max |t| over the window (convex hull of the window's z points) is at most
SAFE x pi / range(c), half of a guaranteed lower bound on its radius; otherwise the iterate is evaluated directly on the
window's rows (the near-zero-rating burn-in days of 2021-22). `asof_scale_exact` evaluates every iterate directly (the
reference used by the tests and the real-data spot check).

AS-1 prior-precision floor (docs/models/asof_scale/experiments.md AS-1; INV-62, L38). Optional `floor=(f, I_ref)`:
the prior precision is P x Ibar while lambda_min(Ibar) >= f x lambda_min(I_ref), and P x (Ibar + f x I_ref)
otherwise, read at every Newton iterate (Ibar is re-read at every iterate). I_ref (2 x 2) = Ibar at s = 0 over every
in-scope row of the fold's burn-in season (2021-22), unweighted, ratings in their standard units (`info_ref`).
floor=None is the SL-R7 construction, bit-for-bit.
"""
from __future__ import annotations

from math import comb, factorial

import numpy as np
import pandas as pd

from nhl_sim.strength_state.tables import assert_pregame

S0 = (0.0, 0.0)
H_GRID = (45, 90, 180, 365)
P_GRID = (2000, 10000)
# simplest first: larger H, then larger P (spec)
GRID_ORDER = [(H, P) for H in sorted(H_GRID, reverse=True) for P in sorted(P_GRID, reverse=True)]
ORDER = 20                  # Taylor order of K'(t) and K''(t) (needs cumulants kappa_1 .. kappa_{ORDER + 2})
TOL = 1e-8
MAX_IT = 500
SAFE = 0.5                  # series used only while max |t| <= SAFE x pi / range(c) (a lower bound on its radius)
EIG_REL = 1e-10


def skey(H, P):
    return f"H{int(H)}_P{int(P)}"


def _softmax(Z):
    Z = Z - Z.max(1, keepdims=True)
    np.exp(Z, out=Z)
    Z /= Z.sum(1, keepdims=True)
    return Z


def row_cumulants(A: np.ndarray, C: np.ndarray, order: int = ORDER) -> np.ndarray:
    """(n, order + 2) cumulants kappa_1 .. kappa_{order+2} of c (per row C[i]) under softmax(A[i])."""
    p = _softmax(np.array(A, float, copy=True))
    mu = (p * C).sum(1)
    d = C - mu[:, None]
    nmax = order + 2
    m = np.zeros((len(A), nmax + 1))
    dp = np.ones_like(d)
    for r in range(1, nmax + 1):
        dp = dp * d
        if r >= 2:
            m[:, r] = (p * dp).sum(1)
    kap = np.zeros((len(A), nmax + 1))
    for n in range(2, nmax + 1):
        v = m[:, n].copy()
        for k in range(2, n - 1):
            v -= comb(n - 1, k - 1) * kap[:, k] * m[:, n - k]
        kap[:, n] = v
    kap[:, 1] = mu
    return kap[:, 1:]


def _solve(Hf, G):
    """Newton step restricted to the eigen-directions of Hf with eigenvalue > EIG_REL x the largest: directions
    without information in the window (all-zero or collinear early-season ratings) keep s_prev."""
    lam, V = np.linalg.eigh(Hf)
    keep = lam > EIG_REL * lam.max()
    return V[:, keep] @ ((V[:, keep].T @ G) / lam[keep])


def info_ref(A, C, zf, za):
    """AS-1 I_ref: the per-attempt Fisher information matrix at s = 0, unweighted, over the given rows."""
    p = _softmax(np.array(A, float, copy=True))
    C = np.asarray(C, float)
    E = (p * C).sum(1)
    V = (p * C * C).sum(1) - E * E
    Z2 = np.column_stack([zf, za]).astype(float)
    return (Z2 * V[:, None]).T @ Z2 / len(V)


def floor_binds(Ibar, floor):
    """AS-1: whether the floor binds for a window information Ibar (per-event)."""
    f, Iref = floor
    return not np.linalg.eigvalsh(Ibar)[0] >= f * np.linalg.eigvalsh(Iref)[0]


def _newton2(s_prev, stats, P, tol=TOL, max_it=MAX_IT, floor=None):
    """stats(s) -> (g (2,), I (2, 2), sw): data score and information of the weighted window at s.
    Solves the template's stationarity condition G(s) = g(s) - P Ibar(s) (s - s_prev) = 0 (Ibar = I / sw re-read at
    every iterate) by Newton from s_prev. Optimiser safeguard (does not move the solution): if the full step does not
    reduce the Newton decrement G' Hf^-1 G, it is halved until it does (reached only in the near-zero-rating burn-in
    days, where the information is tiny and the full step overshoots); full steps are taken otherwise, as in G-R3."""
    s_prev = np.asarray(s_prev, float)

    def ev(s):
        g, I, sw = stats(s)
        if not sw > 0 or not np.trace(I) > 0:
            return None
        Ibar = I / sw
        if floor is not None and floor_binds(Ibar, floor):          # AS-1
            Ibar = Ibar + floor[0] * np.asarray(floor[1], float)
        G = g - P * Ibar @ (s - s_prev)
        Hf = I + P * Ibar
        d = _solve(Hf, G)
        return d, float(G @ d), float(sw)
    s = s_prev.copy()
    cur = ev(s)
    if cur is None:
        return s_prev.copy(), float(stats(s)[2])
    for _ in range(max_it):
        d, phi, sw = cur
        if np.abs(d).max() < tol:
            s = s + d
            break
        alpha = 1.0
        for _h in range(60):
            new = ev(s + alpha * d)
            if new is not None and np.isfinite(new[1]) and new[1] < phi:
                break
            alpha *= 0.5
        if new is None:
            raise FloatingPointError("as-of scale: lost information during the line search")
        s = s + alpha * d
        cur = new
    else:
        raise FloatingPointError(f"as-of scale did not converge (s {s})")
    if not np.isfinite(s).all():
        raise FloatingPointError("as-of scale diverged")
    return s, sw


def _days(date):
    d = pd.to_datetime(pd.Series(date)).to_numpy("datetime64[D]")
    order = np.argsort(d, kind="stable")
    ds = d[order]
    days = np.unique(ds)
    return order, ds, days, np.searchsorted(ds, days, "left"), np.searchsorted(ds, days, "right")


def _frame(out):
    f = pd.DataFrame(out)
    f["created_at"] = pd.to_datetime(f.created_at, utc=True)
    assert_pregame(f.rename(columns={"first_drop": "puck_drop"}))
    return f


def _snap_rows(days, start, end, dr):
    """first / last puck drop per date and created_at = previous date's last drop + 6 h."""
    rows, last = [], None
    for k, day in enumerate(days):
        drops = dr.iloc[start[k]:end[k]]
        rows.append(dict(date=pd.Timestamp(day), created_at=None if last is None else last + pd.Timedelta(hours=6),
                         first_drop=drops.min(), last_drop=drops.max()))
        last = drops.max()
    return rows


# --------------------------------------------------------------------------------------------- window evaluation
def _exact_stats(A, C, cy, Z2, w):
    def stats(sv):
        t = Z2 @ sv
        p = _softmax(A + t[:, None] * C)
        E = (p * C).sum(1)
        V = (p * C * C).sum(1) - E * E
        return Z2.T @ (w * (cy - E)), (Z2 * (w * V)[:, None]).T @ Z2, float(w.sum())
    return stats


def fit_once(A, C, y, zf, za, w=None, s0=S0):
    """Unshrunk weighted MLE of the slope pair on the given rows (P = 0; the season-own-MLE diagnostic)."""
    A, C = np.asarray(A, float), np.asarray(C, float)
    y = np.asarray(y, np.int64)
    Z2 = np.column_stack([zf, za]).astype(float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    st = _exact_stats(A, C, C[np.arange(len(y)), y], Z2, w)
    return _newton2(np.asarray(s0, float), st, 0.0)[0]


def daily_moments(date, drop, A, C, y, zf, za, order=ORDER, chunk=50000):
    """Rows sorted by game date, plus per date the weight-1 sums of the rows dated on that date:
       sw, Y_j = sum c_y z_j, Mg[n, a] = sum kappa_{n+1} zf^a za^(n+1-a), Mh[n, a] = sum kappa_{n+2} zf^a za^(n+2-a),
       n = 0 .. order; and the running max |zf|, |za| over the rows dated before each date (the |t| bound)."""
    order_ix, ds, days, start, end = _days(date)
    A = np.asarray(A, float)[order_ix]
    C = np.asarray(C, float)[order_ix]
    y = np.asarray(y, np.int64)[order_ix]
    zf, za = np.asarray(zf, float)[order_ix], np.asarray(za, float)[order_ix]
    kap = np.empty((len(y), order + 2))
    for i in range(0, len(y), chunk):
        kap[i:i + chunk] = row_cumulants(A[i:i + chunk], C[i:i + chunk], order)
    cy = C[np.arange(len(y)), y]
    dr = pd.to_datetime(pd.Series(drop), utc=True).iloc[order_ix].reset_index(drop=True)
    D = order + 3
    nd = len(days)
    sw = np.zeros(nd)
    Y = np.zeros((nd, 2))
    Mg = np.zeros((nd, order + 1, D))      # index a (power of zf); power of za = n + 1 - a
    Mh = np.zeros((nd, order + 1, D))      # power of za = n + 2 - a
    zmax_day = np.zeros((nd, 2))
    hull = np.zeros((0, 2))
    hull_before = []                       # extreme points of every (zf, za) dated before the date: max |t| = max |V s|
    for k in range(nd):
        sl = slice(start[k], end[k])
        f, a_, kk = zf[sl], za[sl], kap[sl]
        pf = f[:, None] ** np.arange(D)[None, :]
        pa = a_[:, None] ** np.arange(D)[None, :]
        sw[k] = end[k] - start[k]
        Y[k] = [(cy[sl] * f).sum(), (cy[sl] * a_).sum()]
        zmax_day[k] = [np.abs(f).max(), np.abs(a_).max()]
        hull_before.append(hull)
        hull = _hull(np.vstack([hull, np.column_stack([f, a_])]))
        for n in range(order + 1):
            for a in range(n + 2):
                Mg[k, n, a] = (kk[:, n] * pf[:, a] * pa[:, n + 1 - a]).sum()
            for a in range(n + 3):
                Mh[k, n, a] = (kk[:, n + 1] * pf[:, a] * pa[:, n + 2 - a]).sum()
    zmax_before = np.vstack([np.zeros((1, 2)), np.maximum.accumulate(zmax_day, 0)[:-1]])
    meta = _snap_rows(days, start, end, dr)
    rng_c = float((C.max(1) - C.min(1)).max()) if len(C) else 1.0
    return dict(days=days, sw=sw, Y=Y, Mg=Mg, Mh=Mh, meta=meta, order=order, start=start, n_day=(end - start),
                zmax_before=zmax_before, hull_before=hull_before, t_safe=SAFE * np.pi / rng_c, rows=dict(A=A, C=C, cy=cy, Z2=np.column_stack([zf, za]),
                                                                              dnum=ds.astype(np.int64)))


def _hull(pts):
    """Extreme points of a 2-D point set (convex hull vertices; bounding-box corners when degenerate, an upper bound)."""
    if len(pts) == 0:
        return pts
    try:
        from scipy.spatial import ConvexHull
        return pts[ConvexHull(pts).vertices]
    except Exception:
        lo, hi = pts.min(0), pts.max(0)
        return np.array([[lo[0], lo[1]], [lo[0], hi[1]], [hi[0], lo[1]], [hi[0], hi[1]]])


def _series_stats(order):
    fac = np.array([factorial(n) for n in range(order + 1)], float)
    binom = [np.array([comb(n, b) for b in range(n + 1)], float) for n in range(order + 1)]

    def stats(s, sw, Y, Mg, Mh):
        sf, sa = s
        g = Y.copy()
        I = np.zeros((2, 2))
        for n in range(order + 1):
            b = np.arange(n + 1)
            cf = binom[n] * sf ** b * sa ** (n - b) / fac[n]          # coefficient of zf^b za^(n-b) in t^n / n!
            g[0] -= (cf * Mg[n, b + 1]).sum()
            g[1] -= (cf * Mg[n, b]).sum()
            I[0, 0] += (cf * Mh[n, b + 2]).sum()
            I[0, 1] += (cf * Mh[n, b + 1]).sum()
            I[1, 1] += (cf * Mh[n, b]).sum()
        I[1, 0] = I[0, 1]
        return g, I, float(sw)
    return stats


def asof_from_moments(mom, H, P, s0=S0, exact=False, floor=None):
    """Per-date as-of pair. Each Newton iterate is evaluated by the series while its max |t| over the window is within
    t_safe, otherwise (or with exact=True) directly on the window's rows; n_exact counts the direct evaluations."""
    days = mom["days"]
    st = _series_stats(mom["order"])
    rw = mom["rows"]
    dnum = days.astype(np.int64)
    sw = 0.0
    Y = np.zeros(2)
    Mg = np.zeros_like(mom["Mg"][0])
    Mh = np.zeros_like(mom["Mh"][0])
    s = np.asarray(s0, float)
    out = []
    nb = 0
    for k in range(len(days)):
        if k > 0:
            dec = 0.5 ** ((dnum[k] - dnum[k - 1]) / H)
            sw = dec * (sw + mom["sw"][k - 1])
            Y = dec * (Y + mom["Y"][k - 1])
            Mg = dec * (Mg + mom["Mg"][k - 1])
            Mh = dec * (Mh + mom["Mh"][k - 1])
            nb += int(mom["n_day"][k - 1])
        hv = mom["hull_before"][k]
        cnt = dict(exact=0)
        if nb > 0:
            cache = {}

            def stats(sv, k=k, nb=nb, sw=sw, Y=Y, Mg=Mg, Mh=Mh, hv=hv, cache=cache, cnt=cnt):
                if not exact and np.abs(hv @ sv).max() <= mom["t_safe"]:
                    return st(sv, sw, Y, Mg, Mh)
                if "ex" not in cache:
                    w = 0.5 ** ((dnum[k] - rw["dnum"][:nb]) / H)
                    cache["ex"] = _exact_stats(rw["A"][:nb], rw["C"][:nb], rw["cy"][:nb], rw["Z2"][:nb], w)
                cnt["exact"] += 1
                return cache["ex"](sv)
            s, neff = _newton2(s, stats, P, floor=floor)
            n_ex = cnt["exact"]
            if floor is not None:
                g_, I_, sw_ = stats(s)
                bnd = bool(sw_ > 0 and np.trace(I_) > 0 and floor_binds(I_ / sw_, floor))
        else:
            neff = 0.0
            bnd = False
        rec = dict(mom["meta"][k])
        rec.update(s_for=float(s[0]), s_against=float(s[1]), n_eff=neff, n_before=nb,
                   n_exact=n_ex if nb > 0 else cnt["exact"])
        if floor is not None:
            rec["floor_binds"] = bnd
        out.append(rec)
    return _frame(out)


def asof_scale(date, drop, A, C, y, zf, za, H, P, s0=S0, order=ORDER, floor=None):
    """Production path (series evaluation where valid, direct evaluation elsewhere)."""
    return asof_from_moments(daily_moments(date, drop, A, C, y, zf, za, order), H, P, s0, floor=floor)


def asof_scale_exact(date, drop, A, C, y, zf, za, H, P, s0=S0, floor=None):
    """Reference: every Newton iterate evaluated directly on the window's rows."""
    return asof_from_moments(daily_moments(date, drop, A, C, y, zf, za, order=2), H, P, s0, exact=True, floor=floor)


def attach_scale(dates, sc: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Per-row (s_for, s_against) from a per-date snapshot frame (one cell), keyed by game date."""
    idx = pd.to_datetime(sc.date).to_numpy("datetime64[D]")
    k = pd.to_datetime(pd.Series(dates)).to_numpy("datetime64[D]")
    f = pd.Series(sc.s_for.to_numpy(), index=idx).reindex(k).to_numpy()
    a = pd.Series(sc.s_against.to_numpy(), index=idx).reindex(k).to_numpy()
    if np.isnan(f).any() or np.isnan(a).any():
        raise ValueError("rows without a scale snapshot")
    return f, a
