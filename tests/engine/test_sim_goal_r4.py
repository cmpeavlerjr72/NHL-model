"""G-R4 (INV-74, Lane G4): the goal C1s-sap engine flag (attr["goal"]["sc_game"]).

- Flag off: bit-identical to HEAD 4c7570d (Lane B5 engine_b1aas) on every l1xas_parity_cases case (fixture
  tests/fixtures/sim_goal_r4_flag_parity.json, recorded by scripts/diag_engine_l1xas_parity_fixture.py --commit 4c7570d
  BEFORE the edit).
- Flag on with sc_game[g, per, sc] = sc_logit[sc] for every game and period: bit-identical to flag off (the lookup is the
  only change); a period-specific term moves only that period; goal_prob indexes game x period x score; validation.
- Served vs offline: the fold-2 C1s-sap tables against the G-R4 offline predictions (<= 1e-6), when the data is on disk.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import l1xas_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402

from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_goal_r4_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_bit_identical_to_head(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    assert T2.digest(C.run(SIM, name, ERA_2015)) == FIX["cases"][name]


def _run(scg_fn=None, n=30):
    t, g, gt, _, _ = C.syn_stack(False)
    if scg_fn is not None:
        goal = t["attr"]["goal"]
        goal["sc_game"] = scg_fn(len(g), np.asarray(goal["sc_logit"], float))
    return SIM.simulate(t, g, gt, n, ERA_2015, seed0=1, per_team_types=False, seasons=C.C.mixed_seasons(len(g)))


def test_flag_on_with_pooled_terms_is_identical():
    off = _run(None)
    on = _run(lambda G, sl: np.broadcast_to(sl, (G, 4, 7)).copy())
    assert T2.digest(on) == T2.digest(off)


def test_period_term_moves_only_that_period():
    base = _run(lambda G, sl: np.broadcast_to(sl, (G, 4, 7)).copy())

    def p3(G, sl):
        x = np.broadcast_to(sl, (G, 4, 7)).copy()
        x[:, 2, :] += 1.5
        return x
    hi = _run(p3)
    assert hi["attr_goals"].sum() > base["attr_goals"].sum()
    assert (hi["score"].sum() > base["score"].sum())


def test_goal_prob_indexes_game_period_score():
    G = 2
    AS = dict(goal_cls=np.zeros((3, 5)), goal_game=np.zeros((G, 2, 5)), goal_sc=np.zeros(7),
              goal_sc_game=np.zeros((G, 4, 7)))
    AS["goal_sc_game"][1, 2, 5] = 0.8
    gi, tm, st, sc, cls = np.array([1, 1, 0]), 0, np.array([0, 0, 0]), np.array([5, 5, 5]), np.array([0, 0, 0])
    v = SIM.goal_prob(AS, gi, tm, st, sc, cls, 2)
    np.testing.assert_allclose(v, 1 / (1 + np.exp(-np.array([0.8, 0.8, 0.0]))), rtol=0, atol=1e-15)
    np.testing.assert_allclose(SIM.goal_prob(AS, gi, tm, st, sc, cls, 1), 0.5, rtol=0, atol=1e-15)
    with pytest.raises(ValueError):
        SIM.goal_prob(AS, gi, tm, st, sc, cls)


def test_validation():
    with pytest.raises(ValueError):
        _run(lambda G, sl: np.zeros((G, 3, 7)))
    with pytest.raises(ValueError):
        _run(lambda G, sl: np.full((G, 4, 7), np.nan))


def test_served_vs_offline_fold2():
    root = Path(__file__).resolve().parents[2]
    if not (root / "results/goal_g_r4/fold2/fold2_rows.parquet").exists() or not C.real_available():
        pytest.skip("gitignored G-R4 / G-R3 results not on disk")
    from nhl_sim.data.load import load_games
    from nhl_sim.engine import c1s_tables as CT
    from nhl_sim.engine import goal_r4_tables as GR
    games = np.sort(load_games([20242025], columns=["game_id"]).game_id.to_numpy())
    P = CT._goal_parts(games)
    goal, _ = GR.goal_r4_tables(games, P=P)
    par = GR.goal_r4_parity(games, goal, P, use_engine=True)
    assert par["max_abs_diff"] <= 1e-6
