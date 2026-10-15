"""Closed-loop sim loop on synthetic lookup tables (offline, fast)."""
import numpy as np

from nhl_sim.engine.rules import ERA_2015
from nhl_sim.engine.sim import simulate


def tables(lam_per_h=0.0, goal_per_h=0.0, p_coinc=0.0, G=3):
    lam = np.full((G, 2, 100, 5, 5, 5), lam_per_h, np.float32)
    types = np.zeros((6, 5, 4, 4))
    types[..., 0] = 1.0 - p_coinc
    types[..., 3] = p_coinc
    return dict(lam=lam, types=types, coinc_smp=np.array([True]), coinc_pim=np.array([4], np.int16),
                goal_rate=np.full((3, 3), goal_per_h), stop_rate_ot=0.02)


def test_no_penalties_no_goals_is_all_5v5_then_3v3_ot_and_shootout():
    o = simulate(tables(), np.array([1, 2, 3]), np.array([2, 2, 2]), 4, ERA_2015)
    assert (o["toi"][:, 0] == 3600).all() and (o["toi"][:, 4] == 300).all()
    assert (o["end_state"] == 3).all() and (o["ppo"] == 0).all()


def test_playoff_ties_continue_until_a_goal():
    o = simulate(tables(goal_per_h=3.0), np.array([1, 2, 3]), np.array([3, 3, 3]), 20, ERA_2015)
    assert o["unfinished"] == 0
    assert set(np.unique(o["end_state"])) <= {1, 2}
    assert (o["score"][:, 0] != o["score"][:, 1]).all()


def test_penalties_create_pp_time_and_streams_are_paired():
    t = tables(lam_per_h=3.0, goal_per_h=3.0, p_coinc=0.2)
    o1 = simulate(t, np.array([1, 2, 3]), np.array([2, 2, 2]), 10, ERA_2015)
    o2 = simulate(t, np.array([1, 2, 3]), np.array([2, 2, 2]), 10, ERA_2015)
    assert (o1["toi"] == o2["toi"]).all() and (o1["score"] == o2["score"]).all()
    assert o1["ppo"].sum() > 0 and o1["toi"][:, 1].sum() > 0 and o1["n_type"][..., 3].sum() > 0
    # a seed-offset batch reproduces the matching seeds of a larger batch
    o3 = simulate(t, np.array([1, 2, 3]), np.array([2, 2, 2]), 5, ERA_2015, seed0=5)
    big = o1["toi"].reshape(3, 10, -1)[:, 5:]
    assert (o3["toi"].reshape(3, 5, -1) == big).all()
