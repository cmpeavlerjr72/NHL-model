"""SL-R1: the engine lookup of a stage-4 arm serves the trained distribution (L4). For a sample of real fold-2
unblocked attempts in reachable states, the lookup's class distribution at (game, team, clock interval, rating group,
score bucket) equals the offline prediction of the same fitted arm on that attempt's own feature row. Uses the
gitignored fitted models and cached tables in results/shot_attribute_r1; skipped when absent."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhl_sim.shot_attribute import models as M
from nhl_sim.shot_attribute.lookup import attr_table, clock_intervals
from nhl_sim.shot_attribute.tables import cell_of, N_CLASS

RES = Path("results/shot_attribute_r1")
FZ = Path("docs/models/shot_attribute/sl_r1_frozen_params.json")
ARMS = [a for a in ("L1", "L2", "L3") if (RES / "models" / (f"{a}.txt" if a == "L3" else f"{a}.json")).exists()]


def _model(arm):
    if arm == "L3":
        import lightgbm as lgb
        return lgb.Booster(model_file=str(RES / "models" / "L3.txt"))
    return json.loads((RES / "models" / f"{arm}.json").read_text())


def test_cell_edges():
    # 10 ft straight on is band 10-20; 30 deg exactly is narrow; behind the line is cell 12
    assert cell_of(np.array([79.0]), np.array([0.0]))[0] == 2
    assert cell_of(np.array([89.0 - 15 * np.cos(np.pi / 6)]), np.array([7.5 - 1e-9]))[0] == 2
    assert cell_of(np.array([90.0]), np.array([3.0]))[0] == 12
    assert cell_of(np.array([0.0]), np.array([0.0]))[0] == 10


@pytest.mark.skipif(not ARMS or not FZ.exists(), reason="fitted SL-R1 models not on disk")
@pytest.mark.parametrize("arm", ARMS)
def test_lookup_matches_offline(arm):
    fz = json.loads(FZ.read_text())
    rows = pd.read_parquet(RES / "fold2_rows.parquet")
    rows = rows[rows.grp <= 2]
    games = np.sort(rows.game_id.unique())[:6]
    m = _model(arm)
    cdf, imap = attr_table(arm, m, pd.DataFrame({"game_id": games, "season": 20242025}), 2, fz["w"],
                           fz["prior_strength_attempts"])
    raw = M.load_rows([20242025])
    raw = raw[raw.game_id.isin(games) & ~raw.blocked & (raw.grp <= 2) & (raw.t < 6000)]
    r = M.attach_features(raw, 2, fz["w"], fz["prior_strength_attempts"])
    P = M.predict_arm(arm, m, r)
    gi = np.searchsorted(games, r.game_id.to_numpy())
    minute = np.minimum(r.t.to_numpy() // 60, 99)
    c = cdf[gi, r.team.to_numpy(), imap[minute], r.grp.to_numpy(), r.sc.to_numpy()]
    p = np.diff(np.concatenate([np.zeros((len(c), 1)), c.astype(np.float64)], 1), axis=1)
    assert p.shape == (len(r), N_CLASS)
    assert np.abs(p - P).max() < 2e-5
