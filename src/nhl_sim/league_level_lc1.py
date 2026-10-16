"""LC-1 league level (D16; SA-R2 and SS-R3c), shared by every cascade stage.

level(game) = log( shrunk ), the log of the ABSOLUTE as-of de-seasonalised league rate (events per team-hour):
  shrunk = (E + K r_prev) / (H + K)
  E = events of the CURRENT season in games with an earlier game date, each divided by exp(p(bin of its game))
      (de-seasonalised with the training-only season-phase profile p),
  H = team-hours of exposure of those games,
  r_prev = the previous season's final de-seasonalised rate (E / H over all of that season),
  K = 2 k x (exposure share): k league-games of prior; a league-game is two team-games of about one team-hour, so
      K = 2k team-hours for an all-state level (as SS-R2), and for a strength-group level K = 2k x the group's
      share of team-hours in the previous season (labelled reading of "strength k" for a group level).
It enters every arm as a fixed offset with coefficient 1 (with p(bin) added): cells and other terms are multipliers
on the current league level. No ratio to the previous season is used anywhere (L27).

First data season (2021-22, a training season in every fold, never a test season): there is no previous season, so
its prior r_prev is its OWN final de-seasonalised rate (labelled; a within-season look-ahead on training rows only).
created_at = 6 h after the last puck drop of the previous game date; callers assert created_at < puck_drop.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def lc1_level(long: pd.DataFrame, gbin: pd.Series, p: np.ndarray, ks, count_col: str = "taken",
              minutes_col: str = "minutes", prefix: str = "level", total_minutes_col: str | None = None) -> pd.DataFrame:
    """long: team-game rows (season, date, drop, game_id, <count_col>, <minutes_col>[, <total_minutes_col>]); a
    group level passes total_minutes_col so K is scaled by the group's exposure share. Returns one row per game:
    game_id, season, bin, p, created_at, puck_drop, <prefix>_k{k} (absolute log rate per team-hour), r_prev."""
    L0 = long.assign(_b=gbin.reindex(long.game_id).to_numpy())
    if L0._b.isna().any():
        raise ValueError("game without a season-phase bin")
    L0["_adj"] = L0[count_col].to_numpy(float) / np.exp(p[L0._b.astype(int).to_numpy()])
    L0["_h"] = L0[minutes_col].to_numpy(float) / 60.0
    seasons = sorted(L0.season.unique())
    final = {s: (L0[L0.season == s]._adj.sum() / L0[L0.season == s]._h.sum()) for s in seasons}
    share = {s: (L0[L0.season == s]._h.sum() / (L0[L0.season == s][total_minutes_col].sum() / 60.0)
                 if total_minutes_col else 1.0) for s in seasons}
    out = []
    last_drop = None
    for i, season in enumerate(seasons):
        prev = seasons[i - 1] if i > 0 else season          # first season: its own final rate (labelled)
        r_prev, sh = final[prev], share[prev]
        L = L0[L0.season == season]
        E = H = 0.0
        for d in np.sort(L.date.unique()):
            day = L[L.date == d]
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            g = day.groupby("game_id").agg(drop=("drop", "first"), _b=("_b", "first")).reset_index()
            rec = pd.DataFrame({"game_id": g.game_id.to_numpy(), "season": season, "bin": g._b.astype(int).to_numpy(),
                                "created_at": created, "puck_drop": pd.to_datetime(g["drop"], utc=True),
                                "r_prev": r_prev})
            rec["p"] = p[rec.bin.to_numpy()]
            for k in ks:
                K = 2.0 * k * sh
                rec[f"{prefix}_k{k}"] = float(np.log((E + K * r_prev) / (H + K)))
            out.append(rec)
            E += float(day._adj.sum())
            H += float(day._h.sum())
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r


def per_season_parity(seasons: np.ndarray, y: np.ndarray, mu: np.ndarray, tol: float = 0.005) -> pd.DataFrame:
    """LC-1 parity (D16): mean predicted rate equals the actual rate within tol in EACH training season separately.
    Rows share exposure, so predicted / actual counts per season is the rate ratio. Returns the table; the caller
    raises on a failure."""
    d = pd.DataFrame({"season": seasons, "y": y, "mu": mu}).groupby("season").sum()
    d["pred_over_actual_minus_1"] = d.mu / d.y - 1
    d["pass"] = d.pred_over_actual_minus_1.abs() <= tol
    return d
