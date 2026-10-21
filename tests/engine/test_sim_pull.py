"""EG-R1 part A (INV-66, Lane H8a): goalie pull + EN cascade engine flag (tables["pull"]).

- Flag off: bit-identical to HEAD d5e387a on every l1xas_parity_cases case (fixture tests/fixtures/sim_pull_flag_parity.json,
  recorded by scripts/diag_engine_l1xas_parity_fixture.py --commit d5e387a BEFORE the edit).
- Return rules (GameState): the goalie returns at a goal against and at the own tying goal, not at a non-tying goal for;
  in a full sim the goalie-out state never persists past a tying goal.
- Served pull hazard == offline pull.hazard (P1 and P0) on the 2024-25 pull rows, < 1e-6.
- A synthetic pull-on run finishes, visits the EN states, carries the markers, and keeps goals == score.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import l1xas_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402

from nhl_sim.end_game import pull as PL  # noqa: E402
from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine import state as STATE  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_pull_flag_parity.json").read_text())
MOD = Path("data/processed/end_game/models_v1")


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_bit_identical_to_head(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    assert T2.digest(C.run(SIM, name, ERA_2015)) == FIX["cases"][name]


def _gs(score_h, score_a, pulled_team):
    gs = STATE.GameState(np.array([2]), ERA_2015)
    gs.track_pull = True
    gs.t = 3500
    gs.score[0] = (score_h, score_a)
    gs.pulled[0, pulled_team] = True
    return gs


def test_return_at_goal_against():
    gs = _gs(1, 0, 1)                    # away trails 0-1 with its goalie out; home scores into the empty net
    gs.goal(np.array([0]), 0)
    assert not gs.pulled[0, 1] and gs.pulled_before[0, 1] and gs.last_return[0, 1] == 3500 and gs.n_ret_ga[0, 1] == 1


def test_return_at_own_tying_goal():
    gs = _gs(1, 0, 1)
    gs.goal(np.array([0]), 1)            # away ties 1-1
    assert not gs.pulled[0, 1] and gs.n_ret_tie[0, 1] == 1


def test_no_return_at_non_tying_goal_for():
    gs = _gs(2, 0, 1)
    gs.goal(np.array([0]), 1)            # 2-1: still trailing, goalie stays out
    assert gs.pulled[0, 1] and not gs.pulled_before[0, 1]


def test_track_pull_off_changes_nothing():
    gs = _gs(1, 0, 1)
    gs.track_pull = False
    gs.goal(np.array([0]), 0)
    assert gs.pulled[0, 1] and not gs.pulled_before[0, 1]


def _pull_tables(G, h=0.01, kind="P1"):
    rng = np.random.default_rng(7)
    if kind == "P1":
        hz = dict(kind="P1", table=np.full((3, 60, 3, 2, 2), h))
    else:
        hz = dict(kind="P0", h_first=np.full((3, 2, 600), h), h_repull=np.full(601, h))
    return dict(hazard=hz, en_lam=np.tile([150.0, 45.0], (G, 1)), p_en_goal=np.ones(G),
                eaf_cls=rng.normal(-2.5, 0.3, 78), eaf_game=rng.normal(0, 0.1, (G, 2)),
                p_block_en=rng.uniform(0.15, 0.4, (G, 2, 2)), p_miss_en=rng.uniform(0.2, 0.45, (G, 2, 2, 78)),
                label="goalie pull: test", stand_in={"en_attempts": "STAND-IN test", "en_goal": "STAND-IN test"})


def _syn_run(kind="P1", h=0.01):
    t, g, gt, n, s0 = C.syn_stack(False)
    t["pull"] = _pull_tables(len(g), h, kind)
    return SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=False, seasons=C.C.mixed_seasons(len(g)))


@pytest.mark.parametrize("kind", ["P1", "P0"])
def test_pull_on_synthetic_run(kind):
    o = _syn_run(kind)
    assert o["unfinished"] == 0
    assert o["att_st"].shape[2] == 7 and o["attr_goals"].shape[2] == 7
    assert o["att_st"][:, :, 5].sum() > 0 and o["att_st"][:, :, 6].sum() > 0
    assert o["attr_goals"].sum() == o["score"].sum()
    en_ag = o["attr_goals"][:, :, 6]
    assert en_ag.sum() > 0 and (en_ag == o["attr_sog"][:, :, 6]).all()        # p_en_goal = 1: every EN SOG scores
    ft = o["first_pull_t"]
    assert ((ft == -1) | ((ft >= 3000) & (ft < 3600))).all()
    assert (o["pull_s"] <= 600).all() and o["pull_s"].sum() > 0
    assert o["n_pulls"].sum() >= o["n_repulls"].sum()
    assert str(o["pull_model"][0]) == "goalie pull: test" and len(o["pull_stand_in"]) == 2


def test_goalie_never_out_past_a_tying_goal(monkeypatch):
    orig = STATE.GameState.goal
    seen = {"ties": 0}

    def checked(self, idx, team):
        orig(self, idx, team)
        idx = np.asarray(idx, np.int64)
        if idx.size and self.track_pull:
            tied = self.score[idx, 0] == self.score[idx, 1]
            seen["ties"] += int(tied.sum())
            assert not self.pulled[idx[tied]].any(), "a goalie is still out after a tying goal"

    monkeypatch.setattr(STATE.GameState, "goal", checked)
    o = _syn_run("P1", h=0.03)
    assert seen["ties"] > 0 and o["n_ret_tie"].sum() > 0


def test_pull_needs_default_cascade():
    t, g, gt, n, s0 = C.syn_stack(False)
    t["pull"] = _pull_tables(len(g))
    t["attr"].pop("goal")
    t["attr"].pop("p_miss_game")
    t["attr"]["stand_in"].pop("miss")
    with pytest.raises(ValueError):
        SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, seasons=C.C.mixed_seasons(len(g)))


@pytest.mark.parametrize("arm", ["P1", "P0"])
def test_served_hazard_equals_offline(arm):
    import pandas as pd
    p = Path("data/processed/end_game/pull_rows_v1_20242025.parquet")
    if not p.exists():
        pytest.skip("pull rows not built")
    m = json.loads((MOD / f"fold2_{arm}.json").read_text())
    rows = pd.read_parquet(p)
    if arm == "P1":
        PS = dict(kind="P1", table=PL.p1_table(m), reg_end=3600)
    else:
        h0, h1 = PL.p0_tables(m)
        PS = dict(kind="P0", h_first=h0, h_repull=h1, reg_end=3600)
    dmax = 0.0
    for s, x in rows.groupby("s"):
        sv = SIM.pull_hazard(PS, x.dcat.to_numpy(), int(s), x.pen.to_numpy(), x.pb.to_numpy(), x.is_home.to_numpy(), x.lag.to_numpy())
        off = PL.hazard(m, x.dcat, x.s, x.pen, x.pb, x.is_home, x.lag)
        dmax = max(dmax, float(np.abs(sv - off).max()))
    assert dmax < 1e-6
