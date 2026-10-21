"""SL-R7 L1x-as in engine/sim.py (attr["l1x"], default off; Lane A7, 2026-10-21).

- Flag off: every output array is bit-identical (sha256) to the pre-change engine (80f0b2e) on the INV-60 cases and the
  full INV-60 stack switched on; fixture tests/fixtures/sim_l1xas_flag_parity.json
  (scripts/diag_engine_l1xas_parity_fixture.py, reads the engine source from git).
- Wiring: zero L1x logits reproduce the levelled L0s path's class draws; non-zero logits move them; the served class
  row equals softmax(log state_pdf + log game_mult + game_logit + sc_logit) with sc_logit's OT row used at t >= 3600.
- Served vs offline (real tables; skipped when the gitignored results are absent): within 1e-6 of the SL-R7 fold-2
  L1x-as prediction file. Refusals: l1x without state_pdf / game_mult, l1x with the L0s labelled as a stand-in.
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

FIX = json.loads(Path("tests/fixtures/sim_l1xas_flag_parity.json").read_text())


@pytest.mark.parametrize("name", list(C.CASES))
def test_flag_off_bit_identical_to_pre_change_engine(name):
    if name.startswith("real") and not C.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    out = C.run(SIM, name, ERA_2015)
    assert out["unfinished"] == 0 and "attr_model" not in out
    assert T2.digest(out) == FIX["cases"][name]


def _with_l1x(scale=0.0, seed=3):
    t, g, gt, n, s0 = C.syn_stack(True)
    G = len(g)
    rng = np.random.default_rng(seed)
    attr = dict(t["attr"])
    attr["stand_in"] = {k: v for k, v in attr["stand_in"].items() if k != "attr"}
    attr["l1x"] = dict(game_logit=scale * rng.normal(size=(G, 2, 3, 78)), sc_logit=scale * rng.normal(size=(2, 7, 78)),
                       label="stage 4: test L1x-as")
    return t, attr, g, gt, n, s0


def _run(t, attr, g, gt, n, s0):
    return SIM.simulate(dict(t, attr=attr), g, gt, n, ERA_2015, seed0=s0, per_team_types=True,
                        seasons=C.C.mixed_seasons(len(g)))


def test_zero_logits_reproduce_levelled_l0s_draws():
    t, attr, g, gt, n, s0 = _with_l1x(0.0)
    base = dict(attr)
    base.pop("l1x")
    base["stand_in"] = dict(base["stand_in"], attr="STAND-IN test attr")
    o0 = _run(t, base, g, gt, n, s0)
    o1 = _run(t, attr, g, gt, n, s0)
    for k in ("attr_fen", "attr_cell", "attr_type", "attr_goals", "score"):
        np.testing.assert_array_equal(o0[k], o1[k])
    assert str(o1["attr_model"][0]) == "stage 4: test L1x-as" and not any(m.startswith("attr:") for m in o1["stand_in"])


def test_nonzero_logits_move_draws_and_rows_are_the_softmax():
    t, attr, g, gt, n, s0 = _with_l1x(0.5)
    o1 = _run(t, attr, g, gt, n, s0)
    base = dict(attr, l1x=dict(attr["l1x"], game_logit=np.zeros_like(attr["l1x"]["game_logit"]),
                               sc_logit=np.zeros_like(attr["l1x"]["sc_logit"])))
    o0 = _run(t, base, g, gt, n, s0)
    assert not np.array_equal(o0["attr_cell"], o1["attr_cell"])
    lx = attr["l1x"]
    AS = dict(state_pdf=attr["state_pdf"], game_mult=attr["game_mult"], l1x_game=lx["game_logit"], l1x_sc=lx["sc_logit"],
              l1x_base=np.log(attr["state_pdf"]), l1x_lgm=np.log(attr["game_mult"]))
    gi, st, sc = np.array([0, 1, 2]), np.array([0, 1, 4]), np.array([3, 0, 6])
    for t_, pt in ((100, 0), (3700, 1)):
        row = SIM.class_cdf(AS, None, gi, 1, st, sc, None, t_)
        z = (np.log(attr["state_pdf"][st, pt]) + np.log(attr["game_mult"][gi, SIM.ST_RGRP[st]])
             + lx["game_logit"][gi, 1, SIM.ST_RGRP[st]] + lx["sc_logit"][pt, sc])
        p = np.exp(z - z.max(1, keepdims=True))
        np.testing.assert_allclose(np.diff(row, axis=1, prepend=0.0), p / p.sum(1, keepdims=True), rtol=0, atol=1e-14)


@pytest.mark.parametrize("bad", ["no_game_mult", "labelled_stand_in", "bad_shape"])
def test_refusals(bad):
    t, attr, g, gt, n, s0 = _with_l1x(0.1)
    if bad == "no_game_mult":
        attr.pop("game_mult")
        attr["era_mult"] = np.ones((3, 3, 78))
    elif bad == "labelled_stand_in":
        attr["stand_in"] = dict(attr["stand_in"], attr="STAND-IN test attr")
    else:
        attr["l1x"] = dict(attr["l1x"], sc_logit=np.zeros((7, 78)))
    with pytest.raises(ValueError):
        _run(t, attr, g, gt, n, s0)


def _real():
    return all(Path(p).exists() for p in ("results/shot_attribute_r7/fold2_rows.parquet", "results/shot_attribute_r7/select.json",
                                          "results/shot_attribute_r6_d38/models/L1x.json"))


@pytest.mark.skipif(not _real(), reason="gitignored results not on disk")
def test_served_matches_offline_l1xas():
    import pandas as pd
    from nhl_sim.engine import c1s_tables as CT
    from nhl_sim.shot_attribute import serve_l1xas as SV
    games = np.sort(pd.read_parquet("results/shot_attribute_r7/fold2_rows.parquet", columns=["game_id"]).game_id.unique())
    sp, gm, _ = CT.l0s_m1k500_tables(games)
    lx, info = SV.l1xas_tables(games)
    p = SV.l1xas_parity(games, sp, gm, lx)
    assert info["cell"] == "H45_P10000" and p["n_rows"] > 100_000 and p["max_abs_diff"] < 1e-6
