"""SA-R1 shot-attempt hazard arms A0-A5 (docs/models/shot_attempt/experiments.md SA-R1).

Every arm carries the as-of de-seasonalised league level + season-phase profile as a FIXED offset (coefficient 1),
implemented as in SS-R2/SS-R3 (`strength_state.models_r2.eff`): the fitting code sees exposure x exp(level).
  A0  cells st x ptype (piecewise constant; closed-form cell effects with a 0.5 pseudo-event, Lane H code)
  A1  A0 + own attempts-for rating + opponent attempts-against rating (row's strength group) + home + b2b own/opp
  A2  A1 + score bucket (7) x period (1, 2, 3, OT) + last-5-min-of-3rd x score bucket
  A5  A2 + as-of arena recording factor
  A4  A2 mean + per-game shared gamma latent (variance from fold-1 train), graded by the exact negative-multinomial
      marginal per game
  A3  LightGBM Poisson on the A5 features + game-minute clock
Feature builders raise on missing inputs (L5). Ratings are relative to their snapshot league mean (L1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import gammaln

from nhl_sim.data.load import PROCESSED, load_games
from nhl_sim.shot_attempt.tables import GROUP_OF_ST, N_SC
from nhl_sim.strength_state import models as HM

SA = PROCESSED / "shot_attempt"
SS = PROCESSED / "strength_state"
V = "v1"
ARMS_GLM = ("A0", "A1", "A2", "A5")
LGB_FEATURES = ["st", "ptype", "period", "last5", "sc", "own_r", "opp_r", "is_home", "b2b_own", "b2b_opp", "arena_f",
                "clock"]
OPP_GROUP = np.array([0, 2, 1], np.int8)   # opponent's group when own group is ES / PP / PK
THIN_GROUPS = {"s5v5": 0, "s44": 3, "s33": 4}   # SA-R3 "lc1s" level groups -> team-view strength state


def wkey(w, b):
    return f"w{float(w)}_b{int(b)}"


def load_rows(seasons) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(SA / f"attempt_rows_{V}_{s}.parquet") for s in seasons], ignore_index=True)


def attach_features(rows: pd.DataFrame, w: float, b: int, k: int, fold: int, arena: bool = True, tv: str = V,
                    level: str = "r3") -> pd.DataFrame:
    """tv: version of the ratings / level / arena tables ("v1" SA-R1, "v2" SA-R2). level: "r3" (SA-R1, SS-R3
    method), "lc1" (SA-R2, D16 all-state LC-1 level + its profile), "lc1g" (SA-R2 A2g / A3g: the LC-1 level and
    profile of the row's strength group ES / PP-for / PK; EN rows use ES, labelled), "lc1s" (SA-R3 A3g-s: lc1g with
    separate 5v5 / 4v4 / 3v3 levels and profiles from league_level_v3)."""
    g = load_games(sorted(rows.season.unique()), columns=["game_id", "home_id", "away_id"])
    r = rows.merge(g.drop(columns="season"), on="game_id", how="left", validate="many_to_one")
    if r.home_id.isna().any():
        raise ValueError("rows without a game in games.parquet")
    r["team_id"] = np.where(r.team == 0, r.home_id, r.away_id)
    r["opp_id"] = np.where(r.team == 0, r.away_id, r.home_id)
    key = wkey(w, b)
    cols = [f"{p}_{gg}_{key}" for p in ("rf", "ra") for gg in ("es", "pp", "pk")]
    rt = pd.read_parquet(SA / f"ratings_grid_{tv}.parquet", columns=["game_id", "team_id", *cols])
    rt = rt.rename(columns={f"{p}_{gg}_{key}": f"{p}{i}" for p in ("rf", "ra")
                            for i, gg in enumerate(("es", "pp", "pk"))})
    tg = pd.read_parquet(SS / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    own = rt.merge(tg, on=["game_id", "team_id"], how="left", validate="one_to_one")
    r = r.merge(own.rename(columns={"b2b": "b2b_own"}), on=["game_id", "team_id"], how="left")
    r = r.merge(own.rename(columns={"team_id": "opp_id", "b2b": "b2b_opp",
                                    **{f"{p}{i}": f"o_{p}{i}" for p in ("rf", "ra") for i in range(3)}}),
                on=["game_id", "opp_id"], how="left")
    grp = GROUP_OF_ST[r.st.to_numpy()]
    og = OPP_GROUP[grp]
    RF = r[["rf0", "rf1", "rf2"]].to_numpy()
    OA = r[["o_ra0", "o_ra1", "o_ra2"]].to_numpy()
    ix = np.arange(len(r))
    r["own_r"] = RF[ix, grp]
    r["opp_r"] = OA[ix, og]
    r["own_rf_es"], r["opp_ra_es"] = r.rf0, r.o_ra0
    if level == "r3":
        lv = pd.read_parquet(SA / f"league_level_{tv}_f{fold}.parquet", columns=["game_id", f"level_k{k}", "p"])
        lv["level"] = lv[f"level_k{k}"] + lv["p"]
        r = r.merge(lv[["game_id", "level"]], on="game_id", how="left", validate="many_to_one")
    elif level == "lc1":
        lv = pd.read_parquet(SA / f"league_level_{tv}_f{fold}.parquet", columns=["game_id", f"level_k{k}", "p_level"])
        lv["level"] = lv[f"level_k{k}"] + lv["p_level"]
        r = r.merge(lv[["game_id", "level"]], on="game_id", how="left", validate="many_to_one")
    elif level == "lc1g":
        gc = [f"level_{g}_k{k}" for g in ("es", "pp", "pk")] + [f"p_level_{g}" for g in ("es", "pp", "pk")]
        lv = pd.read_parquet(SA / f"league_level_{tv}_f{fold}.parquet", columns=["game_id", *gc])
        r = r.merge(lv, on="game_id", how="left", validate="many_to_one")
        LV = np.stack([r[f"level_{g}_k{k}"].to_numpy() + r[f"p_level_{g}"].to_numpy() for g in ("es", "pp", "pk")], 1)
        r["level"] = LV[np.arange(len(r)), grp]
        r = r.drop(columns=gc)
    elif level == "lc1s":
        # SA-R3 A3g-s: five groups. PP-for / PK (and EN, which keeps the SA-R2 ES level, labelled) as "lc1g" (tv
        # tables); 5v5, 4v4 and 3v3 rows take their own LC-1 level + profile from league_level_v3 (k = 5 only).
        gc = [f"level_{g}_k{k}" for g in ("es", "pp", "pk")] + [f"p_level_{g}" for g in ("es", "pp", "pk")]
        lv = pd.read_parquet(SA / f"league_level_{tv}_f{fold}.parquet", columns=["game_id", *gc])
        tc = [f"level_{g}_k{k}" for g in THIN_GROUPS] + [f"p_level_{g}" for g in THIN_GROUPS]
        lt = pd.read_parquet(SA / f"league_level_v3_f{fold}.parquet", columns=["game_id", *tc])
        r = r.merge(lv, on="game_id", how="left", validate="many_to_one")
        r = r.merge(lt, on="game_id", how="left", validate="many_to_one")
        LV = np.stack([r[f"level_{g}_k{k}"].to_numpy() + r[f"p_level_{g}"].to_numpy() for g in ("es", "pp", "pk")], 1)
        lev = LV[np.arange(len(r)), grp]
        st_ = r.st.to_numpy()
        for g, s_ in THIN_GROUPS.items():
            m = st_ == s_
            lev = np.where(m, r[f"level_{g}_k{k}"].to_numpy() + r[f"p_level_{g}"].to_numpy(), lev)
        r["level"] = lev
        r = r.drop(columns=gc + tc)
    else:
        raise ValueError(level)
    need = ["own_r", "opp_r", "b2b_own", "b2b_opp", "level"]
    if arena:
        af = pd.read_parquet(SA / f"arena_{tv}.parquet", columns=["game_id", "arena_f", "w", "b"])
        if not (np.allclose(af.w, w) and (af.b == b).all()):
            raise ValueError("arena table was built at another ratings grid point")
        r = r.merge(af[["game_id", "arena_f"]], on="game_id", how="left", validate="many_to_one")
        need.append("arena_f")
    for c in need:
        if r[c].isna().any():
            raise ValueError(f"missing feature {c} on {int(r[c].isna().sum())} rows")
    r["clock"] = (r.t0 // 60).astype(np.int32)
    r["cell"] = r.st.astype(np.int64) * 10 + r.ptype
    drop = [c for c in r.columns if c.startswith(("rf", "ra", "o_r"))]
    return r.drop(columns=drop)


def eff(r: pd.DataFrame) -> pd.DataFrame:
    return r.assign(exposure_s=r.exposure_s.to_numpy(float) * np.exp(r.level.to_numpy(float)))


# --------------------------------------------------------------------------- GLM design
def design(r: pd.DataFrame, arm: str):
    cols = [r.own_r.to_numpy(float), r.opp_r.to_numpy(float), r.is_home.to_numpy(float), r.b2b_own.to_numpy(float),
            r.b2b_opp.to_numpy(float)]
    names = ["own_r", "opp_r", "is_home", "b2b_own", "b2b_opp"]
    if arm in ("A2", "A2g", "A5", "A4"):
        sc, per, l5 = r.sc.to_numpy(), r.period.to_numpy(), r.last5.to_numpy()
        for p in (1, 2, 3, 4):
            for s in range(N_SC):
                if s == 3 and p in (1, 4):      # reference: tied in P1; tied OT is in the cells
                    continue
                cols.append(((sc == s) & (per == p)).astype(float))
                names.append(f"sc{s - 3:+d}xP{p}")
        for s in range(N_SC):
            cols.append(((sc == s) & (l5 == 1)).astype(float))
            names.append(f"last5xsc{s - 3:+d}")
    if arm == "A5":
        cols.append(r.arena_f.to_numpy(float))
        names.append("arena_f")
    return np.column_stack(cols), names


def fit_glm(r: pd.DataFrame, arm: str, iters: int = 100, tol: float = 1e-10) -> dict:
    e = eff(r)
    cells = np.sort(e.cell.unique())
    cc = np.searchsorted(cells, e.cell.to_numpy())
    y = e.y.to_numpy(float)
    E = e.exposure_s.to_numpy(float) / 3600.0
    pool = y.sum() / E.sum()
    if arm == "A0":
        a = HM._cell_alpha(cc, y, E, len(cells), pool)
        return dict(arm=arm, cells=cells.tolist(), alpha=a.tolist(), beta=[], names=[], keep=[], pool=pool)
    X, names = design(e, arm)
    keep = np.abs(X).sum(0) > 0
    X = X[:, keep]
    beta = np.zeros(X.shape[1])
    last = -np.inf
    for _ in range(iters):
        ex = np.exp(X @ beta)
        a = HM._cell_alpha(cc, y, E * ex, len(cells), pool)
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
    a = HM._cell_alpha(cc, y, E * ex, len(cells), pool)
    return dict(arm=arm, cells=cells.tolist(), alpha=a.tolist(), beta=beta.tolist(),
                names=[n for n, k_ in zip(names, keep) if k_], keep=keep.tolist(), pool=pool)


def predict_glm(m: dict, r: pd.DataFrame) -> np.ndarray:
    e = eff(r)
    cells = np.asarray(m["cells"])
    pos = np.clip(np.searchsorted(cells, e.cell.to_numpy()), 0, len(cells) - 1)
    if not (cells[pos] == e.cell.to_numpy()).all():
        miss = np.unique(e.cell.to_numpy()[cells[pos] != e.cell.to_numpy()])
        raise ValueError(f"strength x period-type cells unseen in training: {miss.tolist()}")
    eta = np.asarray(m["alpha"])[pos].copy()
    if m["beta"]:
        X, _ = design(e, m["arm"])
        eta = eta + X[:, np.asarray(m["keep"], bool)] @ np.asarray(m["beta"])
    return np.exp(eta) * e.exposure_s.to_numpy(float) / 3600.0


# --------------------------------------------------------------------------- LightGBM (A3)
def lgb_dataset(r: pd.DataFrame):
    import lightgbm as lgb
    e = eff(r)
    return lgb.Dataset(e[LGB_FEATURES].astype(float), label=e.y.to_numpy(float),
                       init_score=np.log(e.exposure_s.to_numpy(float) / 3600.0), categorical_feature=["st"],
                       free_raw_data=False)


def fit_lgb(r, num_leaves, min_data, n_rounds, seed, threads=6):
    import lightgbm as lgb
    return lgb.train(HM.lgb_params(num_leaves, min_data, seed, threads), lgb_dataset(r), num_boost_round=n_rounds)


def predict_lgb(model, r):
    e = eff(r)
    raw = model.predict(e[LGB_FEATURES].astype(float), raw_score=True)
    return np.exp(raw) * e.exposure_s.to_numpy(float) / 3600.0


# --------------------------------------------------------------------------- SA-R3 thin-state cells (A3g-c / A2g-c)
THIN_STATES = (3, 4)          # 4v4, 3v3 (team view)


def thin_cells(r: pd.DataFrame, mu: np.ndarray, b_c: float) -> list:
    """Fixed log-offset per team-view state (7 entries; 0 except 4v4 / 3v3): log(training actual / training
    prediction) gamma-shrunk to 0 with strength b_c expected attempts: log((Y + b_c) / (M + b_c))."""
    c = np.zeros(7)
    st = r.st.to_numpy()
    y = r.y.to_numpy(float)
    for s_ in THIN_STATES:
        m = st == s_
        c[s_] = float(np.log((y[m].sum() + b_c) / (mu[m].sum() + b_c)))
    return c.tolist()


def predict_arm(arm: str, model, r: pd.DataFrame) -> np.ndarray:
    """Expected attempts per row for any arm. A cell arm ("-c" suffix) is a dict {"base": booster | glm dict,
    "cell": 7 log-offsets by team-view state}: mu = base mu x exp(cell[st])."""
    if arm.endswith("-c"):
        base = model["base"]
        mu = predict_lgb(base, r) if arm.startswith("A3") else predict_glm(base, r)
        return mu * np.exp(np.asarray(model["cell"], float)[r.st.to_numpy().astype(np.int64)])
    return predict_lgb(model, r) if arm.startswith("A3") else predict_glm(model, r)


# --------------------------------------------------------------------------- likelihoods
def pois_ll(y, mu):
    return y * np.log(mu) - mu - gammaln(y + 1.0)


def game_pos(r):
    games = np.sort(r.game_id.unique())
    return games, np.searchsorted(games, r.game_id.to_numpy())


def per_game_ll(r: pd.DataFrame, mu: np.ndarray, latent_v: float = 0.0) -> np.ndarray:
    """Per-game joint LL of all row counts of both teams (sorted game order). latent_v > 0: exact marginal under a
    per-game gamma(1/v, v) multiplier shared by every row of the game (negative multinomial):
      sum_r [y log mu - log y!] + lgamma(Y + a) - lgamma(a) + a log a - (Y + a) log(a + M),  a = 1/v."""
    games, gp = game_pos(r)
    y = r.y.to_numpy(float)
    G = len(games)
    if latent_v <= 0:
        return np.bincount(gp, weights=pois_ll(y, mu), minlength=G)
    base = np.bincount(gp, weights=y * np.log(mu) - gammaln(y + 1.0), minlength=G)
    Y = np.bincount(gp, weights=y, minlength=G)
    Msum = np.bincount(gp, weights=mu, minlength=G)
    a = 1.0 / latent_v
    return base + gammaln(Y + a) - gammaln(a) + a * np.log(a) - (Y + a) * np.log(a + Msum)


def fit_latent_v(r: pd.DataFrame, mu: np.ndarray) -> dict:
    from scipy.optimize import minimize_scalar
    f = lambda lv: -per_game_ll(r, mu, float(np.exp(lv))).sum()  # noqa: E731
    res = minimize_scalar(f, bounds=(np.log(1e-5), np.log(1.0)), method="bounded", options={"xatol": 1e-4})
    v = float(np.exp(res.x))
    return dict(latent_v=v, ll_gain_per_game=float((per_game_ll(r, mu, v) - per_game_ll(r, mu)).mean()))
