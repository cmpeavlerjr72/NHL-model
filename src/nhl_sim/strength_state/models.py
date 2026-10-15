"""SS-R1 hazard arms H0-H3 and type arms T0-T1: feature assembly, fitting, prediction.

Feature builders raise on missing inputs (L5). Every rating is relative to its snapshot league mean (L1).
The held-out season has no season level of its own in training: its season feature is mapped to the LAST
training season (the most recent season effect), for every arm alike.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED, load_games

SS = PROCESSED / "strength_state"
N_ST, N_SC, N_PD = 6, 5, 5
STRENGTH_NAMES = ("5v5", "PP", "PK", "4v4", "3v3", "other")
TYPE_CLASSES = ("minor", "double", "major", "coincidental")
LGB_FEATURES = ["season_f", "st", "ptype", "period", "last5", "sc", "pdiff", "taken_own", "drawn_opp", "is_home",
                "b2b_own", "b2b_opp", "clock"]


def load_rows(seasons, version="v1") -> pd.DataFrame:
    return pd.concat([pd.read_parquet(SS / f"hazard_rows_{version}_{s}.parquet") for s in seasons],
                     ignore_index=True)


def attach_features(rows: pd.DataFrame, w: float, b: float, last_train_season: int, version="v1") -> pd.DataFrame:
    g = load_games(sorted(rows.season.unique()), columns=["game_id", "home_id", "away_id"])
    r = rows.merge(g[["game_id", "home_id", "away_id"]], on="game_id", how="left", validate="many_to_one")
    if r.home_id.isna().any():
        raise ValueError("rows without a game in games.parquet")
    r["team_id"] = np.where(r.team == 0, r.home_id, r.away_id)
    r["opp_id"] = np.where(r.team == 0, r.away_id, r.home_id)
    rt = pd.read_parquet(SS / f"ratings_grid_{version}.parquet",
                         columns=["game_id", "team_id", f"taken_w{w}_b{b}", f"drawn_w{w}_b{b}"])
    rt.columns = ["game_id", "team_id", "taken", "drawn"]
    tg = pd.read_parquet(SS / f"team_game_{version}.parquet", columns=["game_id", "team_id", "b2b"])
    own = rt.merge(tg, on=["game_id", "team_id"], how="left")
    r = r.merge(own.rename(columns={"taken": "taken_own", "drawn": "drawn_own", "b2b": "b2b_own"}),
                on=["game_id", "team_id"], how="left")
    r = r.merge(own.rename(columns={"team_id": "opp_id", "taken": "taken_opp", "drawn": "drawn_opp",
                                    "b2b": "b2b_opp"}), on=["game_id", "opp_id"], how="left")
    for c in ("taken_own", "drawn_opp", "b2b_own", "b2b_opp"):
        if r[c].isna().any():
            raise ValueError(f"missing feature {c} on {int(r[c].isna().sum())} rows")
    r["season_f"] = np.minimum(r.season, last_train_season)
    r["clock"] = (r.t0 // 60).astype(np.int32)   # game minute; constant within a row (rows cut on the minute grid)
    r["cell"] = (r.season_f.astype(np.int64) % 10000) * 100 + r.st * 10 + r.ptype
    return r


# --------------------------------------------------------------------------- GLM (Poisson, cell fixed effects)
def design(r: pd.DataFrame, arm: str) -> np.ndarray:
    cols = [r.taken_own.to_numpy(), r.drawn_opp.to_numpy(), r.is_home.to_numpy(), r.b2b_own.to_numpy(),
            r.b2b_opp.to_numpy()]
    if arm == "H2":
        sc, pdf, per, l5 = r.sc.to_numpy(), r.pdiff.to_numpy(), r.period.to_numpy(), r.last5.to_numpy()
        cols += [(sc == k).astype(float) for k in (0, 1, 3, 4)]          # ref: tied
        cols += [(per == 2).astype(float), (per == 3).astype(float)]      # ref: P1; OT is in the cells
        cols += [((sc == k) & (l5 == 1)).astype(float) for k in range(5)]
        cols += [(pdf == k).astype(float) for k in (0, 1, 3, 4)]         # ref: even penalty count
    return np.column_stack(cols).astype(np.float64)


DESIGN_NAMES = {
    "H1": ["taken_own", "drawn_opp", "is_home", "b2b_own", "b2b_opp"],
    "H2": ["taken_own", "drawn_opp", "is_home", "b2b_own", "b2b_opp", "sc<=-2", "sc-1", "sc+1", "sc>=+2", "P2", "P3",
           "last5xsc<=-2", "last5xsc-1", "last5xsc0", "last5xsc+1", "last5xsc>=+2", "pd<=-2", "pd-1", "pd+1",
           "pd>=+2"],
}


def _cell_alpha(cell_codes, y, base, n_cells, pool_rate):
    """Closed-form cell effects given the other terms; 0.5 pseudo-event toward the pooled rate per cell."""
    ys = np.bincount(cell_codes, weights=y, minlength=n_cells)
    bs = np.bincount(cell_codes, weights=base, minlength=n_cells)
    return np.log((ys + 0.5) / (bs + 0.5 / pool_rate))


def fit_glm(r: pd.DataFrame, arm: str, iters: int = 100, tol: float = 1e-9) -> dict:
    cells = np.sort(r.cell.unique())
    cc = np.searchsorted(cells, r.cell.to_numpy())
    y = r.y.to_numpy(float)
    E = r.exposure_s.to_numpy(float) / 3600.0
    pool = y.sum() / E.sum()
    if arm == "H0":
        a = _cell_alpha(cc, y, E, len(cells), pool)
        return dict(arm=arm, cells=cells.tolist(), alpha=a.tolist(), beta=[], pool=pool,
                    fallback=_fallback(r, y, E, pool))
    X = design(r, arm)
    beta = np.zeros(X.shape[1])
    last = -np.inf
    for _ in range(iters):
        ex = np.exp(X @ beta)
        a = _cell_alpha(cc, y, E * ex, len(cells), pool)
        mu = E * ex * np.exp(a[cc])
        ll = float((y * np.log(mu) - mu).sum())
        g = X.T @ (y - mu)
        H = (X * mu[:, None]).T @ X + 1e-8 * np.eye(X.shape[1])
        step = np.linalg.solve(H, g)
        beta = beta + step
        if abs(ll - last) < tol * max(1.0, abs(ll)) and np.abs(step).max() < 1e-7:
            break
        last = ll
    ex = np.exp(X @ beta)
    a = _cell_alpha(cc, y, E * ex, len(cells), pool)
    return dict(arm=arm, cells=cells.tolist(), alpha=a.tolist(), beta=beta.tolist(), pool=pool,
                names=DESIGN_NAMES[arm], fallback=_fallback(r, y, E * ex, pool))


def _fallback(r, y, base, pool):
    """Season-pooled (strength x period-type) effects, used only for a test cell absent from training (e.g.
    3v3 in regulation never occurred in 2023-24)."""
    k = (r.st * 10 + r.ptype).to_numpy()
    keys = np.sort(np.unique(k))
    kk = np.searchsorted(keys, k)
    a = _cell_alpha(kk, y, base, len(keys), pool)
    return {int(key): float(v) for key, v in zip(keys, a)}


def predict_glm(m: dict, r: pd.DataFrame) -> np.ndarray:
    """Expected count per row (mu = rate_per_hour x exposure_h)."""
    cells = np.asarray(m["cells"])
    alpha = np.asarray(m["alpha"])
    pos = np.searchsorted(cells, r.cell.to_numpy())
    pos = np.clip(pos, 0, len(cells) - 1)
    found = cells[pos] == r.cell.to_numpy()
    eta = alpha[pos].copy()
    if not found.all():
        fb = {int(k): v for k, v in m["fallback"].items()}
        sk = (r.st * 10 + r.ptype).to_numpy()[~found]
        if not all(int(x) in fb for x in np.unique(sk)):
            raise ValueError("strength x period-type cell unseen in every training season")
        eta[~found] = [fb[int(x)] for x in sk]
    if m["beta"]:
        eta = eta + design(r, m["arm"]) @ np.asarray(m["beta"])
    return np.exp(eta) * r.exposure_s.to_numpy(float) / 3600.0


# --------------------------------------------------------------------------- LightGBM (H3)
def lgb_params(num_leaves, min_data, seed, threads=6):
    return dict(objective="poisson", learning_rate=0.05, num_leaves=num_leaves, min_data_in_leaf=min_data,
                seed=seed, num_threads=threads, deterministic=True, force_row_wise=True, verbose=-1)


def lgb_dataset(r: pd.DataFrame):
    import lightgbm as lgb
    return lgb.Dataset(r[LGB_FEATURES].astype(float), label=r.y.to_numpy(float),
                       init_score=np.log(r.exposure_s.to_numpy(float) / 3600.0),
                       categorical_feature=["st"], free_raw_data=False)


def fit_lgb(r: pd.DataFrame, num_leaves, min_data, n_rounds, seed):
    import lightgbm as lgb
    return lgb.train(lgb_params(num_leaves, min_data, seed), lgb_dataset(r), num_boost_round=n_rounds)


def predict_lgb(model, r: pd.DataFrame) -> np.ndarray:
    raw = model.predict(r[LGB_FEATURES].astype(float), raw_score=True)
    return np.exp(raw) * r.exposure_s.to_numpy(float) / 3600.0


# --------------------------------------------------------------------------- metrics
def pois_ll(y, mu):
    from scipy.special import gammaln
    return y * np.log(mu) - mu - gammaln(y + 1.0)


def per_game_ll(r: pd.DataFrame, mu: np.ndarray) -> pd.Series:
    return pd.Series(pois_ll(r.y.to_numpy(float), mu)).groupby(r.game_id.to_numpy()).sum()


# --------------------------------------------------------------------------- type arms
def type_frame(seasons, last_train_season, version="v1") -> pd.DataFrame:
    t = pd.read_parquet(SS / f"type_rows_{version}.parquet")
    t = t[t.season.isin(seasons)].copy()
    t["season_f"] = np.minimum(t.season, last_train_season)
    t["k"] = t.cls.map({c: i for i, c in enumerate(TYPE_CLASSES)}).astype(int)
    return t


def fit_t0(t: pd.DataFrame) -> dict:
    out = {}
    for s, g in t.groupby("season_f"):
        c = np.bincount(g.k, minlength=len(TYPE_CLASSES)) + 0.5
        out[int(s)] = (c / c.sum()).tolist()
    return dict(arm="T0", p=out)


def predict_t0(m, t):
    return np.array([m["p"][int(s)] for s in t.season_f])


def t1_design(t: pd.DataFrame, seasons_ref) -> np.ndarray:
    cols = [(t.season_f == s).astype(float) for s in seasons_ref[1:]]
    cols += [(t.st == k).astype(float) for k in range(1, N_ST)]
    cols += [(t.sc == k).astype(float) for k in (0, 1, 3, 4)]
    cols += [(t.period == k).astype(float) for k in (2, 3, 4)]
    return np.column_stack(cols)


def fit_t1(t: pd.DataFrame) -> dict:
    from sklearn.linear_model import LogisticRegression
    seasons_ref = sorted(int(s) for s in t.season_f.unique())
    X = t1_design(t, seasons_ref)
    m = LogisticRegression(penalty=None, max_iter=2000)
    m.fit(X, t.k.to_numpy())
    if list(m.classes_) != list(range(len(TYPE_CLASSES))):
        raise ValueError("a type class is absent from training")
    return dict(arm="T1", seasons_ref=seasons_ref, coef=m.coef_.tolist(), intercept=m.intercept_.tolist())


def predict_t1(m, t):
    X = t1_design(t, m["seasons_ref"])
    z = X @ np.asarray(m["coef"]).T + np.asarray(m["intercept"])
    z -= z.max(1, keepdims=True)
    p = np.exp(z)
    return p / p.sum(1, keepdims=True)
