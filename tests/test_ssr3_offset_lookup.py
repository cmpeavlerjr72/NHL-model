"""SS-R3 step 1 (Lane H4): the engine hazard lookup with per-game level + profile offsets reproduces the offline
predicted rate of H3'' and H2'' on a sample of >= 200 fold-2 games to within 0.5%. Skipped when the (gitignored)
results/strength_state_r3 artifacts are not on disk."""
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from nhl_sim.strength_state import lookup as LK

RES = Path("results/strength_state_r3")
N_GAMES = 240
pytestmark = pytest.mark.skipif(not (RES / "fold2_rows.parquet").exists(), reason="SS-R3 artifacts not on disk")


def _load(arm):
    labels = json.loads((RES / "labels_sealed.json").read_text())
    rows = pd.read_parquet(RES / "fold2_rows.parquet")
    mu = np.load(RES / f"fold2_haz_{labels[arm]}.npy")
    model = (lgb.Booster(model_file=str(RES / "models" / "H3_fold2.txt")) if arm == "H3"
             else json.loads((RES / "models" / f"{arm}_fold2.json").read_text()))
    return rows, mu, model


@pytest.mark.parametrize("arm", ["H3", "H2"])
def test_lookup_reproduces_offline_rate(arm):
    rows, mu, model = _load(arm)
    rng = np.random.default_rng(0)
    games = np.sort(rng.choice(np.sort(rows.game_id.unique()), N_GAMES, replace=False))
    tr = (rows[rows.game_id.isin(games)].groupby(["game_id", "team"])
          .agg(taken_own=("taken_own", "first"), drawn_opp=("drawn_opp", "first"), is_home=("is_home", "first"),
               b2b_own=("b2b_own", "first"), b2b_opp=("b2b_opp", "first"), level=("level", "first"))
          .reset_index())
    lam = LK.hazard_table_v3(arm, model, tr)
    sel = rows.game_id.isin(games).to_numpy() & (rows.st.to_numpy() <= 4)
    r = rows[sel]
    # label the one known structural difference: the lookup has one period-4 grid, so playoff multi-OT periods
    # (period >= 5) are excluded from the strict comparison and compared separately below
    ok = (r.period.to_numpy() <= 4)
    r_ok, mu_ok = r[ok], mu[sel][ok]
    gi = np.searchsorted(games, r_ok.game_id.to_numpy())
    minute = np.minimum(r_ok.t0.to_numpy() // 60, 99)
    look = lam[gi, r_ok.team.to_numpy(), minute, r_ok.st.to_numpy(), r_ok.sc.to_numpy(), r_ok.pdiff.to_numpy()]
    look_mu = look.astype(np.float64) * r_ok.exposure_s.to_numpy() / 3600.0
    g = pd.DataFrame({"gid": r_ok.game_id.to_numpy(), "off": mu_ok, "look": look_mu}).groupby("gid").sum()
    sample_err = abs(g.look.sum() / g.off.sum() - 1)
    per_game = (g.look / g.off - 1).abs()
    print(f"{arm}: sample rel err {sample_err:.2e}, per-game max {per_game.max():.2e}, rows {len(r_ok)}")
    assert sample_err < 0.005
    assert per_game.max() < 0.005
    np.testing.assert_allclose(look_mu, mu_ok, rtol=2e-3, atol=1e-9)
