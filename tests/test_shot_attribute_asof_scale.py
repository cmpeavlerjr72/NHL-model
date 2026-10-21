"""SL-R7 leakage tests: the as-of two-slope response scale for a date uses only attempts dated strictly earlier; the
series evaluation matches the direct evaluation of the same objective."""
import numpy as np
import pandas as pd

from nhl_sim.shot_attribute import scale as SC

K = 12
TRUE = np.array([0.06, -0.04])


def _frame(seed=0, n_days=40, per_day=300, zero_days=0):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-10-07", periods=n_days, freq="D")
    date = np.repeat(days.strftime("%Y-%m-%d").to_numpy(), per_day)
    drop = pd.to_datetime(np.repeat(days, per_day)).tz_localize("UTC") + pd.Timedelta(hours=23)
    n = len(date)
    Cg = rng.normal(0, 1.0, (3, K))
    Cg -= Cg.mean(1, keepdims=True)
    C = Cg[rng.integers(0, 3, n)]
    A = rng.normal(0, 0.7, (n, K))
    zf, za = rng.normal(size=n), rng.normal(size=n)
    if zero_days:
        early = np.isin(date, days[:zero_days].strftime("%Y-%m-%d"))
        zf[early] = 0.0
        za[early] = 0.0
    Z = A + (TRUE[0] * zf + TRUE[1] * za)[:, None] * C
    p = np.exp(Z - Z.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    y = (p.cumsum(1) < rng.random(n)[:, None]).sum(1)
    return date, drop, A, C, y, zf, za


def _s(f):
    return f[["s_for", "s_against"]].to_numpy()


def test_scale_uses_only_earlier_attempts():
    date, drop, A, C, y, zf, za = _frame()
    for fn in (SC.asof_scale, SC.asof_scale_exact):
        base = fn(date, drop, A, C, y, zf, za, H=90, P=2000)
        cut = "2022-10-27"
        later = date >= cut
        y2, zf2, za2 = y.copy(), zf.copy(), za.copy()
        y2[later] = K - 1 - y2[later]                     # flip every outcome on or after the cut date
        zf2[later], za2[later] = -zf2[later], -za2[later]  # and every rating
        alt = fn(date, drop, A, C, y2, zf2, za2, H=90, P=2000)
        keep = (base.date <= pd.Timestamp(cut)).to_numpy()
        np.testing.assert_array_equal(_s(base)[keep], _s(alt)[keep])
        assert not np.allclose(_s(base)[~keep], _s(alt)[~keep])


def test_first_date_is_prior_and_created_before_drop():
    date, drop, A, C, y, zf, za = _frame(1)
    f = SC.asof_scale(date, drop, A, C, y, zf, za, H=180, P=10000)
    assert f.s_for.iloc[0] == SC.S0[0] and f.s_against.iloc[0] == SC.S0[1] and f.n_before.iloc[0] == 0
    m = f.created_at.notna()
    assert (f.created_at[m] < f.first_drop[m]).all()
    # with enough data the scale moves from the prior (0, 0) toward the generating pair
    assert 0.02 < f.s_for.iloc[-1] < 0.10 and -0.08 < f.s_against.iloc[-1] < 0.0


def test_shuffling_same_day_rows_does_not_change_scale():
    date, drop, A, C, y, zf, za = _frame(2)
    a = SC.asof_scale(date, drop, A, C, y, zf, za, H=90, P=2000)
    p = np.random.default_rng(5).permutation(len(date))
    b = SC.asof_scale(date[p], drop[p], A[p], C[p], y[p], zf[p], za[p], H=90, P=2000)
    np.testing.assert_allclose(_s(a), _s(b), rtol=0, atol=1e-10)


def test_series_matches_exact():
    date, drop, A, C, y, zf, za = _frame(3, n_days=25, per_day=200)
    for H, P in ((45, 2000), (365, 10000)):
        a = SC.asof_scale(date, drop, A, C, y, zf, za, H=H, P=P)
        b = SC.asof_scale_exact(date, drop, A, C, y, zf, za, H=H, P=P)
        np.testing.assert_allclose(_s(a), _s(b), rtol=0, atol=1e-9)
        np.testing.assert_allclose(a.n_eff.to_numpy(), b.n_eff.to_numpy(), rtol=1e-12)


def test_all_zero_rating_dates_carry_the_prior():
    date, drop, A, C, y, zf, za = _frame(4, zero_days=3)
    f = SC.asof_scale(date, drop, A, C, y, zf, za, H=90, P=2000)
    # dates 2-4 see only all-zero-rating rows: no information, s stays at the prior (no 0/0)
    assert np.isfinite(_s(f)).all()
    assert (_s(f)[:4] == 0.0).all() and not (_s(f)[4] == 0.0).all()


def test_near_zero_burn_in_ratings_match_exact():
    # near-zero, collinear ratings on the first dates (as in 2021-22): the pair jumps far from 0, where the series is
    # outside its radius; the production path must fall back to direct evaluation and agree with the reference
    date, drop, A, C, y, zf, za = _frame(6, n_days=20, per_day=200, zero_days=1)
    d2 = date == "2022-10-08"
    zf[d2] *= 1e-4
    za[d2] = zf[d2] * 1.1
    a = SC.asof_scale(date, drop, A, C, y, zf, za, H=90, P=2000)
    b = SC.asof_scale_exact(date, drop, A, C, y, zf, za, H=90, P=2000)
    assert np.isfinite(_s(a)).all() and a.n_exact.sum() > 0
    np.testing.assert_allclose(_s(a), _s(b), rtol=0, atol=1e-8)
