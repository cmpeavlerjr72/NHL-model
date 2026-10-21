"""Stage 8 step 0, part C: rebound proxy and faceoffs (item 5). Training seasons only."""
import time
from diag_stage8_step0_common import *

t0 = time.time()
G = games()
EV = load_events(SEASONS, columns=["game_id", "season", "game_type", "sort_order", "period", "period_type", "event", "game_time_s",
                                   "owner_team_id", "owner_is_home", "home_goalie", "away_goalie", "home_skaters", "away_skaters",
                                   "strength_state", "shooting_team_id", "zone", "faceoff_winner_id", "faceoff_loser_id", "shot_type"])
EV = EV.sort_values(["game_id", "game_time_s", "sort_order"], kind="stable").reset_index(drop=True)
EV = EV[EV.period_type != "SO"].reset_index(drop=True)
out = []
def H(s): out.append("\n" + s + "\n")

# ---------------- rebound proxy ----------------
ATT = ["SHOT", "MISS", "BLOCK", "GOAL"]
BRK = ["STOPPAGE", "FACEOFF", "PENALTY", "PERIOD_START", "PERIOD_END", "GOAL"]
EV["brk"] = EV.event.isin(BRK) & ~((EV.event == "GOAL") & False)
# a GOAL is both an attempt and a play-ending event: the next attempt starts a new segment
EV["seg"] = EV.groupby("game_id").brk.cumsum()
# segment for a GOAL itself should be the segment it ends (shift by own break)
EV.loc[EV.event == "GOAL", "seg"] = EV.loc[EV.event == "GOAL", "seg"] - 1
A = EV[EV.event.isin(ATT)].copy()
A["team"] = A.shooting_team_id
A["p_event"] = A.groupby("game_id").event.shift(1)
A["p_team"] = A.groupby("game_id").team.shift(1)
A["p_t"] = A.groupby("game_id").game_time_s.shift(1)
A["p_seg"] = A.groupby("game_id").seg.shift(1)
A["p_period"] = A.groupby("game_id").period.shift(1)
A["dt"] = A.game_time_s - A.p_t
A["reb"] = (A.p_seg == A.seg) & (A.p_team == A.team) & (A.dt >= 0) & (A.dt <= 3) & (A.p_period == A.period)
U = A[A.event.isin(["SHOT", "MISS", "GOAL"])].copy()           # unblocked attempts
U["goal"] = U.event == "GOAL"
U["sog"] = U.event.isin(["SHOT", "GOAL"])
U["state"] = U.strength_state
U["pclass"] = np.where(U.reb, U.p_event, "none")

def rb_table(keys, title, note=""):
    rows = []
    for k, d in U.groupby(keys):
        k = k if isinstance(k, tuple) else (k,)
        r, o = d[d.reb], d[~d.reb]
        rows.append(dict(**dict(zip(keys, k)), unblocked=len(d), reb_n=len(r), reb_share=len(r) / len(d), goal_rate_per_unblocked_reb=r.goal.mean() if len(r) else np.nan,
                         goal_rate_per_unblocked_other=o.goal.mean() if len(o) else np.nan, goal_per_sog_reb=r[r.sog].goal.mean() if r.sog.sum() else np.nan,
                         goal_per_sog_other=o[o.sog].goal.mean(), sog_share_of_reb=r.sog.mean() if len(r) else np.nan,
                         flag="UNDERPOWERED" if len(r) < 100 else ""))
    T = pd.DataFrame(rows)
    for c in ("season",):
        if c in T: T[c] = T[c].map(SLAB)
    if "game_type" in T: T["game_type"] = T.game_type.map(GT)
    H(title)
    if note: out.append(note + "\n")
    out.append(md(T, 4))

H("### 5.0 Rebound proxy definition")
out.append("Unblocked attempt = SHOT, MISS or GOAL (shootouts excluded). It is a rebound proxy if the immediately preceding shot attempt (SHOT, MISS, BLOCK or GOAL) in the same period was by the same team, was at most 3 game-clock seconds earlier, and no STOPPAGE, FACEOFF, PENALTY, GOAL or period event lies between them (so no whistle intervened). `game_time_s` has 1 s resolution, so the window is effectively 3 to 4 s. Blocked attempts are not themselves classified (they cannot be rebounds-on-goal). The prior attempt's class says whether the puck came off a save (SHOT), a miss (off the glass / boards) or a block.\n")
U["is_reb_n"] = U.reb
rb_table(["season", "game_type"], "### 5a. Rebound proxy by season and game type")
rb_table(["state"], "### 5b. Rebound proxy by strength state of the shooting team (3 seasons pooled, RS + PO)", "State from the shooting team's view: PP = shooting team has the man advantage, PK = shorthanded, EN_FOR = own goalie pulled, EN_AGAINST = shooting into an empty net.")
rb_table(["season", "state"], "### 5b2. By season and strength state")
U["prior_class"] = np.where(U.reb, U.p_event, "no rebound")
rows = []
for (pc), d in U[U.reb].groupby("p_event"):
    rows.append(dict(prior_attempt_class=pc, n=len(d), share_of_rebound_proxies=len(d) / U.reb.sum(), goal_rate_per_unblocked=d.goal.mean(), goal_per_sog=d[d.sog].goal.mean(),
                     sog_share=d.sog.mean(), flag="UNDERPOWERED" if len(d) < 100 else ""))
H("### 5c. Rebound proxies by the prior attempt's class (3 seasons pooled)")
out.append(md(pd.DataFrame(rows), 4))
rows = []
for (pc, s), d in U[U.reb].groupby(["p_event", "state"]):
    rows.append(dict(prior_attempt_class=pc, state=s, n=len(d), goal_rate_per_unblocked=d.goal.mean(), flag="UNDERPOWERED" if len(d) < 100 else ""))
H("### 5c2. Prior class by strength state (pooled)")
out.append(md(pd.DataFrame(rows), 4))
rows = []
for dtv, d in U[U.reb].groupby("dt"):
    rows.append(dict(seconds_since_prior_attempt=int(dtv), n=len(d), goal_rate_per_unblocked=d.goal.mean(), goal_per_sog=d[d.sog].goal.mean(), flag="UNDERPOWERED" if len(d) < 100 else ""))
H("### 5d. Rebound proxy by clock gap to the prior attempt (pooled)")
out.append(md(pd.DataFrame(rows), 4))
# per-prior-class and non-rebound base rate by shot type
rows = []
for st, d in U.groupby("shot_type"):
    rows.append(dict(shot_type=st, unblocked=len(d), rebound_share=d.reb.mean(), goal_rate=d.goal.mean(), goal_rate_rebound=d[d.reb].goal.mean() if d.reb.sum() else np.nan, reb_n=int(d.reb.sum()), flag="UNDERPOWERED" if d.reb.sum() < 100 else ""))
H("### 5e. Rebound-proxy share by shot type (pooled)")
out.append(md(pd.DataFrame(rows), 4))
# also the same-team any-intervening-opp-attempt variant
A["p2_team"] = A.groupby("game_id").team.shift(2)
# per-game rebound proxies per game
pg = U.groupby(["season", "game_type"]).agg(rebounds=("reb", "sum"), n=("reb", "size"))
ng = G.groupby(["season", "game_type"]).size()
pg["rebounds_per_game"] = pg.rebounds / ng
pg["unblocked_per_game"] = pg.n / ng
pg = pg.reset_index(); pg["season"] = pg.season.map(SLAB); pg["game_type"] = pg.game_type.map(GT)
H("### 5f. Rebound proxies per game")
out.append(md(pg, 3))
# per-game dispersion by team: is the team-level rebound share a stable attribute?
tm = U.groupby(["season", "team"]).agg(n=("reb", "size"), r=("reb", "sum"))
tm["share"] = tm.r / tm.n
sd = tm.groupby("season").share.agg(["mean", "std", "min", "max"])
sd["binomial_sd"] = np.sqrt(tm.groupby("season").apply(lambda x: (x.share.mean() * (1 - x.share.mean()) / x.n).mean()))
sd.index = [SLAB[i] for i in sd.index]
H("### 5g. Team spread of the rebound-proxy share (own shots; 32 teams per season)")
out.append(md(sd, 4))
# split-half team persistence across seasons
a = tm.reset_index().pivot(index="team", columns="season", values="share")
out.append("\nCross-season correlation of team rebound-proxy share: " + "; ".join(f"{SLAB[a_]} vs {SLAB[b_]} r={a[a_].corr(a[b_]):.3f}" for a_, b_ in ((SEASONS[0], SEASONS[1]), (SEASONS[1], SEASONS[2]))) + "\n")

# ---------------- faceoffs ----------------
F = EV[EV.event == "FACEOFF"].copy()
F["winner_home"] = F.owner_is_home.astype(bool)
F["zone_home_view"] = np.where(F.zone == "N", "N", np.where(F.winner_home, F.zone, np.where(F.zone == "O", "D", "O")))  # home team's zone
F["gstate"] = np.where((F.home_goalie == 0) | (F.away_goalie == 0), "EN",
                        np.where(F.home_skaters == F.away_skaters, F.home_skaters.astype("Int64").astype(str) + "v" + F.away_skaters.astype("Int64").astype(str),
                                 np.maximum(F.home_skaters, F.away_skaters).astype("Int64").astype(str) + "v" + np.minimum(F.home_skaters, F.away_skaters).astype("Int64").astype(str)))
# restrict to plausible
keep = {"5v5", "4v4", "3v3", "5v4", "5v3", "4v3", "EN"}
F["gstate"] = np.where(F.gstate.isin(keep), F.gstate, "other")
rows = []
for (s, gt_), d in F.groupby(["season", "game_type"]):
    n = ng[(s, gt_)]
    row = dict(season=SLAB[s], type=GT[gt_], games=n, faceoffs_per_game=len(d) / n)
    for z in ("N", "O", "D"):
        row[f"zone_{z}_home_view_per_game"] = (d.zone_home_view == z).sum() / n
    rows.append(row)
H("### 5h. Faceoffs per game by zone (zone from the home team's view: O = home offensive zone, D = home defensive zone)")
out.append(md(pd.DataFrame(rows), 3))
rows = []
for (s, gt_), d in F.groupby(["season", "game_type"]):
    n = ng[(s, gt_)]
    vc = d.gstate.value_counts()
    row = dict(season=SLAB[s], type=GT[gt_])
    for k in ["5v5", "5v4", "4v4", "3v3", "5v3", "4v3", "EN", "other"]:
        row[k + "_per_game"] = vc.get(k, 0) / n
    rows.append(row)
H("### 5i. Faceoffs per game by strength state (unordered skater counts; EN = either goalie out)")
out.append(md(pd.DataFrame(rows), 3))
rows = []
for gs, d in F[F.game_type == 2].groupby("gstate"):
    row = dict(state=gs, n=len(d), home_win_share=d.winner_home.mean(), flag="UNDERPOWERED" if len(d) < 100 else "")
    for z in ("N", "O", "D"):
        x = d[d.zone_home_view == z]
        row[f"n_{z}"] = len(x); row[f"home_win_{z}"] = x.winner_home.mean() if len(x) else np.nan
    rows.append(row)
H("### 5j. Home faceoff win share by strength state and zone (regular season, pooled)")
out.append(md(pd.DataFrame(rows), 4))
# team win share
games_ = G.set_index("game_id")
F["winner_team"] = F.owner_team_id
F["loser_team"] = np.where(F.winner_home, F.game_id.map(games_.away_id), F.game_id.map(games_.home_id))
def team_share(d):
    w = d.groupby("winner_team").size(); l = d.groupby("loser_team").size()
    t = pd.concat([w.rename("w"), l.rename("l")], axis=1).fillna(0)
    t["n"] = t.w + t.l; t["share"] = t.w / t.n
    return t
rows = []
shares = {}
for s in SEASONS:
    for label_, d in (("all", F[(F.season == s) & (F.game_type == 2)]), ("5v5 only", F[(F.season == s) & (F.game_type == 2) & (F.gstate == "5v5")])):
        t = team_share(d)
        bsd = np.sqrt((0.25 / t.n).mean())
        d2 = d.copy()
        h1 = team_share(d2[d2.game_id % 2 == 0]); h2 = team_share(d2[d2.game_id % 2 == 1])
        r_split = h1.share.corr(h2.share)
        rows.append(dict(season=SLAB[s], faceoffs=label_, n_teams=len(t), mean_n_per_team=t.n.mean(), mean_share=t.share.mean(), sd_across_teams=t.share.std(), binomial_sd=bsd,
                         ratio_obs_to_binomial=t.share.std() / bsd, min=t.share.min(), max=t.share.max(), odd_even_game_split_corr=r_split))
        shares[(s, label_)] = t.share
H("### 5k. Faceoff win share spread across teams (regular season)")
out.append("Win share = wins / (wins + losses) for the team; mean is 0.5 by construction. `ratio_obs_to_binomial` of 1.0 means the spread is what chance alone gives; `odd_even_game_split_corr` is the correlation of team shares computed on odd vs even game ids (about 16 teams' worth of persistence evidence: values near 0 mean no stable team signal).\n")
out.append(md(pd.DataFrame(rows), 4))
cc = []
for lab in ("all", "5v5 only"):
    for a_, b_ in ((SEASONS[0], SEASONS[1]), (SEASONS[1], SEASONS[2])):
        cc.append(dict(faceoffs=lab, pair=f"{SLAB[a_]} vs {SLAB[b_]}", team_share_corr=shares[(a_, lab)].corr(shares[(b_, lab)])))
out.append("\nCross-season correlation of team win share:\n")
out.append(md(pd.DataFrame(cc), 3))
# playoffs team shares quick
(OUT / "part_c.md").write_text("\n".join(out), encoding="utf-8")
print("done", round(time.time() - t0, 1))
