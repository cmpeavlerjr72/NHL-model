"""SB-R5 leakage tests: the as-of two-slope block scale for a date uses only attempts dated strictly earlier (with and
without the AS-1 floor); first date = prior; within-day shuffle; zero-information dates carry the prior; the floor binds
only while the ratings have no spread."""
import numpy as np
import pandas as pd

from nhl_sim.block import scale as SC

TRUE = np.array([0.15, -0.25])


def _frame(seed=0, n_days=40, per_day=300, ramp=False, zero_days=0):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-10-07", periods=n_days, freq="D")
    date = np.repeat(days.strftime("%Y-%m-%d").to_numpy(), per_day)
    drop = pd.to_datetime(np.repeat(days, per_day)).tz_localize("UTC") + pd.Timedelta(hours=23)
    n = len(date)
    k = np.repeat(np.arange(n_days), per_day)
    sc = np.minimum(1.0, (k / 10.0) ** 2) if ramp else np.ones(n)
    zf, za = rng.normal(size=n) * sc, rng.normal(size=n) * sc
    if zero_days:
        zf[k < zero_days] = 0.0
        za[k < zero_days] = 0.0
    off = rng.normal(-1.1, 0.4, n)
    y = (rng.random(n) < 1 / (1 + np.exp(-(off + TRUE[0] * zf + TRUE[1] * za)))).astype(float)
    return date, drop, off, y, zf, za


def _s(f):
    return f[["s_for", "s_against"]].to_numpy()


def _floor(off, zf, za):
    return (SC.F_FLOOR, SC.info_ref(off[-3000:], zf[-3000:], za[-3000:]))


def test_scale_uses_only_earlier_attempts():
    date, drop, off, y, zf, za = _frame(ramp=True)
    for fl in (None, _floor(off, zf, za)):
        base = SC.asof_scale(date, drop, off, y, zf, za, H=90, P=2000, floor=fl)
        cut = "2022-10-27"
        later = date >= cut
        y2, zf2, za2 = y.copy(), zf.copy(), za.copy()
        y2[later] = 1 - y2[later]
        zf2[later], za2[later] = -zf2[later], -za2[later]
        alt = SC.asof_scale(date, drop, off, y2, zf2, za2, H=90, P=2000, floor=fl)
        keep = (base.date <= pd.Timestamp(cut)).to_numpy()
        np.testing.assert_array_equal(_s(base)[keep], _s(alt)[keep])
        assert not np.allclose(_s(base)[~keep], _s(alt)[~keep])


def test_first_date_is_prior_created_before_drop_and_recovers_slopes():
    date, drop, off, y, zf, za = _frame(1, n_days=60)
    f = SC.asof_scale(date, drop, off, y, zf, za, H=180, P=2000, floor=_floor(off, zf, za))
    assert (_s(f)[0] == 0.0).all() and f.n_before.iloc[0] == 0
    m = f.created_at.notna()
    assert (f.created_at[m] < f.first_drop[m]).all()
    assert 0.08 < f.s_for.iloc[-1] < 0.22 and -0.32 < f.s_against.iloc[-1] < -0.18


def test_shuffling_same_day_rows_does_not_change_scale():
    date, drop, off, y, zf, za = _frame(2, ramp=True)
    fl = _floor(off, zf, za)
    a = SC.asof_scale(date, drop, off, y, zf, za, H=45, P=10000, floor=fl)
    p = np.random.default_rng(5).permutation(len(date))
    b = SC.asof_scale(date[p], drop[p], off[p], y[p], zf[p], za[p], H=45, P=10000, floor=fl)
    np.testing.assert_allclose(_s(a), _s(b), rtol=0, atol=1e-10)


def test_zero_information_dates_carry_the_prior():
    date, drop, off, y, zf, za = _frame(4, zero_days=3)
    for fl in (None, _floor(off, zf, za)):
        f = SC.asof_scale(date, drop, off, y, zf, za, H=90, P=2000, floor=fl)
        assert np.isfinite(_s(f)).all()
        assert (_s(f)[:4] == 0.0).all() and not (_s(f)[4] == 0.0).all()


def test_floor_binds_only_without_spread_and_damps_start():
    date, drop, off, y, zf, za = _frame(6, ramp=True)
    fl = _floor(off, zf, za)
    f = SC.asof_scale(date, drop, off, y, zf, za, H=90, P=2000, floor=fl)
    u = SC.asof_scale(date, drop, off, y, zf, za, H=90, P=2000)
    assert f.floor_binds.iloc[2:5].all() and not f.floor_binds.iloc[-5:].any()
    assert np.abs(_s(f)[:10]).max() <= np.abs(_s(u)[:10]).max()
    assert "floor_binds" not in u.columns
