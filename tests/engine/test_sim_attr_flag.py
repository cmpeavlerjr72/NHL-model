"""SL-R1: the stage-4 shot-attribute variant of `engine/sim.py` (tables["attr"], default off).

- Flag off: every output array is bit-identical (sha256) to the pre-change engine (b024504) on fixed seed sets,
  fixture tests/fixtures/sim_attr_flag_parity.json (recorded by scripts/diag_engine_attr_parity_fixture.py), incl.
  the stage-1 incumbent path (per_team_types) and a real-table case (skipped when the gitignored results are absent).
- Flag on (synthetic): the bookkeeping is consistent (unblocked <= attempts, cell / type counts sum to unblocked) and
  a degenerate table (block prob 0, one class with xG 1) turns every attempt into a goal-class draw.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attr_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402

from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_attr_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_is_bit_identical_to_pre_change_engine(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    mk, per_team = C.CASES[name]
    t, g, gt, n, s0 = mk()
    assert "attr" not in t
    out = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=per_team)
    assert out["unfinished"] == 0
    assert T2.digest(out) == FIX["cases"][name]


def _attr(G, rng, nc=78, ni=2):
    p = rng.dirichlet(np.ones(nc) * 0.5, size=(G, 2, ni, 3, 7))
    return dict(cdf=np.cumsum(p, -1).astype(np.float32), interval_of_minute=(np.arange(100) >= 60).astype(np.int64),
                p_block=np.array([0.25, 0.2, 0.3, 0.25, 0.25]), xg=rng.uniform(0.01, 0.2, size=(nc, 3)), n_type=6)


def test_flag_on_bookkeeping():
    t, g, gt, n, s0 = T2.synthetic(True, True)
    t["attr"] = _attr(len(g), np.random.default_rng(11))
    out = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=True)
    assert out["unfinished"] == 0
    fen, att = out["attr_fen"], out["att_st"]
    assert (fen <= att).all() and fen.sum() > 0
    assert (out["attr_cell"].sum(-1) == fen).all() and (out["attr_type"].sum(-1) == fen).all()
    assert out["attr_goals"].sum() == out["score"].sum()
    blocked = 1 - fen.sum() / att.sum()
    assert 0.18 < blocked < 0.32


def test_flag_on_degenerate_table():
    t, g, gt, n, s0 = T2.synthetic(False, True)
    G = len(g)
    cdf = np.zeros((G, 2, 2, 3, 7, 78), np.float32)
    cdf[..., 5:] = 1.0                                   # every draw is class 5
    xg = np.zeros((78, 3))
    xg[5] = 1.0
    t["attr"] = dict(cdf=cdf, interval_of_minute=np.zeros(100, np.int64), p_block=np.zeros(5), xg=xg, n_type=6)
    out = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0)
    assert (out["attr_fen"] == out["att_st"]).all()
    assert (out["attr_cell"][..., 0] == out["attr_fen"]).all()
    assert (out["attr_type"][..., 5] == out["attr_fen"]).all()
    assert (out["attr_goals"] == out["attr_fen"]).all()


def test_attr_needs_attempt_table():
    t, g, gt, n, s0 = T2.synthetic(False, False)
    t["attr"] = _attr(len(g), np.random.default_rng(1))
    with pytest.raises(ValueError):
        SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0)
