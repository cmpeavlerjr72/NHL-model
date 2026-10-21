"""EG-R1 part C (INV-67, Lane H8b): the shootout S1 engine flag (tables["shootout"]).

- Flag off: bit-identical to HEAD 6ac4389 (Lane H8a engine_pull) on every l1xas_parity_cases case (fixture
  tests/fixtures/sim_otso_flag_parity.json, recorded by scripts/diag_engine_l1xas_parity_fixture.py --commit 6ac4389
  BEFORE the edit).
- Flag on: everything before the shootout is unchanged (score, end state, played seconds), the winners come from the
  attempt-level mechanics (goals consistent with the winner, never level), non-shootout sims carry zeros, the draws are
  independent of the batch layout (paired streams), and the served table is validated.
- The default-off 3v3 table builder leaves the table untouched.
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

FIX = json.loads(Path("tests/fixtures/sim_otso_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_bit_identical_to_head(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    assert T2.digest(C.run(SIM, name, ERA_2015)) == FIX["cases"][name]


def _tables(G, p=0.31, hf=0.85):
    return dict(p_home=np.full(G, p), p_away=np.full(G, p), home_first=np.full(G, hf), label="shootout S1: test")


def _run(shoot=None, n=40, seed0=3):
    t, g, gt, _, _ = C.syn_stack(False)
    if shoot is not None:
        t["shootout"] = shoot(len(g))
    return SIM.simulate(t, g, gt, n, ERA_2015, seed0=seed0, per_team_types=False, seasons=C.C.mixed_seasons(len(g)))


def test_flag_on_changes_only_the_shootout():
    off, on = _run(), _run(_tables)
    for k in ("score", "end_state", "played_s", "game_idx", "seed"):
        assert np.array_equal(off[k], on[k]), k
    so = on["end_state"] == 3
    reg_rs = (on["end_state"] != 3)
    assert so.sum() >= 20, "synthetic run has too few shootouts to test"
    gh, ga = on["so_goals_home"], on["so_goals_away"]
    assert (gh[so] != ga[so]).all()                                    # a shootout always has a winner
    assert (on["so_home_win"][so] == (gh[so] > ga[so])).all()
    assert (on["so_home_win"][~so] == False).all()                     # noqa: E712
    assert (on["so_n_att"][reg_rs] == 0).all() and (gh[reg_rs] == 0).all()
    assert on["so_n_att"][so].min() >= 4 and on["so_n_att"][so].max() < 100
    assert str(on["shootout_model"][0]) == "shootout S1: test"
    assert "so_n_att" not in off and "shootout_model" not in off


def test_shootout_is_independent_of_batch_layout():
    full = _run(_tables, n=40, seed0=3)
    a = _run(_tables, n=20, seed0=3)
    b = _run(_tables, n=20, seed0=23)
    G = len(np.unique(full["game_idx"]))
    f = {k: full[k].reshape(G, 40) for k in ("so_home_win", "so_n_att", "so_goals_home", "so_goals_away")}
    x = {k: a[k].reshape(G, 20) for k in f}
    y = {k: b[k].reshape(G, 20) for k in f}
    for k in f:
        assert np.array_equal(f[k][:, :20], x[k]) and np.array_equal(f[k][:, 20:], y[k]), k


def test_engine_shootouts_use_the_mechanics():
    # smoke check only (the closed form is tested at 200,000 draws in tests/test_end_game_otso.py): about 6% of the
    # synthetic sims reach a shootout; the share past round 3 is near 0.3456 at p = 0.31, within sampling error
    o = _run(lambda G: _tables(G, 0.31), n=100)
    so = o["end_state"] == 3
    assert so.sum() > 30
    assert abs((o["so_n_att"][so] > 6).mean() - 0.3456) < 0.2
    assert 0.2 < (o["so_goals_home"][so] + o["so_goals_away"][so]).sum() / o["so_n_att"][so].sum() < 0.45


def test_bad_shootout_table_is_refused():
    with pytest.raises(ValueError):
        _run(lambda G: dict(_tables(G), p_home=np.full(G, 1.2)))
    with pytest.raises(ValueError):
        _run(lambda G: {k: v for k, v in _tables(G).items() if k != "label"})


def test_late_goal_recording_with_the_pull_flag():
    """EG-R1 recording (Lane H8b): with tables['pull'] the output carries late_goals (N, 2, 4): goals in the last 120 s
    of regulation by the scorer's lead / tied / trail 1 / trail 2+ before the goal. Consistency with the score, and the
    arrays are absent without the flag."""
    import test_sim_pull as TP
    o = TP._syn_run("P1", h=0.03)
    lg = o["late_goals"]
    assert lg.shape == (len(o["score"]), 2, 4) and lg.min() >= 0
    assert (lg.sum(2) <= o["score"]).all() and lg.sum() > 0
    assert lg[:, :, 2:].sum() > 0                                       # trailing teams score late (EN-for / pulled)
    assert "late_goals" not in _run()
