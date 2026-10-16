"""G-R1 arms (docs/models/goal/experiments.md G-R1). Target: goal (1) vs save (0) per SOG with a goalie in net.

  C0  cell table (cell x type x strength group, training rows) + level delta (logit offset, coefficient 1)
  C1  logistic: C0 offset + strength-group intercepts (unpenalised) + score bucket (6 dummies, tied = reference) + home
      + b2b own / opp + arena distance factor (fitted) + goalie rating and team finishing rating as FIXED offsets
      s x c (c = fold-1-train-fitted coefficient of that rating in the free C1 fit, raw units; not refit)
  C2  LightGBM binary on the C1 features minus both ratings (sg, sc, is_home, b2b_own, b2b_opp, arena_f), init_score =
      logit C0 + the two rating offsets at their fixed scales (L32, D31)
L33 / D26: EAF rows (shooting team's own goalie pulled: late and trailing by construction) do not share score splits:
their score dummies are zeroed in C1 and they get no tree deviations in C2 (served the C2 init). Labelled.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.block.models import fit_logit_offset  # read-only reuse (unpenalised one-hots + tiny ridge)
from nhl_sim.goal.data import N_SG, sigmoid

EAF = 5
NUM = ["is_home", "b2b_own", "b2b_opp", "arena_f"]
LGB_FEATURES = ["sg", "sc", "is_home", "b2b_own", "b2b_opp", "arena_f"]


def design_base(r: pd.DataFrame) -> np.ndarray:
    """sg one-hots (6) | score dummies (6) | is_home, b2b_own, b2b_opp, arena_f."""
    sc = np.eye(7)[r.sc.to_numpy()][:, [0, 1, 2, 4, 5, 6]]
    sc[(r.sg == EAF).to_numpy()] = 0.0
    return np.hstack([np.eye(N_SG)[r.sg.to_numpy()], sc, r[NUM].to_numpy(float)])


I_ARENA = N_SG + 6 + 3


def design_free(r: pd.DataFrame) -> np.ndarray:
    """Base + goalie rating + team rating (free coefficients; columns -2, -1)."""
    return np.hstack([design_base(r), r[["g_r", "t_r"]].to_numpy(float)])


def fit_free(r, off):
    w, nit = fit_logit_offset(design_free(r), r.y.to_numpy(), off, n_free=N_SG)
    return dict(coef=w.tolist(), c_g=float(w[-2]), c_t=float(w[-1]), n_iter=nit)


def rating_off(r, spec):
    """spec: dict(c_g, s_g, c_t, s_t); a missing key means that rating enters freely (not in the offset)."""
    o = np.zeros(len(r))
    if "s_g" in spec:
        o += spec["s_g"] * spec["c_g"] * r.g_r.to_numpy(float)
    if "s_t" in spec:
        o += spec["s_t"] * spec["c_t"] * r.t_r.to_numpy(float)
    return o


def design_c1(r, spec):
    X = design_base(r)
    if "s_g" not in spec:
        X = np.hstack([X, r[["g_r"]].to_numpy(float)])
    if "s_t" not in spec:
        X = np.hstack([X, r[["t_r"]].to_numpy(float)])
    return X


def fit_c1(r, off, spec):
    w, nit = fit_logit_offset(design_c1(r, spec), r.y.to_numpy(), off + rating_off(r, spec), n_free=N_SG)
    return dict(arm="C1", coef=w.tolist(), spec=spec, n_iter=nit)


def logit_c1(m, r, off):
    return design_c1(r, m["spec"]) @ np.asarray(m["coef"]) + off + rating_off(r, m["spec"])


def predict_c1(m, r, off):
    return sigmoid(logit_c1(m, r, off))


def lgb_params(num_leaves, min_data, seed, threads=4):
    return dict(objective="binary", learning_rate=0.05, num_leaves=num_leaves, min_data_in_leaf=min_data, seed=seed,
                num_threads=threads, deterministic=True, force_row_wise=True, verbose=-1)


def lgb_X(r):
    return r[LGB_FEATURES].astype(float)


def lgb_mask(r):
    """Rows the trees are trained on / applied to (EAF excluded, L33)."""
    return (r.sg != EAF).to_numpy()


def predict_c2(booster, r, init_logit):
    z = init_logit.copy()
    m = lgb_mask(r)
    z[m] += booster.predict(lgb_X(r[m]), raw_score=True)
    return sigmoid(z)
