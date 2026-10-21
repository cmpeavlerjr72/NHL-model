"""SB-R5 as-of response scale on the Ra block ratings (docs/models/block/experiments.md SB-R5; INV-64, INV-53; the SL-R7
template `src/nhl_sim/shot_attribute/scale.py` on a binary logistic, with the AS-1 floor, INV-62).

B1a-as:
  logit p = logit B0' + (x - x_bar) . W + s_for,t x zf + s_against,t x za
  B0'     the engine stand-in (D41 / INV-54): SB-R1 B0 + M1 K500 on 5v5 / PP / PK / EN, own level groups for 4v4 / 3v3
  W       the FROZEN non-rating terms of the fold's SB-R4 B1a fit (score dummies, home, b2b own / opp, arena factor), centred
          at their mean over the fold's training rows (the SL-R7 template's (x - x_bar) . W); fixed offset
  zf, za  own_r (shooting team's Ra blocked-against rating, row's rating group) / opp_r (defending team's Ra blocks-for
          rating), divided by their SD over the fold's 2021-22 in-scope rows (unit only)
  (s_for,t, s_against,t): an as-of estimate per game date d:
    window   every in-scope attempt (SB-R1 row scope) dated strictly before d, across seasons, weight 0.5^((d - date_i) / H)
    fit      two-slope binary logistic with the offset fixed, maximising
                 sum_i w_i ll_i(s) - 0.5 (s - s_prev)' (P x Ibar) (s - s_prev)
             Ibar = sum_i w_i p_i (1 - p_i) z_i z_i' / sum_i w_i, re-read at every Newton iterate; AS-1 floor: P x (Ibar +
             f x I_ref) while lambda_min(Ibar) < f x lambda_min(I_ref); s_prev = the previous date's pair; Newton from s_prev
             (the SL-R7 solver `_newton2`: eigen-restricted step, decrement-halving safeguard), max |step| < 1e-8
    start    (0, 0); 2021-22 is burn-in, never judged or served
    snapshot created_at = the previous date's last puck drop + 6 h, asserted < puck_drop of every game on d
Every Newton iterate is evaluated directly on the window's rows (no series): the binary window is cheap enough.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attribute.scale import S0, _days, _frame, _newton2, _snap_rows, floor_binds, skey  # noqa: F401

H_GRID = (45, 90, 180, 365)
P_GRID = (2000, 10000)
GRID_ORDER = [(H, P) for H in sorted(H_GRID, reverse=True) for P in sorted(P_GRID, reverse=True)]
F_FLOOR = 0.5                         # AS-1 selected f (docs/tests/asof_floor_as1_2026-10-21.md)


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def info_ref(off, zf, za):
    """AS-1 I_ref (2 x 2): the per-attempt Fisher information at s = 0, unweighted, over the given rows."""
    p = _sig(np.asarray(off, float))
    v = p * (1 - p)
    Z = np.column_stack([zf, za]).astype(float)
    return (Z * v[:, None]).T @ Z / len(v)


def _stats(off, y, Z, w):
    sw = float(w.sum())

    def stats(sv):
        p = _sig(off + Z @ sv)
        v = w * p * (1 - p)
        return Z.T @ (w * (y - p)), (Z * v[:, None]).T @ Z, sw
    return stats


def fit_once(off, y, zf, za, w=None, s0=S0):
    """Unshrunk weighted MLE of the pair (P = 0; the season-own-MLE diagnostic)."""
    Z = np.column_stack([zf, za]).astype(float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)
    return _newton2(np.asarray(s0, float), _stats(np.asarray(off, float), np.asarray(y, float), Z, w), 0.0)[0]


def asof_scale(date, drop, off, y, zf, za, H, P, s0=S0, floor=None):
    """Per-date as-of pair (s_for, s_against). floor = (f, I_ref) (AS-1) or None. s on date d uses rows dated < d only."""
    order, ds, days, start, end = _days(date)
    off = np.asarray(off, float)[order]
    y = np.asarray(y, float)[order]
    Z = np.column_stack([np.asarray(zf, float)[order], np.asarray(za, float)[order]])
    dr = pd.to_datetime(pd.Series(drop), utc=True).iloc[order].reset_index(drop=True)
    meta = _snap_rows(days, start, end, dr)
    dnum = ds.astype(np.int64)
    s = np.asarray(s0, float)
    out = []
    for k, day in enumerate(days):
        nb = int(start[k])
        bnd = False
        if nb > 0:
            w = 0.5 ** ((day.astype(np.int64) - dnum[:nb]) / H)
            st = _stats(off[:nb], y[:nb], Z[:nb], w)
            s, neff = _newton2(s, st, P, floor=floor)
            if floor is not None:
                _, I_, sw_ = st(s)
                bnd = bool(sw_ > 0 and np.trace(I_) > 0 and floor_binds(I_ / sw_, floor))
        else:
            neff = 0.0
        rec = dict(meta[k])
        rec.update(s_for=float(s[0]), s_against=float(s[1]), n_eff=neff, n_before=nb)
        if floor is not None:
            rec["floor_binds"] = bnd
        out.append(rec)
    return _frame(out)


def attach_scale(dates, sc: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Per-row (s_for, s_against) from a per-date snapshot frame (one cell), keyed by game date."""
    idx = pd.to_datetime(sc.date).to_numpy("datetime64[D]")
    k = pd.to_datetime(pd.Series(dates)).to_numpy("datetime64[D]")
    f = pd.Series(sc.s_for.to_numpy(), index=idx).reindex(k).to_numpy()
    a = pd.Series(sc.s_against.to_numpy(), index=idx).reindex(k).to_numpy()
    if np.isnan(f).any() or np.isnan(a).any():
        raise ValueError("rows without a scale snapshot")
    return f, a
