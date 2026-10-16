"""SL-R1 arms L0-L3 (docs/models/shot_attribute/experiments.md SL-R1), on UNBLOCKED attempts (step-0 rule (b)).

Every arm returns P(joint class) over the 78 classes (cell x type) per attempt.
  L0  empirical joint frequency per (strength group x period type) cell; Dirichlet posterior mean with ALPHA0
      pseudo-attempts spread on the pooled joint frequency (labelled: keeps unseen classes finite)
  L1  factorised multinomial logit P(cell) x P(type | cell): L0 one-hots + score bucket (7) + home + b2b own / opp +
      own shot-quality-for rating + opponent shot-quality-against rating (row's strength group; EN rows use ES,
      labelled); the type model adds the 13 cell one-hots
  L2  L1 + as-of arena distance-recording factor
  L3  LightGBM multiclass on the joint (78), L2 features + game clock (minute) + period
Feature builders raise on missing inputs (L5). Ratings are relative to their snapshot league mean (L1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED, load_games
from nhl_sim.shot_attribute.tables import N_CELL, N_CLASS, N_TYPE, OPP_RATING_GROUP, RATING_GROUP

SA = PROCESSED / "shot_attribute"
V = "v1"
ALPHA0 = 10.0
N_L0 = 10                      # 5 groups x 2 period types
C_REG = 1e4                    # inverse L2 strength for the MNLs (near-unpenalised; resolves one-hot collinearity)
LGB_FEATURES = ["grp", "ptype", "sc", "is_home", "b2b_own", "b2b_opp", "own_r", "opp_r", "arena_f", "clock", "period"]


def wkey(w, b):
    return f"w{float(w)}_b{int(b)}"


def load_rows(seasons) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(SA / f"attempt_attr_{V}_{s}.parquet") for s in seasons], ignore_index=True)


def attach_features(rows: pd.DataFrame, fold: int, w: float, b: int, arena: bool = True) -> pd.DataFrame:
    """Unblocked rows only, with own_r / opp_r at grid point (w, b) of the fold's ratings, b2b, arena_f, clock."""
    r = rows[~rows.blocked].copy()
    g = load_games(sorted(r.season.unique()), columns=["game_id", "home_id", "away_id", "game_date_local"])
    r = r.merge(g.drop(columns="season"), on="game_id", how="left", validate="many_to_one")
    if r.home_id.isna().any():
        raise ValueError("rows without a game in games.parquet")
    r["team_id"] = np.where(r.team == 0, r.home_id, r.away_id)
    r["opp_id"] = np.where(r.team == 0, r.away_id, r.home_id)
    k = wkey(w, b)
    cols = {f"{p}_{gg}_{k}": f"{p}{i}" for p in ("rf", "ra") for i, gg in enumerate(("es", "pp", "pk"))}
    rt = pd.read_parquet(SA / f"sq_ratings_{V}_f{fold}.parquet", columns=["game_id", "team_id", *cols]).rename(columns=cols)
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    own = rt.merge(tg, on=["game_id", "team_id"], how="left", validate="one_to_one")
    r = r.merge(own.rename(columns={"b2b": "b2b_own"}), on=["game_id", "team_id"], how="left", validate="many_to_one")
    r = r.merge(own.rename(columns={"team_id": "opp_id", "b2b": "b2b_opp",
                                    **{f"{p}{i}": f"o_{p}{i}" for p in ("rf", "ra") for i in range(3)}}),
                on=["game_id", "opp_id"], how="left", validate="many_to_one")
    rg = RATING_GROUP[r.grp.to_numpy()]
    og = OPP_RATING_GROUP[rg]
    ix = np.arange(len(r))
    r["own_r"] = r[["rf0", "rf1", "rf2"]].to_numpy()[ix, rg]
    r["opp_r"] = r[["o_ra0", "o_ra1", "o_ra2"]].to_numpy()[ix, og]
    r["own_rf_es"], r["opp_ra_es"] = r.rf0, r.o_ra0
    need = ["own_r", "opp_r", "b2b_own", "b2b_opp"]
    if arena:
        af = pd.read_parquet(SA / f"arena_dist_{V}.parquet", columns=["game_id", "arena", "arena_f"])
        r = r.merge(af, on="game_id", how="left", validate="many_to_one")
        need.append("arena_f")
    for c in need:
        if r[c].isna().any():
            raise ValueError(f"missing feature {c} on {int(r[c].isna().sum())} rows")
    r["clock"] = (r.t // 60).astype(np.int32)
    r["l0"] = (r.grp.astype(np.int64) * 2 + r.ptype).astype(np.int8)
    return r.drop(columns=[c for c in r.columns if c.startswith(("rf", "ra", "o_r"))])


# --------------------------------------------------------------------------- L0
def fit_l0(r: pd.DataFrame) -> dict:
    n = np.zeros((N_L0, N_CLASS))
    np.add.at(n, (r.l0.to_numpy(), r.cls.to_numpy()), 1)
    pooled = (n.sum(0) + 0.5) / (n.sum() + 0.5 * N_CLASS)
    p = (n + ALPHA0 * pooled) / (n.sum(1, keepdims=True) + ALPHA0)
    return dict(arm="L0", p=p.tolist())


def predict_l0(m: dict, r: pd.DataFrame) -> np.ndarray:
    return np.asarray(m["p"])[r.l0.to_numpy()]


# --------------------------------------------------------------------------- L1 / L2 (factorised MNL)
def base_design(r: pd.DataFrame, arena: bool) -> np.ndarray:
    l0 = np.eye(N_L0)[r.l0.to_numpy()]
    sc = np.eye(7)[r.sc.to_numpy()][:, [0, 1, 2, 4, 5, 6]]          # reference: tied
    cols = [l0, sc, r[["is_home", "b2b_own", "b2b_opp", "own_r", "opp_r"]].to_numpy(float)]
    if arena:
        cols.append(r[["arena_f"]].to_numpy(float))
    return np.hstack(cols)


def _scale(X):
    s = X.std(0)
    s[s == 0] = 1.0
    return s


def fit_mnl(r: pd.DataFrame, arm: str) -> dict:
    from sklearn.linear_model import LogisticRegression
    arena = arm == "L2"
    X = base_design(r, arena)
    sx = _scale(X)
    mc = LogisticRegression(C=C_REG, max_iter=5000, tol=1e-8)
    mc.fit(X / sx, r.cell.to_numpy())
    Xt = np.hstack([np.eye(N_CELL)[r.cell.to_numpy()], X])
    st = _scale(Xt)
    mt = LogisticRegression(C=C_REG, max_iter=5000, tol=1e-8)
    mt.fit(Xt / st, r.type6.to_numpy())
    if list(mc.classes_) != list(range(N_CELL)) or list(mt.classes_) != list(range(N_TYPE)):
        raise ValueError("a cell or type class is absent from training")
    return dict(arm=arm, arena=arena, cell_coef=(mc.coef_ / sx).tolist(), cell_int=mc.intercept_.tolist(),
                type_coef=(mt.coef_ / st).tolist(), type_int=mt.intercept_.tolist(),
                n_iter=[int(mc.n_iter_[0]), int(mt.n_iter_[0])])


def _softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def predict_mnl(m: dict, r: pd.DataFrame) -> np.ndarray:
    X = base_design(r, m["arena"])
    pc = _softmax(X @ np.asarray(m["cell_coef"]).T + np.asarray(m["cell_int"]))
    Wt = np.asarray(m["type_coef"])
    base = X @ Wt[:, N_CELL:].T + np.asarray(m["type_int"])          # (n, 6)
    out = np.empty((len(r), N_CLASS))
    for c in range(N_CELL):
        pt = _softmax(base + Wt[:, c][None, :])
        out[:, c * N_TYPE:(c + 1) * N_TYPE] = pc[:, [c]] * pt
    return out


# --------------------------------------------------------------------------- L3 (LightGBM multiclass)
def lgb_params(num_leaves, min_data, seed, threads=8):
    return dict(objective="multiclass", num_class=N_CLASS, learning_rate=0.05, num_leaves=num_leaves,
                min_data_in_leaf=min_data, seed=seed, num_threads=threads, deterministic=True, force_row_wise=True,
                verbose=-1)


def lgb_dataset(r: pd.DataFrame, ref=None):
    import lightgbm as lgb
    return lgb.Dataset(r[LGB_FEATURES].astype(float), label=r.cls.to_numpy(), categorical_feature=["grp"],
                       free_raw_data=False, reference=ref)


def predict_lgb(model, r: pd.DataFrame) -> np.ndarray:
    return model.predict(r[LGB_FEATURES].astype(float))


def predict_arm(arm: str, model, r: pd.DataFrame) -> np.ndarray:
    if arm == "L0":
        return predict_l0(model, r)
    if arm in ("L1", "L2"):
        return predict_mnl(model, r)
    return predict_lgb(model, r)


def joint_ll(P: np.ndarray, cls: np.ndarray) -> np.ndarray:
    return np.log(np.maximum(P[np.arange(len(cls)), cls], 1e-300))
