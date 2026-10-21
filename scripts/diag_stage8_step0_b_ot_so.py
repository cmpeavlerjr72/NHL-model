"""Stage 8 step 0, part B: overtime (item 2) and shootout (item 3). Training seasons only."""
import time
from diag_stage8_step0_common import *

t0 = time.time()
G = games()
EV = load_events(SEASONS, columns=["game_id", "season", "game_type", "sort_order", "period", "period_type", "event", "game_time_s",
                                   "owner_team_id", "owner_is_home", "home_goalie", "away_goalie", "home_skaters", "away_skaters",
                                   "shooter_id", "goalie_id", "strength_state", "pen_minutes", "pen_type"])
EV = EV.sort_values(["game_id", "game_time_s", "sort_order"], kind="stable").reset_index(drop=True)
out = []
def H(s): out.append("\n" + s + "\n")
def pct(x, q): return np.nanpercentile(x, q) if len(x) else np.nan

# ---------------- OT: share of games tied after regulation ----------------
rows = []
for (s, gt_), g in G.groupby(["season", "game_type"]):
    n = len(g); e = g.end_state_box
    rows.append(dict(season=SLAB[s], type=GT[gt_], games=n, tied_after_reg=(e != "REG").sum(), reg_tie_rate=(e != "REG").mean(),
                     decided_in_OT=(e == "OT").sum(), shootout=(e == "SO").sum(), so_rate_all_games=(e == "SO").mean(),
                     so_share_of_tied=(e == "SO").sum() / max((e != "REG").sum(), 1), pbp_vs_box_end_state_mismatch=int((g.end_state_pbp != g.end_state_box).sum()),
                     flag="UNDERPOWERED" if (e != "REG").sum() < 100 else ""))
H("### 2a. Games tied after regulation and how they end (end state from the box score / verified finals; pbp end state mismatch count alongside)")
out.append(md(pd.DataFrame(rows), 4))

# ---------------- OT length ----------------
rs = G[(G.game_type == 2) & (G.end_state_box != "REG")].game_id
ot = EV[EV.game_id.isin(rs) & (EV.period == 4)]
ends = ot[ot.event == "PERIOD_END"].groupby("game_id").game_time_s.max() - 3600
goal_ot = ot[ot.event == "GOAL"].groupby("game_id").game_time_s.min() - 3600
gg = G.set_index("game_id")
rows = []
for s in SEASONS:
    ids = gg[(gg.season == s) & (gg.game_type == 2) & (gg.end_state_box != "REG")].index
    L = pd.Series({i: (goal_ot[i] if i in goal_ot.index else 300.0) for i in ids})
    ended_goal = np.array([i in goal_ot.index for i in ids])
    ES = gg.loc[ids].end_state_box
    rows.append(dict(season=SLAB[s], tied_games=len(ids), ended_by_OT_goal=int(ended_goal.sum()), went_to_SO=int((ES == "SO").sum()), share_goal=ended_goal.mean(),
                     share_SO=1 - ended_goal.mean(), mean_OT_s=L.mean(), median_OT_s=L.median(), p25=pct(L, 25), p75=pct(L, 75),
                     goal_in_first60=(L[ended_goal] <= 60).sum() / max(len(L), 1), goal_in_first120=(L[ended_goal] <= 120).sum() / max(len(L), 1),
                     OT_goal_games_mean_s=L[ended_goal].mean(), flag="UNDERPOWERED" if len(ids) < 100 else ""))
H("### 2b. Regular-season overtime: how it ends and how long it lasts (OT clock seconds; SO games count as 300 s)")
out.append("Check on the end state: games with end_state OT must have exactly one OT goal and games with SO none (see sanity table 2b2).\n")
out.append(md(pd.DataFrame(rows), 3))
san = []
for s in SEASONS:
    ids = gg[(gg.season == s) & (gg.game_type == 2) & (gg.end_state_box != "REG")].index
    cnt = ot[ot.event == "GOAL"].groupby("game_id").size().reindex(ids).fillna(0)
    es = gg.loc[ids].end_state_box
    san.append(dict(season=SLAB[s], OT_games_with_1_goal=int(((es == "OT") & (cnt == 1)).sum()), OT_games_not_1_goal=int(((es == "OT") & (cnt != 1)).sum()),
                    SO_games_with_0_OT_goals=int(((es == "SO") & (cnt == 0)).sum()), SO_games_with_OT_goals=int(((es == "SO") & (cnt > 0)).sum())))
H("### 2b2. Sanity: OT goal counts vs end state")
out.append(md(pd.DataFrame(san), 0))
# hazard by OT minute
rows = []
for s in SEASONS:
    ids = gg[(gg.season == s) & (gg.game_type == 2) & (gg.end_state_box != "REG")].index
    L = np.array([(goal_ot[i] if i in goal_ot.index else 300.0) for i in ids]); evt = np.array([i in goal_ot.index for i in ids])
    for m in range(5):
        lo, hi = 60 * m, 60 * (m + 1)
        expo = np.clip(L - lo, 0, 60).sum()
        k = ((L > lo) & (L <= hi) & evt).sum()
        rows.append(dict(season=SLAB[s], ot_minute=m + 1, games_alive_at_start=int((L > lo).sum()), goals=int(k), exposure_min=expo / 60, goals_per_min=k / (expo / 60) if expo else np.nan,
                         flag="UNDERPOWERED" if k < 100 else ""))
pooled = []
for m in range(5):
    sub = [r for r in rows if r["ot_minute"] == m + 1]
    k = sum(r["goals"] for r in sub); ex = sum(r["exposure_min"] for r in sub)
    pooled.append(dict(season="pooled", ot_minute=m + 1, games_alive_at_start=sum(r["games_alive_at_start"] for r in sub), goals=k, exposure_min=ex, goals_per_min=k / ex, flag="UNDERPOWERED" if k < 100 else ""))
rows = rows + pooled
H("### 2c. OT goal hazard by OT minute (all strengths, both teams combined)")
out.append("Exposure uses the game's OT end (goal time, or 300 s for shootout games). Cells under 100 goals are UNDERPOWERED by the brief's rule.\n")
out.append(md(pd.DataFrame(rows), 4))

# ---------------- state exposure in OT ----------------
def label(h, a, hg, ag):
    if hg == 0 or ag == 0:
        return f"EN ({int(h)}v{int(a)})"
    return f"{int(max(h, a))}v{int(min(h, a))}" if h != a else f"{int(h)}v{int(a)}"

def ot_tables(period_mask, title, gtype, per_label=True):
    d = EV[(EV.game_type == gtype) & period_mask(EV)].copy()
    d = d[d.game_id.isin(G[G.game_type == gtype].game_id)]
    d = d[d.home_skaters.notna() & d.away_skaters.notna() & d.home_goalie.notna() & d.away_goalie.notna()].copy()
    d["lab"] = [label(h, a, hg, ag) for h, a, hg, ag in zip(d.home_skaters, d.away_skaters, d.home_goalie, d.away_goalie)]
    nonplay = d.event.isin(["PERIOD_END", "GAME_END", "SHOOTOUT_COMPLETE"])
    d.loc[nonplay, "lab"] = np.nan
    d["lab"] = d.groupby(["game_id", "period"]).lab.ffill()
    d["next_t"] = d.groupby(["game_id", "period"]).game_time_s.shift(-1)
    d["next_lab"] = d.groupby(["game_id", "period"]).lab.shift(-1)
    d["dt"] = (d.next_t - d.game_time_s).fillna(0)
    exp_prev = d.groupby(["season", "lab"]).dt.sum()          # time attributed to the state of the earlier event
    exp_next = d.groupby(["season", "next_lab"]).dt.sum()       # time attributed to the state of the later event
    att = d[d.event.isin(["SHOT", "MISS", "BLOCK", "GOAL"])].groupby(["season", "lab"]).size().rename("attempts")
    sog = d[d.event.isin(["SHOT", "GOAL"])].groupby(["season", "lab"]).size().rename("sog")
    gl = d[d.event == "GOAL"].groupby(["season", "lab"]).size().rename("goals")
    T = pd.concat([exp_prev.rename("exposure_s_prevstate"), exp_next.rename("exposure_s_nextstate").rename_axis(["season", "lab"]), att, sog, gl], axis=1).fillna(0).reset_index()
    T.columns = ["season", "state"] + list(T.columns[2:])
    T["exposure_s_mid"] = (T.exposure_s_prevstate + T.exposure_s_nextstate) / 2
    for c in ("attempts", "sog", "goals"):
        T[c + "_per60"] = T[c] / (T.exposure_s_mid / 3600) if True else 0
        T[c + "_per60_lo"] = T[c] / (np.maximum(T.exposure_s_prevstate, T.exposure_s_nextstate) / 3600)
        T[c + "_per60_hi"] = T[c] / (np.minimum(T.exposure_s_prevstate, T.exposure_s_nextstate).clip(lower=1) / 3600)
    T["season"] = T.season.map(SLAB)
    T["flag"] = np.where(T.attempts < 100, "UNDERPOWERED", "")
    T["goals_flag"] = np.where(T.goals < 100, "goals<100", "")
    H(title)
    return T, d

T, d4 = ot_tables(lambda e: e.period == 4, "### 2d. Regular-season OT (period 4): exposure and event rates by strength state, both teams combined", 2)
out.append("Exposure: seconds between consecutive events are attributed to the state in the situation code of the earlier event (`prevstate`) or the later event (`nextstate`); the situation code changes only at events, so penalty expiry and the state after a whistle are known only at the next event. `_lo` / `_hi` are the rates under the two extreme attributions, `per60` uses their mean. 3v3 state is the INV-35 hazard target. Per-team rate = combined / 2.\n")
cols = ["season", "state", "exposure_s_prevstate", "exposure_s_nextstate", "attempts", "sog", "goals", "attempts_per60", "sog_per60", "goals_per60", "goals_per60_lo", "goals_per60_hi", "flag", "goals_flag"]
out.append(md(T[T.exposure_s_mid > 30][cols].sort_values(["state", "season"]), 3))
# pooled
tp = T.groupby("state")[["exposure_s_prevstate", "exposure_s_nextstate", "attempts", "sog", "goals"]].sum().reset_index()
tp["exposure_s_mid"] = (tp.exposure_s_prevstate + tp.exposure_s_nextstate) / 2
for c in ("attempts", "sog", "goals"):
    tp[c + "_per60"] = tp[c] / (tp.exposure_s_mid / 3600)
tp["goals_per60_lo"] = tp.goals / (np.maximum(tp.exposure_s_prevstate, tp.exposure_s_nextstate) / 3600)
tp["goals_per60_hi"] = tp.goals / (np.minimum(tp.exposure_s_prevstate, tp.exposure_s_nextstate).clip(lower=1) / 3600)
tp["share_of_OT_time"] = tp.exposure_s_mid / tp.exposure_s_mid.sum()
tp["flag"] = np.where(tp.attempts < 100, "UNDERPOWERED", "")
H("### 2e. Regular-season OT, three seasons pooled, by strength state")
out.append(md(tp[tp.exposure_s_mid > 30].sort_values("exposure_s_mid", ascending=False), 3))
# 3v3 per team and the 3v3 time, penalties
pen = d4[(d4.event == "PENALTY")]
rows = []
for s in SEASONS:
    ids = gg[(gg.season == s) & (gg.game_type == 2) & (gg.end_state_box != "REG")].index
    p_ = pen[pen.season == s]
    tot = T[(T.season == SLAB[s])].exposure_s_mid.sum()
    t33 = T[(T.season == SLAB[s]) & (T.state == "3v3")].exposure_s_mid.sum()
    rows.append(dict(season=SLAB[s], ot_games=len(ids), penalties_called_in_OT=len(p_), per_100_ot_games=100 * len(p_) / len(ids), total_OT_clock_s=tot, share_time_3v3=t33 / tot,
                     games_with_penalty=p_.game_id.nunique(), flag="UNDERPOWERED" if len(p_) < 100 else ""))
H("### 2f. Penalties and non-3v3 time in regulation-season OT")
out.append(md(pd.DataFrame(rows), 3))
pc = pen.groupby(["season", "pen_minutes"]).size().unstack(fill_value=0)
pc.index = [SLAB[i] for i in pc.index]
out.append("\nOT penalty minutes (counts):\n")
out.append(md(pc, 0))
# home/away split of OT winners (RS) and SO winners
rows = []
for s in SEASONS:
    g = gg[(gg.season == s) & (gg.game_type == 2)]
    o = g[g.end_state_box == "OT"]; so = g[g.end_state_box == "SO"]
    rows.append(dict(season=SLAB[s], ot_decided=len(o), home_wins_in_OT=(o.home_score_box > o.away_score_box).mean(), so_decided=len(so),
                     home_wins_in_SO=(so.home_score_box > so.away_score_box).mean(), home_win_in_regulation_decided=(g[g.end_state_box == "REG"].home_score_box > g[g.end_state_box == "REG"].away_score_box).mean(),
                     flag="UNDERPOWERED" if len(o) < 100 or len(so) < 100 else ""))
H("### 2g. Home share of winners: OT goal, shootout, regulation decided (regular season)")
out.append("OT cells with n < 100 are UNDERPOWERED. Binomial SE on a 0.5 proportion at n = 100 is about 0.05.\n")
out.append(md(pd.DataFrame(rows), 3))
# playoff OT
Tp, dpo = ot_tables(lambda e: e.period >= 4, "### 2h. Playoff OT (periods 4+, 5v5 continuous): exposure and event rates by strength state", 3)
out.append("All playoff OT cells are small; flagged UNDERPOWERED where fewer than 100 attempts.\n")
out.append(md(Tp[Tp.exposure_s_mid > 30][cols].sort_values(["state", "season"]), 3))
rows = []
for s in SEASONS:
    g = gg[(gg.season == s) & (gg.game_type == 3)]
    ids = g[g.end_state_box != "REG"].index
    periods = dpo[dpo.season == s].groupby("game_id").period.max()
    rows.append(dict(season=SLAB[s], po_games=len(g), ot_games=len(ids), ot_rate=len(ids) / len(g), games_2plus_OT=int((periods.reindex(ids) >= 5).sum()),
                     home_wins_in_OT=(g.loc[ids].home_score_box > g.loc[ids].away_score_box).mean(), flag="UNDERPOWERED"))
out.append("\nPlayoff OT summary:\n")
out.append(md(pd.DataFrame(rows), 3))

# ---------------- Shootout ----------------
so = EV[(EV.period_type == "SO") & EV.event.isin(["SHOT", "MISS", "GOAL", "FAILED_SHOT_ATTEMPT"])].copy()
so = so.sort_values(["game_id", "sort_order"])
so["k"] = so.groupby("game_id").cumcount()
so["round"] = so.k // 2 + 1
so["success"] = so.event == "GOAL"
so["shoot_home"] = so.owner_is_home.astype(bool)
H("### 3a. Shootout data integrity")
integ = []
for s in SEASONS:
    d = so[so.season == s]
    alt = d.groupby("game_id").owner_team_id.apply(lambda x: bool((x.values[1:] != x.values[:-1]).all()))
    sog_ids = G[(G.season == s) & (G.end_state_box == "SO")].game_id
    natt = d.groupby("game_id").size()
    # decided check: goals by team vs end result
    gl = d[d.success].groupby(["game_id", "shoot_home"]).size().unstack(fill_value=0).reindex(sog_ids).fillna(0)
    hw = (gl.get(True, 0) > gl.get(False, 0))
    gh = gg.loc[sog_ids]
    agree = (hw.values == (gh.home_score_box > gh.away_score_box).values).mean()
    integ.append(dict(season=SLAB[s], so_games_by_end_state=len(sog_ids), games_with_attempt_events=d.game_id.nunique(), attempts=len(d), strictly_alternating_share=alt.mean(),
                      null_shooter_id=int(d.shooter_id.isna().sum()), null_goalie_id=int(d.goalie_id.isna().sum()), events_FAILED_SHOT_ATTEMPT=int((d.event == "FAILED_SHOT_ATTEMPT").sum()),
                      winner_by_SO_goals_matches_final=agree, home_shoots_first_share=d[d.k == 0].shoot_home.mean()))
out.append(md(pd.DataFrame(integ), 3))

H("### 3b. Rounds per shootout")
rows = []
for s in SEASONS:
    d = so[so.season == s]
    natt = d.groupby("game_id").size()
    rnd = (natt + 1) // 2
    rows.append(dict(season=SLAB[s], shootouts=len(natt), mean_attempts=natt.mean(), mean_rounds=rnd.mean(), share_3_rounds_or_fewer=(natt <= 6).mean(), share_past_round_3=(natt > 6).mean(),
                     share_ended_after_attempt_4_or_5=((natt == 4) | (natt == 5)).mean(), max_rounds=int(rnd.max()), flag="UNDERPOWERED" if len(natt) < 100 else ""))
out.append(md(pd.DataFrame(rows), 3))
pooled = so.groupby("game_id").size()
out.append("\nPooled attempts-per-shootout distribution (counts): " + ", ".join(f"{k}: {v}" for k, v in pooled.value_counts().sort_index().items()) + "\n")

H("### 3c. Per-attempt success by round and by home / away shooter")
rows = []
for s in list(SEASONS) + ["pooled"]:
    d = so if s == "pooled" else so[so.season == s]
    for r in [1, 2, 3, 4, 5, "6+"]:
        x = d[d["round"] >= 6] if r == "6+" else d[d["round"] == r]
        for side, lab in ((None, "both"), (True, "home"), (False, "away")):
            y = x if side is None else x[x.shoot_home == side]
            rows.append(dict(season=SLAB.get(s, s), round=r, shooter=lab, attempts=len(y), goals=int(y.success.sum()), success_rate=y.success.mean() if len(y) else np.nan,
                             flag="UNDERPOWERED" if len(y) < 100 else ""))
R = pd.DataFrame(rows)
out.append(md(R[R.shooter == "both"], 3))
out.append("\nBy shooter side:\n")
out.append(md(R[R.shooter != "both"].pivot_table(index=["season", "round"], columns="shooter", values=["attempts", "success_rate"]).reset_index().round(3), 3))
d = so
out.append(f"\nOverall pooled success {d.success.mean():.4f} over {len(d)} attempts; home {d[d.shoot_home].success.mean():.4f}, away {d[~d.shoot_home].success.mean():.4f}; first shooter of the round {d[d.k % 2 == 0].success.mean():.4f}, second shooter {d[d.k % 2 == 1].success.mean():.4f}. Per-season overall: "
           + "; ".join(f"{SLAB[s]} {so[so.season == s].success.mean():.4f} (n={int((so.season == s).sum())})" for s in SEASONS) + "\n")

H("### 3d. Shooter and goalie identity: is a per-shooter model feasible?")
rows = []
for who, col in (("shooter", "shooter_id"), ("goalie", "goalie_id")):
    c = so.groupby(col).agg(n=("success", "size"), g=("success", "sum"))
    for thr in (5, 10, 20, 30):
        sel = c[c.n >= thr]
        rows.append(dict(entity=who, min_attempts=thr, n_entities=len(sel), share_of_all_attempts=sel.n.sum() / len(so), distinct_total=len(c)))
out.append(md(pd.DataFrame(rows), 3))
c = so.groupby("shooter_id").agg(n=("success", "size"), g=("success", "sum"))
cs = c[c.n >= 10]
p0 = so.success.mean()
exp_var = (cs.n * p0 * (1 - p0)).sum()
obs_var = ((cs.g - cs.n * p0) ** 2).sum()
cg = so.groupby("goalie_id").agg(n=("success", "size"), g=("success", "sum")); cgs = cg[cg.n >= 10]
exp_g = (cgs.n * p0 * (1 - p0)).sum(); obs_g = ((cgs.g - cgs.n * p0) ** 2).sum()
out.append(f"\nDispersion check (observed squared deviation of goals from n*p0 over binomial expectation; 1.0 means no shooter / goalie signal beyond chance): shooters with >= 10 attempts {obs_var / exp_var:.3f} over {len(cs)} shooters ({int(cs.n.sum())} attempts); goalies with >= 10 attempts faced {obs_g / exp_g:.3f} over {len(cgs)} goalies ({int(cgs.n.sum())} attempts). With 90% of shooters near 10-30 attempts the test has little power: treat as UNDERPOWERED for any individual shooter.\n")
# split-half reliability for shooters
(OUT / "part_b.md").write_text("\n".join(out), encoding="utf-8")
print("done", round(time.time() - t0, 1))
