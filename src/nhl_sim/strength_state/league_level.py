"""SS-R2 change 2: as-of in-season league penalty level (LEARNINGS L21).

level(game) = log( shrunk / r_prev ), where
  r_prev  = previous season's final league rate of penalty-taking events per team-hour (all game types),
  shrunk  = (E + 2 k r_prev) / (H + 2 k): E events and H team-hours of the CURRENT season in games with an earlier
            game date (strictly before this game's date), gamma-shrunk toward r_prev with strength k league-games
            (one league-game = 2 team-games of about one team-hour each).
It is a log ratio vs the previous season's final rate (a level relative to a league snapshot, never a raw level),
and every arm uses it as a fixed offset (coefficient 1): H0' = H0 cells x exp(level).
The first loadable season (2021-22) has no previous season: its level is 0 (no prior exists to measure drift
against). It is a training season in both folds, never a test season.
created_at = 6 h after the last puck drop of the previous game date; created_at < puck_drop is enforced.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def asof_league_level(long: pd.DataFrame, k: float) -> pd.DataFrame:
    """long: team-game rows (season, date, drop, game_id, taken, minutes), as team_game_<v>.parquet.
    Returns one row per game: game_id, season, level, r_prev, created_at, puck_drop."""
    out = []
    r_prev = None
    last_drop = None
    for season in sorted(long.season.unique()):
        L = long[long.season == season]
        E = H = 0.0
        for d in np.sort(L.date.unique()):
            day = L[L.date == d]
            if r_prev is None:
                lvl = 0.0
            else:
                lvl = float(np.log(((E + 2 * k * r_prev) / (H + 2 * k)) / r_prev))
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            g = day.groupby("game_id").agg(drop=("drop", "first")).reset_index()
            out.append(pd.DataFrame({"game_id": g.game_id.to_numpy(), "season": season, "level": lvl,
                                     "r_prev": np.nan if r_prev is None else r_prev, "created_at": created,
                                     "puck_drop": pd.to_datetime(g["drop"], utc=True)}))
            E += float(day.taken.sum())
            H += float(day.minutes.sum()) / 60.0
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        r_prev = E / H
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r
