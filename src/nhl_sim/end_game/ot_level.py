"""EG-R1 part B (INV-35): the own as-of 3v3 attempt level for regular-season overtime.

Rows: stage-3 attempt rows (`data/processed/shot_attempt/attempt_rows_v1_<season>.parquet`) in the team-view 3v3
state (st == 4), regular season. Both team views are used: counts are team-attempts, exposure is team-hours, so the
level is attempts per TEAM-hour (per 60 combined = 2x). 3v3 exists only in regular-season OT (playoff OT is 5v5).

Constructions (one value per game, from games dated strictly EARLIER; created_at = 6 h after the last puck drop of
the previous game date, asserted < puck_drop). K is a prior in ATTEMPTS at the previous season's final rate r_prev
(the block / goal / miss M1 form):
  M1_K   shrunk = (n + K) / (h + K / r_prev), n, h the season-to-date 3v3 attempts and team-hours
  M2_H   M1 with K = 2000 and n, h discounted by 0.5^(gap days / H) at each date (the LC-2 / SL-R2 form)
  E      era intercept: pooled rate of the fold's TRAINING rows of the game's recording era (reported, never
         selectable, D35); an era without training rows falls back to the pooled training rate (labelled)
  O      oracle: the season's own final 3v3 rate (diagnostic, never selectable)
r_prev for the first data season (2021-22) is its own final rate (look-ahead, labelled; never judged).
No season-phase profile is applied (3v3 time is a few minutes in a small share of games; a profile is not identifiable).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED, load_games
from nhl_sim.engine.rules import recording_era

SA = PROCESSED / "shot_attempt"
ST_3V3 = 4
SIMPLICITY = ("M1_K2000", "M1_K500", "M2_H30")   # selection order, simplest first (larger K = nearer the prior-only level)
GRID = {"M1_K500": ("M1", 500.0), "M1_K2000": ("M1", 2000.0), "M2_H30": ("M2", (30.0, 2000.0))}
TOL = 0.005                                       # SA-R2 parity limit (relative), per judged season
TIE = 0.001                                       # ties within 0.1 pp go to the simpler arm
JUDGED = {1: [20222023], 2: [20222023, 20232024]}  # genuine-prior training seasons by fold
TRAIN = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}


def game_table(seasons) -> pd.DataFrame:
    """One row per game (all game types): game_id, season, game_type, date (str), drop (UTC), in date order."""
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet",
                         columns=["game_id", "season", "date", "drop"])
    tg = tg[tg.season.isin(seasons)].drop_duplicates("game_id")
    gm = load_games(list(seasons), columns=["game_id", "game_type"])
    g = tg.merge(gm.drop(columns="season", errors="ignore"), on="game_id", how="left", validate="one_to_one")
    return g.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)


def load_rows(seasons) -> pd.DataFrame:
    """Regular-season 3v3 rows (team view, both teams): game_id, season, y, y_goal, exposure_s."""
    out = []
    for s in seasons:
        r = pd.read_parquet(SA / f"attempt_rows_v1_{s}.parquet",
                            columns=["game_id", "season", "game_type", "st", "y", "y_goal", "exposure_s", "is_home",
                                     "period"])
        out.append(r[(r.st == ST_3V3) & (r.game_type == 2)].drop(columns="game_type"))
    return pd.concat(out, ignore_index=True)


def game_counts(rows: pd.DataFrame, games: pd.DataFrame):
    """-> (n attempts, h team-hours) per game in `games` order."""
    gi = pd.Series(np.arange(len(games)), index=games.game_id.to_numpy())
    ix = gi.reindex(rows.game_id.to_numpy()).to_numpy()
    if np.isnan(ix.astype(float)).any():
        raise ValueError("3v3 rows for a game missing from the game list")
    ix = ix.astype(np.int64)
    n = np.bincount(ix, weights=rows.y.to_numpy(float), minlength=len(games))
    h = np.bincount(ix, weights=rows.exposure_s.to_numpy(float) / 3600.0, minlength=len(games))
    return n, h


def assert_pregame(meta: pd.DataFrame) -> None:
    """created_at < puck_drop on every game that has a created_at (the first game of the data has none: prior only)."""
    m = meta.created_at.notna()
    if not (meta.created_at[m] < meta.puck_drop[m]).all():
        raise AssertionError("level created_at is not before puck drop")


def asof_levels(rows: pd.DataFrame, games: pd.DataFrame, specs: dict, train_seasons=None):
    """specs {name: (kind, param)}, kind M1 (K) / M2 ((half_life, K)) / E / O. -> (meta, {name: (G,) attempts per
    team-hour}), games in date order. E needs train_seasons."""
    games = games.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)
    n, h = game_counts(rows, games)
    seasons = sorted(games.season.unique())
    gs = games.season.to_numpy()
    final = {s: n[gs == s].sum() / h[gs == s].sum() for s in seasons}
    out = {k: np.zeros(len(games)) for k in specs}
    created = np.full(len(games), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    last_drop = None
    era_of = {s: recording_era(s) for s in seasons}
    if any(v[0] == "E" for v in specs.values()):
        tr = [s for s in seasons if s in set(train_seasons)]
        pooled = sum(n[gs == s].sum() for s in tr) / sum(h[gs == s].sum() for s in tr)
        era_rate = {}
        for e in (1, 2):
            ss = [s for s in tr if era_of[s] == e]
            era_rate[e] = (sum(n[gs == s].sum() for s in ss) / sum(h[gs == s].sum() for s in ss)) if ss else pooled
    for i, season in enumerate(seasons):
        r_prev = final[seasons[i - 1]] if i > 0 else final[season]
        idx_s = np.flatnonzero(gs == season)
        dates = games.date.to_numpy()[idx_s]
        st = {k: [0.0, 0.0] for k in specs}
        prev_date = None
        for d in np.unique(dates):
            ix = idx_s[dates == d]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            gap = 0.0 if prev_date is None else float((pd.Timestamp(d) - pd.Timestamp(prev_date)).days)
            for k, (kind, par) in specs.items():
                sn, sh = st[k]
                if kind == "O":
                    v = final[season]
                elif kind == "E":
                    v = era_rate[era_of[season]]
                elif kind == "M1":
                    v = (sn + par) / (sh + par / r_prev)
                elif kind == "M2":
                    hl, K = par
                    f = 0.5 ** (gap / hl)
                    sn, sh = sn * f, sh * f
                    st[k] = [sn, sh]
                    v = (sn + K) / (sh + K / r_prev)
                else:
                    raise ValueError(kind)
                out[k][ix] = v
            for k in specs:
                st[k] = [st[k][0] + n[ix].sum(), st[k][1] + h[ix].sum()]
            prev_date = d
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": gs, "game_type": games.game_type.to_numpy(),
                         "created_at": pd.to_datetime(created).tz_localize("UTC"),
                         "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    assert_pregame(meta)
    return meta, out


def level_parity(rows: pd.DataFrame, meta: pd.DataFrame, lev: dict, seasons) -> pd.DataFrame:
    """Per season and construction: predicted 3v3 attempts (level x exposure) over actual - 1 (rows share exposure)."""
    gi = pd.Series(np.arange(len(meta)), index=meta.game_id.to_numpy())
    r = rows[rows.season.isin(seasons)]
    ix = gi.reindex(r.game_id.to_numpy()).to_numpy().astype(np.int64)
    hh = r.exposure_s.to_numpy(float) / 3600.0
    out = []
    for s in seasons:
        m = (r.season == s).to_numpy()
        y = r.y.to_numpy(float)[m].sum()
        for k, v in lev.items():
            mu = (v[ix[m]] * hh[m]).sum()
            out.append(dict(season=s, level=k, actual=y, predicted=mu, parity=mu / y - 1.0,
                            team_hours=hh[m].sum(), games_with_3v3=int(r[m].game_id.nunique())))
    return pd.DataFrame(out)


def select_level(par: pd.DataFrame, judged, candidates=SIMPLICITY, tol=TOL, tie=TIE) -> dict:
    """SA-R2 / LC-2 rule: the simplest candidate whose |parity| <= tol in EVERY judged season; if none passes, the
    smallest max |parity|, ties within `tie` going to the simpler. E and O are never candidates."""
    mx = {k: float(par[(par.level == k) & par.season.isin(judged)].parity.abs().max()) for k in candidates}
    passing = [k for k in candidates if mx[k] <= tol]
    if passing:
        return dict(selected=passing[0], how="simplest passer", max_abs_parity=mx)
    best = min(mx.values())
    sel = next(k for k in candidates if mx[k] <= best + tie)
    return dict(selected=sel, how="fallback: smallest max |parity|, ties within 0.1 pp to the simpler "
                                  "(no construction passes)", max_abs_parity=mx)
