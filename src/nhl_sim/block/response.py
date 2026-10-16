"""SB-R3 helpers (docs/models/block/experiments.md SB-R3, D29): rating-response diagnostics and response-side arms.

  fit_se            offset logistic on a raw design, with model-based (Hessian) and game-cluster sandwich SEs
  exposure          as-of rating exposure: the team's games already played this season before the game (same-date safe)
  persistence_rows  binomial cells for the time-forward persistence slope: the as-of rating at team-game t against the
                    realised blocks in the team's games t+1..t+20 of the same season (per game x stratum, B0 offset)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from nhl_sim.block.data import sigmoid

WINDOW = 20


def fit_se(X: np.ndarray, y: np.ndarray, off: np.ndarray, cluster: np.ndarray | None = None, wts: np.ndarray | None = None,
           n_trials: np.ndarray | None = None):
    """Unpenalised binomial logistic with offset. y = successes, n_trials = trials (default 1), wts = row weights.
    Returns dict(coef, se_model, se_cluster or None)."""
    n_t = np.ones(len(y)) if n_trials is None else n_trials.astype(float)
    wt = np.ones(len(y)) if wts is None else wts.astype(float)
    y = y.astype(float)
    sx = X.std(0)
    sx[sx == 0] = 1.0
    mx = np.zeros(X.shape[1])
    Z = X / sx
    N = (wt * n_t).sum()

    def f(b):
        eta = Z @ b + off
        ll = wt * (n_t * np.logaddexp(0.0, eta) - y * eta)
        g = Z.T @ (wt * (n_t * sigmoid(eta) - y))
        return ll.sum() / N, g / N

    res = minimize(f, np.zeros(Z.shape[1]), jac=True, method="L-BFGS-B",
                   options=dict(maxiter=5000, maxfun=10000, ftol=1e-15, gtol=1e-10))
    b = res.x / sx
    eta = X @ b + off
    p = sigmoid(eta)
    H = (X * (wt * n_t * p * (1 - p))[:, None]).T @ X
    Hi = np.linalg.pinv(H)
    out = dict(coef=b, se_model=np.sqrt(np.diag(Hi)), se_cluster=None, nit=int(res.nit), mx=mx)
    if cluster is not None:
        sc = X * (wt * (y - n_t * p))[:, None]
        _, inv = np.unique(cluster, return_inverse=True)
        S = np.zeros((inv.max() + 1, X.shape[1]))
        np.add.at(S, inv, sc)
        V = Hi @ (S.T @ S) @ Hi
        out["se_cluster"] = np.sqrt(np.diag(V))
    return out


def exposure(games: pd.DataFrame) -> pd.DataFrame:
    """-> game_id, team_id, n_prior: the team's games of the same season dated strictly before this game."""
    g = games[["game_id", "season", "date", "home_id", "away_id"]]
    long = pd.concat([g.rename(columns={"home_id": "team_id"}).drop(columns="away_id"),
                      g.rename(columns={"away_id": "team_id"}).drop(columns="home_id")], ignore_index=True)
    long = long.sort_values(["season", "team_id", "date", "game_id"], kind="stable")
    long["n_prior"] = long.groupby(["season", "team_id"]).cumcount()
    # same-date safety: a team never plays twice on one date; assert
    if long.duplicated(["season", "team_id", "date"]).any():
        raise ValueError("team with two games on one date")
    return long[["game_id", "team_id", "n_prior"]]


def persistence_cells(r: pd.DataFrame, logit_p0: np.ndarray, window: int = WINDOW) -> pd.DataFrame:
    """r: assembled rows (one season or several) with game_id, season, date, team_id, opp_id, grp, l0, y, own_r, opp_r.
    For each shooting team T and each team-game t, the as-of ratings at t (T's own blocked-against rating own_r for the
    row's group, and for the 'against' side the defending team D's blocks-for rating opp_r) are paired with the
    realised block outcomes of the same team's games t+1..t+window in the same season.
    Cells are aggregated per (side, team, t, later game, l0): successes, trials, mean B0 logit (exact per l0 within a game
    up to the level offset, which is constant within a game x group).
    -> DataFrame side ('own' | 'opp'), season, team, t_game, game_id, k (lag), x (rating at t), y, n, off."""
    r = r.assign(lp0=logit_p0)
    out = []
    for side, team_col, rcol in (("own", "team_id", "own_r"), ("opp", "opp_id", "opp_r")):
        # cells per (team, game, l0) for the realised outcome
        c = r.groupby([team_col, "game_id", "l0"], sort=False).agg(season=("season", "first"), date=("date", "first"),
                                                                    y=("y", "sum"), n=("y", "size"),
                                                                    off=("lp0", "mean")).reset_index()
        # rating at t per (team, game, row group): the team's rating for that rating group (l0 // 2 = grp)
        rt = r.groupby([team_col, "game_id", "grp"], sort=False)[rcol].first().rename("x").reset_index()
        c["grp"] = (c.l0 // 2).astype(int)
        tg = c[[team_col, "season", "date", "game_id"]].drop_duplicates(["season", team_col, "game_id"])
        tg = tg.sort_values([team_col, "season", "date", "game_id"], kind="stable")
        tg["seq"] = tg.groupby([team_col, "season"]).cumcount()
        c = c.merge(tg[[team_col, "game_id", "seq"]], on=[team_col, "game_id"], how="left", validate="many_to_one")
        rt = rt.merge(tg[[team_col, "game_id", "seq", "season"]], on=[team_col, "game_id"], how="left", validate="many_to_one")
        for k in range(1, window + 1):
            src = rt.assign(seq=rt.seq + k).rename(columns={"game_id": "t_game"})
            m = c.merge(src[[team_col, "season", "seq", "grp", "x", "t_game"]], on=[team_col, "season", "seq", "grp"],
                        how="inner")
            m["k"] = k
            out.append(m.assign(side=side).rename(columns={team_col: "team"})[
                ["side", "season", "team", "t_game", "game_id", "k", "grp", "x", "y", "n", "off"]])
    return pd.concat(out, ignore_index=True)
