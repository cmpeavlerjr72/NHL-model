"""SL-R2 level and offset arms: synthetic checks (no data files)."""
import numpy as np
import pandas as pd

from nhl_sim.shot_attribute import mix_level as ML
from nhl_sim.shot_attribute.models_m import class_base, fit_mnl_offset
from nhl_sim.shot_attribute.tables import N_CELL, N_CLASS, N_TYPE


def _games():
    d = ["2021-10-01", "2021-10-02", "2022-10-01", "2022-10-03", "2022-10-03"]
    return pd.DataFrame({"game_id": [1, 2, 3, 4, 5], "season": [20212022, 20212022, 20222023, 20222023, 20222023],
                         "date": d, "drop": [x + "T23:00:00Z" for x in d]})


def _rows(rng, n=4000):
    g = rng.integers(1, 6, n)
    return pd.DataFrame({"game_id": g, "grp": rng.integers(0, 3, n), "cell": rng.integers(0, N_CELL, n),
                         "season": np.where(g <= 2, 20212022, 20222023)})


def test_asof_levels_use_only_earlier_dates_and_prior():
    rng = np.random.default_rng(0)
    u = _rows(rng)
    meta, lv = ML.asof_levels(u, _games(), {"M0": ("M0", None), "M1": ("M1", 500), "O": ("O", None)})
    C = ML.game_counts(u, meta)
    final21 = C[:2].sum(0) / C[:2].sum(0).sum(1, keepdims=True)
    # first game date of 2022-23: M1 = prior (no season-to-date counts) = 2021-22 final; M0 constant
    assert np.allclose(lv["M1"][2], final21) and np.allclose(lv["M0"][2:], final21)
    # game 4/5 (same date) see only game 3's counts
    exp = (C[2] + 500 * final21) / (C[2].sum(1, keepdims=True) + 500)
    assert np.allclose(lv["M1"][3], exp) and np.allclose(lv["M1"][4], exp)
    assert (meta.created_at.dropna() < meta.puck_drop[meta.created_at.notna()]).all()
    assert np.allclose(lv["O"][2:].sum(-1), 1)


def test_offset_moves_cell_marginal_to_level_and_keeps_type_given_cell():
    rng = np.random.default_rng(1)
    P = rng.dirichlet(np.ones(N_CLASS), 5)
    s_train = rng.dirichlet(np.ones(N_CELL))
    s_new = rng.dirichlet(np.ones(N_CELL))
    Q = ML.apply_cell_offset(P, np.log(s_new / s_train)[None, :].repeat(5, 0))
    cellP = P.reshape(5, N_CELL, N_TYPE).sum(-1)
    cellQ = Q.reshape(5, N_CELL, N_TYPE).sum(-1)
    r = cellQ / cellP / (s_new / s_train)
    assert np.allclose(r, r[:, :1])
    assert np.allclose(Q.reshape(5, N_CELL, N_TYPE) / cellQ[..., None], P.reshape(5, N_CELL, N_TYPE) / cellP[..., None])


def test_offset_mnl_recovers_offset_model():
    rng = np.random.default_rng(2)
    n, K = 20000, 4
    X = rng.normal(size=(n, 2))
    W = np.array([[0.5, -0.3], [0.0, 0.4], [-0.2, 0.1], [0.3, 0.0]])
    b = np.array([0.2, -0.1, 0.0, 0.3])
    off = rng.normal(scale=0.5, size=(n, K))
    eta = X @ W.T + b + off
    p = np.exp(eta - eta.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    y = (p.cumsum(1) > rng.random(n)[:, None]).argmax(1)
    cw, ci, _ = fit_mnl_offset(X, y, off, C=1e4, K=K)
    # softmax is identified up to a common shift per column: compare centred coefficients
    assert np.allclose(cw - cw.mean(0), W - W.mean(0), atol=0.06)
    assert np.allclose(ci - ci.mean(), b - b.mean(), atol=0.06)


def test_class_base_is_log_frequency():
    cls = np.array([0, 0, 1, 77])
    b = class_base(cls)
    assert np.isclose(np.exp(b[0]), 0.5) and np.isclose(np.exp(b[77]), 0.25) and b[5] < -30
