"""G-R4 leakage and construction tests: the as-of score-bucket deviations for a date use only SOG dated strictly earlier."""
import numpy as np
import pandas as pd

from nhl_sim.goal import score_asof as SA

TRUE = np.array([-0.10, 0.08, 0.05, 0.12])


def _frame(seed=0, n_days=40, per_day=400):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-10-07", periods=n_days, freq="D")
    date = np.repeat(days.strftime("%Y-%m-%d").to_numpy(), per_day)
    drop = pd.to_datetime(np.repeat(days, per_day)).tz_localize("UTC") + pd.Timedelta(hours=23)
    b = rng.choice(5, size=len(date), p=[0.13, 0.18, 0.38, 0.18, 0.13])
    X = (b[:, None] == np.asarray(SA.DEV_B)[None, :]).astype(float)
    off = rng.normal(-2.3, 0.3, size=len(date))
    y = (rng.random(len(date)) < 1 / (1 + np.exp(-(off + X @ TRUE)))).astype(float)
    return date, drop, off, y, X


def _floor(off, X):
    return (SA.F_FLOOR, SA.info_ref(off, X))


def test_deviations_use_only_earlier_shots():
    date, drop, off, y, X = _frame()
    fl = _floor(off, X)
    base = SA.asof_dev(date, drop, off, y, X, H=90, P=2000, floor=fl)
    cut = "2022-10-27"
    later = date >= cut
    y2 = y.copy()
    y2[later] = 1 - y2[later]                      # flip every outcome on or after the cut date
    off2 = off.copy()
    off2[later] += 1.0
    alt = SA.asof_dev(date, drop, off2, y2, X, H=90, P=2000, floor=fl)
    cols = [f"d_{j}" for j in range(SA.N_DEV)]
    k = base.date <= pd.Timestamp(cut)
    np.testing.assert_array_equal(base.loc[k, cols].to_numpy(), alt.loc[k, cols].to_numpy())
    assert not np.allclose(base.loc[~k, cols].to_numpy(), alt.loc[~k, cols].to_numpy())


def test_first_date_is_prior_and_created_before_drop():
    date, drop, off, y, X = _frame(1)
    f = SA.asof_dev(date, drop, off, y, X, H=180, P=10000, floor=_floor(off, X))
    assert (f.loc[0, [f"d_{j}" for j in range(4)]] == 0).all() and f.n_before.iloc[0] == 0
    m = f.created_at.notna()
    assert (f.created_at[m] < f.first_drop[m]).all()


def test_recovers_generating_deviations():
    date, drop, off, y, X = _frame(2, n_days=80, per_day=1500)
    f = SA.asof_dev(date, drop, off, y, X, H=365, P=2000, floor=_floor(off, X))
    last = f[[f"d_{j}" for j in range(4)]].iloc[-1].to_numpy()
    assert np.abs(last - TRUE).max() < 0.06
    mle = SA.fit_once(off, y, X)
    assert np.abs(mle - TRUE).max() < 0.06


def test_shuffling_same_day_rows_does_not_change_deviations():
    date, drop, off, y, X = _frame(3)
    fl = _floor(off, X)
    a = SA.asof_dev(date, drop, off, y, X, H=90, P=2000, floor=fl)
    p = np.random.default_rng(5).permutation(len(date))
    b = SA.asof_dev(date[p], drop[p], off[p], y[p], X[p], H=90, P=2000, floor=fl)
    cols = [f"d_{j}" for j in range(4)]
    np.testing.assert_allclose(a[cols].to_numpy(), b[cols].to_numpy(), rtol=0, atol=1e-10)


def test_one_bucket_matches_scalar_goalie_template_without_floor():
    """With one column and no floor, the 4-dummy estimator is the G-R3 one-parameter scale on a 0/1 rating."""
    from nhl_sim.goal import scale as GS
    date, drop, off, y, X = _frame(4)
    a = SA.asof_dev(date, drop, off, y, X[:, [1]], H=90, P=2000)
    b = GS.asof_scale(date, drop, y, off, X[:, 1], H=90, P=2000)
    np.testing.assert_allclose(a.d_0.to_numpy(), b.s.to_numpy(), rtol=0, atol=1e-7)


def test_bucket_map_and_designs():
    r = pd.DataFrame({"sc": np.arange(7).repeat(4), "sg": np.tile([0, 1, 2, 5], 7), "period": np.tile([1, 2, 3, 4], 7)})
    assert SA.bucket(r).tolist() == np.array([0, 0, 1, 2, 3, 4, 4]).repeat(4).tolist()
    X = SA.dev_design(r)
    assert (X[r.sg == 5] == 0).all() and (X[(r.sc == 3).to_numpy()] == 0).all()
    assert (X.sum(1)[((r.sg != 5) & (r.sc != 3)).to_numpy()] == 1).all()
    Xs = SA.sp_design_score(r)
    assert Xs.shape[1] == 14 and (Xs[(r.period == 4).to_numpy() | (r.sg == 5).to_numpy()] == 0).all()
    sh = np.full((5, 3), 1 / 3)
    Xi = SA.sap_design(r, sh)
    assert Xi.shape[1] == 10
    m = dict(shares=sh.tolist(), coef=list(np.arange(10) / 10))
    T = SA.sap_term_table(m)
    np.testing.assert_allclose((T * sh).sum(1), 0, atol=1e-15)
