"""SA-R3 parity (L4): the engine attempt lookup reproduces the offline fold-2 predicted rate of every SA-R3 arm
(A3g, A3g-c, A2g-c, A3g-s with the "lc1s" thin-state levels) within 0.5% on a sample of >= 200 fold-2 games.
Skipped when the gitignored results/shot_attempt_r3 artifacts are absent. Reachable states only (st <= 4); rows past
minute 99 are excluded (the lookup clamps)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RES = Path("results/shot_attempt_r3")
N_GAMES = 220
pytestmark = pytest.mark.skipif(not (RES / "fold2_rows.parquet").exists(), reason="SA-R3 artifacts not on disk")


def _load(arm):
    import lightgbm as lgb
    if arm.endswith("-c"):
        m = json.loads((RES / "models" / f"{arm}.json").read_text())
        return {"base": _load(m["base_model"].rsplit(".", 1)[0]), "cell": m["cell"]}
    if arm.startswith("A3"):
        return lgb.Booster(model_file=str(RES / "models" / f"{arm}.txt"))
    return json.loads((RES / "models" / f"{arm}.json").read_text())


@pytest.mark.parametrize("arm", ["A3g", "A3g-c", "A2g-c", "A3g-s"])
def test_lookup_reproduces_offline_rate_r3(arm):
    from nhl_sim.shot_attempt.lookup import attempt_table
    labels = json.loads((RES / "labels_sealed.json").read_text())
    fz = json.loads(Path("docs/models/shot_attempt/sa_r3_frozen_params.json").read_text())
    rows = pd.read_parquet(RES / "fold2_rows.parquet")
    mu = np.load(RES / f"fold2_haz_{labels[arm]}.npy")
    rng = np.random.default_rng(0)
    games = np.sort(rng.choice(np.sort(rows.game_id.unique()), N_GAMES, replace=False))
    gdf = pd.DataFrame({"game_id": games, "season": 20242025})
    lam = attempt_table(arm, _load(arm), gdf, fz, fold=2, tv="v2", level="lc1s" if arm == "A3g-s" else "lc1g")
    sel = rows.game_id.isin(games).to_numpy() & (rows.st.to_numpy() <= 4) & (rows.t0.to_numpy() < 6000)
    r = rows[sel]
    gi = np.searchsorted(games, r.game_id.to_numpy())
    look = lam[gi, r.team.to_numpy(), r.t0.to_numpy() // 60, r.st.to_numpy(), r.sc.to_numpy()]
    look_mu = look.astype(np.float64) * r.exposure_s.to_numpy() / 3600.0
    g = pd.DataFrame({"gid": r.game_id.to_numpy(), "off": mu[sel], "look": look_mu}).groupby("gid").sum()
    assert abs(g.look.sum() / g.off.sum() - 1) < 0.005
    assert (g.look / g.off - 1).abs().max() < 0.005
    for s_ in (3, 4):                                   # the thin cells this round is about
        m = r.st.to_numpy() == s_
        assert abs(look_mu[m].sum() / mu[sel][m].sum() - 1) < 0.005
    np.testing.assert_allclose(look_mu, mu[sel], rtol=2e-3, atol=1e-9)
