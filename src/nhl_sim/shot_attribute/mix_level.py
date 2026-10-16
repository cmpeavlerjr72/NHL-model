"""SL-R2 as-of league location-mix level (docs/models/shot_attribute/experiments.md SL-R2, step 0; D23).

The level is, per level group (ES with EN pooled into it, PP-for, PK) a vector of league shares over the 13 location
cells of UNBLOCKED attempts. It enters an arm as a per-cell offset log(s_asof / s_train) with coefficient 1, where
s_train is the arm's pooled training share (per level group). Type is not levelled.

Constructions (per game; one value per game date, from games dated strictly earlier):
  M0      prior only: last season's final shares, constant all season
  M1_K    (n_std + K s_prev) / (N_std + K): season to date shrunk to last season's final shares (K attempts / group)
  M2_H    M1 with K = 2000 and the season-to-date counts discounted by 0.5^(age days / H) (the LC-2 form)
  E       era intercept: pooled shares of the fold's TRAINING rows of the same recording era (era 1 = 2021-22..2022-23,
          era 2 = 2023-24 on); an era without training rows falls back to the pooled training shares (labelled)
  O       oracle: the season's own final shares (diagnostic, never selectable)
s_prev = previous season's final shares (all games, unblocked attempts). First data season (2021-22): its own final
shares (look-ahead, labelled, as LC-1). created_at = 6 h after the last puck drop of the previous game date.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE

LEVEL_GROUP = np.array([0, 1, 2, 0, 0], np.int8)        # strength group (ES, PP, PK, ENF, ENA) -> level group
LG_NAMES = ("ES+EN", "PP", "PK")
N_LG = 3
ERA_OF_SEASON = {20212022: 1, 20222023: 1, 20232024: 2, 20242025: 2, 20252026: 2, 20262027: 2}
SIMPLICITY = ("M0", "E", "M1", "M2")                     # selection order (simplest first)


def game_counts(u: pd.DataFrame, games: pd.DataFrame) -> np.ndarray:
    """u: unblocked rows (game_id, grp, cell). games: one row per game, in the order used. -> (G, 3, 13) counts."""
    gi = pd.Series(np.arange(len(games)), index=games.game_id.to_numpy())
    ix = gi.reindex(u.game_id.to_numpy()).to_numpy()
    if np.isnan(ix.astype(float)).any():
        raise ValueError("attempt rows for a game missing from the game list")
    C = np.zeros((len(games), N_LG, N_CELL))
    np.add.at(C, (ix.astype(np.int64), LEVEL_GROUP[u.grp.to_numpy()], u.cell.to_numpy().astype(np.int64)), 1.0)
    return C


def asof_levels(u: pd.DataFrame, games: pd.DataFrame, specs: dict) -> tuple[pd.DataFrame, dict]:
    """games: game_id, season, date (str), drop (UTC str). specs: {name: (kind, param)}, kind in
    M0 / M1 (param K) / M2 (param (half_life_days, K)) / O.
    -> (meta frame per game: game_id, season, created_at, puck_drop), {name: (G, 3, 13) shares}, games in date order."""
    games = games.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)
    C = game_counts(u, games)
    seasons = sorted(games.season.unique())
    final = {s: C[(games.season == s).to_numpy()].sum(0) for s in seasons}
    final = {s: v / v.sum(1, keepdims=True) for s, v in final.items()}
    out = {n: np.zeros((len(games), N_LG, N_CELL)) for n in specs}
    created = np.full(len(games), np.datetime64("NaT"), dtype="datetime64[ns]")
    last_drop = None
    for i, season in enumerate(seasons):
        s_prev = final[seasons[i - 1]] if i > 0 else final[season]
        idx_s = np.flatnonzero((games.season == season).to_numpy())
        dates = games.date.to_numpy()[idx_s]
        st = {n: np.zeros((N_LG, N_CELL)) for n in specs}
        prev_date = None
        for d in np.unique(dates):
            ix = idx_s[dates == d]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            gap = 0.0 if prev_date is None else float((pd.Timestamp(d) - pd.Timestamp(prev_date)).days)
            for n, (kind, par) in specs.items():
                n_ = st[n]
                if kind == "M0":
                    v = s_prev
                elif kind == "O":
                    v = final[season]
                elif kind == "M1":
                    K = float(par)
                    v = (n_ + K * s_prev) / (n_.sum(1, keepdims=True) + K)
                elif kind == "M2":
                    hl, K = par
                    n_ = n_ * 0.5 ** (gap / hl)
                    st[n] = n_
                    v = (n_ + K * s_prev) / (n_.sum(1, keepdims=True) + K)
                else:
                    raise ValueError(kind)
                out[n][ix] = v
            day = C[ix].sum(0)
            for n in specs:
                st[n] = st[n] + day
            prev_date = d
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": games.season.to_numpy(),
                         "created_at": pd.to_datetime(created).tz_localize("UTC"),
                         "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    ok = meta.created_at.notna()
    if not (meta.created_at[ok] < meta.puck_drop[ok]).all():
        raise AssertionError("created_at >= puck_drop on a level row")
    return meta, out


def era_level(u_train: pd.DataFrame, games: pd.DataFrame) -> np.ndarray:
    """E: per game, the pooled shares of the training rows of the game's recording era; fallback (no training rows
    in that era): pooled training shares over all eras (labelled). -> (G, 3, 13) in the order of `games`."""
    era_tr = u_train.season.map(ERA_OF_SEASON).to_numpy()
    pooled = share_table(u_train)
    by_era = {}
    for e in (1, 2):
        m = era_tr == e
        by_era[e] = share_table(u_train[m]) if m.any() else pooled
    eras = games.season.map(ERA_OF_SEASON).to_numpy()
    return np.stack([by_era[e] for e in eras])


def share_table(u: pd.DataFrame) -> np.ndarray:
    """(3, 13) pooled cell shares per level group."""
    C = np.zeros((N_LG, N_CELL))
    np.add.at(C, (LEVEL_GROUP[u.grp.to_numpy()], u.cell.to_numpy().astype(np.int64)), 1.0)
    if (C == 0).any():
        raise ValueError("a (level group, cell) is empty in the share table")
    return C / C.sum(1, keepdims=True)


def row_offset(rows: pd.DataFrame, level: pd.DataFrame, s_train: np.ndarray) -> np.ndarray:
    """Per-row cell offset (n, 13) = log(s_asof[game, level group] / s_train[level group]).
    level: game_id + columns s_{lg}_{cell} (3 x 13 shares)."""
    cols = [f"s_{g}_{c}" for g in range(N_LG) for c in range(N_CELL)]
    L = level.set_index("game_id")[cols].reindex(rows.game_id.to_numpy()).to_numpy()
    if np.isnan(L).any():
        raise ValueError("rows without a level")
    L = L.reshape(len(rows), N_LG, N_CELL)
    lg = LEVEL_GROUP[rows.grp.to_numpy()]
    s = L[np.arange(len(rows)), lg]
    return np.log(s / s_train[lg])


def level_frame(meta: pd.DataFrame, S: np.ndarray) -> pd.DataFrame:
    f = meta[["game_id", "season", "created_at", "puck_drop"]].copy()
    flat = S.reshape(len(S), -1)
    for k, (g, c) in enumerate((g, c) for g in range(N_LG) for c in range(N_CELL)):
        f[f"s_{g}_{c}"] = flat[:, k]
    return f


def apply_cell_offset(P: np.ndarray, off: np.ndarray) -> np.ndarray:
    """Joint (n, 78) probabilities x exp(per-cell offset), renormalised (type given cell unchanged)."""
    Q = P * np.repeat(np.exp(off), N_TYPE, axis=1)
    return Q / Q.sum(1, keepdims=True)
