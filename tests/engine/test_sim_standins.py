"""D32 stand-ins in engine/sim.py: block B0 (attr["p_block_game"]) and stage-4 L0s (attr["state_pdf"]), both default off.

- Flag off: every output array is bit-identical (sha256) to the pre-change engine (3ce7112) on the SL-R3 era cases plus
  the SL-R3 levelled pdf path, fixture tests/fixtures/sim_standin_flag_parity.json
  (scripts/diag_engine_standin_parity_fixture.py).
- Flag on, wiring: a B0 table constant over games / period type reproduces the empirical-stub draws, and an L0s table
  whose 4v4 / 3v3 rows equal 5v5 reproduces the levelled pdf path, bit for bit (apart from the stand_in marker).
- Flag on, real tables: the engine-served block probability and class probabilities (sim.block_prob / sim.class_cdf)
  match the offline fold-2 B0 / L0s predictions within 1e-6 (skipped when the gitignored results are absent).
- Schema: whenever a stand-in is on, the output carries a `stand_in` marker naming it; a stand-in table without its
  label is refused; flag-off output has no marker.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import standin_parity_cases as C  # noqa: E402
import attr_parity_cases as A  # noqa: E402
import t2_parity_cases as T2  # noqa: E402

from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine import standins as SI  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_standin_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_bit_identical_to_pre_change_engine(name):
    if name.startswith("real") and not A.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    out = C.run(SIM, name, ERA_2015)
    assert out["unfinished"] == 0
    assert "stand_in" not in out
    assert T2.digest(out) == FIX["cases"][name]


def _base(per_team=True, seed=13):
    t, g, gt, n, s0 = C.syn_levelled(per_team, seed)
    return t, g, gt, n, s0, C.mixed_seasons(len(g))


def _drop_marker(d):
    return {k: v for k, v in d.items() if k != "stand_in"}


def test_b0_constant_table_reproduces_stub_draws():
    t, g, gt, n, s0, seasons = _base()
    pb = np.array([0.25, 0.2, 0.3])
    t["attr"]["p_block"] = pb[[0, 1, 2, 0, 0]]
    o_stub = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=True, seasons=seasons)
    attr = {k: v for k, v in t["attr"].items() if k != "p_block"}
    attr.update(p_block_game=np.broadcast_to(pb[None, :, None], (len(g), 3, 2)).copy(), stand_in={"block": SI.BLOCK_LABEL})
    o_b0 = SIM.simulate(dict(t, attr=attr), g, gt, n, ERA_2015, seed0=s0, per_team_types=True, seasons=seasons)
    assert T2.digest(_drop_marker(o_b0)) == T2.digest(o_stub)


def test_l0s_state_table_reproduces_levelled_pdf_path():
    t, g, gt, n, s0, seasons = _base()
    rng = np.random.default_rng(29)
    sp = rng.dirichlet(np.ones(78) * 0.5, size=(7, 2))
    sp[3] = sp[0]
    sp[4] = sp[0]
    # pdf path equivalent: pdf[g, team, interval (= period type), rating group, sc] = sp[group state, interval]
    pdf = np.broadcast_to(sp[[0, 1, 2]].transpose(1, 0, 2)[None, None, :, :, None, :], (len(g), 2, 2, 3, 7, 78)).copy()
    o_pdf = SIM.simulate(dict(t, attr=dict(t["attr"], pdf=pdf)), g, gt, n, ERA_2015, seed0=s0, per_team_types=True,
                         seasons=seasons)
    attr = {k: v for k, v in t["attr"].items() if k != "pdf"}
    attr.update(state_pdf=sp, stand_in={"attr": SI.ATTR_LABEL})
    o_l0s = SIM.simulate(dict(t, attr=attr), g, gt, n, ERA_2015, seed0=s0, per_team_types=True, seasons=seasons)
    assert o_l0s["attr_fen"].sum() > 0
    assert T2.digest(_drop_marker(o_l0s)) == T2.digest(o_pdf)


def _both_on(t, g):
    rng = np.random.default_rng(3)
    attr = {k: v for k, v in t["attr"].items() if k not in ("pdf", "p_block")}
    attr.update(state_pdf=rng.dirichlet(np.ones(78), size=(7, 2)), p_block_game=rng.uniform(0.1, 0.35, size=(len(g), 3, 2)),
                stand_in=dict(SI.STAND_IN))
    return attr


def test_stand_in_marker_in_output_schema():
    t, g, gt, n, s0, seasons = _base(False)
    out = SIM.simulate(dict(t, attr=_both_on(t, g)), g, gt, n, ERA_2015, seed0=s0, seasons=seasons)
    assert out["unfinished"] == 0
    marker = list(out["stand_in"])
    assert marker == [f"attr: {SI.ATTR_LABEL}", f"block: {SI.BLOCK_LABEL}"]
    assert all("STAND-IN" in m for m in marker)
    assert (out["attr_fen"] <= out["att_st"]).all() and out["attr_goals"].sum() == out["score"].sum()


@pytest.mark.parametrize("drop", ["block", "attr"])
def test_unlabelled_stand_in_is_refused(drop):
    t, g, gt, n, s0, seasons = _base(False)
    attr = _both_on(t, g)
    attr["stand_in"] = {k: v for k, v in attr["stand_in"].items() if k != drop}
    with pytest.raises(ValueError, match="STAND-IN"):
        SIM.simulate(dict(t, attr=attr), g, gt, n, ERA_2015, seed0=s0, seasons=seasons)


def test_l0s_needs_level():
    t, g, gt, n, s0, seasons = _base(False)
    attr = _both_on(t, g)
    attr.pop("era_mult")
    with pytest.raises(ValueError):
        SIM.simulate(dict(t, attr=attr), g, gt, n, ERA_2015, seed0=s0, seasons=seasons)


def _real_standins_available():
    return all(Path(p).exists() for p in ("results/block_sb_r1/models/B0.json", "results/block_sb_r1/fold2_rows.parquet",
                                          "results/shot_attribute_r4/models/L0s.json",
                                          "results/shot_attribute_r4/fold2_rows.parquet",
                                          "results/strength_state_r3/fold2_rows.parquet"))


@pytest.mark.skipif(not _real_standins_available(), reason="gitignored SB-R1 / SL-R4 results not on disk")
def test_served_matches_offline_b0_and_l0s():
    import pandas as pd
    games = np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"]).game_id.unique())
    pbg, _ = SI.block_b0_table(games)
    pb = SI.b0_parity(games, pbg)
    assert pb["n_rows"] > 100_000 and pb["max_abs_diff"] < 1e-6
    sp, em, _ = SI.l0s_tables()
    pl = SI.l0s_parity(sp, em)
    assert pl["n_rows"] > 100_000 and pl["max_abs_diff"] < 1e-6
    assert pl["n_st5"] > 0 and pl["n_st6"] > 0                     # EN rows served the baseline, also within 1e-6
