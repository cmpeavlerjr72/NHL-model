"""SA-R3 (INV-32) T2 engine merge: the per-team penalty-type table of the SS-R5 sibling `sim_ss_r5.py` lives in
`engine/sim.py` behind the default-off flag `per_team_types`.

Parity (bit-identical, sha256 of every output array):
  - flag OFF = the pre-merge engine/sim.py on fixed seed sets (fixture tests/fixtures/sim_t2_merge_parity.json,
    recorded by scripts/diag_engine_t2_parity_fixture.py from the pre-merge file), stub-goal and attempt variants;
  - flag ON = `sim_ss_r5.simulate` on the same seeds and per-team tables.
The real-table cases use results/strength_state_r5 (gitignored) and are skipped when it is absent.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t2_parity_cases as C  # noqa: E402

from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine import sim_ss_r5 as R5  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_t2_merge_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.OFF_CASES))
def test_flag_off_is_bit_identical_to_pre_merge_engine(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("results/strength_state_r5 not on disk")
    assert name in FIX["cases"], "fixture missing a case"
    t, g, gt, n, s0 = C.OFF_CASES[name]()
    out = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0)
    assert out["unfinished"] == 0
    assert C.digest(out) == FIX["cases"][name]
    out2 = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=False)
    assert C.digest(out2) == FIX["cases"][name]


@pytest.mark.parametrize("case", ["syn", "real"])
def test_flag_on_is_bit_identical_to_sim_ss_r5(case):
    if case == "real" and not C.real_available():
        pytest.skip("results/strength_state_r5 not on disk")
    t, g, gt, n, s0 = C.synthetic(True, False) if case == "syn" else C.real(True)
    a = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=True)
    b = R5.simulate(t, g, gt, n, ERA_2015, seed0=s0)
    assert a["unfinished"] == 0 and set(a) == set(b)
    assert C.digest(a) == C.digest(b)
    assert int(a["n_type"].sum()) > 0


def test_per_team_table_equal_to_shared_reproduces_flag_off_with_attempts():
    t, g, gt, n, s0 = C.synthetic(False, True)
    off = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0)
    t2 = dict(t, types=np.broadcast_to(t["types"], (len(g), 2) + t["types"].shape).copy())
    on = SIM.simulate(t2, g, gt, n, ERA_2015, seed0=s0, per_team_types=True)
    assert C.digest(on) == C.digest(off)


def test_shape_guards():
    t, g, gt, n, s0 = C.synthetic(True, False)
    with pytest.raises(ValueError):
        SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0)
    t, g, gt, n, s0 = C.synthetic(False, False)
    with pytest.raises(ValueError):
        SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=True)
