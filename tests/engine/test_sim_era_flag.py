"""SL-R3: recording-era flag in GameState (D24) and the levelled stage-4 lookup of engine/sim.py.

- Parity: with the levelled path unused (stage-4 option off, or the SL-R1 cdf path), and with or without seasons=,
  every output array is bit-identical (sha256) to the pre-change engine (27cffc0), fixture
  tests/fixtures/sim_era_flag_parity.json (scripts/diag_engine_era_parity_fixture.py).
- rules.recording_era: 1 before 2023-24, 2 from 2023-24 on; mix_level's era map agrees.
- Levelled path: a unit era_mult with pdf = increments of a float64 cdf reproduces the cdf path bit for bit; the
  engine reads the era from GameState (a multiplier on era 1 only leaves era-2 games untouched and moves era-1 games);
  a missing seasons= raises.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attr_parity_cases as A  # noqa: E402
import era_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402

from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine.rules import ERA_2015, recording_era  # noqa: E402
from nhl_sim.engine.state import GameState  # noqa: E402

FIX = json.loads(Path("tests/fixtures/sim_era_flag_parity.json").read_text())


@pytest.mark.parametrize("with_seasons", [False, True])
@pytest.mark.parametrize("name", list(C.CASES))
def test_unlevelled_paths_bit_identical_to_pre_change_engine(name, with_seasons):
    if name.startswith("real") and not A.real_available():
        pytest.skip("gitignored stage-1 / stage-3 tables not on disk")
    mk, per_team = C.CASES[name]
    t, g, gt, n, s0 = mk()
    kw = dict(seasons=np.where(np.arange(len(g)) % 2 == 0, 20222023, 20242025)) if with_seasons else {}
    out = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=per_team, **kw)
    assert out["unfinished"] == 0
    assert T2.digest(out) == FIX["cases"][name]


def test_recording_era_boundary_fixed():
    assert recording_era(20212022) == 1 and recording_era(20222023) == 1
    assert recording_era(20232024) == 2 and recording_era(20242025) == 2 and recording_era(20262027) == 2
    assert recording_era(np.array([20222023, 20232024])).tolist() == [1, 2]
    with pytest.raises(ValueError):
        recording_era(20142015)
    from nhl_sim.shot_attribute.mix_level import ERA_OF_SEASON
    assert all(recording_era(s) == e for s, e in ERA_OF_SEASON.items())


def test_gamestate_rec_era():
    gs = GameState(np.array([2, 2, 3]), ERA_2015, season=np.array([20212022, 20232024, 20242025]))
    assert gs.rec_era.tolist() == [1, 2, 2]
    assert GameState(np.array([2]), ERA_2015).rec_era is None


def _levelled(seed=3):
    t, g, gt, n, s0 = T2.synthetic(True, True)
    rng = np.random.default_rng(seed)
    p = rng.dirichlet(np.ones(78) * 0.5, size=(len(g), 2, 2, 3, 7)).astype(np.float32)
    cdf = np.cumsum(p.astype(np.float64), -1)
    cdf /= cdf[..., -1:]
    base = dict(interval_of_minute=(np.arange(100) >= 60).astype(np.int64), p_block=np.array([0.25, 0.2, 0.3, 0.25, 0.25]),
                xg=rng.uniform(0.01, 0.2, size=(78, 3)), n_type=6)
    return t, g, gt, n, s0, p, cdf, base


def test_unit_level_reproduces_cdf_path():
    t, g, gt, n, s0, p, cdf, base = _levelled()
    seasons = np.full(len(g), 20242025)
    t1 = dict(t, attr=dict(base, cdf=cdf))
    t2 = dict(t, attr=dict(base, pdf=p, era_mult=np.ones((3, 3, 78))))
    o1 = SIM.simulate(t1, g, gt, n, ERA_2015, seed0=s0, per_team_types=True)
    o2 = SIM.simulate(t2, g, gt, n, ERA_2015, seed0=s0, per_team_types=True, seasons=seasons)
    assert T2.digest(o1) == T2.digest(o2)


def test_engine_reads_era_from_gamestate():
    t, g, gt, n, s0, p, cdf, base = _levelled()
    seasons = np.where(np.arange(len(g)) < 3, 20222023, 20242025)       # games 0-2 era 1, 3-5 era 2
    em = np.ones((3, 3, 78))
    em[1, :, :6] = 50.0                                                  # era 1: strongly favour cell 0
    o_unit = SIM.simulate(dict(t, attr=dict(base, pdf=p, era_mult=np.ones((3, 3, 78)))), g, gt, n, ERA_2015, seed0=s0,
                          per_team_types=True, seasons=seasons)
    o_lev = SIM.simulate(dict(t, attr=dict(base, pdf=p, era_mult=em)), g, gt, n, ERA_2015, seed0=s0,
                         per_team_types=True, seasons=seasons)
    e1 = o_lev["game_idx"] < 3
    # era-2 games: identical class draws while their score paths are identical; era-1 games: cell 0 much more often
    share = lambda o, m: o["attr_cell"][m][..., 0].sum() / o["attr_fen"][m].sum()  # noqa: E731
    assert share(o_lev, e1) > 3 * share(o_unit, e1)
    assert abs(share(o_lev, ~e1) - share(o_unit, ~e1)) < 0.01
    # the same tables with every game in era 2 equal the unit run exactly
    o_e2 = SIM.simulate(dict(t, attr=dict(base, pdf=p, era_mult=em)), g, gt, n, ERA_2015, seed0=s0,
                        per_team_types=True, seasons=np.full(len(g), 20242025))
    assert T2.digest(o_e2) == T2.digest(o_unit)


def test_levelled_path_needs_seasons():
    t, g, gt, n, s0, p, cdf, base = _levelled()
    with pytest.raises(ValueError):
        SIM.simulate(dict(t, attr=dict(base, pdf=p, era_mult=np.ones((3, 3, 78)))), g, gt, n, ERA_2015, seed0=s0,
                     per_team_types=True)
