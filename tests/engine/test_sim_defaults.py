"""INV-63 (Lane E3): the engine's default table set (nhl_sim.engine.defaults).

- Explicit-flag / flag-off paths stay bit-identical to HEAD 16f877f: fixture tests/fixtures/sim_defaults_flag_parity.json
  (scripts/diag_engine_l1xas_parity_fixture.py --commit 16f877f, cases l1xas_parity_cases).
- The default set carries L1x-as and C1s: the output has no `attr` stand-in label, lists block B0 and miss S0t, and has
  the attr_model / goal_model / oracle_goalie markers. The explicit L0s path keeps the `attr` label.
  (Real tables; skipped when the gitignored results are absent.)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import l1xas_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402

from nhl_sim.engine import defaults as DF  # noqa: E402
from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_defaults_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_paths_bit_identical_to_head(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    assert T2.digest(C.run(SIM, name, ERA_2015)) == FIX["cases"][name]


def test_default_stand_in_has_no_attr_label():
    assert set(DF.DEFAULT_STAND_IN) == {"block", "miss"}


def _real_run(builder):
    """One seed over the full fold-2 game list (the table builders need the whole list)."""
    if not C.real_available():
        pytest.skip("gitignored tables not on disk")
    import pandas as pd
    from nhl_sim.data.load import load_games
    LC2 = Path("results/strength_state_lc2/r5")
    ATT = Path("results/shot_attempt_r3/att_lam_A3g-c_fold2.npy")
    try:
        g = np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"]).game_id.unique())
        t = dict(lam=np.load(LC2 / "lam_H3_fold2.npy"), types=np.load(LC2 / "types_T2_fold2.npy"),
                 coinc_smp=np.array([True, False, True]), coinc_pim=np.array([4, 2, 10], np.int16),
                 goal_rate=np.full((3, 3), 2.5), stop_rate_ot=0.02, att_lam=np.load(ATT),
                 p_goal=np.array([0.055, 0.12, 0.05, 0.07, 0.09]))
        attr, _ = builder(g)
    except FileNotFoundError:
        pytest.skip("gitignored model tables not on disk")
    gt = load_games([20242025], columns=["game_id", "game_type"]).set_index("game_id").loc[g].game_type.to_numpy()
    return SIM.simulate(dict(t, attr=attr), g, gt, 1, ERA_2015, seed0=0, per_team_types=True,
                        seasons=np.full(len(g), 20242025))


def test_default_set_serves_l1xas_and_c1s():
    o = _real_run(DF.default_attr)
    marks = [str(x) for x in o["stand_in"]]
    assert not any(m.startswith("attr:") for m in marks)
    assert any(m.startswith("block:") for m in marks) and any(m.startswith("miss:") for m in marks)
    assert "L1x-as" in str(o["attr_model"][0])
    assert "C1s" in str(o["goal_model"][0])
    assert "ORACLE" in str(o["oracle_goalie"][0])


def test_explicit_l0s_path_keeps_attr_label():
    o = _real_run(DF.l0s_attr)
    assert any(str(m).startswith("attr:") for m in o["stand_in"])
    assert "attr_model" not in o
