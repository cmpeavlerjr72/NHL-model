"""EG-R1 part C (INV-67): the shootout. S1 = rules mechanics with a constant per-attempt success probability (an
as-of M1 K500 level over attempts) and the as-of home-shoots-first share; S2 = S1 + a shooter rating (offline only).

Rules mechanics (`simulate_shootout`): three rounds, the two teams alternate (the first shooter's team shoots
attempts 1, 3, 5, ...), the shootout ends EARLY as soon as one team has more goals than the other can reach with its
remaining round-1-to-3 attempts; if the teams are level after three rounds, sudden death follows: both teams shoot a
round and the shootout ends at the end of the first round in which the goal counts differ. Every attempt is an
independent Bernoulli(p of the shooting side). Pure function of the uniforms passed in (engine streams are
(seed, game_id, "shootout") counters), so paired arms share draws.

As-of levels (`asof_m1`): one value per game from games dated strictly earlier, shrunk to the previous season's final
value: (x + K v_prev) / (m + K); the first data season uses its own final value (labelled look-ahead, never judged).
created_at = 6 h after the last puck drop of the previous game date, asserted < puck_drop.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MAX_ATTEMPTS = 100            # 50 rounds; the chance a shootout lasts that long is < 1e-10 at p = 0.31
K_SUCCESS = 500.0             # attempts of prior at the previous season's final success rate (M1 K500)
K_FIRST = 100.0               # shootouts of prior for the home-shoots-first share (labelled choice, spec silent)
REG_ROUNDS = 3


def simulate_shootout(u: np.ndarray, p_first: np.ndarray, p_second: np.ndarray):
    """u: (N, A) uniforms, one per attempt slot (attempt index j = 0..A-1); p_first / p_second: (N,) per-attempt
    success probabilities of the team that shoots first / second. Returns (first_wins (N,) bool, n_attempts (N,) int,
    goals_first (N,), goals_second (N,)). A shootout still level after A attempts raises (the caller sizes A)."""
    N, A = u.shape
    gf = np.zeros(N, np.int32)
    gs = np.zeros(N, np.int32)
    n_att = np.zeros(N, np.int32)
    done = np.zeros(N, bool)
    for j in range(A):
        act = ~done
        if not act.any():
            break
        first_shoots = (j % 2 == 0)
        p = p_first if first_shoots else p_second
        goal = (u[:, j] < p) & act
        if first_shoots:
            gf += goal
        else:
            gs += goal
        n_att[act] = j + 1
        if j < 2 * REG_ROUNDS:                              # regulation rounds: early termination when decided
            a_f, a_s = (j + 2) // 2, (j + 1) // 2           # attempts taken so far by first / second shooter team
            rem_f, rem_s = REG_ROUNDS - a_f, REG_ROUNDS - a_s
            decided = (gf > gs + rem_s) | (gs > gf + rem_f)
        elif j % 2 == 1:                                    # sudden death: decided at the end of a round
            decided = gf != gs
        else:
            decided = np.zeros(N, bool)
        done |= decided & act
    if not done.all():
        raise RuntimeError(f"{int((~done).sum())} shootouts undecided after {A} attempts")
    return gf > gs, n_att, gf, gs


def shootout_home_win(u_first: np.ndarray, u_att: np.ndarray, p_home: np.ndarray, p_away: np.ndarray,
                      home_first_share: np.ndarray):
    """Engine form. u_first (N,): the home-shoots-first draw; u_att (N, A): attempt draws. Returns
    (home_wins (N,) bool, n_attempts, goals_home, goals_away, home_first (N,) bool)."""
    home_first = u_first < home_first_share
    p_f = np.where(home_first, p_home, p_away)
    p_s = np.where(home_first, p_away, p_home)
    fw, n_att, gf, gs = simulate_shootout(u_att, p_f, p_s)
    home_win = np.where(home_first, fw, ~fw)
    gh = np.where(home_first, gf, gs)
    ga = np.where(home_first, gs, gf)
    return home_win, n_att, gh, ga, home_first


def asof_m1(games: pd.DataFrame, x: np.ndarray, m: np.ndarray, K: float):
    """games: game_id, season, date (str), drop (UTC str), in date order. x, m: per-game successes and trials.
    -> (meta, value (G,)): shrunk as-of value per game."""
    games = games.reset_index(drop=True)
    seasons = sorted(games.season.unique())
    gs = games.season.to_numpy()
    final = {s: x[gs == s].sum() / m[gs == s].sum() for s in seasons}
    val = np.zeros(len(games))
    created = np.full(len(games), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    last_drop = None
    for i, season in enumerate(seasons):
        v_prev = final[seasons[i - 1]] if i > 0 else final[season]
        idx = np.flatnonzero(gs == season)
        dates = games.date.to_numpy()[idx]
        sx = sm = 0.0
        for d in np.unique(dates):
            ix = idx[dates == d]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            val[ix] = (sx + K * v_prev) / (sm + K)
            sx += x[ix].sum()
            sm += m[ix].sum()
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": gs,
                         "created_at": pd.to_datetime(created).tz_localize("UTC"),
                         "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    m_ = meta.created_at.notna()
    if not (meta.created_at[m_] < meta.puck_drop[m_]).all():
        raise AssertionError("shootout level created_at is not before puck drop")
    return meta, val


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def asof_shooter_ratings(att: pd.DataFrame, w: float = 0.7, b: float = 50.0) -> pd.Series:
    """S2 (offline): as-of shooter log-odds rating per ATTEMPT row. att: one row per shootout attempt in date order
    (game_id, season, date, shooter_id, success). For the attempt's game, only attempts in games dated strictly
    earlier (same season) enter, plus the previous season's final relative rating at weight w:
      mu_i = sigmoid(logit(league rate to date) + w prev_i);  rating_i = logit((X_i + b mu_i) / (N_i + b)) - logit(league rate to date)
    (relative to the snapshot league mean; prev_i = the shooter's final rating of the previous season, 0 if unseen;
    the league rate before any attempt of a season is the previous season's). Returns a Series aligned to att.index."""
    att = att.sort_values(["date", "game_id"], kind="stable")
    rating = pd.Series(np.nan, index=att.index)
    prev_final: dict = {}
    prev_lg = None
    for season in sorted(att.season.unique()):
        A = att[att.season == season]
        X: dict = {}
        Nn: dict = {}
        tot_x = tot_n = 0.0
        lg0 = prev_lg if prev_lg is not None else float(A.success.mean())      # first data season: own mean (labelled)

        def r_of(sid, lg):
            mu = _sigmoid(_logit(lg) + w * prev_final.get(sid, 0.0))
            return float(_logit((X.get(sid, 0.0) + b * mu) / (Nn.get(sid, 0.0) + b)) - _logit(lg))

        for d in A.date.unique():
            day = A[A.date == d]
            lg = tot_x / tot_n if tot_n > 0 else lg0
            for idx, sid in zip(day.index, day.shooter_id):
                rating[idx] = r_of(sid, lg)
            for sid, s_ in zip(day.shooter_id, day.success):
                X[sid] = X.get(sid, 0.0) + float(s_)
                Nn[sid] = Nn.get(sid, 0.0) + 1.0
            tot_x += float(day.success.sum())
            tot_n += float(len(day))
        lg_f = tot_x / tot_n
        prev_final = {sid: r_of(sid, lg_f) for sid in set(X) | set(prev_final)}
        prev_lg = lg_f
    return rating
