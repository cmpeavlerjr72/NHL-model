"""EG-R1 part A (INV-66): goalie-pull detection, engine-rule pull episodes, hazard rows, the P0 / P1 arms and the
offline pull-process simulator used by the bias checks. Lane H8a, 2026-10-21.

Detection (the step-0 audit rule, `scripts/diag_stage8_step0_a_pulls.py`, reused verbatim in `detect_pulls`): a pull is
a gap >= 3 s inside a period in which a team has no goalie shift on the ice; it is a delayed-penalty (DP) pull if the
opponent owns a DELAYED_PENALTY event in [start - 3, end + 1] or the pull ends within 3 s of a PENALTY on the opponent,
except that a team trailing in the last 5:00 of P3 is always an EN-style pull.

Engine-rule episodes (`episodes_and_rows`): the engine's return rules (spec, "deterministic, no parameter") are: the
goalie returns at a tying goal and at a goal against, nowhere else. A data pull episode therefore starts at a non-DP
pull start while trailing inside the window (last 600 s of regulation) and runs until the first goal against or tying
goal (that second included) or the end of regulation. A shift-chart return that is not one of those (a stoppage, a
non-tying goal for, in play) does not end the episode: the goalie-in seconds until the next shift gap are "bridged"
(counted, reported). Rows: team-game-seconds s in [3000, 3600) where the team trails by >= 1 BEFORE the second (goals
at t < s), is not in an episode, and no DP pull of either team covers s. y = 1 at the episode's engine start second:
the pull second a, or a + 1 when a goal is scored at second a (the post-goal score is then the pre-event state, the
engine draws the pull at the start of a second). pulled_before = an episode of this team ended earlier in the window.
penalty state = skater counts of the last event before s with the team's goalie in net (the audit's pre-pull state):
pk = own < opp, pp = own > opp. Regular season only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WIN0, WIN1 = 3000, 3600          # window: 600 s left in regulation to 0
NSEC = WIN1 - WIN0
NBIN = NSEC // 10                # 10-s seconds-left bins
MIN_GAP = 3
CLIP = 1e-6                      # numerical guard on every hazard when scoring LL (both arms, stated before scoring)

EV_COLS = ["game_id", "season", "game_type", "sort_order", "period", "period_type", "event", "game_time_s",
           "owner_team_id", "home_goalie", "away_goalie", "home_skaters", "away_skaters"]


def rem_bin(s):
    """seconds-left bin 0..59 of game second s in [3000, 3600): rem = 3600 - s in 1..600, bin = (rem - 1) // 10."""
    return (WIN1 - np.asarray(s) - 1) // 10


def dcat_of(deficit):
    """deficit 1 / 2 / >=3 -> 0 / 1 / 2."""
    return np.minimum(np.asarray(deficit), 3) - 1


# ============================================================================================= detection (audit rule)
def detect_pulls(G: pd.DataFrame, EV: pd.DataFrame, SH: pd.DataFrame) -> pd.DataFrame:
    """The audit's pull table (scripts/diag_stage8_step0_a_pulls.py, first loop), one row per goalie-shift gap >= 3 s.
    G games, EV events (EV_COLS), SH goalie shifts. Regular season and playoffs; shootout periods excluded."""
    EV = EV.sort_values(["game_id", "game_time_s", "sort_order"], kind="stable").reset_index(drop=True)
    gmeta = G.set_index("game_id")[["season", "game_type", "home_id", "away_id"]]
    pulls = []
    shg = {k: d for k, d in SH.groupby(["game_id", "team_id"], sort=False)}
    for gid, ev in EV.groupby("game_id", sort=False):
        if gid not in gmeta.index:
            continue
        m = gmeta.loc[gid]
        if m.game_type not in (2, 3):
            continue
        t = ev.game_time_s.to_numpy(); et = ev.event.to_numpy()
        goals = ev[ev.event == "GOAL"]
        gt = goals.game_time_s.to_numpy(); go = goals.owner_team_id.to_numpy()
        dly = ev[ev.event == "DELAYED_PENALTY"]
        dt_ = dly.game_time_s.to_numpy(); do = dly.owner_team_id.to_numpy()
        stop_t = t[np.isin(et, ["STOPPAGE", "FACEOFF", "PENALTY", "DELAYED_PENALTY"])]
        pn = ev[ev.event == "PENALTY"]
        pn_t = pn.game_time_s.to_numpy(); pn_o = pn.owner_team_id.to_numpy()
        pst = ev[ev.event == "PERIOD_START"].groupby("period").game_time_s.first()
        pen = ev[ev.event == "PERIOD_END"].groupby("period").game_time_s.last()
        ptype = ev.groupby("period").period_type.first()
        for team, is_home, opp in ((m.home_id, True, m.away_id), (m.away_id, False, m.home_id)):
            s = shg.get((gid, team))
            if s is None:
                continue
            gflag = (ev.home_goalie if is_home else ev.away_goalie).to_numpy()
            sk_for = (ev.home_skaters if is_home else ev.away_skaters).to_numpy()
            sk_ag = (ev.away_skaters if is_home else ev.home_skaters).to_numpy()
            for p in pen.index:
                if p not in pst.index or ptype.get(p) == "SO":
                    continue
                ps, pe = float(pst[p]), float(pen[p])
                ss = s[s.period == p].sort_values("start_s")
                cur = ps
                iv = []
                for a, b in zip(ss.start_s, ss.end_s):
                    if a > cur:
                        iv.append((cur, float(a)))
                    cur = max(cur, float(b))
                if cur < pe:
                    iv.append((cur, pe))
                for a, b in iv:
                    if b - a < MIN_GAP:
                        continue
                    idx = np.where((t <= a) & (gflag == 1))[0]
                    if len(idx):
                        i = idx[-1]; f, ag = sk_for[i], sk_ag[i]
                    else:
                        f = ag = np.nan
                    dg = float((go[gt <= a] == team).sum() - (go[gt <= a] == opp).sum())
                    cause = "in_play"
                    near_g = np.where(np.abs(gt - b) <= 1)[0]
                    if b >= pe - 0.5:
                        cause = "period_end"
                    if len(near_g):
                        cause = "goal_for" if (go[near_g] == team).any() else "goal_against"
                        if (go[near_g] == team).any() and (go[near_g] == opp).any():
                            cause = "goal_both"
                    elif cause != "period_end" and (np.abs(stop_t - b) <= 1).any():
                        cause = "stoppage"
                    dp_event = bool(((do == opp) & (dt_ >= a - 3) & (dt_ <= b + 1)).any())
                    pen_end = bool(((pn_o == opp) & (np.abs(pn_t - b) <= 3)).any())
                    n_flag0 = int(((t >= a) & (t <= b) & (gflag == 0)).sum())
                    dp = dp_event or pen_end
                    if p == 3 and (3600 - a) <= 300 and dg < 0:
                        dp = False
                    pulls.append(dict(game_id=gid, season=m.season, game_type=m.game_type, team_id=team, is_home=is_home,
                                      period=p, start=a, end=b, dur=b - a, pend=pe, sk_for=f, sk_ag=ag, deficit=-dg,
                                      dp_overlap=dp, cause=cause, n_flag0=n_flag0))
    return pd.DataFrame(pulls)


# ============================================================================================ episodes and rows
def _pen_state(ev_t, gflag, sk_f, sk_a):
    """(NSEC,) penalty state 0 none / 1 pk / 2 pp per second s (last event before s with own goalie in)."""
    ok = gflag == 1
    tt, f, a = ev_t[ok], sk_f[ok], sk_a[ok]
    sec = np.arange(WIN0, WIN1)
    i = np.searchsorted(tt, sec, side="left") - 1          # last event with t < s
    out = np.zeros(NSEC, np.int8)
    v = i >= 0
    ff, aa = f[i[v]], a[i[v]]
    out[v] = np.where(ff < aa, 1, np.where(ff > aa, 2, 0))
    return out


def episodes_and_rows(G: pd.DataFrame, EV: pd.DataFrame, P: pd.DataFrame, has_shifts: set):
    """-> (rows, episodes, paths). G games (RS rows only are built), EV events, P = detect_pulls output.
    has_shifts: {(game_id, team_id)} with goalie shifts (team-games without them are skipped, counted by the caller).
    rows: one per row second (see module doc). episodes: one per engine-rule episode. paths: one per team-game with
    goalie shifts: per-second arrays (as lists) for the offline simulator: deficit pre-second, penalty state, DP-on,
    return-goal flags (goal against at s; own tying goal at s)."""
    gm = G[G.game_type == 2].set_index("game_id")
    EV = EV[EV.game_id.isin(gm.index)].sort_values(["game_id", "game_time_s", "sort_order"], kind="stable")
    Pg = {k: d for k, d in P[(P.game_type == 2) & (P.period == 3)].groupby("game_id")}
    sec = np.arange(WIN0, WIN1)
    R, E, PA = [], [], []
    for gid, ev in EV.groupby("game_id", sort=False):
        m = gm.loc[gid]
        pp_ = Pg.get(gid, P.iloc[:0])
        t = ev.game_time_s.to_numpy()
        g = ev[(ev.event == "GOAL") & (ev.period_type != "SO")]
        gt, go = g.game_time_s.to_numpy(), g.owner_team_id.to_numpy()
        # DP-on: any DP pull (either team) covering s
        dp_on = np.zeros(NSEC, bool)
        for r in pp_[pp_.dp_overlap].itertuples():
            lo, hi = max(int(r.start), WIN0), min(int(r.end), WIN1)
            if hi > lo:
                dp_on[lo - WIN0:hi - WIN0] = True
        for team, is_home, opp in ((m.home_id, 1, m.away_id), (m.away_id, 0, m.home_id)):
            if (gid, team) not in has_shifts:
                continue
            own_g = np.searchsorted(np.sort(gt[go == team]), sec, side="left")      # goals with t < s
            opp_g = np.searchsorted(np.sort(gt[go == opp]), sec, side="left")
            deficit = (opp_g - own_g).astype(np.int16)
            gflag = (ev.home_goalie if is_home else ev.away_goalie).to_numpy()
            sk_f = (ev.home_skaters if is_home else ev.away_skaters).to_numpy()
            sk_a = (ev.away_skaters if is_home else ev.home_skaters).to_numpy()
            pen = _pen_state(t, gflag, sk_f, sk_a)
            # return triggers at second s: opponent goal at s; own goal at s that ties (deficit before = 1 and no opp goal)
            own_at = np.zeros(NSEC, np.int16)
            for x in gt[(go == team) & (gt >= WIN0) & (gt < WIN1)]:
                own_at[int(x) - WIN0] += 1
            opp_at = np.zeros(NSEC, np.int16)
            for x in gt[(go == opp) & (gt >= WIN0) & (gt < WIN1)]:
                opp_at[int(x) - WIN0] += 1
            post = deficit + opp_at - own_at                                           # deficit after second s
            tie_at = (deficit >= 1) & (post <= 0) & (own_at > 0)
            ret_at = (opp_at > 0) | tie_at
            mine = pp_[(pp_.team_id == team)].sort_values("start")
            lit = np.zeros(NSEC, bool)                                                 # literal non-DP shift gap
            for r in mine[~mine.dp_overlap].itertuples():
                lo, hi = max(int(r.start), WIN0), min(int(r.end), WIN1)
                if hi > lo:
                    lit[lo - WIN0:hi - WIN0] = True
            # candidate starts: non-DP gap starts inside the window while trailing (post-goal score at the start second)
            starts = []
            for r in mine[~mine.dp_overlap].itertuples():
                a = int(r.start)
                if a < WIN0 or a >= WIN1:
                    continue
                i = a - WIN0
                a_eng = a + 1 if (own_at[i] + opp_at[i]) > 0 else a
                if a_eng >= WIN1:
                    continue
                if deficit[a_eng - WIN0] >= 1:
                    starts.append((a_eng, a, r.cause, float(r.dur)))
            starts = sorted(set(starts))
            out = np.zeros(NSEC, bool)
            pb = np.zeros(NSEC, bool)
            last_ret = np.full(NSEC, -1, np.int32)                                    # second of the last return
            k = 0
            in_ep = False
            ep = None
            ended_any = False
            ret_sec = -1
            ns = len(starts)
            mine_ep = []
            for i in range(NSEC):
                s = WIN0 + i
                pb[i] = ended_any
                last_ret[i] = ret_sec
                if not in_ep:
                    while k < ns and starts[k][0] < s:                               # starts absorbed / skipped
                        k += 1
                    if k < ns and starts[k][0] == s and deficit[i] >= 1 and not dp_on[i]:
                        in_ep = True
                        ep = dict(game_id=gid, team_id=team, is_home=is_home, start=s, shift_start=starts[k][1],
                                  deficit=int(deficit[i]), pen=int(pen[i]), pulled_before=bool(ended_any),
                                  first_cause=starts[k][2])
                        k += 1
                if in_ep:
                    out[i] = True
                    if ret_at[i]:
                        in_ep = False
                        ended_any = True
                        ret_sec = s
                        ep.update(end=s + 1, cause="tie" if tie_at[i] else "goal_against")
                        mine_ep.append(ep)
            if in_ep:
                ep.update(end=WIN1, cause="period_end")
                mine_ep.append(ep)
            E.extend(mine_ep)
            row = (deficit >= 1) & ~out & ~dp_on
            # y: an episode starts at s (an episode start second is an 'in' second before the start)
            y = np.zeros(NSEC, bool)
            for e in mine_ep:
                y[e["start"] - WIN0] = True
            row |= y
            ii = np.flatnonzero(row)
            if ii.size:
                R.append(pd.DataFrame(dict(game_id=gid, team_id=team, is_home=np.int8(is_home), s=(ii + WIN0).astype(np.int16),
                                           dcat=dcat_of(deficit[ii]).astype(np.int8), pen=pen[ii], pb=pb[ii].astype(np.int8),
                                           lag=np.where(last_ret[ii] >= 0, ii + WIN0 - last_ret[ii], -1).astype(np.int16),
                                           y=y[ii].astype(np.int8))))
            PA.append(dict(game_id=gid, team_id=team, is_home=is_home, deficit=deficit.astype(np.int8).tobytes(),
                           pen=pen.tobytes(), dp=dp_on.astype(np.int8).tobytes(), ret=ret_at.astype(np.int8).tobytes(),
                           tie=tie_at.astype(np.int8).tobytes(), ga=(opp_at > 0).astype(np.int8).tobytes(),
                           out_engine=int(out.sum()), out_literal=int(lit.sum()), bridged=int((out & ~lit).sum()),
                           literal_outside=int((lit & ~out).sum())))
    rows = pd.concat(R, ignore_index=True) if R else pd.DataFrame()
    return rows, pd.DataFrame(E), pd.DataFrame(PA)


def unpack(paths: pd.DataFrame, col: str) -> np.ndarray:
    """(n_team_games, NSEC) int8 array from a paths column."""
    return np.stack([np.frombuffer(b, np.int8) for b in paths[col]]).astype(np.int16)


# ============================================================================================ arms
PRIOR_SD = 10.0
N_P1 = 3 * NBIN + 4                     # deficit x bin cells | pk | pp | pulled_before | home


def _cells(rows: pd.DataFrame) -> pd.DataFrame:
    b = rem_bin(rows.s.to_numpy())
    k = pd.DataFrame(dict(dcat=rows.dcat.to_numpy(), bin=b, pen=rows.pen.to_numpy(), pb=rows.pb.to_numpy(),
                          home=rows.is_home.to_numpy(), y=rows.y.to_numpy()))
    return k.groupby(["dcat", "bin", "pen", "pb", "home"]).y.agg(["size", "sum"]).reset_index()


def _design(dcat, b, pen, pb, home) -> np.ndarray:
    dcat, b, pen, pb, home = (np.asarray(x) for x in (dcat, b, pen, pb, home))
    n = len(dcat)
    X = np.zeros((n, N_P1))
    X[np.arange(n), dcat * NBIN + b] = 1.0
    X[:, 3 * NBIN] = pen == 1
    X[:, 3 * NBIN + 1] = pen == 2
    X[:, 3 * NBIN + 2] = pb
    X[:, 3 * NBIN + 3] = home
    return X


def fit_p1(rows: pd.DataFrame, max_iter: int = 100) -> dict:
    """P1: logistic per second, one-hot deficit x 10-s bin + pk + pp + pulled_before + home; Newton on the aggregated
    cells with a Gaussian prior SD PRIOR_SD on every coefficient (numerical guard for empty cells)."""
    c = _cells(rows)
    X = _design(c.dcat, c["bin"], c.pen, c.pb, c.home)
    n, y = c["size"].to_numpy(float), c["sum"].to_numpy(float)
    w = np.zeros(N_P1)
    w[:3 * NBIN] = np.log(y.sum() / n.sum())
    lam = 1.0 / PRIOR_SD ** 2

    def obj(w_):
        z = X @ w_
        return float((y * z - n * np.logaddexp(0.0, z)).sum() - 0.5 * lam * (w_ @ w_))

    f = obj(w)
    for it in range(max_iter):
        p = 1.0 / (1.0 + np.exp(-(X @ w)))
        g = X.T @ (y - n * p) - lam * w
        H = (X * (n * p * (1 - p))[:, None]).T @ X + lam * np.eye(N_P1)
        step = np.linalg.solve(H, g)
        t = 1.0
        while obj(w + t * step) < f - 1e-12 and t > 1e-8:          # backtracking (Newton overshoots on empty cells)
            t *= 0.5
        w = w + t * step
        f_new = obj(w)
        if abs(f_new - f) < 1e-9 and np.abs(t * step).max() < 1e-6:
            f = f_new
            break
        f = f_new
    return dict(arm="P1", coef=w.tolist(), n_iter=it + 1, prior_sd=PRIOR_SD, n_rows=int(n.sum()), n_pulls=int(y.sum()))


def p1_table(m: dict) -> np.ndarray:
    """Served P1 lookup: probability per second [dcat 3, bin 60, pen 3, pb 2, home 2]."""
    w = np.asarray(m["coef"], np.float64)
    d, b, pe, pb, h = np.meshgrid(np.arange(3), np.arange(NBIN), np.arange(3), np.arange(2), np.arange(2), indexing="ij")
    z = _design(d.ravel(), b.ravel(), pe.ravel(), pb.ravel(), h.ravel()) @ w
    return (1.0 / (1.0 + np.exp(-z))).reshape(3, NBIN, 3, 2, 2)


def fit_p0(rows: pd.DataFrame) -> dict:
    """P0: empirical first-pull hazard per (deficit, penalty-on, second) and re-pull hazard per second since the
    return (no smoothing)."""
    r0 = rows[rows.pb == 0]
    po = (r0.pen > 0).astype(int).to_numpy()
    i = r0.s.to_numpy().astype(np.int64) - WIN0
    n = np.zeros((3, 2, NSEC)); y = np.zeros((3, 2, NSEC))
    np.add.at(n, (r0.dcat.to_numpy(), po, i), 1); np.add.at(y, (r0.dcat.to_numpy(), po, i), r0.y.to_numpy())
    r1 = rows[rows.pb == 1]
    lag = np.clip(r1.lag.to_numpy().astype(np.int64), 0, NSEC)
    n1 = np.bincount(lag, minlength=NSEC + 1).astype(float)
    y1 = np.bincount(lag, weights=r1.y.to_numpy().astype(float), minlength=NSEC + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        h0 = np.where(n > 0, y / n, 0.0)
        h1 = np.where(n1 > 0, y1 / n1, 0.0)
    return dict(arm="P0", h_first=h0.tolist(), h_repull=h1.tolist(), n_rows=int(len(rows)), n_pulls=int(rows.y.sum()),
                n_first=int(r0.y.sum()), n_repull=int(r1.y.sum()))


def p0_tables(m: dict) -> tuple[np.ndarray, np.ndarray]:
    """Served P0 lookups: h_first [dcat 3, penalty-on 2, second 600], h_repull [lag 0..600]."""
    return np.asarray(m["h_first"], np.float64), np.asarray(m["h_repull"], np.float64)


def hazard(m: dict, dcat, s, pen, pb, home, lag) -> np.ndarray:
    """Per-second pull probability under arm m (P0 or P1) for arrays of row features."""
    dcat, s, pen, pb, home, lag = (np.asarray(x).astype(np.int64) for x in (dcat, s, pen, pb, home, lag))
    if m["arm"] == "P1":
        if "_table" not in m:
            m["_table"] = p1_table(m)
        return m["_table"][dcat, rem_bin(s), pen, pb, home]
    if m["arm"] == "P0":
        if "_h0" not in m:
            m["_h0"], m["_h1"] = p0_tables(m)
        a = m["_h0"][dcat, (pen > 0).astype(np.int64), s - WIN0]
        b = m["_h1"][np.clip(lag, 0, NSEC)]
        return np.where(pb == 1, b, a)
    raise ValueError(m["arm"])


def team_game_ll(m: dict, rows: pd.DataFrame) -> pd.Series:
    """Per-team-game Bernoulli LL over the rows, hazards clipped to [CLIP, 1 - CLIP]."""
    h = np.clip(hazard(m, rows.dcat, rows.s, rows.pen, rows.pb, rows.is_home, rows.lag), CLIP, 1 - CLIP)
    y = rows.y.to_numpy()
    ll = np.where(y == 1, np.log(h), np.log1p(-h))
    return pd.Series(ll).groupby([rows.game_id.to_numpy(), rows.team_id.to_numpy()]).sum()


# ============================================================================================ offline simulator
def actual_stats(paths: pd.DataFrame, ep: pd.DataFrame) -> dict:
    """Bias-check quantities on the data (engine-rule episodes)."""
    ng = paths.game_id.nunique()
    first = ep[~ep.pulled_before.astype(bool)]
    fd = np.minimum(first.deficit, 3)
    med = {d: float((WIN1 - first[fd == d].start).median()) for d in (1, 2, 3)}
    dfc, dp = unpack(paths, "deficit"), unpack(paths, "dp")
    den = ((dfc == 1) & (dp == 0)).any(1)
    key = paths.game_id.astype(str) + "_" + paths.team_id.astype(str)
    e1 = ep[ep.deficit == 1]
    num = key.isin(set(e1.game_id.astype(str) + "_" + e1.team_id.astype(str))).to_numpy() & den
    ga = ep[ep.cause == "goal_against"]
    nxt = ep.sort_values("start").groupby(["game_id", "team_id"]).start.shift(-1)
    return dict(pulled_s_per_game=float(paths.out_engine.sum() / ng), literal_s_per_game=float(paths.out_literal.sum() / ng),
                first_median_trail1=med[1], first_median_trail2=med[2], first_median_trail3=med[3],
                n_first=[int((fd == d).sum()) for d in (1, 2, 3)],
                share_trail1_pulled=float(num.sum() / den.sum()), n_trail1_team_games=int(den.sum()),
                repull_share=float(nxt.reindex(ga.index).notna().mean()), n_ended_goal_against=int(len(ga)))


def simulate_offline(m: dict, paths: pd.DataFrame, reps: int = 200, seed: int = 0) -> dict:
    """The arm's pull process on the actual paths (score before each second, penalty state, DP-on, goal seconds) with
    the engine's return rules; `reps` replications per team-game."""
    rng = np.random.default_rng(seed)
    dfc, pen, dp, ret, tie = (np.repeat(unpack(paths, c), reps, 0) for c in ("deficit", "pen", "dp", "ret", "tie"))
    home = np.repeat(paths.is_home.to_numpy().astype(np.int64), reps)
    N = dfc.shape[0]
    out = np.zeros(N, bool); pb = np.zeros(N, np.int64); last = np.full(N, -1, np.int64)
    out_s = np.zeros(N, np.int64)
    first_s = np.full(N, -1, np.int64); first_d = np.zeros(N, np.int64); any_t1 = np.zeros(N, bool)
    n_ga = 0; n_ga_rep = 0
    ga_open = np.zeros(N, bool)                       # an episode ended by a goal against, not yet followed by a pull
    for i in range(NSEC):
        s = WIN0 + i
        el = (dfc[:, i] >= 1) & ~out & (dp[:, i] == 0)
        j = np.flatnonzero(el)
        if j.size:
            h = hazard(m, dcat_of(dfc[j, i]), np.full(j.size, s), pen[j, i], pb[j], home[j],
                       np.where(last[j] >= 0, s - last[j], -1))
            hit = j[rng.random(j.size) < h]
            out[hit] = True
            nf = hit[first_s[hit] < 0]
            first_s[nf] = s; first_d[nf] = np.minimum(dfc[nf, i], 3)
            any_t1[hit[dfc[hit, i] == 1]] = True
            n_ga_rep += int(ga_open[hit].sum()); ga_open[hit] = False
        out_s += out
        r = out & (ret[:, i] == 1)
        g_a = r & (tie[:, i] == 0)
        n_ga += int(g_a.sum())
        ga_open[g_a] = True
        out[r] = False; pb[r] = 1; last[r] = s
    ng = paths.game_id.nunique()
    den = ((dfc == 1) & (dp == 0)).any(1)
    med = {d: float(np.median(WIN1 - first_s[(first_s >= 0) & (first_d == d)])) for d in (1, 2, 3)}
    return dict(pulled_s_per_game=float(out_s.sum() / reps / ng), first_median_trail1=med[1], first_median_trail2=med[2],
                first_median_trail3=med[3], share_trail1_pulled=float((any_t1 & den).sum() / den.sum()),
                repull_share=float(n_ga_rep / max(n_ga, 1)), reps=reps)


def bias_checks(sim: dict, act: dict) -> dict:
    """Pre-registered checks: pulled time per game within 10%, first-pull median by deficit within 10 s, trailing-by-1
    pulled share within 3 pp, re-pull share within 5 pp."""
    c = dict(pulled_time=abs(sim["pulled_s_per_game"] / act["pulled_s_per_game"] - 1) <= 0.10,
             **{f"median_trail{d}": abs(sim[f"first_median_trail{d}"] - act[f"first_median_trail{d}"]) <= 10 for d in (1, 2, 3)},
             trail1_share=abs(sim["share_trail1_pulled"] - act["share_trail1_pulled"]) <= 0.03,
             repull_share=abs(sim["repull_share"] - act["repull_share"]) <= 0.05)
    c["all"] = bool(all(c.values()))
    return {k: bool(v) for k, v in c.items()}
