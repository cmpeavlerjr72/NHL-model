"""EG-R1 closed loop (Lane H8b, INV-35 / INV-67 on top of Lane H8a's INV-66): 200-seed fold-2 loop with the goalie pull
(P1 + EN cascade), the own 3v3 OT attempt level and the S1 shootout all ON, everything else the engine default set
(D43 / INV-63; ORACLE GOALIE). The paired reference loops are Lane H8a's pull-ON loop (results/end_game_pull_on_v1: same
engine, 3v3 level = A3g-c, shootout = 50/50 stub) and its pull-OFF loop (results/end_game_pull_off_v1, bit-identical in
content to Lane E3's results/engine_defaults_v1).

    run_end_game_otso_v1.py sim   --seed0 0 --nseeds 50 [--ot3v3 on|off] [--shootout on|off]   -> results/end_game_otso_v1
    run_end_game_otso_v1.py grade                                                               -> docs/tests/end_game_eg_r1_otso_loop_2026-10-21.md
"""
import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.data.load import load_events, load_games  # noqa: E402
from nhl_sim.end_game import en as EN  # noqa: E402
from nhl_sim.engine import defaults as DF  # noqa: E402
from nhl_sim.engine.rules import era_for_season  # noqa: E402
from nhl_sim.engine.sim import TOI_COLS, simulate  # noqa: E402
from nhl_sim.shot_attribute import serve_l1xas as SV  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE  # noqa: E402

TEST, LAST_TRAIN = 20242025, 20232024
TAG = "end_game_otso_v1"
REFS = {"E3 / pull-off (H8a)": "end_game_pull_off_v1", "pull-on (H8a)": "end_game_pull_on_v1"}
NL = chr(10)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_sim(a):
    out = ROOT / "results" / TAG
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", TAG, a.seed0, a.nseeds, "ot3v3", a.ot3v3, "shootout", a.shootout, flush=True)
    E2 = load_mod("e2run", "run_engine_c1s_v1.py")
    G2 = E2.g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"], ainfo = DF.att_table(games, ot3v3=(a.ot3v3 == "on"))
    from nhl_sim.shot_attempt.lookup import goal_stub
    tables["p_goal"] = goal_stub(LAST_TRAIN)
    tables["attr"], info = DF.default_attr(games)
    tables["pull"], pinfo = EN.pull_tables(games)
    par = EN.en_parity(games, tables["attr"], tables["pull"])
    for k, v in par.items():
        print(now(), f"EN {k} parity: max |diff| {v['max_abs_diff']:.3e} over {v['n_rows']:,} rows", flush=True)
    if {k: v for k, v in par.items() if not v["max_abs_diff"] <= 1e-6}:
        raise RuntimeError("EN served != offline")
    pinfo["parity"] = par
    if a.shootout == "on":
        tables["shootout"] = DF.shootout_tables(games)
    gt = load_games([TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    parts, extras = [], []
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        o = simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(TEST), seed0=s0, per_team_types=True,
                     seasons=np.full(len(games), TEST))
        es = np.array(["", "REG", "OT", "SO"])[o["end_state"]]
        if (es == "").any():
            raise RuntimeError("unfinished sims")
        if str(o["attr_model"][0]) != SV.LABEL:
            raise RuntimeError("stage 4 is not served as L1x-as")
        gi = o["game_idx"]
        cols = {"game_id": games[gi], "seed": o["seed"].astype(np.int32), "home_goals": o["score"][:, 0],
                "away_goals": o["score"][:, 1], "end_state": es,
                "home_win": np.where(es == "SO", o["so_home_win"], o["score"][:, 0] > o["score"][:, 1]),
                "played_s": o["played_s"], "stand_in": np.int8(1), "oracle_goalie": np.int8(1),
                "goalie_vs_h": o["goalie_against"][gi, 0], "goalie_vs_a": o["goalie_against"][gi, 1]}
        for p, ti in (("h", 0), ("a", 1)):
            for k in range(5):
                cols[f"att_{p}_st{k}"] = o["att_st"][:, ti, k]
                cols[f"fen_{p}_st{k}"] = o["attr_fen"][:, ti, k]
                cols[f"xg_{p}_st{k}"] = o["attr_xg"][:, ti, k].astype(np.float32)
                cols[f"gl_{p}_st{k}"] = o["attr_goals"][:, ti, k]
                cols[f"sog_{p}_st{k}"] = o["attr_sog"][:, ti, k]
                cols[f"gp_{p}_st{k}"] = o["attr_gprob"][:, ti, k].astype(np.float32)
                for c in range(N_CELL):
                    cols[f"cell_{p}_st{k}_{c}"] = o["attr_cell"][:, ti, k, c].astype(np.int16)
                for c in range(N_TYPE):
                    cols[f"type_{p}_st{k}_{c}"] = o["attr_type"][:, ti, k, c].astype(np.int16)
            for k in range(7):
                cols[f"att_{p}_sc{k}"] = o["att_sc"][:, ti, k]
        for s_ in range(5):
            for c in range(7):
                cols[f"toi_{s_}_{c}"] = o["toi_st_sc"][:, s_, c]
        parts.append(pd.DataFrame(cols))
        x = {"game_id": games[gi], "seed": o["seed"].astype(np.int32)}
        for i, c in enumerate(TOI_COLS):
            x[c] = o["toi"][:, i]
        x["played_s"] = o["played_s"]
        x["ppo_home"], x["ppo_away"] = o["ppo"][:, 0], o["ppo"][:, 1]
        x["pen_home"], x["pen_away"] = o["pen_count"][:, 0], o["pen_count"][:, 1]
        x["pim"] = o["pim"]
        for j, c in enumerate(("minor", "double", "major", "coinc")):
            x[f"n_{c}_home"], x[f"n_{c}_away"] = o["n_type"][:, 0, j], o["n_type"][:, 1, j]
        x["minors_home"], x["minors_away"] = o["n_minor"][:, 0], o["n_minor"][:, 1]
        x["minors_pp_ended_home"], x["minors_pp_ended_away"] = o["n_minor_pp_ended"][:, 0], o["n_minor_pp_ended"][:, 1]
        x["coinc_4v4"] = o["coinc_4v4"]
        for p, ti in (("h", 0), ("a", 1)):
            for k in (5, 6):
                for nm, arr in (("att", o["att_st"]), ("fen", o["attr_fen"]), ("sog", o["attr_sog"]), ("gl", o["attr_goals"])):
                    x[f"{nm}_{p}_st{k}"] = arr[:, ti, k]
            for nm in ("pull_s", "n_pulls", "n_repulls", "first_pull_t", "first_pull_def", "pull_at_trail1", "trail1_seen",
                       "n_ret_ga", "n_ret_tie", "n_repull_after_ga"):
                x[f"{nm}_{p}"] = o[nm][:, ti]
            for c in range(4):
                x[f"late_{p}_{c}"] = o["late_goals"][:, ti, c]
        for k in (5, 6):
            for c in range(7):
                x[f"toi_{k}_{c}"] = o["toi_st_sc"][:, k, c]
        x["toi_en_s"] = o["pull_s"].sum(1)
        if a.shootout == "on":
            for nm in ("so_n_att", "so_goals_home", "so_goals_away", "so_home_first"):
                x[nm] = o[nm]
        x["so_home_win"] = o["so_home_win"]
        extras.append(pd.DataFrame(x))
        print(now(), f"seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    pd.concat(parts, ignore_index=True).to_parquet(out / f"part_{a.seed0:04d}.parquet", index=False)
    pd.concat(extras, ignore_index=True).to_parquet(out / f"extra_{a.seed0:04d}.parquet", index=False)
    meta = dict(tag=TAG, pull="on", ot3v3=a.ot3v3, shootout=a.shootout, seed0=a.seed0, nseeds=a.nseeds, fold=2, season=TEST,
                sealed_touched=False, stand_in=[str(m) for m in o["stand_in"]], attr_model=str(o["attr_model"][0]),
                goal_model=str(o["goal_model"][0]), oracle_goalie=str(o["oracle_goalie"][0]), pull_model=str(o["pull_model"][0]),
                pull_stand_in=[str(m) for m in o["pull_stand_in"]], pull_info=pinfo, att_info=ainfo,
                shootout_model=str(o["shootout_model"][0]) if a.shootout == "on" else "50/50 stub",
                delayed_penalty="no engine state (INV-70)")
    (out / f"meta_{a.seed0:04d}.json").write_text(json.dumps(meta, default=float, indent=1))
    print(now(), "done", flush=True)


def _concat(out, pat):
    return pd.concat([pd.read_parquet(f) for f in sorted(out.glob(pat))], ignore_index=True)


def md(df, nd=4):
    return df.round(nd).to_markdown(index=False)


def parse_tables(path):
    """{(section, key): (sim, status)} from a gate report's markdown tables with sim and status columns."""
    res, sec, hdr = {}, "", None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            sec, hdr = line.strip("# ").strip(), None
        elif line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if hdr is None:
                hdr = cells
            elif any(c in hdr for c in ("sim", "xg_sim", "sim_pct")) and "status" in hdr and len(cells) > hdr.index("status"):
                d = dict(zip(hdr, cells))
                sc = next(c for c in ("sim", "xg_sim", "sim_pct") if c in hdr)
                try:
                    res[(sec, d[hdr[0]] if hdr[0] else cells[0])] = (float(d[sc]), d["status"])
                except ValueError:
                    pass
        else:
            hdr = None if not line.startswith("|") else hdr
    return res


def cmd_grade(a):
    out = ROOT / "results" / TAG
    P = load_mod("pullrun", "run_end_game_pull_v1.py")
    for m in sorted(out.glob("meta_*.json")):
        d = json.loads(m.read_text())
        if "info" not in d:
            d["info"] = {"parity": {k: v for k, v in ((d.get("pull_info") or {}).get("parity") or {}).items()}}
            m.write_text(json.dumps(d, indent=1, default=float))
    G = load_mod("g3v4", "run_shot_attribute_g3_v4.py")
    G.DATE = f"{TAG}_2026-10-21"
    G.BANNER = ("> **EG-R1 closed loop (Lane H8b, on Lane H8a's pull).** Engine default set (D43 / INV-63): L1x-as, C1s ORACLE "
                "GOALIE, STAND-INS block B0 / miss S0t; goalie pull P1 + EN cascade (EN attempt and EN goal levels STAND-IN); "
                "3v3 OT attempt level = own as-of M1 K500 (served A3g-c re-levelled); shootout = S1 (rules mechanics, as-of "
                "success and home-first share). No delayed-penalty state (INV-70); no rebounds / faceoffs (stage 7 absent). "
                "Report text produced by the SL-R7 grader.")
    G.cmd_grade(argparse.Namespace(tag=TAG))
    x = _concat(out, "extra_*.parquet")
    gm = pd.read_parquet(out / "games.parquet")
    en = x[["game_id", "seed"]].assign(home_en_goals=x.gl_h_st6, away_en_goals=x.gl_a_st6)
    gm = gm.drop(columns=[c for c in ("home_en_goals", "away_en_goals") if c in gm.columns]).merge(en, on=["game_id", "seed"])
    gm.to_parquet(out / "games.parquet", index=False)
    st = x[["game_id", "seed", *TOI_COLS, "toi_en_s", "played_s", "ppo_home", "ppo_away", "pen_home", "pen_away", "pim",
            *[c for c in x.columns if c.startswith(("n_minor", "n_double", "n_major", "n_coinc", "minors_"))], "coinc_4v4"]]
    st.to_parquet(out / "strength_toi.parquet", index=False)
    EV = load_mod("evalgates", "eval_gates.py")
    rep_all = ROOT / f"docs/tests/gates_g1g5g7_{TAG}_2026-10-21.md"
    res_all = EV.main(["--results", str(out), "--season", str(TEST), "--out", str(rep_all)])
    rep_rs = ROOT / f"docs/tests/gates_g1g5g7_{TAG}_RS_2026-10-21.md"
    res_rs = EV.main(["--results", str(out), "--season", str(TEST), "--segment", "RS", "--out", str(rep_rs)])
    P.en_table(x, out)
    extra_tables(x, gm, out, res_all, res_rs)


def real_late_goals():
    """Actual goals in the last 2 min of regulation by the scorer's deficit before the goal (RS 2024-25; pbp x in
    [3481, 3600] <-> sim seconds [3480, 3600)), per game."""
    ev = load_events([TEST], columns=["game_id", "game_type", "sort_order", "period", "period_type", "event", "game_time_s",
                                      "owner_is_home"])
    ev = ev[(ev.game_type == 2) & (ev.event == "GOAL") & (ev.period_type != "SO")].sort_values(["game_id", "sort_order"])
    own = ev.owner_is_home.astype(bool).to_numpy()
    # running score before each goal, per game
    ev["oh"], ev["oa"] = own.astype(int), (~own).astype(int)
    ev["h_before"] = ev.groupby("game_id").oh.cumsum() - ev.oh
    ev["a_before"] = ev.groupby("game_id").oa.cumsum() - ev.oa
    lead = np.where(own, ev.h_before - ev.a_before, ev.a_before - ev.h_before)
    ev["cat"] = np.where(lead > 0, 0, np.where(lead == 0, 1, np.where(lead == -1, 2, 3)))
    late = ev[(ev.game_time_s >= 3481) & (ev.game_time_s <= 3600)]
    n_games = load_games([TEST], columns=["game_id", "game_type"]).query("game_type == 2").game_id.nunique()
    return late.groupby("cat").size().reindex(range(4), fill_value=0) / n_games, n_games


def real_ot_so():
    from nhl_sim.eval.gates import real_games
    r = real_games(TEST)
    r = r[r.game_type == 2]
    tied = r[r.end_state != "REG"]
    ot, so = r[r.end_state == "OT"], r[r.end_state == "SO"]
    return dict(games=len(r), tie_rate=len(tied) / len(r), so_share_all=len(so) / len(r), ot_goal_share_of_tied=len(ot) / len(tied),
                ot_home_win=float((ot.home_goals > ot.away_goals).mean()), so_home_win=float(so.home_win.mean()),
                n_tied=len(tied), n_ot=len(ot), n_so=len(so))


def real_3v3():
    from nhl_sim.end_game import ot_level as OL
    r = OL.load_rows([TEST])
    hrs = r.exposure_s.sum() / 3600.0 / 2.0                   # game hours: both team views carry the same clock
    return dict(att_per60=r.y.sum() / hrs, goals_per60=r.y_goal.sum() / hrs, hours=hrs)


def extra_tables(x, gm, out, res_all, res_rs):
    gt = load_games([TEST], columns=["game_id", "game_type"])
    need = ["game_id", "seed", "att_h_st4", "att_a_st4", "sog_h_st4", "sog_a_st4", "gl_h_st4", "gl_a_st4",
            *[f"toi_4_{c}" for c in range(7)]]
    parts = pd.concat([pd.read_parquet(f, columns=need) for f in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    x = x.merge(gt, on="game_id").merge(parts, on=["game_id", "seed"])
    rs = x[x.game_type == 2]
    n = len(rs)
    seeds = rs.seed.nunique()
    L = []
    # ---- G7
    g7 = {"all": res_all["G7"], "RS": res_rs["G7"]}
    rows = []
    for seg, r in g7.items():
        for c in r["checks"]:
            rows.append(dict(segment=seg, check=c["check"], sim=c["sim"], real=c["real"], tol=c["tol"], status=c["status"], n=c["n"], note=c["note"]))
    G7 = pd.DataFrame(rows)
    L += ["## G7 (pull ON + 3v3 level + S1)", "", md(G7), ""]
    # ---- OT / SO tables
    ro = real_ot_so()
    es = rs.merge(gm[["game_id", "seed", "end_state", "home_goals", "away_goals", "home_win"]], on=["game_id", "seed"])
    tied = es[es.end_state != "REG"]
    ot, so = es[es.end_state == "OT"], es[es.end_state == "SO"]
    sim_ot = dict(tie_rate=len(tied) / len(es), so_share_all=len(so) / len(es), ot_goal_share_of_tied=len(ot) / len(tied),
                  ot_home_win=float((ot.home_goals > ot.away_goals).mean()), so_home_win=float(so.home_win.mean()))
    t = pd.DataFrame([dict(metric=k, sim=sim_ot[k], actual=ro[k], diff_pp=100 * (sim_ot[k] - ro[k]),
                           note={"ot_goal_share_of_tied": "gate: within 3 pp (UNDERPOWERED, about %d OT games)" % ro["n_ot"],
                                 "ot_home_win": "reported", "so_home_win": "reported (S1 has no home edge beyond shooting first), %d actual SO games" % ro["n_so"],
                                 "tie_rate": "G7: within 1.5 pp", "so_share_all": "G7: within 1.0 pp"}[k]) for k in sim_ot])
    L += ["## OT table (regular season, all seeds)", "", md(t), ""]
    # 3v3 per 60 from the sim: both teams' attempts / SOG / goals in team-view 3v3 over the 3v3 clock
    toi3 = rs[[f"toi_4_{c}" for c in range(7)]].sum().sum()
    r3 = real_3v3()
    sim3 = dict(att_per60=float((rs.att_h_st4.sum() + rs.att_a_st4.sum()) / (toi3 / 3600.0)),
                sog_per60=float((rs.sog_h_st4.sum() + rs.sog_a_st4.sum()) / (toi3 / 3600.0)),
                goals_per60=float((rs.gl_h_st4.sum() + rs.gl_a_st4.sum()) / (toi3 / 3600.0)), hours_per_season=float(toi3 / 3600.0 / seeds))
    t3 = pd.DataFrame([dict(metric="3v3 attempts per 60 (both teams)", sim=sim3["att_per60"], actual=r3["att_per60"], rel=sim3["att_per60"] / r3["att_per60"] - 1),
                       dict(metric="3v3 goals per 60 (both teams)", sim=sim3["goals_per60"], actual=r3["goals_per60"], rel=sim3["goals_per60"] / r3["goals_per60"] - 1),
                       dict(metric="3v3 SOG per 60 (both teams, sim only; the audit's 2021-24 pooled figure is 73.4)", sim=sim3["sog_per60"], actual=np.nan, rel=np.nan),
                       dict(metric="3v3 hours per season (sim mean over seeds vs actual)", sim=sim3["hours_per_season"], actual=r3["hours"], rel=sim3["hours_per_season"] / r3["hours"] - 1)])
    L += ["Sim 3v3 clock is the team-view 3v3 time-on-ice; actual from the attempt rows (2024-25 RS).", "", md(t3), ""]
    # ---- SO table
    if "so_n_att" in rs.columns:
        sox = rs[rs.so_n_att > 0]
        att = load_shootouts_actual()
        t4 = pd.DataFrame([
            dict(metric="per-attempt success", sim=float((sox.so_goals_home + sox.so_goals_away).sum() / sox.so_n_att.sum()), actual=att["success"]),
            dict(metric="share of shootouts past round 3", sim=float((sox.so_n_att > 6).mean()), actual=att["past3"]),
            dict(metric="winner home share", sim=float((sox.so_goals_home > sox.so_goals_away).mean()), actual=att["home_win"]),
            dict(metric="home team shoots first", sim=float(sox.so_home_first.mean()), actual=att["home_first"]),
            dict(metric="mean attempts", sim=float(sox.so_n_att.mean()), actual=att["mean_att"])])
        L += [f"## Shootout table (sim {len(sox)} shootouts over {seeds} seeds; actual {att['n']} shootouts, UNDERPOWERED)", "", md(t4), ""]
    # ---- EN late goals by deficit
    rl, ng = real_late_goals()
    names = ["scorer leading", "tied", "scorer trailing by 1", "scorer trailing by 2+"]
    tl = pd.DataFrame([dict(scorer_state_before=names[c], sim_per_game=float((rs[f"late_h_{c}"].sum() + rs[f"late_a_{c}"].sum()) / n),
                            actual_per_game=float(rl[c])) for c in range(4)])
    tl.loc[len(tl)] = dict(scorer_state_before="all", sim_per_game=tl.sim_per_game.sum(), actual_per_game=tl.actual_per_game.sum())
    L += ["## Goals in the last 2 minutes of regulation by the scorer's deficit before the goal (per RS game, EN goals included)", "",
          "pbp times 3481-3600 s map to sim seconds 3480-3599 (an attempt at pbp second x is the row of second x - 1).", "", md(tl), ""]
    (out / "extra_tables.md").write_text(NL.join(L), encoding="utf-8")
    G7.to_csv(out / "g7.csv", index=False)
    print(NL.join(L))
    # ---- G1-G3 vs the references
    cmp_rows = []
    mine = {}
    for f in ROOT.glob(f"docs/tests/gates_g[23]_sl_r7_L1xas_{TAG}*.md"):
        mine.update({(f.name.split("_")[1],) + k: v for k, v in parse_tables(f).items()})
    mine.update({("g1",) + k: v for k, v in parse_tables(ROOT / f"docs/tests/gates_g1g5g7_{TAG}_2026-10-21.md").items() if "G1" in k[0]})
    for lab, tag in REFS.items():
        ref = {}
        for f in ROOT.glob(f"docs/tests/gates_g[23]_sl_r7_L1xas_{tag}*.md"):
            ref.update({(f.name.split("_")[1],) + k: v for k, v in parse_tables(f).items()})
        rp = ROOT / f"docs/tests/gates_g1g5g7_{tag}_2026-10-21.md"
        if rp.exists():
            ref.update({("g1",) + k: v for k, v in parse_tables(rp).items() if "G1" in k[0]})
        for k, (sv, stt) in mine.items():
            if k in ref and ref[k][1] != "UNREACHABLE":
                cmp_rows.append(dict(ref=lab, gate=k[0], section=k[1][:48], cell=k[2], sim=sv, ref_sim=ref[k][0], diff=sv - ref[k][0],
                                     status=stt, ref_status=ref[k][1], status_changed=stt != ref[k][1]))
    C = pd.DataFrame(cmp_rows)
    C.to_csv(out / "gate_compare.csv", index=False)
    print(C.groupby(["ref", "gate"]).agg(cells=("cell", "size"), status_changed=("status_changed", "sum"), max_abs_diff=("diff", lambda v: float(np.abs(v).max()))))


def load_shootouts_actual():
    from nhl_sim.end_game import shootout as SOF
    a = SOF.so_attempts([TEST])
    g = a.groupby("game_id").agg(n=("k", "size"), hf=("shoot_home", "first"))
    goals = a[a.success == 1].groupby(["game_id", "shoot_home"]).size().unstack(fill_value=0).reindex(g.index).fillna(0)
    return dict(n=len(g), success=float(a.success.mean()), past3=float((g.n > 6).mean()), home_win=float((goals[True] > goals[False]).mean()),
                home_first=float(g.hf.mean()), mean_att=float(g.n.mean()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--ot3v3", choices=["on", "off"], default="on")
    ap.add_argument("--shootout", choices=["on", "off"], default="on")
    ap.add_argument("--tag", default=TAG)
    a = ap.parse_args()
    TAG = a.tag
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
