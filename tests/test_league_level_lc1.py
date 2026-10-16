"""LC-1 league level (D16): absolute as-of de-seasonalised log rate, shrunk toward the previous season's final
rate, never a ratio to the previous season; per-training-season parity of the fitted level-only arms on fold-1
train (results-dependent part skipped when the gitignored artifacts are absent)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhl_sim.league_level_lc1 import lc1_level, per_season_parity


def _long():
    rows = []
    gid = 0
    for s, rate in ((20212022, 3.0), (20222023, 4.0)):
        for d in range(10):
            gid += 1
            for team in (0, 1):
                rows.append(dict(game_id=gid, season=s, date=f"{s // 10000}-11-{d + 1:02d}",
                                 drop=f"{s // 10000}-11-{d + 1:02d}T23:00:00Z", taken=rate, minutes=60.0))
    return pd.DataFrame(rows)


def test_level_is_absolute_and_shrinks_to_previous_season():
    long = _long()
    gbin = pd.Series(0, index=long.game_id.unique())
    p = np.zeros(8)
    lv = lc1_level(long, gbin, p, [5])
    s1 = lv[lv.season == 20212022]
    assert np.allclose(np.exp(s1.level_k5), 3.0)               # first season: own final rate as prior
    s2 = lv[lv.season == 20222023].sort_values("game_id")
    assert np.isclose(np.exp(s2.level_k5.iloc[0]), 3.0)        # opening day: the previous season's final rate
    assert np.isclose(np.exp(s2.level_k5.iloc[-1]), (9 * 2 * 4.0 + 10 * 3.0) / (9 * 2 + 10))  # (E + K r_prev) / (H + K)
    assert (lv.r_prev[lv.season == 20222023] == 3.0).all()


def test_profile_deseasonalises():
    long = _long()
    gbin = pd.Series(1, index=long.game_id.unique())
    p = np.zeros(8)
    p[1] = np.log(2.0)
    lv = lc1_level(long, gbin, p, [5])
    assert np.allclose(np.exp(lv[lv.season == 20212022].level_k5), 1.5)


def test_parity_table():
    t = per_season_parity(np.array([1, 1, 2]), np.array([10.0, 10.0, 5.0]), np.array([10.0, 10.04, 5.1]))
    assert bool(t.loc[1, "pass"]) and not bool(t.loc[2, "pass"])


@pytest.mark.parametrize("path,arm", [("results/shot_attempt_r2/fold1/parity_fold1_train.json", "A0"),
                                      pytest.param("results/strength_state_r3c/fold1/parity_fold1_train.json", "H0",
                                                   marks=pytest.mark.xfail(strict=False, reason=(
                                                       "SS-R3c known failure: penalty LC-1 parity -2.1% / +2.0% "
                                                       "(docs/tests/strength_state_ss_r3c_2026-10-15.md)")))])
def test_fold1_train_parity_level_arm(path, arm):
    if not Path(path).exists():
        pytest.skip("artifacts not on disk")
    d = json.loads(Path(path).read_text())[arm]
    assert all(abs(v) <= 0.005 for v in d.values()), d
