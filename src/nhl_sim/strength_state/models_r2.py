"""SS-R2 hazard arms H0'-H3' (docs/models/strength_state/experiments.md SS-R2). Reuses the SS-R1 fitting code
(`models.py`) with the three SS-R2 changes:

1. rows come from the v2 tables (delayed-penalty state, `delayed.py`);
2. no season dummies: the GLM cells are strength state x period type, pooled over the training seasons, and
   H3' drops `season_f`. Every arm carries the as-of in-season league level (`league_level.py`) as a FIXED
   OFFSET (coefficient 1): mu = exposure x exp(level) x exp(arm terms). H0' = H0 cells x exp(level);
3. ratings from the extended grid (w in {0.7, 0.85, 1.0}, prior strength in {1800, 5400}).

The offset is implemented by passing the GLM / LightGBM code an effective exposure = exposure_s x exp(level);
the graded frame keeps the true exposure_s.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.data.load import load_games
from nhl_sim.strength_state import models as M

SS = M.SS
VERSION = "v2"
LGB_FEATURES = ["st", "ptype", "period", "last5", "sc", "pdiff", "taken_own", "drawn_opp", "is_home", "b2b_own",
                "b2b_opp", "clock"]


def wkey(w: float, b: int) -> str:
    return f"w{float(w)}_b{int(b)}"


def load_rows(seasons) -> pd.DataFrame:
    return M.load_rows(seasons, version=VERSION)


def attach_features(rows: pd.DataFrame, w: float, b: int, k: int) -> pd.DataFrame:
    g = load_games(sorted(rows.season.unique()), columns=["game_id", "home_id", "away_id"])
    r = rows.merge(g[["game_id", "home_id", "away_id"]], on="game_id", how="left", validate="many_to_one")
    if r.home_id.isna().any():
        raise ValueError("rows without a game in games.parquet")
    r["team_id"] = np.where(r.team == 0, r.home_id, r.away_id)
    r["opp_id"] = np.where(r.team == 0, r.away_id, r.home_id)
    key = wkey(w, b)
    rt = pd.read_parquet(SS / f"ratings_grid_{VERSION}.parquet",
                         columns=["game_id", "team_id", f"taken_{key}", f"drawn_{key}"])
    rt.columns = ["game_id", "team_id", "taken", "drawn"]
    tg = pd.read_parquet(SS / f"team_game_{VERSION}.parquet", columns=["game_id", "team_id", "b2b"])
    own = rt.merge(tg, on=["game_id", "team_id"], how="left")
    r = r.merge(own.rename(columns={"taken": "taken_own", "drawn": "drawn_own", "b2b": "b2b_own"}),
                on=["game_id", "team_id"], how="left")
    r = r.merge(own.rename(columns={"team_id": "opp_id", "taken": "taken_opp", "drawn": "drawn_opp",
                                    "b2b": "b2b_opp"}), on=["game_id", "opp_id"], how="left")
    lv = pd.read_parquet(SS / f"league_level_{VERSION}.parquet", columns=["game_id", f"level_k{k}"])
    r = r.merge(lv.rename(columns={f"level_k{k}": "level"}), on="game_id", how="left", validate="many_to_one")
    for c in ("taken_own", "drawn_opp", "b2b_own", "b2b_opp", "level"):
        if r[c].isna().any():
            raise ValueError(f"missing feature {c} on {int(r[c].isna().sum())} rows")
    r["clock"] = (r.t0 // 60).astype(np.int32)
    r["cell"] = r.st.astype(np.int64) * 10 + r.ptype          # no season term (SS-R2 change 2)
    return r


def eff(r: pd.DataFrame) -> pd.DataFrame:
    """Frame whose exposure_s carries the league-level offset (exposure x exp(level))."""
    return r.assign(exposure_s=r.exposure_s.to_numpy(float) * np.exp(r.level.to_numpy(float)))


def fit_glm(r, arm):
    return M.fit_glm(eff(r), arm)


def predict_glm(m, r):
    return M.predict_glm(m, eff(r))


def lgb_dataset(r):
    import lightgbm as lgb
    e = eff(r)
    return lgb.Dataset(e[LGB_FEATURES].astype(float), label=e.y.to_numpy(float),
                       init_score=np.log(e.exposure_s.to_numpy(float) / 3600.0),
                       categorical_feature=["st"], free_raw_data=False)


def fit_lgb(r, num_leaves, min_data, n_rounds, seed):
    import lightgbm as lgb
    return lgb.train(M.lgb_params(num_leaves, min_data, seed), lgb_dataset(r), num_boost_round=n_rounds)


def predict_lgb(model, r):
    e = eff(r)
    raw = model.predict(e[LGB_FEATURES].astype(float), raw_score=True)
    return np.exp(raw) * e.exposure_s.to_numpy(float) / 3600.0
