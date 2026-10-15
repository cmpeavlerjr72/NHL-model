import numpy as np
import pandas as pd
import pytest

from nhl_sim.eval import gates as G

TOL = {"min_cell_n": 300, "g5_sd_ratio_lo": .95, "g5_sd_ratio_hi": 1.05, "g5_corr": .05, "g5_ks_p": .1,
       "g5_total_cell_pp": 1.0, "g6_win_pp": 1.5, "g6_goal_diff": .08, "g7_reg_tie_pp": 1.5, "g7_shootout_pp": 1.0,
       "g7_en_goals_per_game": .03, "g9_total_bias": .1, "g9_margin_bias": .08, "g9_slope_lo": .95, "g9_slope_hi": 1.05}


def make_real(n=2000, seed=0):
    r = np.random.default_rng(seed)
    h, a = r.poisson(3.1, n), r.poisson(2.9, n)
    es = np.where(h == a, r.choice(["OT", "SO"], n), "REG")
    h = np.where(es == "OT", h + 1, h)  # home wins every OT in this toy world
    hw = np.where(es == "SO", r.random(n) < .5, h > a)
    return pd.DataFrame({"game_id": np.arange(n), "season": 1, "game_type": 2, "home_goals": h, "away_goals": a,
                         "end_state": es, "home_win": hw, "home_en_goals": 0, "away_en_goals": 0})


def sim_from(real, seeds=20, seed=1):
    r = np.random.default_rng(seed)
    parts = []
    for s in range(seeds):
        d = real.copy()
        d["seed"] = s
        h, a = r.poisson(3.1, len(d)), r.poisson(2.9, len(d))
        es = np.where(h == a, r.choice(["OT", "SO"], len(d)), "REG")
        h = np.where(es == "OT", h + 1, h)
        d["home_goals"], d["away_goals"], d["end_state"] = h, a, es
        d["home_win"] = np.where(es == "SO", r.random(len(d)) < .5, h > a)
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def test_summarize_basic():
    real = make_real()
    s = G.summarize(real)
    assert abs(sum(s[("G5", "total_p", f"k={k}")] for k in G.TOTAL_K) - 1) < 1e-9
    assert abs(sum(s[("G5", "margin_p", f"m={m}")] for m in G.MARGIN_M) - 1) < 1e-9
    assert 0 < s[("G7", "reg_tie_rate", "")] < 1


def test_same_world_passes_and_en_needs_instrumentation():
    real = make_real()
    t = G.targets_table(real, 1)
    sim = sim_from(real).drop(columns=["home_en_goals", "away_en_goals"])
    res = G.evaluate(sim, real, t, TOL)
    assert res["G5"]["status"] == "PASS", res["G5"]["checks"]
    assert res["G6"]["status"] == "PASS"
    assert res["G7"]["status"] == "NEEDS-INSTRUMENTATION"
    assert all(res[g]["status"] == "NEEDS-INSTRUMENTATION" for g in ("G1", "G2", "G3", "G4", "G8"))


def test_distorted_sim_fails():
    real = make_real()
    t = G.targets_table(real, 1)
    sim = sim_from(real)
    sim["home_goals"] = sim.home_goals + (np.random.default_rng(2).random(len(sim)) < .5)  # inflate totals
    sim["home_win"] = True
    res = G.evaluate(sim, real, t, TOL)
    assert res["G5"]["status"] == "FAIL"
    assert res["G6"]["status"] == "FAIL"
    assert res["G9"]["status"] == "FAIL"


def test_underpowered_small_segment():
    real = make_real(100)
    t = G.targets_table(real, 1)
    res = G.evaluate(sim_from(real), real, t, TOL)
    assert res["G5"]["status"] == "UNDERPOWERED"


def test_loader_validation(tmp_path):
    real = make_real(50)
    sim = sim_from(real, 2)
    sim.drop(columns=["season", "game_type", "home_en_goals", "away_en_goals"]).to_parquet(tmp_path / "games.parquet")
    g, _ = G.load_sim_output(tmp_path)
    assert len(g) == 100
    bad = sim.drop(columns=["season", "game_type"]).copy()
    bad.loc[bad.end_state == "SO", "home_goals"] += 1
    bad.to_parquet(tmp_path / "games.parquet")
    with pytest.raises(ValueError):
        G.load_sim_output(tmp_path)
    (tmp_path / "run_meta.json").write_text('{"sealed_touched": true}')
    sim.drop(columns=["season", "game_type"]).to_parquet(tmp_path / "games.parquet")
    with pytest.raises(ValueError):
        G.load_sim_output(tmp_path)


def test_real_games_and_targets_on_real_data():
    from nhl_sim.data.load import load_games  # noqa: F401
    real = G.real_games(20242025)
    assert len(real) == 1398
    # SO games have tied goals, REG/OT untied
    assert (real.home_goals[real.end_state == "SO"] == real.away_goals[real.end_state == "SO"]).all()
    assert (real.home_goals[real.end_state != "SO"] != real.away_goals[real.end_state != "SO"]).all()
    assert 0.3 < (real.home_en_goals + real.away_en_goals).mean() < 0.5


def test_sealed_season_refused():
    from nhl_sim.data.seal import SealedSeasonError
    with pytest.raises(SealedSeasonError):
        G.real_games(20252026)
