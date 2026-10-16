"""SA-R1 parity (L4): the engine attempt lookup reproduces the offline fold-2 predicted rate within 0.5% for a
sample of >= 200 fold-2 games, for every fitted arm. Skipped when the gitignored results/shot_attempt_r1 artifacts
are absent. Reachable states only (st <= 4); rows past minute 99 (deep playoff OT) are excluded (the lookup clamps)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RES = Path("results/shot_attempt_r1")
N_GAMES = 220
pytestmark = pytest.mark.skipif(not (RES / "fold2_rows.parquet").exists(), reason="SA-R1 artifacts not on disk")


@pytest.mark.parametrize("arm", ["A0", "A1", "A2", "A5", "A3"])
def test_lookup_reproduces_offline_rate(arm):
    import lightgbm as lgb

    from nhl_sim.shot_attempt.lookup import attempt_table
    labels = json.loads((RES / "labels_sealed.json").read_text())
    fz = json.loads(Path("docs/models/shot_attempt/sa_r1_frozen_params.json").read_text())
    rows = pd.read_parquet(RES / "fold2_rows.parquet")
    mu = np.load(RES / f"fold2_haz_{labels[arm]}.npy")
    model = (lgb.Booster(model_file=str(RES / "models" / "A3.txt")) if arm == "A3"
             else json.loads((RES / "models" / f"{arm}.json").read_text()))
    rng = np.random.default_rng(0)
    games = np.sort(rng.choice(np.sort(rows.game_id.unique()), N_GAMES, replace=False))
    gdf = pd.DataFrame({"game_id": games, "season": 20242025})
    lam = attempt_table(arm, model, gdf, fz, fold=2)
    sel = rows.game_id.isin(games).to_numpy() & (rows.st.to_numpy() <= 4) & (rows.t0.to_numpy() < 6000)
    r = rows[sel]
    gi = np.searchsorted(games, r.game_id.to_numpy())
    look = lam[gi, r.team.to_numpy(), r.t0.to_numpy() // 60, r.st.to_numpy(), r.sc.to_numpy()]
    look_mu = look.astype(np.float64) * r.exposure_s.to_numpy() / 3600.0
    g = pd.DataFrame({"gid": r.game_id.to_numpy(), "off": mu[sel], "look": look_mu}).groupby("gid").sum()
    sample_err = abs(g.look.sum() / g.off.sum() - 1)
    per_game = (g.look / g.off - 1).abs()
    print(f"{arm}: rows {len(r)}, sample rel err {sample_err:.2e}, per-game max {per_game.max():.2e}")
    assert sample_err < 0.005
    assert per_game.max() < 0.005
    np.testing.assert_allclose(look_mu, mu[sel], rtol=2e-3, atol=1e-9)
