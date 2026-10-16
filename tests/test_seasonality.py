"""SS-R3 seasonality profile: training-only estimation and the as-of de-seasonalised level."""
import numpy as np
import pandas as pd

from nhl_sim.strength_state.seasonality import asof_level_adj, estimate_profile


def _long(rates, seasons=(1, 2, 3)):
    rows, gid = [], 0
    for s in seasons:
        for b in range(8):
            for i in range(4):
                gid += 1
                rows.append(dict(season=s, game_id=gid, date=pd.Timestamp("2020-01-01") + pd.Timedelta(days=gid),
                                 drop=pd.Timestamp("2020-01-01", tz="UTC") + pd.Timedelta(days=gid, hours=19),
                                 taken=int(rates[s][b]), minutes=60.0, bin=b))
    return pd.DataFrame(rows)


def test_profile_uses_training_seasons_only_and_is_a_log_ratio():
    base = {1: [4] * 8, 2: [4] * 8, 3: [40] * 8}
    L = _long(base)
    gbin = L.drop_duplicates("game_id").set_index("game_id").bin
    p12 = estimate_profile(L, gbin, [1, 2])
    assert np.allclose(p12, 0.0)            # flat seasons -> flat profile; season 3 does not leak in
    seas = {1: [6, 4, 4, 4, 4, 4, 4, 2], 2: [6, 4, 4, 4, 4, 4, 4, 2], 3: [4] * 8}
    L2 = _long(seas)
    gb2 = L2.drop_duplicates("game_id").set_index("game_id").bin
    p = estimate_profile(L2, gb2, [1, 2])
    assert p[0] > 0 > p[7]


def test_level_is_asof_and_deseasonalised():
    seas = {1: [6, 4, 4, 4, 4, 4, 4, 2], 2: [6, 4, 4, 4, 4, 4, 4, 2], 3: [6, 4, 4, 4, 4, 4, 4, 2]}
    L = _long(seas)
    gbin = L.drop_duplicates("game_id").set_index("game_id").bin
    p = estimate_profile(L, gbin, [1, 2])
    lv = asof_level_adj(L, gbin, p, [15])
    s3 = lv[lv.season == 3]
    # every season follows the profile exactly -> the de-seasonalised level stays flat (near 0) all season
    assert s3["level_k15"].abs().max() < 0.05
    first = lv.groupby("season").puck_drop.min()
    assert (lv.created_at.dropna() < lv.puck_drop[lv.created_at.notna()]).all()
    assert lv[lv.season == 1]["level_k15"].eq(0).all()
    assert first.is_monotonic_increasing
