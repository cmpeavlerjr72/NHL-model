"""SS-R1 tables: hazard rows (game x team x interval), type rows (one per penalty-taking event), team-game
aggregates, and as-of team penalty ratings (gamma-Poisson shrinkage, season carry-over, league-mean centred).

Hazard-row state is the engine-replayed penalty strength (fold-1 replay agreement 99.99% gap-aware) plus the pbp
goalie state; every feature is the PRE-event state: a penalty at second t is counted in the row holding t-1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.strength_state.timeline import season_timeline

STRENGTH = ("5v5", "PP", "PK", "4v4", "3v3", "other")   # team view; "other" = a goalie pulled
SWAP = np.array([0, 2, 1, 3, 4, 5], np.int8)            # home-view code -> away-view code
MAX_ROW_S = 60
WHISTLE_EVENTS = ("STOPPAGE", "GOAL", "PENALTY", "PERIOD_START")


def _bucket(x):
    return (np.clip(x, -2, 2) + 2).astype(np.int8)       # 0..4 = <=-2, -1, 0, +1, >=+2


def season_rows(ev: pd.DataFrame):
    """One season (or subset) of events -> (rows, type_rows, team_game, tl). `rows` has two rows (home, away view)
    per interval."""
    tl = season_timeline(ev)
    games, sk, prev = tl["games"], tl["sk"], tl["prev"]
    N, T = sk.shape[:2]
    end = games.end_t.to_numpy()
    gi = {g: i for i, g in enumerate(games.game_id.to_numpy())}
    played = np.arange(T)[None, :] < end[:, None]
    gh, ga = prev[..., 3], prev[..., 0]
    skh, ska = sk[..., 0], sk[..., 1]
    st = np.full((N, T), 5, np.int8)
    goal_in = (gh == 1) & (ga == 1)
    eq = goal_in & (skh == ska)
    st[eq & (skh == 5)] = 0
    st[eq & (skh == 4)] = 3
    st[eq & (skh == 3)] = 4
    st[goal_in & (skh > ska)] = 1
    st[goal_in & (skh < ska)] = 2
    # post-event cumulative score and penalty counts at each second
    def cum(times, teams):
        a = np.zeros((N, T + 1, 2), np.int16)
        np.add.at(a, (times[0], np.minimum(times[1], T), teams), 1)
        return np.cumsum(a, axis=1)[:, :T]
    x = ev[(ev.event == "GOAL") & (ev.period_type != "SO")]
    g_i = x.game_id.map(gi).to_numpy()
    score = cum((g_i, x.game_time_s.to_numpy().astype(int)), np.where(x.owner_is_home.astype(bool), 0, 1))
    tg = tl["targets"]
    t_i = tg.game_id.map(gi).to_numpy()
    pens = cum((t_i, tg.t.to_numpy()), tg.team.to_numpy())
    sc_h = _bucket(score[..., 0].astype(np.int16) - score[..., 1])
    pd_h = _bucket(pens[..., 0].astype(np.int16) - pens[..., 1])
    sec = np.arange(T)
    gt = games.game_type.to_numpy()
    per = np.where(sec[None, :] < 3600, sec[None, :] // 1200 + 1, 4).astype(np.int8).repeat(N, 0) if N else None
    last5 = ((sec >= 3300) & (sec < 3600))[None, :].repeat(N, 0)
    wh = np.zeros((N, T), bool)
    w = ev[ev.event.isin(WHISTLE_EVENTS) & (ev.period_type != "SO")]
    wi, wt = w.game_id.map(gi).to_numpy(), w.game_time_s.to_numpy().astype(int)
    ok = wt < T
    wh[wi[ok], wt[ok]] = True
    key = (st.astype(np.int32) * 10000 + sc_h.astype(np.int32) * 1000 + pd_h.astype(np.int32) * 100
           + per.astype(np.int32) * 10 + last5)
    brk = np.ones((N, T), bool)
    brk[:, 1:] = (key[:, 1:] != key[:, :-1]) | wh[:, 1:]
    # 60 s maximum: cut on the fixed game-clock minute grid (NOT relative to the run start). A run-relative
    # chunking makes row boundaries depend on event times, and any within-run clock feature then leaks the row
    # length (an event ends its row at the whistle); see the SS-R1 report, "row-construction leak".
    brk[:, sec % MAX_ROW_S == 0] = True
    # flatten played seconds
    ii, ss = np.nonzero(played)
    b = brk[ii, ss]
    run = np.cumsum(b) - 1
    rid = run.astype(np.int64)
    nrow = rid.max() + 1
    row_id_grid = np.full((N, T), -1, np.int64)
    row_id_grid[ii, ss] = rid
    _, first = np.unique(rid, return_index=True)
    expo = np.bincount(rid, minlength=nrow)
    fi, fs = ii[first], ss[first]
    R = pd.DataFrame({"game_id": games.game_id.to_numpy()[fi], "season": games.season.to_numpy()[fi],
                      "game_type": gt[fi], "t0": fs.astype(np.int32), "exposure_s": expo.astype(np.int32),
                      "st_h": st[fi, fs], "sc_h": sc_h[fi, fs], "pd_h": pd_h[fi, fs], "period": per[fi, fs],
                      "last5": last5[fi, fs]})
    R["row"] = np.arange(nrow)
    # assign penalty-taking events to the pre-event row (the row holding second t-1)
    tt = np.clip(tg.t.to_numpy() - 1, 0, None)
    tt = np.minimum(tt, end[t_i] - 1)
    ev_row = row_id_grid[t_i, tt]
    if (ev_row < 0).any():
        raise ValueError("penalty event outside the played timeline")
    tg = tg.assign(row=ev_row)
    cnt = np.zeros((nrow, 2), np.int32)
    np.add.at(cnt, (ev_row, tg.team.to_numpy()), 1)
    home = R.assign(team=0, is_home=1, st=R.st_h, sc=R.sc_h, pdiff=R.pd_h, y=cnt[:, 0])
    away = R.assign(team=1, is_home=0, st=SWAP[R.st_h.to_numpy()], sc=(4 - R.sc_h).astype(np.int8),
                    pdiff=(4 - R.pd_h).astype(np.int8), y=cnt[:, 1])
    rows = pd.concat([home, away], ignore_index=True).drop(columns=["st_h", "sc_h", "pd_h"])
    rows["ptype"] = (rows.period == 4).astype(np.int8)  # 0 REG, 1 OT
    # type rows: team-view features of the row each event fell in
    rv = R.set_index("row")
    trow = rv.loc[tg.row.to_numpy()]
    st_t = np.where(tg.team.to_numpy() == 0, trow.st_h.to_numpy(), SWAP[trow.st_h.to_numpy()])
    sc_t = np.where(tg.team.to_numpy() == 0, trow.sc_h.to_numpy(), 4 - trow.sc_h.to_numpy())
    types = tg.assign(st=st_t.astype(np.int8), sc=sc_t.astype(np.int8), period=trow.period.to_numpy())
    # team-game aggregates for ratings
    taken = tg.groupby(["game_id", "team"]).size().unstack(fill_value=0).reindex(games.game_id, fill_value=0)
    for c in (0, 1):
        if c not in taken.columns:
            taken[c] = 0
    tgm = games[["game_id", "season", "game_type", "end_t"]].copy()
    tgm["pen_h"], tgm["pen_a"] = taken[0].to_numpy(), taken[1].to_numpy()
    tgm["minutes"] = tgm.end_t / 60.0
    return rows, types, tgm, tl


# --------------------------------------------------------------------------- ratings
def team_game_long(tgm: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """One row per team-game: team_id, date, taken, drawn, minutes."""
    g = tgm.merge(games[["game_id", "game_date_local", "puck_drop_utc", "home_id", "away_id"]], on="game_id")
    h = pd.DataFrame({"game_id": g.game_id, "season": g.season, "date": g.game_date_local, "drop": g.puck_drop_utc,
                      "team_id": g.home_id, "opp_id": g.away_id, "taken": g.pen_h, "drawn": g.pen_a,
                      "minutes": g.minutes, "is_home": 1})
    a = pd.DataFrame({"game_id": g.game_id, "season": g.season, "date": g.game_date_local, "drop": g.puck_drop_utc,
                      "team_id": g.away_id, "opp_id": g.home_id, "taken": g.pen_a, "drawn": g.pen_h,
                      "minutes": g.minutes, "is_home": 0})
    return pd.concat([h, a], ignore_index=True).sort_values(["date", "game_id"]).reset_index(drop=True)


def asof_ratings(long: pd.DataFrame, w: float, b: float) -> pd.DataFrame:
    """As-of ratings per (game, team): log rates relative to the snapshot league mean (L1).
    Uses only games with an earlier game date in the same season, plus the prior (last season's final relative
    value times w, at prior strength b team-minutes). Returns game_id, team_id, taken_rel, drawn_rel, created_at."""
    out = []
    prev_final = {"taken": {}, "drawn": {}}
    last_drop = None
    for season in sorted(long.season.unique()):
        L = long[long.season == season]
        teams = np.sort(L.team_id.unique())
        tix = {t: i for i, t in enumerate(teams)}
        dates = np.sort(L.date.unique())
        K = {k: np.zeros(len(teams)) for k in ("taken", "drawn")}
        M = np.zeros(len(teams))
        prior_rel = {k: np.array([prev_final[k].get(t, 0.0) for t in teams]) for k in ("taken", "drawn")}

        def snapshot():
            res = {}
            for k in ("taken", "drawn"):
                lg = K[k].sum() / M.sum() if M.sum() > 0 else 1.0
                mu = lg * np.exp(w * prior_rel[k])
                r = np.log((K[k] + b * mu) / (M + b))
                res[k] = r - r.mean()
            return res

        for d in dates:
            snap = snapshot()
            day = L[L.date == d]
            ti = day.team_id.map(tix).to_numpy()
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            out.append(pd.DataFrame({"game_id": day.game_id.to_numpy(), "team_id": day.team_id.to_numpy(),
                                     "taken_rel": snap["taken"][ti], "drawn_rel": snap["drawn"][ti],
                                     "created_at": created, "puck_drop": pd.to_datetime(day["drop"], utc=True)}))
            np.add.at(K["taken"], ti, day.taken.to_numpy())
            np.add.at(K["drawn"], ti, day.drawn.to_numpy())
            np.add.at(M, ti, day.minutes.to_numpy())
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        fin = snapshot()
        prev_final = {k: dict(zip(teams, fin[k])) for k in ("taken", "drawn")}
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r


def assert_pregame(r: pd.DataFrame) -> None:
    """created_at < puck_drop on every row with a created_at (season-opening rows use only the prior)."""
    m = r.created_at.notna()
    bad = m & ~(r.created_at < r.puck_drop)
    if bad.any():
        raise AssertionError(f"{int(bad.sum())} rating rows violate created_at < puck_drop")
