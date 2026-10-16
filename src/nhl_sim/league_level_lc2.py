"""LC-2 league-level constructions for penalties (INV-33; docs/models/strength_state/experiments.md section LC-2).

All constructions return the log of an ABSOLUTE de-seasonalised league rate (events per team-hour, rate of the
profile-neutral season); the caller adds the profile p(bin) and enters the sum as a coefficient-1 offset.
Rate form (the "ratio estimator on profile-weighted exposure"): r = E_raw / sum(h * exp(p(bin))).

  L2c  prior only: r_prev constant all season
  L2a  (E_raw + K r_prev) / (Hp + K), K = 2k profile-weighted team-hours, undiscounted
  L2b  L2a with E_raw and Hp discounted by 0.5^(age_days / half_life); prior K = 2k (k = 5) not discounted
  O    oracle: the season's own final rate sum(E_raw) / sum(h exp(p)); diagnostic ceiling, never selectable
r_prev = previous season's final rate sum(E_raw)/sum(h exp(p)) (all games). First data season: its own final rate
(look-ahead, labelled). created_at = 6 h after the last puck drop of the previous game date.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def lc2_level(long: pd.DataFrame, gbin: pd.Series, p: np.ndarray, specs: dict,
              count_col: str = "taken", minutes_col: str = "minutes") -> pd.DataFrame:
    """specs: {column_name: (kind, param)}, kind in L2c, L2a (param k), L2b (param (half_life_days, k)), O.
    One row per game: game_id, season, bin, p, created_at, puck_drop, r_prev, <column_name> (log rate)."""
    L0 = long.assign(_b=gbin.reindex(long.game_id).to_numpy())
    if L0._b.isna().any():
        raise ValueError("game without a season-phase bin")
    L0["_e"] = L0[count_col].to_numpy(float)
    L0["_hp"] = L0[minutes_col].to_numpy(float) / 60.0 * np.exp(p[L0._b.astype(int).to_numpy()])
    seasons = sorted(L0.season.unique())
    final = {s: L0[L0.season == s]._e.sum() / L0[L0.season == s]._hp.sum() for s in seasons}
    out, last_drop = [], None
    for i, season in enumerate(seasons):
        r_prev = final[seasons[i - 1]] if i > 0 else final[season]       # first season: own final (labelled)
        L = L0[L0.season == season]
        st = {n: [0.0, 0.0] for n in specs}                                # undiscounted or discounted E, Hp
        prev_date = None
        for d in np.sort(L.date.unique()):
            day = L[L.date == d]
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            g = day.groupby("game_id").agg(drop=("drop", "first"), _b=("_b", "first")).reset_index()
            rec = pd.DataFrame({"game_id": g.game_id.to_numpy(), "season": season, "bin": g._b.astype(int).to_numpy(),
                                "created_at": created, "puck_drop": pd.to_datetime(g["drop"], utc=True),
                                "r_prev": r_prev})
            rec["p"] = p[rec.bin.to_numpy()]
            gap = 0.0 if prev_date is None else float((pd.Timestamp(d) - pd.Timestamp(prev_date)).days)
            for n, (kind, par) in specs.items():
                E, H = st[n]
                if kind == "L2c":
                    v = r_prev
                elif kind == "O":
                    v = final[season]
                elif kind == "L2a":
                    K = 2.0 * par
                    v = (E + K * r_prev) / (H + K)
                elif kind == "L2b":
                    hl, k = par
                    f = 0.5 ** (gap / hl)
                    E, H = E * f, H * f
                    st[n] = [E, H]
                    K = 2.0 * k
                    v = (E + K * r_prev) / (H + K)
                else:
                    raise ValueError(kind)
                rec[n] = float(np.log(v))
            for n in specs:
                st[n][0] += float(day._e.sum())
                st[n][1] += float(day._hp.sum())
            prev_date = d
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
            out.append(rec)
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r
