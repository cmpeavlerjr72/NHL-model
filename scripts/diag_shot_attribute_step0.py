"""SL-R1 step 0: data audit for the shot location x type model (docs/models/shot_attribute/experiments.md SL-R1).

Training seasons only (2021-22, 2022-23, 2023-24; 2024-25 is the fold-2 test season and is not read here).

    diag_shot_attribute_step0.py  -> results/shot_attribute_r1/step0.json + markdown tables (stdout and
                                     results/shot_attribute_r1/step0_tables.md)

1. Blocked-shot coordinates: origin or block point. Distance distributions of BLOCK vs MISS vs SOG(+GOAL) by the event's
   own strength state (pbp situation code; audit only), stratified by shooter position (D / F from player_box);
   blocker position split; shotType coverage on blocks. Shift charts carry no coordinates, so the blocker-shooter
   distance check is NOT AVAILABLE (reported).
2. Shot-type vocabulary by season (unblocked attempts): share per label, labels that appear / vanish, |shift| > 2 pp.
3. Arena distance bias: per season, mean (recorded - both-teams expected) distance of unblocked attempts per arena,
   expected = league + shooting team's road for-offset + defending team's road against-offset; SE = SD of the per-game
   mean residual / sqrt(games).
4. Coverage: (0, 0) coordinates, missing coordinates, missing type, out-of-range points, sx convention.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_events, load_games, load_player_box  # noqa: E402

SEASONS = [20212022, 20222023, 20232024]
OUT = Path("results/shot_attribute_r1")
COLS = ["game_id", "season", "game_type", "event", "period_type", "situation_code", "strength_state", "owner_is_home",
        "shooting_team_id", "shot_type", "shooter_id", "blocker_id", "reason", "x", "y", "sx", "sy", "game_time_s"]
GOAL_X = 89.0


def dist(sx, sy):
    return np.sqrt((GOAL_X - sx) ** 2 + sy ** 2)


def md(df, fmt=".3f"):
    return df.to_markdown(floatfmt=fmt)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ev = load_events(SEASONS, columns=COLS)
    a = ev[ev.event.isin(["SHOT", "MISS", "BLOCK", "GOAL"]) & (ev.period_type != "SO")].copy()
    a = a[~a.situation_code.isin(["0101", "1010"])]
    a["kind"] = a.event.replace({"GOAL": "SOG", "SHOT": "SOG"})
    a["d"] = dist(a.sx, a.sy)
    pb = load_player_box(SEASONS, columns=["game_id", "player_id", "position"]).drop_duplicates(["game_id", "player_id"])
    pos = pb.set_index(["game_id", "player_id"]).position
    a["shooter_pos"] = pd.Series(list(zip(a.game_id, a.shooter_id)), index=a.index).map(pos)
    a["blocker_pos"] = pd.Series(list(zip(a.game_id, a.blocker_id)), index=a.index).map(pos)
    a["shooter_pd"] = np.where(a.shooter_pos == "D", "D", np.where(a.shooter_pos.isin(["C", "L", "R"]), "F", "?"))
    a["blocker_pd"] = np.where(a.blocker_pos == "D", "D", np.where(a.blocker_pos.isin(["C", "L", "R"]), "F", "?"))
    L, res = [], {}

    # ---------------------------------------------------------------- 1. blocks
    ok = a.sx.notna() & a.sy.notna()
    q = lambda s: pd.Series({"n": len(s), "mean_ft": s.mean(), "p10": s.quantile(.1), "p25": s.quantile(.25),  # noqa: E731
                             "median": s.median(), "p75": s.quantile(.75), "share_lt20": (s < 20).mean(),
                             "share_gt45": (s > 45).mean()})
    t1 = a[ok].groupby(["kind"]).d.apply(q).unstack()
    t1s = a[ok & a.strength_state.isin(["5v5", "PP", "PK", "4v4", "3v3"])].groupby(["strength_state", "kind"]).d.apply(q).unstack()
    t1p = a[ok & (a.shooter_pd != "?")].groupby(["shooter_pd", "kind"]).d.apply(q).unstack()
    t1b = a[ok & (a.kind == "BLOCK")].groupby(["blocker_pd", "reason"]).d.apply(q).unstack()
    t1y = a[ok].groupby(["season", "kind"]).d.apply(q).unstack()
    # blocks by D shooters at 5v5 vs unblocked by D shooters at 5v5: KS-like quantile gaps
    dd = a[ok & (a.shooter_pd == "D") & (a.strength_state == "5v5")]
    qs = np.linspace(.05, .95, 19)
    qd = pd.DataFrame({k: dd[dd.kind == k].d.quantile(qs).to_numpy() for k in ("BLOCK", "MISS", "SOG")}, index=[f"q{v:.2f}" for v in qs])
    type_cov = a.groupby(["season", "event"]).shot_type.apply(lambda s: s.notna().mean()).unstack()
    res["block_type_recorded_share"] = float(a[a.kind == "BLOCK"].shot_type.notna().mean())
    res["block_n"] = int((a.kind == "BLOCK").sum())
    res["block_reason_counts"] = a[a.kind == "BLOCK"].reason.value_counts(dropna=False).to_dict()
    L += ["## 1. Blocked-shot coordinates", "",
          "Distance from the goal-line centre (89, 0) in the shooting team's frame (`sx, sy`, L14). Strength state is the "
          "event's own pbp situation (audit only). Penalty shots and shootout attempts excluded.", "",
          "### 1a. All training seasons, by attempt kind", "", md(t1), "",
          "### 1b. By strength state x kind", "", md(t1s), "",
          "### 1c. By shooter position (player_box) x kind", "", md(t1p), "",
          "### 1d. Defencemen at 5v5: distance quantiles by kind (ft)", "", md(qd, ".1f"), "",
          "### 1e. Blocks by blocker position x block reason", "", md(t1b), "",
          "### 1f. By season x kind", "", md(t1y), "",
          "### 1g. shotType recorded share, by season x event", "", md(type_cov, ".4f"), "",
          f"- shotType recorded on blocks: **{res['block_type_recorded_share']:.2%}** of {res['block_n']:,} blocks.",
          f"- Block reasons: {res['block_reason_counts']}.",
          "- Blocker-vs-shooter recorded position check: NOT AVAILABLE. Shift charts carry player ids and times, no "
          "coordinates, and the pbp records one coordinate pair per block event.", ""]

    # ---------------------------------------------------------------- 2. vocabulary
    u = a[a.kind != "BLOCK"]
    voc = u.assign(lbl=u.shot_type.fillna("<missing>")).groupby(["season", "lbl"]).size().unstack(0).fillna(0)
    share = voc / voc.sum(axis=0) * 100
    share["max_abs_shift_pp"] = share[SEASONS].diff(axis=1).abs().max(axis=1)
    share["appears_or_vanishes"] = (voc[SEASONS] == 0).any(axis=1) & (voc[SEASONS] > 0).any(axis=1)
    share["flag"] = np.where(share.appears_or_vanishes | (share.max_abs_shift_pp > 2), "DRIFT", "")
    coll = {"wrist": "wrist+snap", "snap": "wrist+snap", "slap": "slap", "backhand": "backhand", "tip-in": "tip+defl",
            "deflected": "tip+defl", "wrap-around": "wrap"}
    u6 = u.assign(t6=u.shot_type.map(coll).fillna("other"))
    s6 = u6.groupby(["season", "t6"]).size().unstack(0)
    s6 = s6 / s6.sum(axis=0) * 100
    s6["max_abs_shift_pp"] = s6[SEASONS].diff(axis=1).abs().max(axis=1)
    L += ["## 2. Shot-type vocabulary by season (unblocked attempts, % of attempts)", "", md(share, ".3f"), "",
          "### 2b. After the pre-registered six-class collapse (missing type -> other, labelled)", "", md(s6, ".3f"), ""]
    res["vocab_flags"] = share[share.flag == "DRIFT"].index.tolist()

    # ---------------------------------------------------------------- 3. arena distance bias
    g = load_games(SEASONS, columns=["game_id", "home_id", "away_id", "neutral_site", "venue"])
    u = u[u.sx.notna() & u.sy.notna() & u.strength_state.isin(["5v5", "PP", "PK", "4v4", "3v3"])].merge(
        g.drop(columns="season"), on="game_id")
    u["shoot_id"] = np.where(u.owner_is_home.astype(bool), u.home_id, u.away_id)
    u["def_id"] = np.where(u.owner_is_home.astype(bool), u.away_id, u.home_id)
    u["arena"] = np.where(u.neutral_site.astype(bool), "venue:" + u.venue.astype(str), "team:" + u.home_id.astype(str))
    u["shooter_home"] = u.owner_is_home.astype(bool) & ~u.neutral_site.astype(bool)
    u["defender_home"] = ~u.owner_is_home.astype(bool) & ~u.neutral_site.astype(bool)
    rows = []
    for s in SEASONS:
        x = u[u.season == s]
        road_for = x[~x.shooter_home]           # shooting team on the road (or neutral)
        road_ag = x[~x.defender_home]           # defending team on the road (or neutral)
        lg_f, lg_a = road_for.d.mean(), road_ag.d.mean()
        off = road_for.groupby("shoot_id").d.mean() - lg_f
        dfo = road_ag.groupby("def_id").d.mean() - lg_a
        lg = x.d.mean()
        x = x.assign(e=lg + x.shoot_id.map(off).fillna(0) + x.def_id.map(dfo).fillna(0))
        x = x.assign(r=x.d - x.e)
        pg = x.groupby(["arena", "game_id"]).r.mean().reset_index()
        ar = pg.groupby("arena").r.agg(["mean", "std", "count"])
        ar["se"] = ar["std"] / np.sqrt(ar["count"])
        ar["n_attempts"] = x.groupby("arena").size()
        ar["season"] = s
        rows.append(ar.reset_index())
    AR = pd.concat(rows, ignore_index=True).rename(columns={"mean": "bias_ft", "count": "n_games"})
    piv = AR.pivot(index="arena", columns="season", values="bias_ft")
    pse = AR.pivot(index="arena", columns="season", values="se")
    tab = piv.round(2).astype(str) + " (" + pse.round(2).astype(str) + ")"
    tab["n_games_total"] = AR.groupby("arena").n_games.sum()
    reg = AR[AR.n_games >= 30]
    cors = {}
    for s1, s2 in ((SEASONS[0], SEASONS[1]), (SEASONS[1], SEASONS[2])):
        m = piv[[s1, s2]].dropna()
        cors[f"{s1}->{s2}"] = float(np.corrcoef(m[s1], m[s2])[0, 1])
    z = (reg.bias_ft / reg.se)
    res["arena"] = dict(season_to_season_corr=cors, sd_of_bias_ft={int(s): float(reg[reg.season == s].bias_ft.std()) for s in SEASONS},
                        mean_se_ft=float(reg.se.mean()), share_abs_z_gt2=float((z.abs() > 2).mean()),
                        max_abs_bias_ft=float(reg.bias_ft.abs().max()))
    L += ["## 3. Arena distance bias (unblocked attempts, goalies-in states; ft; mean (SE))", "",
          "Bias = mean over the arena's games of the per-game mean of (recorded distance - expected), expected = season "
          "league mean + shooting team's road for-offset + defending team's road against-offset (labelled construction). "
          "SE = SD of the per-game means / sqrt(games).", "", md(tab.sort_index(), ".2f"), "",
          f"- Season-to-season correlation of arena bias: {cors}.",
          f"- SD of arena bias across arenas with >= 30 games: {res['arena']['sd_of_bias_ft']}; mean SE {res['arena']['mean_se_ft']:.2f} ft; "
          f"share |z| > 2: {res['arena']['share_abs_z_gt2']:.2%}; max |bias| {res['arena']['max_abs_bias_ft']:.2f} ft.", ""]

    # ---------------------------------------------------------------- 4. coverage
    cov = []
    for (s, k), x in a.groupby(["season", "kind"]):
        miss = x.sx.isna() | x.sy.isna()
        cov.append(dict(season=s, kind=k, n=len(x), missing_xy=miss.mean(), zero_xy=((x.x == 0) & (x.y == 0)).mean(),
                        out_of_range=((x.x.abs() > 100) | (x.y.abs() > 42.5)).mean(),
                        sx_pos=(x.sx > 0).mean(), behind_goal_line=(x.sx > GOAL_X).mean(),
                        missing_type=x.shot_type.isna().mean()))
    C = pd.DataFrame(cov).set_index(["season", "kind"])
    L += ["## 4. Coverage", "", md(C, ".4f"), "",
          "- `sx, sy`: shooting team attacks +x, goal line at x = 89 (L14; both axes sign-flipped from raw when needed). "
          "Blocks are owned by the shooting team (L15).", ""]
    res["coverage"] = C.reset_index().to_dict("records")
    (OUT / "step0.json").write_text(json.dumps(res, indent=1, default=str))
    (OUT / "step0_tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
