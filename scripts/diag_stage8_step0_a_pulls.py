"""Stage 8 step 0, part A: goalie pulls / empty net (item 1) and in-game goalie changes (item 4). Training seasons only."""
import time
from diag_stage8_step0_common import *

t0 = time.time()
G = games()
EV = load_events(SEASONS, columns=["game_id", "season", "game_type", "sort_order", "period", "period_type", "event", "game_time_s",
                                   "owner_team_id", "owner_is_home", "home_goalie", "away_goalie", "home_skaters", "away_skaters",
                                   "home_score_pre", "away_score_pre", "goalie_id", "strength_state", "shooter_id"])
SH = load_shifts(SEASONS)
SH = SH[SH.position == "G"].copy()
GB = load_goalie_box(SEASONS)
print("loaded", round(time.time() - t0, 1), flush=True)
EV = EV.sort_values(["game_id", "game_time_s", "sort_order"], kind="stable").reset_index(drop=True)
gmeta = G.set_index("game_id")[["season", "game_type", "home_id", "away_id", "end_state_box"]]
MIN_GAP = 3  # seconds; gap below this is not counted as a pull (sensitivity reported)

pulls, changes, gapall = [], [], []
evg = {gid: d for gid, d in EV.groupby("game_id", sort=False)}
shg = {k: d for k, d in SH.groupby(["game_id", "team_id"], sort=False)}
for gid, ev in evg.items():
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
                gapall.append((m.season, m.game_type, b - a))
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
                if p == 3 and (3600 - a) <= 300 and dg < 0:   # trailing in the last 5:00: treat as an EN-style pull
                    dp = False
                ngf = int(((gt >= a - 1) & (gt <= b + 1) & (go == team)).sum()); nga = int(((gt >= a - 1) & (gt <= b + 1) & (go == opp)).sum())
                pulls.append(dict(game_id=gid, season=m.season, game_type=m.game_type, team_id=team, is_home=is_home, period=p,
                                  start=a, end=b, dur=b - a, pend=pe, rem_reg=(3600 - a) if p <= 3 else np.nan,
                                  sk_for=f, sk_ag=ag, deficit=-dg, dp_overlap=dp, dp_event=dp_event, pen_end=pen_end, n_flag0=n_flag0, cause=cause, goals_for_in=ngf, goals_against_in=nga))
    for team, is_home, opp in ((m.home_id, True, m.away_id), (m.away_id, False, m.home_id)):
        s = shg.get((gid, team))
        if s is None:
            continue
        s = s.sort_values("start_s")
        firsts = s.groupby("player_id").start_s.min().sort_values()
        if len(firsts) < 2:
            continue
        starter_first = firsts.index[0]
        for rel, st in list(firsts.items())[1:]:
            per = int(s[(s.player_id == rel)].period.iloc[0])
            dgc = float((go[gt <= st] == team).sum() - (go[gt <= st] == opp).sum())
            near = bool(((np.abs(gt - st) <= 1) & (go == opp)).any())
            returns = bool((s[s.player_id == starter_first].start_s > st).any())
            changes.append(dict(game_id=gid, season=m.season, game_type=m.game_type, team_id=team, is_home=is_home, relief=rel,
                                start=st, period=per, in_period_s=st - (per - 1) * 1200 if per <= 3 else st - 3600, diff=dgc, after_opp_goal=near,
                                starter_returns=returns, rel_toi=float(s[s.player_id == rel].duration_s.sum())))
print("loop done", round(time.time() - t0, 1), flush=True)
P = pd.DataFrame(pulls); C = pd.DataFrame(changes); GP = pd.DataFrame(gapall, columns=["season", "game_type", "gap"])
P.to_parquet(OUT / "pulls.parquet"); C.to_parquet(OUT / "changes.parquet")

out = []
def H(s): out.append("\n" + s + "\n")
ng = G.groupby(["season", "game_type"]).size().rename("games")
def pct(x, q): return np.nanpercentile(x, q) if len(x) else np.nan

H("### 1.0 Shift-gap length distribution")
cf = P.assign(confirmed=P.n_flag0 > 0).groupby(["season", "game_type"]).confirmed.agg(["size", "mean"]).reset_index()
out.append("Independent confirmation: share of shift-derived pulls (gap >= 3 s) with at least one pbp event inside [start, end] whose own-goalie flag in the situation code is 0:\n")
out.append(md(cf.assign(season=cf.season.map(SLAB), game_type=cf.game_type.map(GT)).rename(columns={"size": "n_pulls", "mean": "share_confirmed"}), 4))
gp = GP.copy(); gp["bin"] = pd.cut(gp.gap, [0, 1, 2, 3, 5, 10, 20, 40, 80, 200, 5000], right=True)
out.append("Goalie-shift gaps within a period (no goalie shift on the ice for a team; period windows from PERIOD_START / PERIOD_END events, shootout excluded), all training seasons and both types, gaps > 0 s:\n")
out.append(md(gp[gp.gap > 0].groupby("bin", observed=True).size().rename("n_gaps").to_frame().T, 0))

R = P[(P.period <= 3)].copy()
R["state"] = np.where(R.sk_for > R.sk_ag, "team_PP", np.where(R.sk_for < R.sk_ag, "team_PK", np.where(R.sk_for == 5, "even_5v5", "even_reduced")))
R.loc[R.sk_for.isna(), "state"] = "unknown"
R["pen_on"] = R.state.isin(["team_PP", "team_PK", "even_reduced"])
R["dcat"] = pd.cut(R.deficit, [-99, -1, 0, 1, 2, 99], labels=["leading", "tied", "trail1", "trail2", "trail3+"])
R = R.sort_values(["game_id", "team_id", "start"])
first_all = R.groupby(["game_id", "team_id"]).head(1)
first_nodp = R[~R.dp_overlap].groupby(["game_id", "team_id"]).head(1)

def tab_first(F, label):
    rows = []
    for (s, gt_, dc, po), d in F.groupby(["season", "game_type", "dcat", "pen_on"], observed=True):
        r = d.rem_reg
        rows.append(dict(season=SLAB[s], type=GT[gt_], deficit=str(dc), penalty_on=po, n=len(d), flag="UNDERPOWERED" if len(d) < 100 else "",
                         p10=pct(r, 10), p25=pct(r, 25), median=pct(r, 50), p75=pct(r, 75), p90=pct(r, 90), mean=r.mean()))
    H(f"### 1a. Seconds remaining in regulation at the first pull per team-game, by deficit at the pull and penalty-on: {label}")
    out.append("`penalty_on` = pre-pull skater counts not 5v5 (taken from the last event with the goalie still in net). Deficit = pulling team's goals against minus for, goals at or before the pull second.\n")
    out.append(md(pd.DataFrame(rows), 1))
tab_first(first_nodp, "pulls NOT overlapping a delayed-penalty event")
tab_first(first_all, "all pulls including delayed-penalty overlaps")

d = first_nodp[first_nodp.dcat.isin(["trail1", "trail2", "trail3+"]) & (first_nodp.period == 3)]
rows = []
for (gt_, dc, stt), x in d.groupby(["game_type", "dcat", "state"], observed=True):
    rows.append(dict(type=GT[gt_], deficit=str(dc), pre_state=stt, n=len(x), flag="UNDERPOWERED" if len(x) < 100 else "", median_rem=x.rem_reg.median(), p25=pct(x.rem_reg, 25), p75=pct(x.rem_reg, 75)))
H("### 1b. Pooled 3 seasons, P3 first non-DP pull while trailing, by pre-pull strength state")
out.append(md(pd.DataFrame(rows), 1))
H("### 1c. Period of the first pull (all first pulls incl. DP overlaps), counts")
sp = first_all.groupby(["season", "game_type", "period"]).size().unstack(fill_value=0)
sp.index = [f"{SLAB[a]} {GT[b]}" for a, b in sp.index]; out.append(md(sp, 0))

Pg = P[P.period <= 3]
gscore = {}
for gid, ev in evg.items():
    g = ev[ev.event == "GOAL"]
    gscore[gid] = (g.game_time_s.to_numpy(), g.owner_team_id.to_numpy())
Gm = G[G.game_type.isin([2, 3])].set_index("game_id")
pidx = {k: d for k, d in Pg.groupby("game_id")}
rows = []
for rem in (300, 180, 120, 60):
    for gid, m in Gm.iterrows():
        gt, go = gscore.get(gid, (np.array([]), np.array([])))
        tau = 3600 - rem
        dfc = int(((go == m.home_id) & (gt <= tau)).sum()) - int(((go == m.away_id) & (gt <= tau)).sum())
        if dfc == 0:
            continue
        trailing = m.away_id if dfc > 0 else m.home_id
        pp = pidx.get(gid)
        pulled = False
        if pp is not None:
            pulled = len(pp[(pp.team_id == trailing) & (pp.end > tau) & (~pp.dp_overlap)]) > 0
        rows.append((gid, m.season, m.game_type, rem, min(abs(dfc), 3), pulled))
S = pd.DataFrame(rows, columns=["game_id", "season", "game_type", "rem", "deficit", "pulled"])
T = S.groupby(["season", "game_type", "rem", "deficit"]).pulled.agg(["size", "mean"]).reset_index()
T["season"] = T.season.map(SLAB); T["game_type"] = T.game_type.map(GT); T["flag"] = np.where(T["size"] < 100, "UNDERPOWERED", "")
H("### 1d. Share of games with a non-DP pull, by deficit at a given time remaining")
out.append("Trailing team (by `deficit` at `rem` seconds left in regulation) pulled at any time from `rem` to the end of regulation (an already-pulled goalie counts). Tied games at `rem` excluded.\n")
out.append(md(T.rename(columns={"size": "n_games", "mean": "share_pulled"}), 3))

P2 = P.sort_values(["game_id", "team_id", "start"]).copy()
P2["next_start"] = P2.groupby(["game_id", "team_id"]).start.shift(-1)
P2["next_period"] = P2.groupby(["game_id", "team_id"]).period.shift(-1)
ga = P2[(P2.cause == "goal_against") & (P2.period == 3) & (~P2.dp_overlap)].copy()
ga["lag"] = np.where(ga.next_period == ga.period, ga.next_start - ga.end, np.nan)
rows = []
for (s, gt_), d in ga.groupby(["season", "game_type"]):
    rows.append(dict(season=SLAB[s], type=GT[gt_], n_pulls_ended_by_goal_against=len(d), flag="UNDERPOWERED" if len(d) < 100 else "",
                     share_repulled_same_period=d.lag.notna().mean(), lag_p25=pct(d.lag, 25), lag_median=pct(d.lag, 50), lag_p75=pct(d.lag, 75),
                     share_repull_within_60s=(d.lag <= 60).mean(), share_repull_within_120s=(d.lag <= 120).mean()))
H("### 1e. Re-pulls after a pull ended by a goal against (P3, non-DP pulls)")
out.append("Ended-by-goal rule: a goal event within 1 s of the shift-derived pull end. Lag = the same team's next pull start minus the return time.\n")
out.append(md(pd.DataFrame(rows), 3))

H("### 1f. How pulls end (non-DP pulls, P3), and final-minute pulls")
rows = []
for (s, gt_), d in P[(P.period == 3) & ~P.dp_overlap].groupby(["season", "game_type"]):
    for lab, x in (("all P3 pulls", d), ("start in final 60 s", d[d.rem_reg <= 60]), ("start 60-180 s left", d[(d.rem_reg > 60) & (d.rem_reg <= 180)]), ("start >180 s left", d[d.rem_reg > 180])):
        vc = x.cause.value_counts()
        rows.append(dict(season=SLAB[s], type=GT[gt_], subset=lab, n=len(x), flag="UNDERPOWERED" if len(x) < 100 else "",
                         **{k: vc.get(k, 0) / max(len(x), 1) for k in ["period_end", "goal_for", "goal_against", "goal_both", "stoppage", "in_play"]}, med_dur=x.dur.median()))
out.append(md(pd.DataFrame(rows), 3))

D = P[P.dp_overlap].copy()
rows = []
for (s, gt_), d in D.groupby(["season", "game_type"]):
    rows.append(dict(season=SLAB[s], type=GT[gt_], n_dp_pulls=len(d), per_game=len(d) / ng[(s, gt_)], flag="UNDERPOWERED" if len(d) < 100 else "", med_dur_s=d.dur.median(),
                     share_leading_or_tied=(d.deficit <= 0).mean(), share_P3=(d.period == 3).mean(), share_goal_for=(d.cause == "goal_for").mean(),
                     share_goal_against=(d.cause == "goal_against").mean(), goals_for_in=d.goals_for_in.sum(), goals_against_in=d.goals_against_in.sum()))
H("### 1g. Pulls overlapping a delayed-penalty event (opponent about to be penalised)")
out.append("Rule: a DELAYED_PENALTY event owned by the other team within [pull start - 3 s, pull end + 1 s], OR the pull ends within 3 s of a PENALTY called on the other team (the pbp logs far fewer DELAYED_PENALTY events than there are delayed-penalty pulls: 95% of P1/P2 pulls end at an opponent penalty call). Exception: a team trailing in the last 5:00 of P3 is treated as an EN-style pull whatever follows (about 3.6% of such pulls end at an opponent penalty and cannot be separated from a delayed-penalty pull).\n")
dpc = D.groupby(["season", "game_type"]).agg(by_event=("dp_event", "mean"), by_penalty_call_only=("pen_end", "mean")).reset_index()
out.append(md(dpc.assign(season=dpc.season.map(SLAB), game_type=dpc.game_type.map(GT)), 3))
out.append(md(pd.DataFrame(rows), 3))

rows = []
for (s, gt_), d in P.groupby(["season", "game_type"]):
    n = ng[(s, gt_)]
    ge = EV[(EV.season == s) & (EV.game_type == gt_) & (EV.event == "GOAL")]
    en_ag = (ge.strength_state == "EN_AGAINST").sum(); en_for = (ge.strength_state == "EN_FOR").sum()
    nd = d[~d.dp_overlap]
    tot = d.dur.sum(); totnd = nd.dur.sum()
    rows.append(dict(season=SLAB[s], type=GT[gt_], games=n, pulls_per_game=len(d) / n, en_time_s_per_game_all=tot / n, en_time_s_per_game_nonDP=totnd / n,
                     en_goals_against_per_game=en_ag / n, en_goals_for_per_game=en_for / n, EN_against_per_pulled_min_all=en_ag / (tot / 60),
                     EN_for_per_pulled_min_all=en_for / (tot / 60), EN_against_per_pulled_min_nonDP=nd.goals_against_in.sum() / (totnd / 60),
                     EN_for_per_pulled_min_nonDP=nd.goals_for_in.sum() / (totnd / 60), n_en_goals_for=en_for,
                     flag="UNDERPOWERED" if en_for < 100 else ""))
H("### 1h. Empty-net goals and EN time per game")
out.append("`en_goals_against_per_game` = goals scored into an empty net (pbp EN_AGAINST; the G7 gate quantity); `en_goals_for_per_game` = goals scored by a team with its own goalie pulled (EN_FOR). Per-pulled-minute rates for the `_nonDP` columns count goals inside shift-derived pull intervals; `_all` columns divide the pbp totals by all pulled minutes. Pulled minutes are team-minutes.\n")
out.append(md(pd.DataFrame(rows), 3))

cov = []
for (s, gt_), ge in EV[EV.event == "GOAL"].groupby(["season", "game_type"]):
    ge = ge[ge.strength_state.isin(["EN_AGAINST", "EN_FOR"])]
    pp = P[(P.season == s) & (P.game_type == gt_)]
    pidx2 = {k: d for k, d in pp.groupby("game_id")}
    hit = 0
    for r in ge.itertuples():
        q = pidx2.get(r.game_id)
        if q is None:
            continue
        gm = gmeta.loc[r.game_id]
        pulled_team = r.owner_team_id if r.strength_state == "EN_FOR" else (gm.away_id if r.owner_team_id == gm.home_id else gm.home_id)
        if ((q.team_id == pulled_team) & (q.start - 1 <= r.game_time_s) & (q.end + 1 >= r.game_time_s)).any():
            hit += 1
    cov.append(dict(season=SLAB[s], type=GT[gt_], en_goals=len(ge), inside_shift_derived_pull=hit, share=hit / max(len(ge), 1)))
H("### 1i. Validation: pbp-flagged EN goals (EN_FOR + EN_AGAINST) falling inside a shift-derived pull (tolerance 1 s)")
out.append(md(pd.DataFrame(cov), 4))

rows = []
fl = EV[(EV.period_type != "SO")]
fl = fl.assign(hp=(fl.home_goalie == 0), ap=(fl.away_goalie == 0))
fg = fl.groupby("game_id").agg(h=("hp", "max"), a=("ap", "max"))
for (s, gt_), gm in G.groupby(["season", "game_type"]):
    f = fg.reindex(gm.game_id)
    pp = P[(P.season == s) & (P.game_type == gt_)]
    rows.append(dict(season=SLAB[s], type=GT[gt_], team_games=2 * len(gm), with_pull_by_event_flags=int(f.h.fillna(False).sum() + f.a.fillna(False).sum()),
                     with_pull_by_shifts=pp.groupby(["game_id", "team_id"]).ngroups))
H("### 1j. Team-games with a pull: event goalie flags vs shift gaps >= 3 s")
out.append("Event flags are seen only at events and also fire on PERIOD_END / GAME_END events (stale code, or an end-of-period pull shorter than 3 s): of the 1,205 flagged events in team-games with no shift gap of 3 s or more, 913 are PERIOD_END or GAME_END events. So the flag count exceeds the shift count; it is not a lower bound.\n")
out.append(md(pd.DataFrame(rows), 0))
sens = []
for g_ in (1, 2, 3, 5):
    x = GP[(GP.gap >= g_)]
    sens.append(dict(min_gap_s=g_, n_pulls_total=len(x), per_game=len(x) / len(G)))
H("### 1k. Sensitivity of pull count to the minimum gap")
out.append(md(pd.DataFrame(sens), 3))

Cm = C.copy()
rows = []
nteam = G.groupby(["season", "game_type"]).size() * 2
for (s, gt_), d in Cm.groupby(["season", "game_type"]):
    rows.append(dict(season=SLAB[s], type=GT[gt_], team_games=nteam[(s, gt_)], relief_appearances=len(d), per_100_team_games=100 * len(d) / nteam[(s, gt_)],
                     flag="UNDERPOWERED" if len(d) < 100 else "", share_P1=(d.period == 1).mean(), share_P2=(d.period == 2).mean(), share_P3=(d.period == 3).mean(),
                     share_OT=(d.period > 3).mean(), share_at_period_start=(d.in_period_s <= 1).mean(), share_right_after_opp_goal=d.after_opp_goal.mean(),
                     share_starter_returns=d.starter_returns.mean(), median_relief_toi_min=d.rel_toi.median() / 60))
H("### 4a. Relief goalie appearances (shift chart: a second distinct goalie id on the ice)")
out.append(md(pd.DataFrame(rows), 3))
Cm["dcat"] = pd.cut(Cm["diff"], [-99, -3, -2, -1, 0, 1, 99], labels=["<=-3", "-2", "-1", "0 (tied)", "+1", ">=+2"])
rows = []
for (s, gt_), d in Cm.groupby(["season", "game_type"]):
    vc = d.dcat.value_counts()
    rows.append(dict(season=SLAB[s], type=GT[gt_], n=len(d), **{str(k): int(vc.get(k, 0)) for k in ["<=-3", "-2", "-1", "0 (tied)", "+1", ">=+2"]}))
H("### 4b. Team score differential (own minus opponent, goals at or before the change second) at the change; counts")
out.append(md(pd.DataFrame(rows), 0))
gbx = GB.merge(G[["game_id", "game_type"]], on="game_id")
rel_box = gbx[(~gbx.starter) & (gbx.toi_s > 0)]
cb = rel_box.groupby(["season", "game_type"]).size().rename("relief_by_goalie_box").reset_index()
cs = Cm.groupby(["season", "game_type"]).size().rename("relief_by_shifts").reset_index()
x = cb.merge(cs, on=["season", "game_type"], how="outer"); x["season"] = x.season.map(SLAB); x["game_type"] = x.game_type.map(GT)
H("### 4c. Cross-check: relief appearances by goalie box (non-starter, TOI > 0) vs shift chart")
out.append(md(x, 0))
starter = GB[GB.starter].groupby(["game_id", "team_id"]).player_id.first().rename("starter_id").reset_index()
sog = EV[(EV.event.isin(["SHOT", "GOAL"])) & (EV.period_type != "SO") & EV.goalie_id.notna()].copy()
sog = sog.merge(G[["game_id", "home_id", "away_id"]], on="game_id")
sog["def_team"] = np.where(sog.owner_team_id == sog.home_id, sog.away_id, sog.home_id)
sog = sog.merge(starter, left_on=["game_id", "def_team"], right_on=["game_id", "team_id"], how="left")
sog["relief"] = sog.goalie_id != sog.starter_id
rows = []
for (s, gt_), d in sog.groupby(["season", "game_type"]):
    rows.append(dict(season=SLAB[s], type=GT[gt_], sog_faced=len(d), share_by_relief=d.relief.mean(), share_by_relief_regulation_only=d[d.period <= 3].relief.mean(),
                     goal_share_by_relief=d[d.event == "GOAL"].relief.mean(), no_starter_match=int(d.starter_id.isna().sum())))
H("### 4d. Share of shots on goal (non-EN, non-shootout) faced by a non-starter goalie")
out.append("Starter = goalie_box `starter` flag (post-game data). Computed from pbp `goalie_id` on SHOT / GOAL events.\n")
out.append(md(pd.DataFrame(rows), 4))
(OUT / "part_a.md").write_text("\n".join(out), encoding="utf-8")
print("done", round(time.time() - t0, 1))
