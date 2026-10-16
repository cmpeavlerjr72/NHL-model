import numpy as np

from nhl_sim.eval import responsiveness as RS


def _make(scale, n=20000, seed=1, per_game=2):
    rng = np.random.default_rng(seed)
    g = np.repeat(np.arange(n // per_game), per_game)
    rating = rng.normal(size=n)
    actual = 3.0 + 0.5 * rating + rng.normal(scale=1.0, size=n)
    pred = 3.0 + 0.5 * scale * rating
    return pred, actual, rating, np.ones(n), g


def test_calibrated_is_one():
    r = RS.slope_ratio(*_make(1.0), n_boot=200)
    assert 0.9 < r["R"] < 1.1 and r["status"] == "PASS"
    assert r["ci"][0] < r["R"] < r["ci"][1]


def test_over_responding_gt_one():
    r = RS.slope_ratio(*_make(1.5), n_boot=200)
    assert r["R"] > 1.3 and r["status"] == "FAIL"


def test_bootstrap_resamples_games_not_rows():
    # strong within-game correlation: noise shared by both rows of a game -> game-block CI must be wider than row CI
    rng = np.random.default_rng(3)
    ng, k = 400, 20
    g = np.repeat(np.arange(ng), k)
    rating = np.repeat(rng.normal(size=ng), k) + rng.normal(scale=0.1, size=ng * k)
    actual = 0.5 * rating + np.repeat(rng.normal(size=ng), k)
    pred = 0.5 * rating
    w = np.ones(ng * k)
    blk = RS.slope_ratio(pred, actual, rating, w, g, n_boot=300)
    row = RS.slope_ratio(pred, actual, rating, w, np.arange(ng * k), n_boot=300)
    assert (blk["ci"][1] - blk["ci"][0]) > 1.5 * (row["ci"][1] - row["ci"][0])
    assert blk["n_games"] == ng and row["n_games"] == ng * k


def test_underpowered_flag():
    r = RS.slope_ratio(*_make(1.0, n=100), n_boot=200)
    assert r["underpowered"]
