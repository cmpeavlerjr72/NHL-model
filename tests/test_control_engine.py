import numpy as np

from nhl_sim.control import engine as E

LH = np.array([2.5, 3.2, 3.8])
LA = np.array([3.0, 2.8, 2.2])


def test_reg_pmfs_normalise_and_nest():
    base = E.reg_pmf("A1", LH, LA, {})
    assert np.allclose(base.sum((1, 2)), 1)
    assert np.allclose(E.reg_pmf("A2", LH, LA, {"lambda3": 1e-9}), base, atol=1e-6)
    assert np.allclose(E.reg_pmf("A3", LH, LA, {"phi": 1e-5}), base, atol=1e-5)


def test_dispersion_models_add_positive_correlation():
    x = np.arange(E.NR)
    for arm, par in (("A2", {"lambda3": 0.5}), ("A3", {"phi": 0.2})):
        P = E.reg_pmf(arm, LH[:1], LA[:1], par)[0]
        cov = (P * np.outer(x, x)).sum() - (P.sum(1) @ x) * (P.sum(0) @ x)
        assert cov > 0.05
        assert abs(P.sum(1) @ x - LH[0]) < 0.02 and abs(P.sum(0) @ x - LA[0]) < 0.02   # marginal means preserved


def test_final_pmf_conserves_mass_and_resolves_ties():
    reg = E.reg_pmf("A1", LH, LA, {})
    F, pw = E.final_pmf(reg, np.array([1.0, 0.6, 0.0]), np.array([0.5, 0.55, 0.5]))
    assert np.allclose(F.sum((1, 2)), 1)
    tie_mass = reg[:, np.arange(E.NR), np.arange(E.NR)].sum(1)
    # playoff game (q=1): no tied final score at all
    assert np.allclose(F[0][np.arange(E.NR), np.arange(E.NR)], 0)
    # RS game q=0: ties stay tied (SO)
    assert np.allclose(F[2][np.arange(E.NR), np.arange(E.NR)], reg[2][np.arange(E.NR), np.arange(E.NR)])
    assert np.all((pw > 0) & (pw < 1))
    assert np.all(tie_mass > 0.1)


def test_sampling_matches_pmf():
    reg = E.reg_pmf("A1", LH[:1], LA[:1], {})
    F, pw = E.final_pmf(reg, np.array([0.7]), np.array([0.55]))
    h, a, es, hw = E.sample_final("A1", LH[:1], LA[:1], np.array([0.7]), np.array([0.55]), {}, 200000, 1)
    emp = np.zeros((E.N, E.N))
    np.add.at(emp, (h[0], a[0]), 1)
    emp /= emp.sum()
    assert np.abs(emp - F[0]).max() < 0.004
    assert abs(hw.mean() - pw[0]) < 0.004
    assert np.all(h[es == "SO"] == a[es == "SO"])


def test_ridge_fit_recovers_strength_order():
    from nhl_sim.control.engine import _center, _newton
    rng = np.random.default_rng(0)
    T, n = 6, 3000
    off = np.array([.3, .15, 0, 0, -.15, -.3])
    h, a = rng.integers(0, T, n), rng.integers(0, T, n)
    ok = h != a
    h, a = h[ok], a[ok]
    X = np.zeros((2 * len(h), 2 + 2 * T))
    X[:, 0] = 1
    X[0::2, 1] = 1
    r = np.arange(len(h))
    X[2 * r, 2 + h] = 1; X[2 * r + 1, 2 + a] = 1
    X[2 * r, 2 + T + a] = 1; X[2 * r + 1, 2 + T + h] = 1
    y = np.empty(2 * len(h))
    y[0::2] = rng.poisson(np.exp(1.0 + .1 + off[h]))
    y[1::2] = rng.poisson(np.exp(1.0 + off[a]))
    pen = np.full(2 + 2 * T, 1.0); pen[:2] = 1e-3
    th = _center(_newton(X, y, pen, np.zeros(2 + 2 * T), np.zeros(2 + 2 * T)), T, 0)
    assert np.corrcoef(th[2:2 + T], off)[0, 1] > 0.98
    assert abs(th[1] - 0.1) < 0.05


def test_empty_fit_returns_prior():
    m = np.arange(5.0)
    assert np.array_equal(E._newton(np.zeros((0, 5)), np.zeros(0), np.ones(5), m, m), m)


def test_asof_ratings_ignore_future_games():
    import copy

    import pytest

    from nhl_sim.data import load
    if not (load.PROCESSED / "games.parquet").exists():
        pytest.skip("no data")
    d = E.build_data()
    s = 20232024
    p1 = E.Chain(d, "gkrest", 10, 0.7).asof(s)
    d2 = copy.deepcopy(d)
    gs = d2.g[d2.g.season == s]
    late = gs.index[gs.date >= gs.date.iloc[len(gs) // 2]]
    d2.g.loc[late, ["hg", "ag"]] = 9
    p2 = E.Chain(d2, "gkrest", 10, 0.7).asof(s)
    n_same = int((gs.date < gs.date.iloc[len(gs) // 2]).sum())
    assert np.allclose(p1.lam_h[:n_same], p2.lam_h[:n_same]) and np.allclose(p1.lam_a[:n_same], p2.lam_a[:n_same])
    assert not np.allclose(p1.lam_h[n_same + 50:], p2.lam_h[n_same + 50:])
