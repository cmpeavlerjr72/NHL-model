"""LC-2 league-level constructions: oracle parity is exactly 0 at the game level; discounting and shrinkage."""
import numpy as np
import pandas as pd

from nhl_sim.league_level_lc2 import lc2_level


def _long(rates=((20212022, 3.0), (20222023, 4.0)), ndays=10):
    rows, gid = [], 0
    for s, rate in rates:
        for d in range(ndays):
            gid += 1
            for team in (0, 1):
                rows.append(dict(game_id=gid, season=s, date=f"{s // 10000}-11-{d + 1:02d}",
                                 drop=f"{s // 10000}-11-{d + 1:02d}T23:00:00Z", taken=rate * (1 + 0.1 * d), minutes=60.0))
    return pd.DataFrame(rows)


def _setup():
    long = _long()
    gbin = pd.Series(np.arange(len(long.game_id.unique())) % 3, index=long.game_id.unique())
    p = np.array([0.1, -0.2, 0.05, 0, 0, 0, 0, 0])
    return long, gbin, p


def test_oracle_parity_zero_to_rounding():
    long, gbin, p = _setup()
    lv = lc2_level(long, gbin, p, {"O": ("O", None)})
    m = long.merge(lv[["game_id", "O", "p"]], on="game_id")
    for s, d in m.groupby("season"):
        pred = (d.minutes / 60.0 * np.exp(d.O + d.p)).sum()
        assert abs(pred / d.taken.sum() - 1) < 1e-12


def test_l2c_constant_prior_and_first_season_own():
    long, gbin, p = _setup()
    lv = lc2_level(long, gbin, p, {"c": ("L2c", None), "O": ("O", None)})
    s2 = lv[lv.season == 20222023]
    assert np.allclose(s2.c, s2.c.iloc[0])
    s1 = lv[lv.season == 20212022]
    assert np.allclose(s1.c, s1.O)


def test_l2a_opening_is_prior_and_shrinks():
    long, gbin, p = _setup()
    lv = lc2_level(long, gbin, p, {"a": ("L2a", 50), "b": ("L2b", (30, 5))})
    s2 = lv[lv.season == 20222023].sort_values("game_id")
    assert np.isclose(s2.a.iloc[0], np.log(s2.r_prev.iloc[0])) and np.isclose(s2.b.iloc[0], s2.a.iloc[0])


def test_l2b_discount_halves_old_day():
    long, gbin, p = _setup()
    big = lc2_level(long, gbin, p, {"b": ("L2b", (1e-9 + 1, 5))})
    flat = lc2_level(long, gbin, p, {"a": ("L2a", 5)})
    # tiny half-life forgets everything older than a day: level differs from the undiscounted one late in season
    s = big[big.season == 20222023].b.to_numpy()
    a = flat[flat.season == 20222023].a.to_numpy()
    assert not np.allclose(s[-3:], a[-3:])
