"""G-R3 leakage test: the as-of goalie response scale s_t for a date uses only shots dated strictly earlier."""
import numpy as np
import pandas as pd

from nhl_sim.goal import scale as SC


def _frame(seed=0, n_days=40, per_day=300):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-10-07", periods=n_days, freq="D")
    date = np.repeat(days.strftime("%Y-%m-%d").to_numpy(), per_day)
    drop = pd.to_datetime(np.repeat(days, per_day)).tz_localize("UTC") + pd.Timedelta(hours=23)
    z = rng.normal(size=len(date))
    off = np.full(len(date), -2.3)
    y = (rng.random(len(date)) < 1 / (1 + np.exp(-(off - 0.4 * z)))).astype(float)
    return date, drop, y, off, z


def test_scale_uses_only_earlier_shots():
    date, drop, y, off, z = _frame()
    base = SC.asof_scale(date, drop, y, off, z, H=90, P=2000)
    cut = "2022-10-27"
    later = date >= cut
    y2 = y.copy()
    y2[later] = 1 - y2[later]                       # flip every outcome on or after the cut date
    z2 = z.copy()
    z2[later] = -z2[later]
    alt = SC.asof_scale(date, drop, y2, off, z2, H=90, P=2000)
    on_or_before = base.date <= pd.Timestamp(cut)
    np.testing.assert_array_equal(base.s[on_or_before].to_numpy(), alt.s[on_or_before].to_numpy())
    assert not np.allclose(base.s[~on_or_before].to_numpy(), alt.s[~on_or_before].to_numpy())


def test_first_date_is_prior_and_created_before_drop():
    date, drop, y, off, z = _frame(1)
    f = SC.asof_scale(date, drop, y, off, z, H=180, P=10000)
    assert f.s.iloc[0] == SC.S0 and f.n_before.iloc[0] == 0
    m = f.created_at.notna()
    assert (f.created_at[m] < f.first_drop[m]).all()
    # with enough data the scale recovers the generating slope (-0.4) from the prior 0
    assert -0.55 < f.s.iloc[-1] < -0.25


def test_shuffling_same_day_rows_does_not_change_scale():
    date, drop, y, off, z = _frame(2)
    a = SC.asof_scale(date, drop, y, off, z, H=90, P=2000)
    p = np.random.default_rng(5).permutation(len(date))
    b = SC.asof_scale(date[p], drop[p], y[p], off[p], z[p], H=90, P=2000)
    np.testing.assert_allclose(a.s.to_numpy(), b.s.to_numpy(), rtol=0, atol=1e-10)
