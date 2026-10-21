"""SB-R5 (INV-64, Lane B5): the block B1a-as engine flag (attr["block_b1aas"]).

- Flag off: bit-identical to HEAD 0838766 (after Lane H8b engine_otso) on every l1xas_parity_cases case (fixture
  tests/fixtures/sim_b1aas_flag_parity.json, recorded by scripts/diag_engine_l1xas_parity_fixture.py --commit 0838766
  BEFORE the edit).
- Flag on: zero logits serve B0' (to rounding); a positive game logit raises the blocked share; the score bucket and
  the shooting team index the right cells; labels are validated; the output carries block_model.
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

FIX = json.loads(Path("tests/fixtures/sim_b1aas_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_bit_identical_to_head(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    assert T2.digest(C.run(SIM, name, ERA_2015)) == FIX["cases"][name]


def _run(gl=0.0, sc=None, label="block: B1a-as test", keep_block_label=False, n=30):
    t, g, gt, _, _ = C.syn_stack(False)
    if gl is not None:
        G = len(g)
        attr = t["attr"]
        attr["block_b1aas"] = dict(game_logit=np.full((G, 2, 5), float(gl)),
                                   sc_logit=np.zeros(7) if sc is None else np.asarray(sc, float), label=label)
        if not keep_block_label:
            attr["stand_in"] = {k: v for k, v in attr["stand_in"].items() if k != "block"}
    return SIM.simulate(t, g, gt, n, ERA_2015, seed0=1, per_team_types=False, seasons=C.C.mixed_seasons(len(g)))


def _blocked_share(o):
    att, fen = o["att_st"].sum(), o["attr_fen"].sum()
    return 1 - fen / att


def test_zero_logits_serve_b0prime():
    off, on = _run(None), _run(0.0)
    assert abs(_blocked_share(on) - _blocked_share(off)) < 1e-3
    assert str(on["block_model"][0]) == "block: B1a-as test" and "block_model" not in off
    assert not any(str(m).startswith("block:") for m in on["stand_in"])


def test_positive_logit_raises_blocks():
    assert _blocked_share(_run(1.0)) > _blocked_share(_run(0.0)) + 0.05


def test_block_prob_indexes_team_and_score():
    G = 3
    pbg = np.full((G, 5, 2), 0.25)
    gl = np.zeros((G, 2, 5))
    gl[1, 1, 2] = 0.7
    scl = np.zeros(7)
    scl[5] = -0.4
    AS = dict(p_block_game=pbg, b1aas_base=np.log(pbg) - np.log1p(-pbg), b1aas_game=gl, b1aas_sc=scl)
    v = SIM.block_prob(AS, np.array([1, 1, 0]), np.array([2, 2, 2]), 3600, 1, np.array([3, 5, 3]))
    lg = np.log(0.25 / 0.75)
    np.testing.assert_allclose(v, 1 / (1 + np.exp(-np.array([lg + 0.7, lg + 0.3, lg]))), rtol=0, atol=1e-15)
    with pytest.raises(ValueError):
        SIM.block_prob(AS, np.array([0]), np.array([0]), 0)


def test_validation():
    with pytest.raises(ValueError):
        _run(0.0, keep_block_label=True)
    with pytest.raises(ValueError):
        _run(0.0, label="")
    with pytest.raises(ValueError):
        _run(np.nan)
