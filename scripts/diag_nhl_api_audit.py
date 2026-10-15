"""Audit of the cached NHL API tables. Writes markdown tables to the path given as argv[1]."""
import sys
from multiprocessing import Pool

from nhl_sim.pbp.shift_cov import game_cov
from pathlib import Path

import numpy as np
import pandas as pd

P = Path("data/processed")
OUT = Path(sys.argv[1])
md = []


def sec(title):
    md.append(f"\n### {title}\n")


def tab(df, floatfmt=3):
    md.append(df.to_markdown(floatfmt=f".{floatfmt}f") + "\n")


def season_label(s):
    return f"{str(s)[:4]}-{str(s)[6:]}"


def main():
    games = pd.read_parquet(P / "games.parquet")
    sched = pd.read_parquet(P / "schedule.parquet")
    ev = pd.concat([pd.read_parquet(f) for f in sorted((P / "events").glob("events_*.parquet"))], ignore_index=True)
    games["gt"] = games.game_type.map({2: "RS", 3: "PO"})
    ev["gt"] = ev.game_type.map({2: "RS", 3: "PO"})

    # 1. coverage
    sec("1. Games pulled vs expected")
    rows = []
    for (s, gt), g in sched.groupby(["season", "game_type"]):
        fin = g[g.game_state.isin(["OFF", "FINAL"])]
        pulled = ((games.season == s) & (games.game_type == gt)).sum()
        exp = 1312 if gt == 2 and s < 20262027 else None
        rows.append(dict(season=season_label(s), type="RS" if gt == 2 else "PO", schedule_listed=len(g),
                         schedule_final=len(fin), pulled_pbp_box_shift=pulled,
                         expected=exp if exp else ("n/a (in progress)" if gt == 2 else "n/a (series length varies)")))
    tab(pd.DataFrame(rows))

    # 2. event vocabulary
    sec("2. Event-type vocabulary and drift (events per game)")
    ng = games.groupby("season").size()
    v = ev.groupby(["season", "type_desc_key"]).size().unstack(0).fillna(0)
    rate = v / ng
    rate.columns = [season_label(c) for c in rate.columns]
    tab(rate.round(3), 3)
    cnt = v.copy()
    cnt.columns = [season_label(c) for c in cnt.columns]
    md.append("Raw counts:\n")
    tab(cnt.astype(int), 0)

    # 3. coordinates
    sec("3. Shot coordinate coverage (non-shootout shot attempts: SHOT, MISS, BLOCK, GOAL)")
    sa = ev[ev.event.isin(["SHOT", "MISS", "BLOCK", "GOAL"]) & (ev.period_type != "SO")]
    t = sa.groupby(["season", "event"]).apply(lambda d: 100 * d.x.notna().mean(), include_groups=False).unstack()
    t["ALL"] = sa.groupby("season").apply(lambda d: 100 * d.x.notna().mean(), include_groups=False)
    t["n_attempts"] = sa.groupby("season").size()
    t.index = [season_label(i) for i in t.index]
    tab(t, 3)
    md.append("Exact (0,0) coordinate share among shot attempts with coordinates, and out-of-bounds counts:\n")
    sc = sa[sa.x.notna()]
    zz = sc.groupby("season").apply(lambda d: pd.Series(dict(
        pct_xy_exactly_0_0=100 * ((d.x == 0) & (d.y == 0)).mean(), x_min=d.x.min(), x_max=d.x.max(),
        y_min=d.y.min(), y_max=d.y.max())), include_groups=False)
    zz.index = [season_label(i) for i in zz.index]
    tab(zz, 3)

    sec("4. Coordinate convention")
    sh = ev[ev.event.isin(["SHOT", "MISS", "GOAL"]) & ev.x.notna() & (ev.period_type != "SO") & ev.home_def_side.notna()]
    o = sh[sh.zone == "O"].copy()
    o["owner_side"] = np.where(o.owner_is_home, o.home_def_side, o.home_def_side.map({"left": "right", "right": "left"}))
    md.append("Raw x sign for offensive-zone (zone=O) shots by the home team's defending side "
              "(if coordinates were already attack-normalised, raw x would be positive for every side):\n")
    c = o.assign(raw_x_pos=o.x > 0).groupby(["owner_is_home", "home_def_side"]).raw_x_pos.agg(["mean", "size"])
    c.columns = ["share_raw_x_positive", "n"]
    tab(c.reset_index(), 4)
    md.append(f"After normalisation (owner attacks +x): zone=O shots with x_norm>0: "
              f"{100*(o.x_norm>0).mean():.3f}% (n={len(o)}).\n")
    b = ev[(ev.event == "BLOCK") & ev.sx.notna()]
    zc = b.zone.value_counts(normalize=True).mul(100).round(1).to_dict()
    md.append(f"Blocked shots: eventOwnerTeamId is the SHOOTING team (matches the shooter's team in boxscore for "
              f"99.99% of blocks, 2024-25 check); x/y are in the shooter's frame (share with x_norm>0 = "
              f"{100*(b.sx>0).mean():.2f}%, mean {b.sx.mean():.1f}, n={len(b)}), but zoneCode is relative to the "
              f"BLOCKING team (zone shares %: {zc}).\n")
    # period flips
    f = ev[ev.home_def_side.notna() & ev.period.between(1, 4) & (ev.game_type == 2)]
    ds = f.groupby(["game_id", "period"]).home_def_side.agg(lambda s: s.mode().iat[0]).unstack()
    flip12 = (ds[1] != ds[2]).mean()
    flip23 = (ds[2] != ds[3]).mean()
    d34 = ds[[3, 4]].dropna()
    flip34 = (d34[3] != d34[4]).mean()
    inper = f.groupby(["game_id", "period"]).home_def_side.nunique()
    md.append(f"Home defending side (RS games): flips P1->P2 in {100*flip12:.2f}% of games, P2->P3 {100*flip23:.2f}%, "
              f"P3->OT {100*flip34:.2f}% (n={len(d34)}). Periods with more than one value of homeTeamDefendingSide "
              f"inside the period: {int((inper>1).sum())} of {len(inper)}.\n")
    md.append("Shot-attempt x_norm/y_norm summary (SHOT/MISS/GOAL): "
              f"x_norm mean {sh.x_norm.mean():.1f}, y range [{sh.y.min()}, {sh.y.max()}]; goals with sx<0 "
              f"(scored from own half): {int(((ev.event=='GOAL')&(ev.sx<0)).sum())}.\n")

    # 5. goal/shot reference numbers
    sec("5. Per-season reference numbers")
    box_sog = games.assign(sog=games.home_sog_box + games.away_sog_box)
    games["total_goals"] = games.home_score_box + games.away_score_box
    games["total_goals_nonso"] = games.home_goals_playersum + games.away_goals_playersum
    rows = []
    reg_ev = ev[ev.period_type != "SO"]
    for (s, gt), g in games.groupby(["season", "gt"]):
        gid = set(g.game_id)
        e = reg_ev[reg_ev.game_id.isin(gid)]
        n = len(g)
        goals = e[e.event == "GOAL"]
        en_goals = goals.goalie_id.isna().sum()
        # PP segments from situation codes: transition into skaters_for>skaters_against (goalies in)
        e2 = e[e.situation_code.notna()].sort_values(["game_id", "sort_order"]).drop_duplicates(["game_id", "situation_code", "game_time_s"])
        hs_, as_ = e2.home_skaters, e2.away_skaters
        gin = (e2.home_goalie == 1) & (e2.away_goalie == 1)
        home_pp = ((hs_ > as_) & gin).values
        away_pp = ((as_ > hs_) & gin).values
        gidv = e2.game_id.values
        newg = np.r_[True, gidv[1:] != gidv[:-1]]
        hp_start = home_pp & ~np.r_[False, home_pp[:-1]] | (home_pp & newg)
        ap_start = away_pp & ~np.r_[False, away_pp[:-1]] | (away_pp & newg)
        pp_opps = hp_start.sum() + ap_start.sum()
        ppg = goals[(goals.strength_state == "PP")].shape[0]
        pens = e[(e.event == "PENALTY")]
        minors = pens[pens.pen_minutes == 2].shape[0]
        shots_sog = e[e.event.isin(["SHOT", "GOAL"])].shape[0]
        rows.append(dict(
            season=season_label(s), type=gt, games=n, goals_per_game=g.total_goals.mean(),
            goals_per_game_ex_SO_bonus=g.total_goals_nonso.mean(),
            sog_per_game_pbp=shots_sog / n, sog_per_game_box=(g.home_sog_box + g.away_sog_box).mean(),
            attempts_per_game=e.event.isin(["SHOT", "MISS", "BLOCK", "GOAL"]).sum() / n,
            pp_segments_per_team_game=pp_opps / (2 * n), pp_goals_per_team_game=ppg / (2 * n),
            pp_pct_approx=100 * ppg / pp_opps, penalties_all_per_game=len(pens) / n,
            minor2_per_team_game=minors / (2 * n),
            ot_rate_pct=100 * (g.end_state_box != "REG").mean(), so_rate_pct=100 * (g.end_state_box == "SO").mean(),
            en_goals_per_game=en_goals / n, home_win_pct=100 * (g.home_score_box > g.away_score_box).mean()))
    r = pd.DataFrame(rows)
    tab(r.set_index(["season", "type"]).T, 3)
    md.append("Notes: `pp_pct_approx` = PP goals (strength state PP, both goalies in net) / PP segments, where a PP "
              "segment is a transition into skater advantage with both goalies on ice, so 5v4 -> 5v3 is one segment and a "
              "PP ended and restarted counts twice. It is a reference scale, not an official NHL PP%. "
              "`so_rate_pct`/`ot_rate_pct` are percent of all games; for playoffs the OT rate counts any OT game and no "
              "SO exists. `en_goals_per_game` = non-shootout goals with no goalie in net (goalieInNetId absent).\n")

    # pbp vs box SOG
    sec("6. pbp-derived SOG vs boxscore SOG (non-shootout)")
    pb = reg_ev[reg_ev.event.isin(["SHOT", "GOAL"])].groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0)
    pb.columns = ["away_sog_pbp", "home_sog_pbp"]
    gg = games.set_index("game_id").join(pb)
    gg["home_diff"] = gg.home_sog_pbp - gg.home_sog_box
    gg["away_diff"] = gg.away_sog_pbp - gg.away_sog_box
    x = gg.groupby("season").apply(lambda d: pd.Series(dict(
        pct_team_games_exact=100 * np.mean(np.r_[d.home_diff == 0, d.away_diff == 0]),
        pct_within_1=100 * np.mean(np.r_[d.home_diff.abs() <= 1, d.away_diff.abs() <= 1]),
        mean_diff=np.r_[d.home_diff, d.away_diff].mean(), max_abs_diff=np.r_[d.home_diff.abs(), d.away_diff.abs()].max())),
                                   include_groups=False)
    x.index = [season_label(i) for i in x.index]
    tab(x, 3)

    # 7. goalie identification
    sec("7. Goalie identification")
    gb = pd.concat([pd.read_parquet(f) for f in sorted((P / "goalie_box").glob("goalie_box_*.parquet"))])
    st = gb.groupby(["game_id", "team_id"]).starter.agg(lambda s: int((s == True).sum())).rename("n_starters").reset_index()  # noqa: E712
    st = st.merge(games[["game_id", "season"]], on="game_id")
    s1 = st.groupby("season").apply(lambda d: pd.Series(dict(
        team_games=len(d), pct_exactly_one_starter=100 * (d.n_starters == 1).mean(),
        pct_zero=100 * (d.n_starters == 0).mean(), pct_two_plus=100 * (d.n_starters > 1).mean())), include_groups=False)
    s1.index = [season_label(i) for i in s1.index]
    tab(s1, 3)
    # starter vs first goalie_in_net per team
    gi = ev[ev.goalie_id.notna() & ev.event.isin(["SHOT", "GOAL", "MISS"]) & (ev.period_type != "SO")].copy()
    gi["def_team"] = np.where(gi.owner_is_home, gi.game_id.map(games.set_index("game_id").away_id),
                              gi.game_id.map(games.set_index("game_id").home_id))
    first = gi.sort_values(["game_id", "sort_order"]).drop_duplicates(["game_id", "def_team"])[["game_id", "def_team", "goalie_id"]]
    first = first.merge(gb[gb.starter == True][["game_id", "team_id", "player_id"]],  # noqa: E712
                        left_on=["game_id", "def_team"], right_on=["game_id", "team_id"], how="left")
    first["match"] = first.goalie_id == first.player_id
    first = first.merge(games[["game_id", "season"]], on="game_id")
    fm = first.groupby("season").match.agg(["mean", "size"])
    fm["mean"] *= 100
    fm.columns = ["pct_first_faced_goalie_is_boxscore_starter", "n_team_games"]
    fm.index = [season_label(i) for i in fm.index]
    tab(fm, 3)
    tg = gb.groupby(["game_id", "team_id"]).size()
    md.append(f"Goalies appearing per team-game: {tg.value_counts().sort_index().to_dict()}. Goalie rows with decision "
              f"missing: {100*gb.decision.isna().mean():.1f}% (non-decision rows are the non-starters/relievers).\n")

    # 8. shifts coverage
    sec("8. Shift-chart coverage")
    sh_all = pd.concat([pd.read_parquet(f) for f in sorted((P / "shifts").glob("shifts_*.parquet"))], ignore_index=True)
    sh_all = sh_all[sh_all.game_id.isin(games.game_id)]


    jobs = []
    shg_by = {g: d for g, d in sh_all.groupby("game_id")}
    ev_by = {g: d[["sort_order", "game_time_s", "situation_code", "home_skaters", "away_skaters", "home_goalie", "away_goalie"]]
             for g, d in ev[ev.game_type.isin([2, 3])].groupby("game_id")}
    for r_ in games.itertuples():
        jobs.append((r_.game_id, shg_by.get(r_.game_id, sh_all.iloc[0:0]), ev_by[r_.game_id], r_.home_id))
    with Pool(4) as pool:
        cov = pd.DataFrame(pool.map(game_cov, jobs, chunksize=50))
    cov = cov.merge(games[["game_id", "season", "gt"]], on="game_id")
    cs = cov.groupby("season").apply(lambda d: pd.Series(dict(
        games=len(d), pct_games_with_shifts=100 * d.has_shifts.mean(),
        pct_reg_time_skater_counts_match_pbp=100 * d.n_match.sum() / d.n_sec.sum(),
        pct_of_pbp_5v5_time_with_5_and_5_identified=100 * d.n_55_match.sum() / d.n_55.sum(),
        pct_games_5v5_identified_ge_95pct=100 * ((d.n_55_match / d.n_55) >= 0.95).mean(),
        games_missing_position_rows=int((d.shift_rows_no_position.fillna(0) > 0).sum()))), include_groups=False)
    cs.index = [season_label(i) for i in cs.index]
    tab(cs, 2)
    md.append("Method: regulation time only (0-3600 s). For each second, skaters on ice = shifts (typeCode 517, goalies "
              "excluded by roster position) with start <= t < end, vs the skater counts of the latest pbp event's "
              "situationCode. `5_and_5_identified` = seconds where pbp says 5v5 (both goalies in) AND shifts give "
              "exactly 5 and 5. Event-timestamp lag around stoppages and shift-boundary rounding (whole seconds) cause "
              "some mismatch even when coverage is complete.\n")
    shl = sh_all.groupby("season").apply(lambda d: pd.Series(dict(
        shift_rows=len(d), pct_missing_start_or_end=100 * (d.start_s.isna() | d.end_s.isna()).mean(),
        median_dur_s=d.duration_s.median(), pct_no_position=100 * d.position.isna().mean())), include_groups=False)
    shl.index = [season_label(i) for i in shl.index]
    tab(shl, 3)

    OUT.write_text("\n".join(md), encoding="utf-8")
    print("wrote", OUT)



if __name__ == "__main__":
    main()