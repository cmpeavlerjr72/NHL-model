"""SM-R2 tier-specific miss level (docs/models/miss/experiments.md SM-R2). Level cell = (level group ES+EN / PP / PK) x
(danger tier high / medium / low, TIER_OF_CELL of the stage-4 location cell); column index = 3 * tier + level_group (9 cells).
Constructions M0 / M1 (K scaled by the tier's share of the group's attempts in the prior season, so K per group sums to K) /
M2 (discounted, half-life, K likewise scaled) / O (oracle) and E (era pooled training share, reported, not selectable, D35).
The level enters as logit(s_asof[game, group, tier]) - logit(s_train[group, tier]) per row. created_at is the previous
game-day's last puck drop + 6 h (as in nhl_sim.block.data.asof_levels, which this generalises; block code is not edited)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.block import data as D
from nhl_sim.shot_attribute.tables import TIER_OF_CELL
from nhl_sim.strength_state.tables import assert_pregame

NC = 9


def col_of(a: pd.DataFrame) -> np.ndarray:
    return (3 * TIER_OF_CELL[a.cell.to_numpy()].astype(np.int64) + D.LEVEL_GROUP[a.grp.to_numpy()]).astype(np.int64)


def game_counts(a, games):
    gi = pd.Series(np.arange(len(games)), index=games.game_id.to_numpy())
    ix = gi.reindex(a.game_id.to_numpy()).to_numpy()
    if np.isnan(ix.astype(float)).any():
        raise ValueError("attempt rows for a game missing from the game list")
    ix = ix.astype(np.int64)
    c = col_of(a)
    B = np.zeros((len(games), NC))
    T = np.zeros((len(games), NC))
    np.add.at(B, (ix, c), a.y.to_numpy().astype(float))
    np.add.at(T, (ix, c), 1.0)
    return B, T


def _kscale(Tprev):
    """(9,) share of the tier within its level group in attempts, summing to 1 over the 3 tiers of a group."""
    t = Tprev.reshape(3, 3)          # [tier, group]
    return (t / t.sum(0, keepdims=True)).reshape(-1)


def asof_levels(a, games, specs):
    games = games.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)
    B, T = game_counts(a, games)
    seasons = sorted(games.season.unique())
    final, fT = {}, {}
    for s in seasons:
        m = (games.season == s).to_numpy()
        final[s] = B[m].sum(0) / T[m].sum(0)
        fT[s] = T[m].sum(0)
    out = {n: np.zeros((len(games), NC)) for n in specs}
    created = np.full(len(games), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    last_drop = None
    for i, season in enumerate(seasons):
        s_prev = final[seasons[i - 1]] if i > 0 else final[season]
        ks = _kscale(fT[seasons[i - 1]] if i > 0 else fT[season])
        idx_s = np.flatnonzero((games.season == season).to_numpy())
        dates = games.date.to_numpy()[idx_s]
        st = {n: [np.zeros(NC), np.zeros(NC)] for n in specs}
        prev_date = None
        for d in np.unique(dates):
            ix = idx_s[dates == d]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            gap = 0.0 if prev_date is None else float((pd.Timestamp(d) - pd.Timestamp(prev_date)).days)
            for n, (kind, par) in specs.items():
                nb, nt = st[n]
                if kind == "M0":
                    v = s_prev
                elif kind == "O":
                    v = final[season]
                elif kind == "M1":
                    K = par * ks
                    v = (nb + K * s_prev) / (nt + K)
                elif kind == "M2":
                    hl, K0 = par
                    f = 0.5 ** (gap / hl)
                    nb, nt = nb * f, nt * f
                    st[n] = [nb, nt]
                    K = K0 * ks
                    v = (nb + K * s_prev) / (nt + K)
                else:
                    raise ValueError(kind)
                out[n][ix] = v
            for n in specs:
                st[n] = [st[n][0] + B[ix].sum(0), st[n][1] + T[ix].sum(0)]
            prev_date = d
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": games.season.to_numpy(),
                         "created_at": pd.to_datetime(created).tz_localize("UTC"),
                         "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    assert_pregame(meta)
    return meta, out


def share_table(a) -> np.ndarray:
    c = col_of(a)
    n = np.bincount(c, minlength=NC).astype(float)
    b = np.bincount(c, weights=a.y.to_numpy().astype(float), minlength=NC)
    if (n == 0).any():
        raise ValueError("empty level cell")
    return b / n


def era_level(a_train, games) -> np.ndarray:
    pooled = share_table(a_train)
    era_tr = D.era_of(a_train.season.to_numpy())
    by = {e: (share_table(a_train[era_tr == e]) if (era_tr == e).any() else pooled) for e in (1, 2)}
    return np.stack([by[e] for e in D.era_of(games.season.to_numpy())])


def level_frame(meta, S):
    f = meta[["game_id", "season", "created_at", "puck_drop"]].copy()
    for g in range(NC):
        f[f"s_{g}"] = S[:, g]
    return f


def row_offset(rows, level, s_train) -> np.ndarray:
    L = level.set_index("game_id")[[f"s_{g}" for g in range(NC)]].reindex(rows.game_id.to_numpy()).to_numpy()
    if np.isnan(L).any():
        raise ValueError("rows without a level")
    c = col_of(rows)
    return D.logit(L[np.arange(len(rows)), c]) - D.logit(s_train[c])
