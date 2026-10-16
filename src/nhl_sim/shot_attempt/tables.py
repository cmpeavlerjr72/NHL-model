"""SA-R1 tables (cascade stage 3, shot-attempt generation): attempt rows, team-game aggregates per strength group,
as-of attempt ratings, league level / season-phase profile inputs, and the as-of arena recording factor.

Rows: one per (game, team, interval) on the fixed one-minute game-clock grid, cut at every change of the PRE-event
strength state (7 team-view levels), score-diff bucket (7 levels), period and last-5-min-of-3rd flag. Strength is
the engine replay of the real penalties (Lane H, `strength_state.timeline`) plus the pbp goalie state, with the
delayed-penalty convention of L20 (`strength_state.delayed`): the seconds of a delayed-penalty signal window keep
the pre-signal goalie state. An attempt at second t is counted in the row holding second t-1 (pre-event state;
the Lane H convention for penalties).

Target: shot attempts (SHOT, MISS, BLOCK, GOAL) owned by the shooting team (L15; owner == shooting team is
asserted). Penalty shots (pbp situation code 0101 / 1010 outside the shootout) and shootout attempts are excluded
and tallied. Every event type must be in the explicit map below or the builder raises (L5).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.pbp.event_map import EVENT_MAP, SHOT_ATTEMPT_TYPES
from nhl_sim.strength_state.delayed import apply_delayed_fix, delayed_windows
from nhl_sim.strength_state.timeline import EV_COLS, season_timeline

SA_EV_COLS = EV_COLS + ["type_desc_key", "shooting_team_id", "owner_team_id"]
ST_NAMES = ("5v5", "PP", "PK", "4v4", "3v3", "EN-for", "EN-against")
N_ST = len(ST_NAMES)
SC_NAMES = ("<=-3", "-2", "-1", "0", "+1", "+2", ">=+3")
N_SC = len(SC_NAMES)
GROUP_OF_ST = np.array([0, 1, 2, 0, 0, 0, 0], np.int8)   # rating group: 0 ES, 1 PP, 2 PK (EN rows use ES, labelled)
GROUPS = ("es", "pp", "pk")
# explicit attempt-type map: canonical event -> pbp typeDescKey. An attempt row whose (event, typeDescKey) is not
# here, or any event type absent from EVENT_MAP's canonical values, raises.
ATTEMPT_TYPE_MAP = {"SHOT": "shot-on-goal", "MISS": "missed-shot", "BLOCK": "blocked-shot", "GOAL": "goal"}
KNOWN_EVENTS = {v[0] for v in EVENT_MAP.values()}
PS_CODES = ("0101", "1010")
MAX_ROW_S = 60
assert set(ATTEMPT_TYPE_MAP) == set(SHOT_ATTEMPT_TYPES)


class UnmappedAttemptEvent(ValueError):
    pass


def check_event_types(ev: pd.DataFrame) -> None:
    bad = set(ev.event.dropna().unique()) - KNOWN_EVENTS
    if bad or ev.event.isna().any():
        raise UnmappedAttemptEvent(f"unmapped event types: {sorted(map(str, bad))} (NaN: {bool(ev.event.isna().any())})")
    a = ev[ev.event.isin(SHOT_ATTEMPT_TYPES)]
    exp = a.event.map(ATTEMPT_TYPE_MAP)
    if (exp != a.type_desc_key).any():
        x = a[exp != a.type_desc_key][["event", "type_desc_key"]].drop_duplicates()
        raise UnmappedAttemptEvent(f"attempt event / typeDescKey combination not in the map: {x.values.tolist()}")


def attempt_events(ev: pd.DataFrame):
    """-> (targets frame game_id, t, team (0 home / 1 away), is_goal, event), tally dict of exclusions."""
    check_event_types(ev)
    a = ev[ev.event.isin(SHOT_ATTEMPT_TYPES)]
    so = a.period_type == "SO"
    ps = ~so & a.situation_code.isin(PS_CODES)
    x = a[~so & ~ps]
    if x.owner_is_home.isna().any():
        raise ValueError("attempt without an owner team")
    if "shooting_team_id" in x.columns and (x.shooting_team_id != x.owner_team_id).any():
        raise ValueError("attempt owner differs from shooting team")
    tg = pd.DataFrame({"game_id": x.game_id.to_numpy(), "t": x.game_time_s.to_numpy().astype(np.int64),
                       "team": np.where(x.owner_is_home.astype(bool), 0, 1), "is_goal": (x.event == "GOAL").to_numpy(),
                       "event": x.event.to_numpy()})
    tally = {"shootout_attempts": int(so.sum()), "penalty_shot_attempts": int(ps.sum()),
             "penalty_shot_goals": int((ps & (a.event == "GOAL")).sum()),
             "failed_shot_attempt_events": int((ev.event == "FAILED_SHOT_ATTEMPT").sum()),
             "target_attempts": int(len(tg))}
    return tg, tally


def team_view_st(sk: np.ndarray, prev: np.ndarray):
    """(N,T) home-view and away-view 7-level strength from engine skaters (N,T,2) and pbp goalie digits."""
    hg, ag = prev[..., 3], prev[..., 0]
    skh, ska = sk[..., 0], sk[..., 1]
    base = np.full(skh.shape, 0, np.int8)
    eq = skh == ska
    base[eq & (skh == 4)] = 3
    base[eq & (skh == 3)] = 4
    base[skh > ska] = 1
    base[skh < ska] = 2
    swap = np.array([0, 2, 1, 3, 4], np.int8)
    st_h = base.copy()
    st_a = swap[base]
    hp, ap = hg == 0, ag == 0
    st_h[hp & ~ap], st_a[hp & ~ap] = 5, 6
    st_h[ap & ~hp], st_a[ap & ~hp] = 6, 5
    st_h[hp & ap], st_a[hp & ap] = 5, 5          # both goalies out (rare): EN-for for both, labelled
    return st_h, st_a


def sc_bucket(diff):
    return (np.clip(diff, -3, 3) + 3).astype(np.int8)


def season_rows(ev: pd.DataFrame, delayed_fix: bool = True):
    """One season (or subset) of events -> (rows, team_game, tally, info). rows: two rows (home view, away view) per
    interval with y (attempts), y_goal, exposure_s, st, sc, period, ptype, last5, is_home, team."""
    ev = ev.sort_values(["game_id", "sort_order"]).reset_index(drop=True)
    tg, tally = attempt_events(ev)
    tl = season_timeline(ev)
    games, sk, prev = tl["games"], tl["sk"], tl["prev"]
    changed = 0
    if delayed_fix:
        win = delayed_windows(ev, games.game_id.to_numpy())
        prev, changed = apply_delayed_fix(prev, win)
    N, T = sk.shape[:2]
    end = games.end_t.to_numpy()
    gi = {g: i for i, g in enumerate(games.game_id.to_numpy())}
    played = np.arange(T)[None, :] < end[:, None]
    st_h, st_a = team_view_st(sk, prev)
    x = ev[(ev.event == "GOAL") & (ev.period_type != "SO")]
    a = np.zeros((N, T + 1, 2), np.int16)
    np.add.at(a, (x.game_id.map(gi).to_numpy(), np.minimum(x.game_time_s.to_numpy().astype(int), T),
                  np.where(x.owner_is_home.astype(bool), 0, 1)), 1)
    score = np.cumsum(a, axis=1)[:, :T]
    sc_h = sc_bucket(score[..., 0].astype(np.int16) - score[..., 1])
    sec = np.arange(T)
    per = np.broadcast_to(np.where(sec < 3600, sec // 1200 + 1, 4).astype(np.int8), (N, T))
    last5 = np.broadcast_to(((sec >= 3300) & (sec < 3600)), (N, T))
    key = st_h.astype(np.int32) * 1000 + st_a.astype(np.int32) * 100 + sc_h.astype(np.int32) * 10 + per * 2 + last5
    brk = np.ones((N, T), bool)
    brk[:, 1:] = key[:, 1:] != key[:, :-1]
    brk[:, sec % MAX_ROW_S == 0] = True
    ii, ss = np.nonzero(played)
    rid = (np.cumsum(brk[ii, ss]) - 1).astype(np.int64)
    nrow = int(rid.max()) + 1
    grid = np.full((N, T), -1, np.int64)
    grid[ii, ss] = rid
    _, first = np.unique(rid, return_index=True)
    expo = np.bincount(rid, minlength=nrow)
    fi, fs = ii[first], ss[first]
    t_i = tg.game_id.map(gi).to_numpy()
    if np.isnan(t_i.astype(float)).any():
        raise ValueError("attempt in a game without a timeline")
    t_i = t_i.astype(np.int64)
    tt = np.minimum(np.clip(tg.t.to_numpy() - 1, 0, None), end[t_i] - 1)
    ev_row = grid[t_i, tt]
    if (ev_row < 0).any():
        raise ValueError("attempt outside the played timeline")
    cnt = np.zeros((nrow, 2), np.int32)
    gcnt = np.zeros((nrow, 2), np.int32)
    np.add.at(cnt, (ev_row, tg.team.to_numpy()), 1)
    np.add.at(gcnt, (ev_row, tg.team.to_numpy()), tg.is_goal.to_numpy().astype(np.int32))
    R = pd.DataFrame({"game_id": games.game_id.to_numpy()[fi], "season": games.season.to_numpy()[fi],
                      "game_type": games.game_type.to_numpy()[fi], "t0": fs.astype(np.int32),
                      "exposure_s": expo.astype(np.int32), "period": per[fi, fs], "last5": last5[fi, fs].astype(np.int8)})
    R["ptype"] = (R.period == 4).astype(np.int8)
    R["row"] = np.arange(nrow)
    home = R.assign(team=np.int8(0), is_home=np.int8(1), st=st_h[fi, fs], sc=sc_h[fi, fs], y=cnt[:, 0],
                    y_goal=gcnt[:, 0], y_opp=cnt[:, 1])
    away = R.assign(team=np.int8(1), is_home=np.int8(0), st=st_a[fi, fs], sc=(6 - sc_h[fi, fs]).astype(np.int8),
                    y=cnt[:, 1], y_goal=gcnt[:, 1], y_opp=cnt[:, 0])
    rows = pd.concat([home, away], ignore_index=True)
    if int(rows.y.sum()) != len(tg):
        raise AssertionError("attempt count mismatch")
    info = dict(delayed_changed_s=int(changed), n_games=int(N), both_pulled_s=int(((st_h == 5) & (st_a == 5) & played).sum()))
    return rows, team_game(rows, games), tally, info


def team_game(rows: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Per (game, team): attempts for / against and minutes per rating group (goalies in), totals."""
    r = rows.assign(grp=np.where(rows.st <= 4, GROUP_OF_ST[rows.st.clip(0, 6).to_numpy()], -1),
                    m=rows.exposure_s / 60.0)
    out = r.groupby(["game_id", "team"]).agg(att=("y", "sum"), att_against=("y_opp", "sum"), minutes=("m", "sum"))
    for k, g in enumerate(GROUPS):
        s = r[r.grp == k].groupby(["game_id", "team"]).agg(f=("y", "sum"), a=("y_opp", "sum"), m=("m", "sum"))
        s.columns = [f"for_{g}", f"against_{g}", f"min_{g}"]
        out = out.join(s, how="left")
    out = out.fillna(0.0).reset_index()
    return out.merge(games[["game_id", "season", "game_type"]], on="game_id", how="left")


# --------------------------------------------------------------------------- arena recording factor (A5)
def arena_key(games: pd.DataFrame) -> pd.Series:
    """Arena = home team id for normal games; neutral-site games use their venue string (labelled choice)."""
    g = games.drop_duplicates("game_id").set_index("game_id")
    return pd.Series(np.where(g.neutral_site.astype(bool), "venue:" + g.venue.astype(str),
                              "team:" + g.home_id.astype(str)), index=g.index)


def asof_arena_factor(tgm: pd.DataFrame, ratings: pd.DataFrame, games: pd.DataFrame, c: float) -> pd.DataFrame:
    """As-of arena recording factor per game: log((A + c) / (E + c)) over ALL earlier-dated games at the arena
    (this season to date and every earlier season in the data), A = total attempts recorded (both teams, goalies-in
    rating groups), E = attempts expected from both teams' as-of ratings:
      E_game = sum_team sum_g minutes_g x R_g x exp(for_g(team) + against_g'(opp)),  g' = ES/PK/PP for g = ES/PP/PK,
    with R_g the league rate of group g of that game's season, using only games dated before the factor's game
    (season to date for the current season; full season for earlier seasons). c = prior pseudo-attempts.
    tgm: team_game rows (+ team_id, opp_id, date, drop); ratings: per (game, team) rf_<g>, ra_<g> (relative log
    rates for / against in group g at the frozen grid point).
    Returns game_id, arena, arena_f, created_at, puck_drop."""
    opp_of = {"es": "es", "pp": "pk", "pk": "pp"}
    d = tgm.merge(ratings, on=["game_id", "team_id"], how="left", validate="one_to_one")
    o = ratings.rename(columns={"team_id": "opp_id", **{f"{p}_{g}": f"opp_{p}_{g}" for p in ("rf", "ra")
                                                         for g in GROUPS}})
    d = d.merge(o, on=["game_id", "opp_id"], how="left", validate="one_to_one")
    for g in GROUPS:
        d[f"x_{g}"] = d[f"min_{g}"] * np.exp(d[f"rf_{g}"] + d[f"opp_ra_{opp_of[g]}"])
    if d[[f"x_{g}" for g in GROUPS]].isna().any().any():
        raise ValueError("missing rating in the arena factor")
    ak = arena_key(games)
    d["arena"] = d.game_id.map(ak)
    gsum = d.groupby("game_id").agg(season=("season", "first"), date=("date", "first"), arena=("arena", "first"),
                                    drop=("drop", "first"), A=("att", "sum"),
                                    **{f"x_{g}": (f"x_{g}", "sum") for g in GROUPS},
                                    **{f"f_{g}": (f"for_{g}", "sum") for g in GROUPS},
                                    **{f"m_{g}": (f"min_{g}", "sum") for g in GROUPS}).reset_index()
    gsum["A"] = gsum[[f"f_{g}" for g in GROUPS]].sum(1)            # goalies-in attempts only
    arenas = np.sort(gsum.arena.unique())
    ai = {a: i for i, a in enumerate(arenas)}
    gsum["ai"] = gsum.arena.map(ai)
    A_prev = np.zeros(len(arenas))
    E_prev = np.zeros(len(arenas))
    out = []
    last_drop = None
    R_prev_season = None
    for season in sorted(gsum.season.unique()):
        S = gsum[gsum.season == season].sort_values(["date", "game_id"])
        A_cur = np.zeros(len(arenas))
        X_cur = np.zeros((len(arenas), 3))
        F = np.zeros(3)
        Mn = np.zeros(3)
        for dte in np.sort(S.date.unique()):
            day = S[S.date == dte]
            R = np.where(Mn > 0, F / np.maximum(Mn, 1e-9), np.nan)
            if np.isnan(R).any():
                R = R_prev_season if R_prev_season is not None else np.zeros(3)
            E_cur = X_cur @ R
            A_tot, E_tot = A_prev + A_cur, E_prev + E_cur
            fac = np.log((A_tot + c) / (E_tot + c))
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            out.append(pd.DataFrame({"game_id": day.game_id.to_numpy(), "arena": day.arena.to_numpy(),
                                     "arena_f": fac[day.ai.to_numpy()], "n_prior_attempts": A_tot[day.ai.to_numpy()],
                                     "created_at": created, "puck_drop": pd.to_datetime(day["drop"], utc=True)}))
            np.add.at(A_cur, day.ai.to_numpy(), day.A.to_numpy())
            np.add.at(X_cur, day.ai.to_numpy(), day[[f"x_{g}" for g in GROUPS]].to_numpy())
            F += day[[f"f_{g}" for g in GROUPS]].sum().to_numpy()
            Mn += day[[f"m_{g}" for g in GROUPS]].sum().to_numpy()      # team-minutes (both teams)
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        R_full = F / Mn
        A_prev += A_cur
        E_prev += X_cur @ R_full
        R_prev_season = R_full
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r
