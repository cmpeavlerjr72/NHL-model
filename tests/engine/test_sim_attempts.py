"""Stage-3 attempt variant of the closed-loop engine (SA-R1): attempt counts follow the lookup rate, goals come only
from attempts x p_goal, the variant is off by default, and streams are paired across runs."""
import numpy as np

from nhl_sim.engine.rules import ERA_2015
from nhl_sim.engine.sim import poisson_k, simulate


def tables(att_per_h=60.0, p_goal=0.0, G=3):
    lam = np.zeros((G, 2, 100, 5, 5, 5), np.float32)
    types = np.zeros((6, 5, 4, 4))
    types[..., 0] = 1.0
    t = dict(lam=lam, types=types, coinc_smp=np.array([True]), coinc_pim=np.array([4], np.int16),
             goal_rate=np.full((3, 3), 50.0), stop_rate_ot=0.02)
    t["att_lam"] = np.full((G, 2, 100, 5, 7), att_per_h, np.float32)
    t["p_goal"] = np.full(5, p_goal)
    return t


def test_poisson_k_matches_poisson_mean():
    u = np.random.default_rng(0).random(2_000_000)
    lam = np.full(u.shape, 0.02)
    k = poisson_k(u, lam)
    assert abs(k.mean() / 0.02 - 1) < 0.01 and k.max() <= 2


def test_attempt_rate_and_no_stub_goals():
    o = simulate(tables(), np.array([1, 2, 3]), np.array([2, 2, 2]), 200, ERA_2015)
    # p_goal = 0: no goals at all (the stub goal table, 50/h, must not be used), every game reaches the shootout
    assert (o["score"] == 0).all() and (o["end_state"] == 3).all()
    played = 3900
    rate = o["att_st"].sum(-1) / played * 3600
    assert abs(rate.mean() / 60.0 - 1) < 0.01
    assert (o["toi_st_sc"].sum((1, 2)) == played).all()
    assert (o["att_sc"].sum(-1) == o["att_st"].sum(-1)).all()


def test_goals_come_from_attempts_and_streams_pair():
    t = tables(att_per_h=60.0, p_goal=0.1)
    o1 = simulate(t, np.array([1, 2, 3]), np.array([2, 2, 2]), 50, ERA_2015)
    o2 = simulate(t, np.array([1, 2, 3]), np.array([2, 2, 2]), 50, ERA_2015)
    assert (o1["score"] == o2["score"]).all() and (o1["att_st"] == o2["att_st"]).all()
    g = o1["score"].sum()
    att = o1["att_st"].sum()
    assert abs(g / att / 0.1 - 1) < 0.1
    assert (o1["score"].sum(1) <= o1["att_st"].sum((1, 2))).all()


def test_default_off_keeps_stub_goal_path():
    t = tables()
    t.pop("att_lam")
    t.pop("p_goal")
    o = simulate(t, np.array([1, 2, 3]), np.array([2, 2, 2]), 5, ERA_2015)
    assert "att_st" not in o and o["score"].sum() > 0
