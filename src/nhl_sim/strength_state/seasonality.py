"""SS-R3: in-season seasonality profile p(b) and the de-seasonalised as-of league level.

Bins b: Oct, Nov, Dec, Jan, Feb, Mar, Apr (regular season by game-date month; the one regular-season game dated in
May is put in Apr) and playoffs (game_type 3). The profile is estimated from TRAINING seasons only:
  p(b) = mean over training seasons of log( rate_b(season) / rate_full(season) ),
rate = penalty-taking events per team-hour, rate_full = the same season's rate over ALL its games (regular season
and playoffs; the interpretation of "full-season rate", labelled in the SS-R3 report). Equal weight across seasons.
p enters every arm as a FIXED offset (coefficient 1): mu = exposure x exp(level_adj + p(b)) x exp(arm terms).

De-seasonalised level (SS-R2's formula on profile-adjusted exposure): events are divided by exp(p(bin of game)),
for the current season to date and for the previous season's final rate r_prev. created_at is 6 h after the last
puck drop of the previous game date (as SS-R2); created_at < puck_drop is enforced by the caller.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BINS = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "PO"]
_MONTH_BIN = {10: 0, 11: 1, 12: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 6, 6: 6}


def game_bins(long: pd.DataFrame, games: pd.DataFrame) -> pd.Series:
    """bin index (0..7) per game_id. games: game_id, game_type, game_date_local."""
    g = games.drop_duplicates("game_id").set_index("game_id")
    month = pd.to_datetime(g.game_date_local).dt.month
    b = month.map(_MONTH_BIN)
    if b.isna().any():
        raise ValueError(f"regular-season month outside the bin map: {sorted(month[b.isna()].unique())}")
    b = b.where(g.game_type != 3, 7)
    po_bad = (g.game_type == 3) & ~month.isin([4, 5, 6])
    if po_bad.any():
        raise ValueError("playoff game outside Apr-Jun")
    return b.astype(int)


def estimate_profile(long: pd.DataFrame, gbin: pd.Series, train_seasons) -> np.ndarray:
    """p(b) from the training seasons only (long = team-game rows with season, game_id, taken, minutes)."""
    L = long[long.season.isin(train_seasons)].copy()
    L["bin"] = L.game_id.map(gbin).to_numpy()
    ps = []
    for s, d in L.groupby("season"):
        full = d.taken.sum() / (d.minutes.sum() / 60.0)
        gb = d.groupby("bin").agg(e=("taken", "sum"), m=("minutes", "sum"))
        gb = gb.reindex(range(len(BINS)))
        ps.append(np.log((gb.e / (gb.m / 60.0)) / full).to_numpy())
    P = np.vstack(ps)
    if np.isnan(P).any():
        raise ValueError("a training season has an empty bin")
    return P.mean(0)


def asof_level_adj(long: pd.DataFrame, gbin: pd.Series, p: np.ndarray, ks) -> pd.DataFrame:
    """One row per game: game_id, season, bin, p, created_at, puck_drop, level_k{k} (de-seasonalised)."""
    out = []
    r_prev = None
    last_drop = None
    for season in sorted(long.season.unique()):
        L = long[long.season == season]
        E = H = 0.0
        for d in np.sort(L.date.unique()):
            day = L[L.date == d]
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            g = day.groupby("game_id").agg(drop=("drop", "first")).reset_index()
            rec = pd.DataFrame({"game_id": g.game_id.to_numpy(), "season": season,
                                "bin": gbin.reindex(g.game_id).to_numpy(), "created_at": created,
                                "puck_drop": pd.to_datetime(g["drop"], utc=True)})
            rec["p"] = p[rec.bin.to_numpy()]
            for k in ks:
                rec[f"level_k{k}"] = 0.0 if r_prev is None else float(
                    np.log(((E + 2 * k * r_prev) / (H + 2 * k)) / r_prev))
            out.append(rec)
            b = gbin.reindex(day.game_id).to_numpy()
            E += float((day.taken.to_numpy() / np.exp(p[b])).sum())
            H += float(day.minutes.sum()) / 60.0
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        r_prev = E / H
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r
