"""G-R3 as-of goalie response scale (docs/models/goal/experiments.md G-R3; INV-53, L35, D36).

The goalie rating enters C1s as s_t x z, z = g_r / SD_REF (standardised as-of goalie rating; SD_REF is a fixed per-fold
constant, the SD of g_r over the first data season's rows, so it is only a unit: s_t is estimated and applied in the same
unit). s_t is an as-of estimate of the goalie-rating logistic coefficient:

  window   every in-scope SOG dated strictly before the game date d (across seasons), weight 0.5^((d - date_i) / H)
  fit      one-parameter logistic slope, offset = C0 logit + team-finishing offset (fixed), maximising
               sum_i w_i ll_i(s) - 0.5 * P * ibar * (s - s_prev)^2
           ibar = sum w p(1-p) z^2 / sum w (per-shot Fisher information at the current iterate), so the prior counts
           as P shots; s_prev = the previous game date's s; Newton from s_prev to |step| < 1e-8
  start    s = S0 = 0 before any data (first data season 2021-22: burn-in, labelled, never judged)
  snapshot one s per game date; created_at = last puck drop of the previous game date + 6 h (LC-2 form), asserted
           < puck_drop for every game on d.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.block.models import fit_logit_offset  # read-only reuse
from nhl_sim.goal.data import N_SG, sigmoid
from nhl_sim.goal.models import design_base
from nhl_sim.strength_state.tables import assert_pregame

S0 = 0.0
H_GRID = (90, 180, 365)
P_GRID = (2000, 10000)
# simplest first: larger H, then larger P (spec)
GRID_ORDER = [(H, P) for H in sorted(H_GRID, reverse=True) for P in sorted(P_GRID, reverse=True)]


def skey(H, P):
    return f"H{int(H)}_P{int(P)}"


def _newton(s_prev, y, off, z, w, P, tol=1e-8, max_it=50):
    s = s_prev
    sw = w.sum()
    for _ in range(max_it):
        p = sigmoid(off + s * z)
        info = w * p * (1 - p) * z * z
        I = info.sum()
        if not I > 0:                                 # no rating spread in the window yet (season-opening priors all 0)
            return s_prev, float(sw)
        ibar = I / sw
        g = (w * (y - p) * z).sum() - P * ibar * (s - s_prev)
        h = I + P * ibar
        step = g / h
        s += step
        if abs(step) < tol:
            break
    if not np.isfinite(s):
        raise FloatingPointError("as-of scale diverged")
    return s, float(sw)


def asof_scale(date, drop, y, off, z, H, P, s0=S0):
    """date (n,) game dates (str/datetime), drop (n,) puck drops (UTC), y (n,) 0/1, off (n,) fixed logit offset, z (n,)
    standardised rating. Returns a per-date frame: date, s, n_eff (summed weight of the window), created_at, first/last
    puck drop of the date. s on date d uses rows with date < d only."""
    d = pd.to_datetime(pd.Series(date)).to_numpy("datetime64[D]")
    dr = pd.to_datetime(pd.Series(drop), utc=True)
    order = np.argsort(d, kind="stable")
    d, y, off, z = d[order], np.asarray(y, float)[order], np.asarray(off, float)[order], np.asarray(z, float)[order]
    dr = dr.iloc[order].reset_index(drop=True)
    days = np.unique(d)
    start = np.searchsorted(d, days, side="left")
    end = np.searchsorted(d, days, side="right")
    dnum = d.astype(np.int64)
    out = []
    s = s0
    last_drop = None
    for k, day in enumerate(days):
        n = start[k]                                  # rows strictly before `day`
        if n > 0:
            age = day.astype(np.int64) - dnum[:n]
            w = 0.5 ** (age / H)
            s, neff = _newton(s, y[:n], off[:n], z[:n], w, P)
        else:
            neff = 0.0
        drops = dr.iloc[start[k]:end[k]]
        created = None if last_drop is None else last_drop + pd.Timedelta(hours=6)
        out.append(dict(date=pd.Timestamp(day), s=s, n_eff=neff, n_before=int(n), created_at=created,
                        first_drop=drops.min(), last_drop=drops.max()))
        last_drop = drops.max()
    f = pd.DataFrame(out)
    f["created_at"] = pd.to_datetime(f.created_at, utc=True)
    chk = f.rename(columns={"first_drop": "puck_drop"})
    assert_pregame(chk)
    return f


def attach_scale(rows: pd.DataFrame, sc: pd.DataFrame) -> np.ndarray:
    m = pd.Series(sc.s.to_numpy(), index=pd.to_datetime(sc.date).to_numpy("datetime64[D]"))
    v = m.reindex(pd.to_datetime(rows.date).to_numpy("datetime64[D]")).to_numpy()
    if np.isnan(v).any():
        raise ValueError("rows without a scale snapshot")
    return v


def team_off(r, spec):
    return spec["s_t"] * spec["c_t"] * r.t_r.to_numpy(float)


def fit_c1s(r, off, spec, goff):
    """C1 with the goalie offset goff = s_t x z (as-of) instead of s_g x c_g x g_r; team at its fixed scale."""
    w, nit = fit_logit_offset(design_base(r), r.y.to_numpy(), off + team_off(r, spec) + goff, n_free=N_SG)
    return dict(arm="C1s", coef=w.tolist(), n_iter=nit)


def predict_c1s(m, r, off, spec, goff):
    return sigmoid(design_base(r) @ np.asarray(m["coef"]) + off + team_off(r, spec) + goff)
