"""EG-R1 parts B and C (Lane H8b): shootout mechanics, as-of levels, regular-season OT sudden death and the served
3v3 table."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhl_sim.end_game import ot_level as OL
from nhl_sim.end_game import shootout as SO
from nhl_sim.engine.rules import ERA_2015
from nhl_sim.engine.sim import team_view_state
from nhl_sim.engine.state import END_OT, END_REG, END_SO, GameState


# --------------------------------------------------------------------------- shootout mechanics
def _run(first, second, A=20):
    """first / second: attempt outcomes (1 goal, 0 miss) in order for the team that shoots first / second; the
    remaining slots are misses. Returns (first_wins, n_attempts, goals_first, goals_second)."""
    u = np.ones((1, A))
    f = list(first) + [0] * A
    s = list(second) + [0] * A
    for j in range(A):
        v = f[j // 2] if j % 2 == 0 else s[j // 2]
        u[0, j] = 0.0 if v else 1.0                       # u < p (= 0.5) is a goal
    fw, n, gf, gs = SO.simulate_shootout(u, np.array([0.5]), np.array([0.5]))
    return bool(fw[0]), int(n[0]), int(gf[0]), int(gs[0])


def test_early_termination_when_decided():
    # first team scores its first two, second team misses two: after attempt 4 (2-0, second has 1 attempt left) over
    assert _run([1, 1, 1], [0, 0, 0]) == (True, 4, 2, 0)
    # second team leads 2-0 after attempt 4 and the first team has one attempt left: over
    assert _run([0, 0, 0], [1, 1, 1]) == (False, 4, 0, 2)
    # 2-1 after four attempts is not decided: the first team's third attempt can still level it
    assert _run([1, 1, 0], [1, 0, 0]) == (True, 6, 2, 1)
    # two-all after six attempts is level: sudden death follows
    assert _run([1, 1, 0, 1], [1, 0, 1, 0]) == (True, 8, 3, 2)


def test_regulation_rounds_are_three_and_alternate():
    # level at 1-1 after three rounds goes to sudden death: attempt 7 is the first shooter's again
    fw, n, gf, gs = _run([1, 0, 0, 1], [1, 0, 0, 0])
    assert n == 8 and fw and (gf, gs) == (2, 1)           # round 4: first scores, second misses -> over after attempt 8


def test_sudden_death_needs_a_complete_round():
    # level after 3 rounds; round 4: first misses, second scores -> second team wins after attempt 8 (not 7)
    fw, n, gf, gs = _run([1, 0, 0, 0], [1, 0, 0, 1])
    assert (fw, n) == (False, 8)
    # round 4 both score, round 5 first misses and second misses, round 6 first scores only
    fw, n, gf, gs = _run([0, 0, 0, 1, 0, 1], [0, 0, 0, 1, 0, 0])
    assert (fw, n) == (True, 12)


def test_goal_conservation_and_winner():
    rng = np.random.default_rng(1)
    u = rng.random((20000, 100))
    fw, n, gf, gs = SO.simulate_shootout(u, np.full(20000, 0.31), np.full(20000, 0.31))
    assert (gf != gs).all() and (fw == (gf > gs)).all()
    assert n.min() >= 4 and n.max() <= 100


def test_past_round_three_share_matches_the_closed_form():
    # past round 3 <=> level after six attempts (early termination can only end a shootout at <= 6 attempts and a
    # level shootout cannot end early): P = sum_k Binom(3, p)(k)^2
    p = 0.31
    pk = np.array([(1 - p) ** 3, 3 * p * (1 - p) ** 2, 3 * p ** 2 * (1 - p), p ** 3])
    rng = np.random.default_rng(2)
    n_sim = 200_000
    fw, n, gf, gs = SO.simulate_shootout(rng.random((n_sim, 100)), np.full(n_sim, p), np.full(n_sim, p))
    assert abs((n > 6).mean() - (pk ** 2).sum()) < 0.004
    assert abs(fw.mean() - 0.5) < 0.005                    # equal p: the first shooter has no edge
    assert abs(((gf + gs).sum() / n.sum()) - p) < 0.01     # per-attempt success is p up to the stopping rule


def test_home_first_share_and_winner_mapping():
    rng = np.random.default_rng(3)
    N = 100_000
    hw, n, gh, ga, hf = SO.shootout_home_win(rng.random(N), rng.random((N, 100)), np.full(N, 0.4), np.full(N, 0.2),
                                             np.full(N, 0.85))
    assert abs(hf.mean() - 0.85) < 0.004
    assert (hw == (gh > ga)).all()
    assert hw.mean() > 0.7                                 # the better-shooting home side wins mostly


def test_undecided_shootout_raises():
    with pytest.raises(RuntimeError):
        SO.simulate_shootout(np.zeros((1, 20)), np.array([1.0]), np.array([1.0]))      # everyone scores forever


# --------------------------------------------------------------------------- as-of levels
def _games(n_days=12, per_day=2, seasons=(20212022, 20222023)):
    rows = []
    gid = 0
    for si, s in enumerate(seasons):
        for d in range(n_days):
            for k in range(per_day):
                gid += 1
                rows.append(dict(game_id=gid, season=s, game_type=2,
                                 date=(pd.Timestamp("2021-10-01") + pd.Timedelta(days=d + 400 * si)).strftime("%Y-%m-%d"),
                                 drop=(pd.Timestamp("2021-10-01 23:00", tz="UTC") + pd.Timedelta(days=d + 400 * si, hours=k)).isoformat()))
    return pd.DataFrame(rows)


def test_shootout_level_is_asof_and_pregame():
    g = _games()
    rng = np.random.default_rng(0)
    m = np.full(len(g), 6.0)
    x = rng.binomial(6, 0.3, len(g)).astype(float)
    meta, v = SO.asof_m1(g, x, m, 500.0)
    assert (meta.created_at.dropna() < meta.puck_drop[meta.created_at.notna()]).all()
    # a game's value does not depend on its own or later results
    x2 = x.copy()
    k0 = len(g) // 2 + 10                       # inside season 2 (season 1's prior is its own final rate, labelled)
    x2[k0:] = 6.0
    _, v2 = SO.asof_m1(g, x2, m, 500.0)
    day = g.date.to_numpy()
    same_day = np.flatnonzero(day == day[k0])
    assert np.allclose(v[:same_day[-1] + 1], v2[:same_day[-1] + 1])        # up to and including the changed game's own day
    assert not np.allclose(v[same_day[-1] + 1:], v2[same_day[-1] + 1:])    # later days do see the change
    # the first game of the second season is the first season's final rate (prior only)
    assert abs(v[len(g) // 2] - x[: len(g) // 2].sum() / m[: len(g) // 2].sum()) < 1e-12


def test_ot_level_m1_matches_the_closed_form_and_ignores_the_future():
    g = _games()
    rows = pd.DataFrame({"game_id": g.game_id.repeat(1).to_numpy(), "season": g.season.to_numpy(),
                         "y": np.arange(len(g)) % 5 + 1.0, "exposure_s": 600.0})
    meta, lev = OL.asof_levels(rows, g, {"a": ("M1", 500.0), "o": ("O", None)})
    gm = g.sort_values(["date", "game_id"]).reset_index(drop=True)
    s1 = rows[rows.season == 20212022]
    r_prev = s1.y.sum() / (s1.exposure_s.sum() / 3600)
    # first game of season 2: prior only
    i = int(np.flatnonzero((gm.season == 20222023).to_numpy())[0])
    assert abs(lev["a"][i] - r_prev) < 1e-9
    # third game day of season 2: (n + K) / (h + K / r_prev) over the two earlier days
    d3 = np.flatnonzero((gm.date == sorted(gm[gm.season == 20222023].date.unique())[2]).to_numpy())[0]
    prior = rows[(rows.season == 20222023) & rows.game_id.isin(gm.game_id[:d3])]
    want = (prior.y.sum() + 500.0) / (prior.exposure_s.sum() / 3600 + 500.0 / r_prev)
    assert abs(lev["a"][d3] - want) < 1e-9
    assert (meta.created_at.dropna() < meta.puck_drop[meta.created_at.notna()]).all()


def test_select_level_rule():
    par = pd.DataFrame([dict(season=s, level=k, parity=v) for k, vals in
                        {"M1_K2000": (0.004, 0.002), "M1_K500": (0.003, 0.001), "M2_H30": (0.001, 0.001)}.items()
                        for s, v in zip((1, 2), vals)])
    assert OL.select_level(par, [1, 2])["selected"] == "M1_K2000"            # simplest passer
    par2 = par.assign(parity=par.parity * 10)
    sel = OL.select_level(par2, [1, 2])
    assert sel["selected"] == "M2_H30" and sel["how"].startswith("fallback")  # none passes; smallest max |parity|
    par3 = par2.assign(parity=[0.040, 0.020, 0.0395, 0.0205, 0.0402, 0.0203])
    assert OL.select_level(par3, [1, 2])["selected"] == "M1_K2000"            # ties within 0.1 pp go to the simpler


# --------------------------------------------------------------------------- OT rules in the engine (item 3)
def _gs(gt, n=4):
    return GameState(np.full(n, gt), ERA_2015)


def test_regular_season_ot_ends_at_the_first_goal():
    gs = _gs(2)
    gs.t = ERA_2015.reg_period_s * 3            # first second of overtime
    gs.settle()
    gs.goal(np.array([0, 2]), np.array([0, 1]))
    assert (~gs.alive[[0, 2]]).all() and gs.alive[[1, 3]].all()
    assert (gs.end_state[[0, 2]] == END_OT).all() and (gs.end_state[[1, 3]] == 0).all()
    assert gs.score[0].tolist() == [1, 0] and gs.score[2].tolist() == [0, 1]


def test_regulation_goal_does_not_end_the_game_and_ties_go_to_ot_then_shootout():
    gs = _gs(2, 3)
    gs.goal(np.array([0]), np.array([0]))                                  # a regulation goal
    assert gs.alive.all()
    gs.goal(np.array([1]), np.array([0]))
    gs.goal(np.array([1]), np.array([1]))                                  # game 1 tied 1-1, game 0 leads 1-0
    for _ in range(3600):
        gs.end_second()
    assert gs.end_state[0] == END_REG
    assert not gs.alive[0] and gs.alive[1] and gs.alive[2]                 # the tied games enter overtime
    for _ in range(ERA_2015.rs_ot_s):
        gs.end_second()
    assert (gs.end_state[[1, 2]] == END_SO).all() and not gs.alive.any()   # no OT goal: shootout (regular season)


def test_playoff_ot_is_sudden_death_without_a_shootout():
    gs = _gs(3, 2)
    gs.t = ERA_2015.reg_period_s * 3 + 5 * 1200 + 7        # fifth playoff overtime: still plays on
    assert gs.alive.all() and not gs.rs_ot().any() and (gs.period() == 9).all()
    gs.goal(np.array([1]), np.array([1]))
    assert gs.end_state.tolist() == [0, END_OT] and gs.alive.tolist() == [True, False]


def test_ot_penalties_are_served_by_the_regulation_states_with_ot_period():
    gs = _gs(2, 4)
    gs.t = 3600
    gs.settle()
    gs.penalty(np.array([0, 1]), np.array([1, 0]), 1)       # sim 0: away minor; sim 1: home minor
    sk = gs.skaters()
    assert sk[0].tolist() == [4, 3] and sk[1].tolist() == [3, 4] and sk[2].tolist() == [3, 3]
    st_h, st_a = team_view_state(sk)
    assert st_h[:3].tolist() == [1, 2, 4] and st_a[:3].tolist() == [2, 1, 4]       # PP / PK / 3v3 team views
    assert (gs.period() == 4).all()                                        # OT period type for the type tables
    # 4v4 after the held skater (post-expiry hold until a stoppage) is reachable and is team-view state 3
    sk44 = np.array([[4, 4]], np.int8)
    assert team_view_state(sk44)[0].tolist() == [3]


# --------------------------------------------------------------------------- served 3v3 table (real tables)
def _real():
    return Path(OL.ATT_TABLE[2]).exists() and Path("results/shot_attempt_r3/models/A3g.txt").exists() \
        and Path("results/strength_state_r3/fold2_rows.parquet").exists()


@pytest.mark.skipif(not _real(), reason="gitignored stage-3 tables not on disk")
def test_served_3v3_table_changes_only_3v3_and_matches_offline():
    games = np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"]).game_id.unique())
    att = np.load(OL.ATT_TABLE[2])
    new, info = OL.served_att_lam(att, games, 2)
    assert new.shape == att.shape and new.dtype == np.float32
    assert (new[:, :, :, :4, :] == att[:, :, :, :4, :]).all()               # 5v5 / PP / PK / 4v4 bit-identical
    assert not (new[:, :, :, 4, :] == att[:, :, :, 4, :]).all()
    par = OL.served_parity(new, games, 2)
    assert par["max_rel_diff"] < 1e-6, par


@pytest.mark.skipif(not _real(), reason="gitignored stage-3 tables not on disk")
def test_refit_cell_reproduces_the_frozen_a3gc_cell_with_the_old_level():
    import json
    tr, _te = OL.frames_3v3(2)
    old = pd.Series(tr.level.to_numpy(), index=tr.game_id.to_numpy())
    old = old[~old.index.duplicated()]
    cell, _ = OL.training_cell(2, old)
    want = json.loads(Path(OL.A3GC_CELL).read_text())["cell"][OL.ST_3V3]
    assert abs(cell - want) < 1e-9


@pytest.mark.skipif(not _real(), reason="gitignored stage-3 tables not on disk")
def test_defaults_att_table_flag_off_is_the_disk_table_and_flag_on_is_3v3_only():
    from nhl_sim.engine import defaults as DF
    games = np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"]).game_id.unique())
    off, info0 = DF.att_table(games)
    on, info1 = DF.att_table(games, ot3v3=True)
    assert info0 == {} and np.array_equal(off, np.load(OL.ATT_TABLE[2]))
    assert (on[:, :, :, :4, :] == off[:, :, :, :4, :]).all() and not (on[:, :, :, 4, :] == off[:, :, :, 4, :]).all()
    assert info1["parity"]["max_rel_diff"] < 1e-6 and info1["level_name"] == "M1_K500"
