"""INV-60 / INV-57 / INV-54 (Lane E2) in engine/sim.py: per-game stage-4 level (game_mult), B0 with own 4v4 / 3v3 groups
((G, 5, 2) p_block_game), miss S0t STAND-IN (p_miss_game) and goal C1s (attr["goal"]); every flag default off.

- Flag off: every output array is bit-identical (sha256) to the pre-change engine (7fac157) on the D32 stand-in fixture
  cases plus the D32 stand-ins switched on as served before, fixture tests/fixtures/sim_c1s_flag_parity.json
  (scripts/diag_engine_c1s_parity_fixture.py).
- Wiring: a game_mult constant over games equal to era_mult reproduces the era-levelled run; a (G, 5, 2) block table
  whose 4v4 / 3v3 rows equal ES reproduces the (G, 3, 2) run; with p_miss = 0 and a goal table equal to logit xG_ref the
  goal path reproduces the xG_ref draws (apart from the new output keys).
- Served vs offline (real tables; skipped when the gitignored results are absent): L0s (M1 K500), B0 (own 4v4 / 3v3),
  miss S0t and goal C1s each within 1e-6.
- Schema: oracle_goalie / goal_model / stand_in markers present; unlabelled stand-ins refused; the seal still refuses
  2025-26 in the table builders.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c1s_parity_cases as C  # noqa: E402
import standin_parity_cases as SC  # noqa: E402
import t2_parity_cases as T2  # noqa: E402

from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_c1s_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_bit_identical_to_pre_change_engine(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    out = C.run(SIM, name, ERA_2015)
    assert out["unfinished"] == 0
    assert "oracle_goalie" not in out and "attr_sog" not in out
    assert T2.digest(out) == FIX["cases"][name]


# ------------------------------------------------------------------------------------------------- wiring
def _base(per_team=True):
    t, g, gt, n, s0 = SC.syn_levelled(per_team)
    return t, g, gt, n, s0, SC.mixed_seasons(len(g))


def _common(d, ref):
    return {k: v for k, v in d.items() if k in ref}


def _run(t, g, gt, n, s0, seasons, per_team=True):
    return SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=per_team, seasons=seasons)


def test_game_mult_equal_to_era_mult_reproduces_era_path():
    from nhl_sim.engine.rules import recording_era
    t, g, gt, n, s0, seasons = _base()
    o_era = _run(t, g, gt, n, s0, seasons)
    attr = {k: v for k, v in t["attr"].items() if k != "era_mult"}
    attr["game_mult"] = t["attr"]["era_mult"][recording_era(seasons)]
    o_g = _run(dict(t, attr=attr), g, gt, n, s0, seasons)
    assert o_g["attr_fen"].sum() > 0
    assert T2.digest(o_g) == T2.digest(o_era)


def test_b0_five_group_table_with_es_rows_reproduces_three_group_table():
    t, g, gt, n, s0, seasons = _base()
    rng = np.random.default_rng(41)
    p3 = rng.uniform(0.1, 0.35, size=(len(g), 3, 2))
    a3 = {k: v for k, v in t["attr"].items() if k != "p_block"}
    a3.update(p_block_game=p3, stand_in={"block": "STAND-IN x"})
    p5 = np.concatenate([p3, p3[:, [0, 0]]], axis=1)
    o3 = _run(dict(t, attr=a3), g, gt, n, s0, seasons)
    o5 = _run(dict(t, attr=dict(a3, p_block_game=p5)), g, gt, n, s0, seasons)
    assert T2.digest(o5) == T2.digest(o3)
    p5[:, 3:] = 0.0                                   # 4v4 / 3v3 groups are served from their own rows
    o0 = _run(dict(t, attr=dict(a3, p_block_game=p5)), g, gt, n, s0, seasons)
    assert (o0["attr_fen"][:, :, 3:] == o0["att_st"][:, :, 3:]).all()


def _goal_attr(t, g, xg_like=True, p_miss=0.0):
    G = len(g)
    xg = t["attr"]["xg"]
    lx = np.log(xg / (1 - xg))
    goal = dict(cls_logit=lx[:, SIM.ST_RGRP] if xg_like else np.zeros((78, 5)), game_logit=np.zeros((G, 2, 5)),
                sc_logit=np.zeros(7), goalie_id=np.arange(2 * G).reshape(G, 2) + 8470000, label="goal: test",
                oracle_goalie="ORACLE GOALIE (test)")
    return dict(t["attr"], p_miss_game=np.full((G, 3, 2, 78), p_miss), goal=goal,
                stand_in={"miss": "STAND-IN test miss"})


def test_zero_miss_and_xg_goal_table_reproduce_xg_draws():
    t, g, gt, n, s0, seasons = _base()
    o_x = _run(t, g, gt, n, s0, seasons)
    o_c = _run(dict(t, attr=_goal_attr(t, g)), g, gt, n, s0, seasons)
    assert T2.digest(_common(o_c, o_x)) == T2.digest(o_x)
    assert (o_c["attr_sog"] == o_c["attr_fen"]).all()
    assert np.isclose(o_c["attr_gprob"], o_c["attr_xg"]).all()


def test_goal_path_conserves_counts_and_carries_markers():
    t, g, gt, n, s0, seasons = _base(False)
    o = _run(dict(t, attr=_goal_attr(t, g, p_miss=0.3)), g, gt, n, s0, seasons, per_team=False)
    assert o["unfinished"] == 0
    assert (o["attr_sog"] <= o["attr_fen"]).all() and (o["attr_goals"] <= o["attr_sog"]).all()
    assert o["attr_goals"].sum() == o["score"].sum()
    assert 0.6 < o["attr_sog"].sum() / o["attr_fen"].sum() < 0.8
    assert "oracle" in str(o["oracle_goalie"][0]).lower() and str(o["goal_model"][0]) == "goal: test"
    assert any(m.startswith("miss: STAND-IN") for m in o["stand_in"])
    assert o["goalie_against"].shape == (len(g), 2)


@pytest.mark.parametrize("bad", ["no_miss_label", "no_oracle", "miss_without_goal", "goal_without_miss"])
def test_refusals(bad):
    t, g, gt, n, s0, seasons = _base(False)
    attr = _goal_attr(t, g)
    if bad == "no_miss_label":
        attr["stand_in"] = {}
    elif bad == "no_oracle":
        attr["goal"] = dict(attr["goal"], oracle_goalie="starter")
    elif bad == "miss_without_goal":
        attr.pop("goal")
    else:
        attr.pop("p_miss_game")
    with pytest.raises(ValueError):
        _run(dict(t, attr=attr), g, gt, n, s0, seasons, per_team=False)


# ------------------------------------------------------------------------------- served vs offline (real)
def _real_c1s_available():
    return all(Path(p).exists() for p in ("results/block_sb_r1/models/B0.json", "results/shot_attribute_r6_d38/models/L0s.json",
                                          "results/miss_sm_r2/models/S0t.json", "results/goal_g_r3/fold2/models/C1s.json",
                                          "results/strength_state_r3/fold2_rows.parquet"))


@pytest.fixture(scope="module")
def games():
    import pandas as pd
    return np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"]).game_id.unique())


@pytest.mark.skipif(not _real_c1s_available(), reason="gitignored results not on disk")
def test_served_matches_offline_l0s_m1k500(games):
    from nhl_sim.engine import c1s_tables as CT
    sp, gm, _ = CT.l0s_m1k500_tables(games)
    p = CT.l0s_parity(games, sp, gm)
    assert p["n_rows"] > 100_000 and p["max_abs_diff"] < 1e-6


@pytest.mark.skipif(not _real_c1s_available(), reason="gitignored results not on disk")
def test_served_matches_offline_b0_own_groups(games):
    from nhl_sim.engine import c1s_tables as CT
    pb, info = CT.block_b0g_table(games)
    p = CT.b0g_parity(games, pb, info)
    assert p["n_rows"] > 100_000 and p["max_abs_diff"] < 1e-6 and info["es_level_recompute_max_dev"] < 1e-12
    by = {r["state"]: r for r in p["by_state"]}
    for s_ in ("4v4", "3v3"):                         # own groups served (not the ES rate)
        assert abs(by[s_]["served_after"] - by[s_]["served_before"]) > 0.01


@pytest.mark.skipif(not _real_c1s_available(), reason="gitignored results not on disk")
def test_served_matches_offline_miss_s0t(games):
    from nhl_sim.engine import c1s_tables as CT
    pm, _ = CT.miss_s0t_table(games)
    p = CT.miss_parity(games, pm)
    assert p["n_rows"] > 100_000 and p["max_abs_diff"] < 1e-6


@pytest.mark.skipif(not _real_c1s_available(), reason="gitignored results not on disk")
def test_served_matches_offline_goal_c1s(games):
    from nhl_sim.engine import c1s_tables as CT
    goal, _ = CT.goal_c1s_tables(games)
    p = CT.goal_parity(games, goal)
    assert p["n_rows"] > 70_000 and p["max_abs_diff"] < 1e-6 and p["n_relief_rows"] > 0
    assert "oracle" in goal["oracle_goalie"].lower() and goal["label"] == "goal: C1s (provisional, D40)"


def test_seal_still_refuses_2025_26(monkeypatch):
    from nhl_sim.data.load import PROCESSED
    from nhl_sim.data.seal import SEALED_SEASON, SealedSeasonError
    from nhl_sim.engine import c1s_tables as CT
    if not (PROCESSED / "games.parquet").exists():
        pytest.skip("no processed data")
    monkeypatch.delenv("NHL_UNSEAL_2025", raising=False)
    with pytest.raises(SealedSeasonError):
        CT.starters(np.array([2025020001]), season=SEALED_SEASON)
