"""Hand-built sequences for every rulebook mechanic in GameState / PenaltyBox (SS-R1 engine scope). Offline."""
import numpy as np
import pytest

from nhl_sim.engine import rng
from nhl_sim.engine.box import DOUBLE, MAJOR, MINOR, BoxOverflow
from nhl_sim.engine.rules import ERA_2015, era_for_season
from nhl_sim.engine.state import END_OT, END_REG, END_SO, GameState

H, A = 0, 1
I0 = np.array([0])


def gs(game_type=2, n=1, t=0, auto_end=True):
    g = GameState(np.full(n, game_type), ERA_2015, auto_end=auto_end)
    adv(g, t)
    return g


def adv(g, to):
    """Advance to second `to` and settle it (expire-first convention: events at `to` come after expiries)."""
    g.settle()
    while g.t < to:
        g.end_second()
        g.settle()


def sk(g):
    g.settle()
    return tuple(int(x) for x in g.skaters()[0])


def test_minor_runs_120_seconds_and_spans_periods():
    g = gs(t=1150)
    g.penalty(I0, A, MINOR)
    assert sk(g) == (5, 4)
    adv(g, 1150 + 119)          # last penalised second is t+119, across the period boundary at 1200
    assert sk(g) == (5, 4)
    adv(g, 1150 + 120)
    assert sk(g) == (5, 5)


def test_pp_goal_ends_minor_and_shorthanded_goal_does_not():
    g = gs(t=100)
    g.penalty(I0, A, MINOR)
    adv(g, 130)
    g.goal(I0, A)                # shorthanded goal: penalty stays
    assert sk(g) == (5, 4)
    g.goal(I0, H)                # PP goal: minor ends
    assert sk(g) == (5, 5)
    assert g.box.n_minor_pp_ended[0, A] == 1 and g.box.n_minor[0, A] == 1


def test_major_not_ended_by_goal_and_runs_300():
    g = gs(t=0)
    g.penalty(I0, A, MAJOR)
    g.goal(I0, H)
    g.goal(I0, H)
    assert sk(g) == (5, 4)
    adv(g, 299)
    assert sk(g) == (5, 4)
    adv(g, 300)
    assert sk(g) == (5, 5)


def test_double_minor_goal_in_first_half_restarts_second_minor():
    g = gs(t=0)
    g.penalty(I0, A, DOUBLE)
    adv(g, 60)
    g.goal(I0, H)               # first half: second minor starts fresh (120 s from now)
    assert sk(g) == (5, 4)
    adv(g, 60 + 119)
    assert sk(g) == (5, 4)
    adv(g, 180)
    assert sk(g) == (5, 5)


def test_goal_at_the_exact_expiry_second_falls_after_the_expiry():
    g = gs(t=0)
    g.penalty(I0, A, DOUBLE)
    adv(g, 120)
    g.goal(I0, H)                    # first minor already expired at 120: the goal ends the second minor
    assert sk(g) == (5, 5)
    g2 = gs(t=0)
    g2.penalty(I0, A, MINOR)         # 0..119
    adv(g2, 10)
    g2.penalty(I0, A, MINOR)         # 10..129
    adv(g2, 120)
    g2.goal(I0, H)                   # the first has expired; the goal ends the second
    assert sk(g2) == (5, 5)


def test_same_player_penalties_are_served_consecutively():
    g = gs(t=0)
    g.penalty(I0, A, MINOR, who=np.array([77]))
    g.penalty(I0, A, MINOR, who=np.array([77]))
    assert sk(g) == (5, 4)
    adv(g, 120)
    assert sk(g) == (5, 4)
    adv(g, 240)
    assert sk(g) == (5, 5)
    g2 = gs(t=0)
    g2.penalty(I0, A, MAJOR, who=np.array([5]))
    g2.penalty(I0, A, MINOR, who=np.array([5]))
    g2.goal(I0, H)                   # the waiting minor is not on the clock: the major is not ended
    assert sk(g2) == (5, 4)
    adv(g2, 419)
    assert sk(g2) == (5, 4)
    adv(g2, 420)
    assert sk(g2) == (5, 5)


def test_rs_ot_coincidental_carryover_expiry_does_not_hold():
    g = gs(t=3500)
    g.coincidental(I0, True)         # 4v4 until 3619
    adv(g, 3600)
    assert sk(g) == (3, 3)
    adv(g, 3621)
    assert sk(g) == (3, 3)


def test_double_minor_goal_in_second_half_ends_it_and_full_length_is_240():
    g = gs(t=0)
    g.penalty(I0, A, DOUBLE)
    adv(g, 150)
    g.goal(I0, H)
    assert sk(g) == (5, 5)
    g2 = gs(t=0)
    g2.penalty(I0, A, DOUBLE)
    adv(g2, 239)
    assert sk(g2) == (5, 4)
    adv(g2, 240)
    assert sk(g2) == (5, 5)


def test_three_skater_floor_and_stacked_queue():
    g = gs(t=0)
    g.penalty(I0, A, MINOR)          # 0..119
    adv(g, 10)
    g.penalty(I0, A, MINOR)          # 10..129
    adv(g, 20)
    g.penalty(I0, A, MINOR)          # queued: starts when the first ends (120), runs 120..239
    assert sk(g) == (5, 3)
    adv(g, 120)
    assert sk(g) == (5, 3)           # queued penalty took over
    adv(g, 130)
    assert sk(g) == (5, 4)
    adv(g, 239)
    assert sk(g) == (5, 4)
    adv(g, 240)
    assert sk(g) == (5, 5)


def test_pp_goal_at_5v3_ends_oldest_and_queued_starts():
    g = gs(t=0)
    g.penalty(I0, A, MINOR)          # oldest
    adv(g, 30)
    g.penalty(I0, A, MINOR)
    g.penalty(I0, A, MINOR)          # queued
    adv(g, 40)
    g.goal(I0, H)                    # ends the oldest (assessed at 0); the queued one starts now
    assert sk(g) == (5, 3)
    adv(g, 30 + 120)                 # second minor (30..149) ends
    assert sk(g) == (5, 4)
    adv(g, 40 + 119)
    assert sk(g) == (5, 4)
    adv(g, 40 + 120)
    assert sk(g) == (5, 5)


def test_pp_goal_skips_major_and_ends_minor():
    g = gs(t=0)
    g.penalty(I0, A, MAJOR)
    adv(g, 10)
    g.penalty(I0, A, MINOR)
    g.goal(I0, H)                    # 5v3 goal: the minor (expirable) ends, the major stays
    assert sk(g) == (5, 4)
    adv(g, 299)
    assert sk(g) == (5, 4)
    adv(g, 300)
    assert sk(g) == (5, 5)


def test_coincidental_minors_5v5_exception_gives_4v4_not_ended_by_goal():
    g = gs(t=0)
    assert bool(g.coincidental(I0, True)[0])
    assert sk(g) == (4, 4)
    assert tuple(g.pen_count[0]) == (1, 1)
    g.goal(I0, H)                    # 4v4 goal is not a PP goal
    assert sk(g) == (4, 4)
    adv(g, 120)
    assert sk(g) == (5, 5)


def test_coincidental_offset_when_not_full_strength_or_not_single_minor():
    g = gs(t=0)
    g.penalty(I0, A, MINOR)
    assert not bool(g.coincidental(I0, True)[0])     # already shorthanded: offsetting, strength unchanged
    assert sk(g) == (5, 4)
    g2 = gs(t=0)
    assert not bool(g2.coincidental(I0, False)[0])   # majors / two minors each: offset
    assert sk(g2) == (5, 5)


def test_pp_goal_during_4v4_plus_minor_ends_the_noncoincidental_minor():
    g = gs(t=0)
    g.coincidental(I0, True)         # 4v4, non-expirable
    adv(g, 20)
    g.penalty(I0, A, MINOR)          # 4v3
    assert sk(g) == (4, 3)
    g.goal(I0, H)
    assert sk(g) == (4, 4)
    adv(g, 120)
    assert sk(g) == (5, 5)


def test_rs_ot_3v3_penalties_add_skaters_and_hold_until_stoppage():
    g = gs(t=3600)
    assert sk(g) == (3, 3)
    g.penalty(I0, A, MINOR)          # 4v3
    assert sk(g) == (4, 3)
    adv(g, 3610)
    g.penalty(I0, A, MINOR)          # 5v3
    assert sk(g) == (5, 3)
    adv(g, 3720)                     # first expires: 5v4 until the next stoppage
    assert sk(g) == (5, 4)
    adv(g, 3725)
    g.stoppage(I0)
    assert sk(g) == (4, 3)
    adv(g, 3730)                     # second expires: 4v4 until a stoppage, then 3v3
    assert sk(g) == (4, 4)
    g.stoppage(I0)
    assert sk(g) == (3, 3)


def test_rs_ot_one_penalty_each_is_3v3_and_coincidental_offsets():
    g = gs(t=3600)
    g.penalty(I0, A, MINOR)
    g.penalty(I0, H, MINOR)
    assert sk(g) == (3, 3)
    g2 = gs(t=3600)
    assert not bool(g2.coincidental(I0, True)[0])
    assert sk(g2) == (3, 3)


def test_regulation_penalty_carries_into_rs_ot_as_4v3():
    g = gs(t=3550)
    g.penalty(I0, A, MINOR)
    g.goal(I0, A)
    g.goal(I0, H)                    # PP goal ties it 1-1 and ends the minor
    assert sk(g) == (5, 5)
    g.penalty(I0, H, MINOR)          # 3550..3669
    adv(g, 3600)
    assert g.alive[0]
    assert sk(g) == (3, 4)


def test_playoff_ot_is_5v5_and_continues():
    g = gs(game_type=3, t=3600)
    assert sk(g) == (5, 5)
    adv(g, 3900)
    assert g.alive[0] and int(g.period()[0]) == 4
    adv(g, 4800)
    assert int(g.period()[0]) == 5
    g.goal(I0, H)
    assert not g.alive[0] and g.end_state[0] == END_OT


def test_end_states():
    g = gs(n=3, t=100)
    g.goal(np.array([0]), H)
    adv(g, 3600)
    assert g.end_state[0] == END_REG and g.alive[1] and g.alive[2]
    g.goal(np.array([1]), A)
    assert g.end_state[1] == END_OT
    adv(g, 3900)
    assert g.end_state[2] == END_SO and not g.alive.any()


def test_dead_sims_do_not_tick():
    g = gs(n=2, t=3600)
    g.penalty(np.array([0, 1]), A, MINOR)
    g.goal(np.array([1]), A)          # sim 1 ends in OT
    adv(g, 3700)
    assert g.box.rem[1].max() == 120


def test_overflow_raises():
    g = gs(t=0)
    for _ in range(8):
        g.penalty(I0, A, MINOR)
    with pytest.raises(BoxOverflow):
        g.penalty(I0, A, MINOR)


def test_era_lookup():
    assert era_for_season(20242025) is ERA_2015
    with pytest.raises(ValueError):
        era_for_season(20102011)


def test_rng_streams_are_pure_functions_of_seed_game_family():
    k1 = rng.stream_keys(np.array([0, 1, 2]), np.array([2024020001] * 3), "penalty")
    k2 = rng.stream_keys(np.array([2, 0]), np.array([2024020001] * 2), "penalty")
    u1, u2 = rng.uniform(k1, 5), rng.uniform(k2, 5)
    assert u1[2] == u2[0] and u1[0] == u2[1]
    assert rng.uniform(k1, 5)[0] != rng.uniform(k1, 6)[0]
    kg = rng.stream_keys(np.array([0]), np.array([2024020001]), "goal")
    assert kg[0] != k1[0]
    big = rng.uniform(rng.stream_keys(np.arange(200000), np.full(200000, 7), "x"), 0)
    assert 0 <= big.min() and big.max() < 1 and abs(big.mean() - 0.5) < 0.005
