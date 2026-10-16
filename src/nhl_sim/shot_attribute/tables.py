"""SL-R1 tables (cascade stage 4, shot location x type; docs/models/shot_attribute/experiments.md SL-R1).

Step 0 ruled blocks rule (b): the target is UNBLOCKED attempts (SHOT, MISS, GOAL); blocked attempts carry no location
(their coordinates are block points) and no type. Rows still include blocks (flag `blocked`) so the stage-5 block stub
and the rebound / rush segment flags can see them.

Per attempt: the PRE-event stage-1 strength state, exactly as the stage-3 attempt rows (`shot_attempt.tables
.season_rows`): engine replay of real penalties + pbp goalie state with the L20 delayed-penalty fix, read at second
t - 1 (an attempt at t is counted in the row holding t - 1); score bucket from goals at seconds <= t - 1.

Location cell (shooting team's frame, L14; goal-line centre (89, 0)): distance bands {0-10, 10-20, 20-30, 30-45, 45-64,
>64 ft} x |angle| {<= 30, > 30 deg} = cells 0..11 (cell = 2 * band + (angle > 30)); cell 12 = behind the goal line
(sx > 89). Type: six classes (wrist + snap, slap, backhand, tip-in + deflected, wrap-around, other; a missing type on
an unblocked attempt -> other, labelled). Joint class = cell * 6 + type (78).
Strength group (5): ES (5v5 + 4v4 + 3v3), PP-for, PK, EN-for, EN-against (team view, pre-event).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attempt.tables import PS_CODES, attempt_events, sc_bucket, team_view_st
from nhl_sim.strength_state.delayed import apply_delayed_fix, delayed_windows
from nhl_sim.strength_state.timeline import EV_COLS, season_timeline

GOAL_X = 89.0
BANDS = (10.0, 20.0, 30.0, 45.0, 64.0)
CELL_NAMES = tuple(f"{lo}-{hi}{a}" for lo, hi in zip((0, 10, 20, 30, 45, 64), (10, 20, 30, 45, 64, "+"))
                   for a in ("n", "w")) + ("behind",)
N_CELL = 13
TYPE_NAMES = ("wrist+snap", "slap", "backhand", "tip+defl", "wrap", "other")
N_TYPE = 6
N_CLASS = N_CELL * N_TYPE
TYPE_MAP = {"wrist": 0, "snap": 0, "slap": 1, "backhand": 2, "tip-in": 3, "deflected": 3, "wrap-around": 4,
            "poke": 5, "bat": 5, "between-legs": 5, "cradle": 5}
KNOWN_TYPES = set(TYPE_MAP)
GROUP_NAMES = ("ES", "PP", "PK", "ENF", "ENA")
GROUP_OF_ST = np.array([0, 1, 2, 0, 0, 3, 4], np.int8)     # team-view st 0..6 -> group
RATING_GROUP = np.array([0, 1, 2, 0, 0], np.int8)           # group -> rating group ES/PP/PK (EN uses ES, labelled)
OPP_RATING_GROUP = np.array([0, 2, 1], np.int8)
# location tiers: high = inside 20 ft and <= 30 deg (cells 0, 2); medium = 20-45 ft (cells 4..7); low = the rest
TIER_OF_CELL = np.array([0, 2, 0, 2, 1, 1, 1, 1, 2, 2, 2, 2, 2], np.int8)
TIER_NAMES = ("high", "medium", "low")
STOP_EVENTS = {"STOPPAGE", "FACEOFF", "GOAL", "PENALTY", "PERIOD_START", "PERIOD_END", "GAME_END"}
ATTR_EV_COLS = sorted(set(EV_COLS) | {"type_desc_key", "shooting_team_id", "owner_team_id", "sx", "sy", "shot_type",
                                      "zone", "shooter_id"})


class UnknownShotType(ValueError):
    pass


def cell_of(sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    sx, sy = np.asarray(sx, float), np.asarray(sy, float)
    if np.isnan(sx).any() or np.isnan(sy).any():
        raise ValueError("unblocked attempt without coordinates")
    dx = GOAL_X - sx
    d = np.sqrt(dx ** 2 + sy ** 2)
    ang = np.degrees(np.arctan2(np.abs(sy), np.maximum(dx, 0.0)))
    band = np.searchsorted(np.asarray(BANDS), d, side="right")      # d == 10 -> band 1 (10-20)
    c = 2 * band + (ang > 30.0)
    return np.where(sx > GOAL_X, 12, c).astype(np.int8)


def cell_distance(cells: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    """Mean recorded distance per cell (13,) from training attempts (the per-cell representative distance)."""
    d = np.sqrt((GOAL_X - np.asarray(sx, float)) ** 2 + np.asarray(sy, float) ** 2)
    s = np.bincount(cells, weights=d, minlength=N_CELL)
    n = np.bincount(cells, minlength=N_CELL)
    return s / np.maximum(n, 1)


def type_of(shot_type: pd.Series) -> np.ndarray:
    bad = set(shot_type.dropna().unique()) - KNOWN_TYPES
    if bad:
        raise UnknownShotType(f"shot types not in the map: {sorted(bad)}")
    return shot_type.map(TYPE_MAP).fillna(5).to_numpy().astype(np.int8)


def season_attempts(ev: pd.DataFrame, delayed_fix: bool = True) -> pd.DataFrame:
    """One season of events -> one row per target attempt (stage-3 target set: SHOT, MISS, BLOCK, GOAL; penalty
    shots and shootout excluded) with its pre-event stage-1 state and attributes."""
    ev = ev.sort_values(["game_id", "sort_order"]).reset_index(drop=True)
    tg, _ = attempt_events(ev)
    a = ev[ev.event.isin(["SHOT", "MISS", "BLOCK", "GOAL"]) & (ev.period_type != "SO")
           & ~ev.situation_code.isin(PS_CODES)]
    if len(a) != len(tg):
        raise AssertionError("attempt set differs from the stage-3 target set")
    tl = season_timeline(ev)
    games, sk, prev = tl["games"], tl["sk"], tl["prev"]
    if delayed_fix:
        win = delayed_windows(ev, games.game_id.to_numpy())
        prev, _ = apply_delayed_fix(prev, win)
    N, T = sk.shape[:2]
    end = games.end_t.to_numpy()
    gi = {g: i for i, g in enumerate(games.game_id.to_numpy())}
    st_h, st_a = team_view_st(sk, prev)
    x = ev[(ev.event == "GOAL") & (ev.period_type != "SO")]
    gc = np.zeros((N, T + 1, 2), np.int16)
    np.add.at(gc, (x.game_id.map(gi).to_numpy(), np.minimum(x.game_time_s.to_numpy().astype(int), T),
                   np.where(x.owner_is_home.astype(bool), 0, 1)), 1)
    score = np.cumsum(gc, axis=1)[:, :T]
    i = a.game_id.map(gi).to_numpy().astype(np.int64)
    t = a.game_time_s.to_numpy().astype(np.int64)
    tt = np.minimum(np.clip(t - 1, 0, None), end[i] - 1)
    team = np.where(a.owner_is_home.astype(bool), 0, 1)
    st = np.where(team == 0, st_h[i, tt], st_a[i, tt]).astype(np.int8)
    dh = score[i, tt, 0].astype(np.int16) - score[i, tt, 1]
    sc = sc_bucket(np.where(team == 0, dh, -dh))
    blocked = (a.event == "BLOCK").to_numpy()
    out = pd.DataFrame({"game_id": a.game_id.to_numpy(), "season": a.season.to_numpy(),
                        "game_type": a.game_type.to_numpy(), "sort_order": a.sort_order.to_numpy(), "t": t.astype(np.int32),
                        "team": team.astype(np.int8), "is_home": (1 - team).astype(np.int8), "event": a.event.to_numpy(),
                        "blocked": blocked, "is_goal": (a.event == "GOAL").to_numpy(), "st": st,
                        "grp": GROUP_OF_ST[st], "sc": sc, "period": np.where(t < 3600, t // 1200 + 1, 4).astype(np.int8),
                        "sx": a.sx.to_numpy(float), "sy": a.sy.to_numpy(float), "shot_type": a.shot_type.to_numpy(),
                        "shooter_id": a.shooter_id.to_numpy()})
    out["ptype"] = (out.period == 4).astype(np.int8)
    out["d"] = np.sqrt((GOAL_X - out.sx) ** 2 + out.sy ** 2)
    ub = ~out.blocked.to_numpy()
    cell = np.full(len(out), -1, np.int8)
    typ = np.full(len(out), -1, np.int8)
    cell[ub] = cell_of(out.sx[ub], out.sy[ub])
    typ[ub] = type_of(out.shot_type[ub])
    out["cell"], out["type6"] = cell, typ
    out["cls"] = np.where(ub, cell.astype(np.int16) * N_TYPE + typ, -1).astype(np.int16)
    out["rebound"], out["rush"] = segment_flags(ev, a)
    return out


def segment_flags(ev: pd.DataFrame, a: pd.DataFrame):
    """Rebound: a prior attempt (any kind) by the same team <= 3 s earlier with no stoppage event between them (by sort
    order). Rush: an event OWNED by the shooting team in its neutral or defensive zone <= 4 s earlier (BLOCK events
    excluded, their zone code is the blocker's, L15). Labelled constructions."""
    e = ev[ev.period_type != "SO"][["game_id", "sort_order", "event", "game_time_s", "owner_is_home", "zone"]]
    e = e.reset_index(drop=True)
    gid = e.game_id.to_numpy()
    tm = e.game_time_s.to_numpy().astype(np.int64)
    is_att = e.event.isin(["SHOT", "MISS", "BLOCK", "GOAL"]).to_numpy()
    is_stop = e.event.isin(STOP_EVENTS).to_numpy()
    own = e.owner_is_home.map({True: 0, False: 1}).fillna(-1).to_numpy().astype(np.int64)
    nd = e.zone.isin(["N", "D"]).to_numpy() & (e.event != "BLOCK").to_numpy()
    pos = pd.Series(np.arange(len(e)), index=pd.MultiIndex.from_arrays([e.game_id, e.sort_order]))
    ia = pos.reindex(pd.MultiIndex.from_arrays([a.game_id, a.sort_order])).to_numpy()
    if np.isnan(ia.astype(float)).any():
        raise ValueError("attempt not found in the event stream")
    ia = ia.astype(np.int64)
    team = np.where(a.owner_is_home.astype(bool), 0, 1)
    reb = np.zeros(len(a), bool)
    rush = np.zeros(len(a), bool)
    for k in range(1, 30):
        j = ia - k
        ok = j >= 0
        jj = np.where(ok, j, 0)
        same = ok & (gid[jj] == gid[ia]) & (tm[ia] - tm[jj] <= 4)
        if not same.any():
            break
        rush |= same & (own[jj] == team) & nd[jj]
        reb_k = same & (tm[ia] - tm[jj] <= 3) & is_att[jj] & (own[jj] == team)
        # no stoppage strictly between j and i
        clear = np.ones(len(a), bool)
        for m in range(1, k):
            clear &= ~is_stop[np.clip(ia - m, 0, None)]
        reb |= reb_k & clear & ~is_stop[jj]
    return reb, rush


# --------------------------------------------------------------------------- xG_ref yardstick
def xg_ref_table(rows: pd.DataFrame) -> np.ndarray:
    """(N_CLASS, 5 groups) empirical goal rate per unblocked attempt per (cell x type x strength group) over the given
    (fold-train) rows. An empty (class, group) cell takes the class's rate pooled over groups; a class empty in
    every group takes the cell's pooled rate; a cell empty everywhere takes the league rate (labelled fallbacks)."""
    u = rows[~rows.blocked]
    n = np.zeros((N_CLASS, 5))
    g = np.zeros((N_CLASS, 5))
    np.add.at(n, (u.cls.to_numpy(), u.grp.to_numpy()), 1)
    np.add.at(g, (u.cls.to_numpy(), u.grp.to_numpy()), u.is_goal.to_numpy().astype(float))
    rate = np.divide(g, n, out=np.full_like(g, np.nan), where=n > 0)
    pooled = np.divide(g.sum(1), n.sum(1), out=np.full(N_CLASS, np.nan), where=n.sum(1) > 0)
    cn = n.sum(1).reshape(N_CELL, N_TYPE).sum(1)
    cg = g.sum(1).reshape(N_CELL, N_TYPE).sum(1)
    lg = g.sum() / n.sum()
    cell_rate = np.where(cn > 0, cg / np.maximum(cn, 1), lg)
    pooled = np.where(np.isnan(pooled), np.repeat(cell_rate, N_TYPE), pooled)
    return np.where(np.isnan(rate), pooled[:, None], rate)


# --------------------------------------------------------------------------- as-of shot-quality ratings
def asof_sq_ratings(long: pd.DataFrame, w: float, b: float) -> pd.DataFrame:
    """long: one row per team-game: game_id, season, date, drop, team_id, xf, nf, xa, na (xG_ref sums / unblocked
    attempt counts for and against in one rating group). Shrunk mean xG_ref per attempt as a log ratio to the
    snapshot league mean (L1): r = log((X + b mu) / (N + b)), mu = league mean x exp(w x last season's final relative
    value), minus the cross-team mean of r. Only games dated before the snapshot (same season) enter it.
    Returns game_id, team_id, rf, ra, created_at, puck_drop."""
    out = []
    prev_final = {"f": {}, "a": {}}
    last_drop = None
    for season in sorted(long.season.unique()):
        L = long[long.season == season]
        teams = np.sort(L.team_id.unique())
        tix = {t_: i for i, t_ in enumerate(teams)}
        X = {k: np.zeros(len(teams)) for k in ("f", "a")}
        Nn = {k: np.zeros(len(teams)) for k in ("f", "a")}
        pri = {k: np.array([prev_final[k].get(t_, 0.0) for t_ in teams]) for k in ("f", "a")}

        def snap():
            res = {}
            for k in ("f", "a"):
                lg = X[k].sum() / Nn[k].sum() if Nn[k].sum() > 0 else 1.0
                mu = lg * np.exp(w * pri[k])
                r = np.log((X[k] + b * mu) / (Nn[k] + b))
                res[k] = r - r.mean()
            return res

        for d in np.sort(L.date.unique()):
            s = snap()
            day = L[L.date == d]
            ti = day.team_id.map(tix).to_numpy()
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            out.append(pd.DataFrame({"game_id": day.game_id.to_numpy(), "team_id": day.team_id.to_numpy(),
                                     "rf": s["f"][ti], "ra": s["a"][ti], "created_at": created,
                                     "puck_drop": pd.to_datetime(day["drop"], utc=True)}))
            for k, (xc, nc) in {"f": ("xf", "nf"), "a": ("xa", "na")}.items():
                np.add.at(X[k], ti, day[xc].to_numpy(float))
                np.add.at(Nn[k], ti, day[nc].to_numpy(float))
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        fin = snap()
        prev_final = {k: dict(zip(teams, fin[k])) for k in ("f", "a")}
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r


# --------------------------------------------------------------------------- as-of arena recording factor (distance)
def asof_arena_distance(u: pd.DataFrame, c: float) -> pd.DataFrame:
    """u: unblocked goalies-in attempts with game_id, season, date, drop, arena, shoot_id, def_id, shooter_road,
    defender_road, d. As-of factor per game: log((A + c Dbar) / (E + c Dbar)) over ALL earlier-dated games at the arena
    (this season to date, every earlier season), A = summed recorded distance, E = summed both-teams expected
    distance, expected = season league mean + shooting team's road for-offset + defending team's road against-offset,
    with the offsets of the current season taken from its earlier-dated games only (earlier seasons: full season).
    Dbar = league mean distance of the past games; c = prior pseudo-attempts. Returns game_id, arena, arena_f,
    n_prior, created_at, puck_drop."""
    arenas = np.sort(u.arena.unique())
    ai = {a_: i for i, a_ in enumerate(arenas)}
    u = u.assign(ai=u.arena.map(ai))
    A_prev = np.zeros(len(arenas))
    E_prev = np.zeros(len(arenas))
    n_prev = np.zeros(len(arenas))
    out = []
    last_drop = None
    for season in sorted(u.season.unique()):
        S = u[u.season == season]
        games = S.groupby("game_id").agg(date=("date", "first"), drop=("drop", "first"), ai=("ai", "first")).reset_index()
        dates = np.sort(games.date.unique())
        for dte in dates:
            past = S[S.date < dte]
            day = games[games.date == dte]
            A_cur = np.zeros(len(arenas))
            E_cur = np.zeros(len(arenas))
            n_cur = np.zeros(len(arenas))
            if len(past):
                e = _expected(past)
                np.add.at(A_cur, past.ai.to_numpy(), past.d.to_numpy())
                np.add.at(E_cur, past.ai.to_numpy(), e)
                np.add.at(n_cur, past.ai.to_numpy(), 1)
            A_t, E_t, n_t = A_prev + A_cur, E_prev + E_cur, n_prev + n_cur
            dbar = A_t.sum() / max(n_t.sum(), 1) if n_t.sum() > 0 else 35.0
            fac = np.log((A_t + c * dbar) / (E_t + c * dbar))
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            out.append(pd.DataFrame({"game_id": day.game_id.to_numpy(), "arena": arenas[day.ai.to_numpy()],
                                     "arena_f": fac[day.ai.to_numpy()], "n_prior": n_t[day.ai.to_numpy()],
                                     "created_at": created, "puck_drop": pd.to_datetime(day["drop"], utc=True)}))
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        e = _expected(S)
        np.add.at(A_prev, S.ai.to_numpy(), S.d.to_numpy())
        np.add.at(E_prev, S.ai.to_numpy(), e)
        np.add.at(n_prev, S.ai.to_numpy(), 1)
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r


def _expected(x: pd.DataFrame) -> np.ndarray:
    rf = x[x.shooter_road]
    ra = x[x.defender_road]
    lg = x.d.mean()
    off = (rf.groupby("shoot_id").d.mean() - rf.d.mean()) if len(rf) else pd.Series(dtype=float)
    dfo = (ra.groupby("def_id").d.mean() - ra.d.mean()) if len(ra) else pd.Series(dtype=float)
    return (lg + x.shoot_id.map(off).fillna(0.0) + x.def_id.map(dfo).fillna(0.0)).to_numpy()
