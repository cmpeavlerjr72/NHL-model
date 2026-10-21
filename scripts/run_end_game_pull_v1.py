"""EG-R1 part A step 5 (Lane H8a, INV-66): 200-seed fold-2 plumbing loop with the goalie-pull flag on (P1 + EN cascade),
everything else the engine default set (D43 / INV-63; ORACLE GOALIE). The same runner with --pull off reproduces Lane
E3's loop (part files bit-identical in content to results/engine_defaults_v1) and adds the G1 columns the E3 loop did not
store, so G1 / G2 / G3 are re-checked pull-on vs pull-off on paired streams.

    run_end_game_pull_v1.py sim   --pull on|off --seed0 0 --nseeds 50     -> results/<tag>/part_*.parquet, extra_*.parquet
    run_end_game_pull_v1.py grade                                          -> docs/tests/end_game_eg_r1_pull_loop_2026-10-21.md
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
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.end_game import en as EN  # noqa: E402
from nhl_sim.engine import defaults as DF  # noqa: E402
from nhl_sim.engine.rules import era_for_season  # noqa: E402
from nhl_sim.engine.sim import TOI_COLS, simulate  # noqa: E402
from nhl_sim.shot_attribute import serve_l1xas as SV  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE  # noqa: E402

TEST, LAST_TRAIN = 20242025, 20232024
TAGS = {"on": "end_game_pull_on_v1", "off": "end_game_pull_off_v1"}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_sim(a):
    tag = TAGS[a.pull]
    out = ROOT / "results" / tag
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", tag, a.seed0, a.nseeds, flush=True)
    E2 = load_mod("e2run", "run_engine_c1s_v1.py")
    G2 = E2.g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"] = np.load(ROOT / "results/shot_attempt_r3/att_lam_A3g-c_fold2.npy")
    from nhl_sim.shot_attempt.lookup import goal_stub
    tables["p_goal"] = goal_stub(LAST_TRAIN)
    tables["attr"], info = DF.default_attr(games)
    pinfo = None
    if a.pull == "on":
        tables["pull"], pinfo = EN.pull_tables(games)
        par = EN.en_parity(games, tables["attr"], tables["pull"])
        for k, v in par.items():
            print(now(), f"EN {k} parity: max |diff| {v['max_abs_diff']:.3e} over {v['n_rows']:,} rows", flush=True)
        bad = {k: v["max_abs_diff"] for k, v in par.items() if not v["max_abs_diff"] <= 1e-6}
        if bad:
            raise RuntimeError(f"EN served != offline: {bad}")
        pinfo["parity"] = par
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
        if a.pull == "on":
            for p, ti in (("h", 0), ("a", 1)):
                for k in (5, 6):
                    for nm, arr in (("att", o["att_st"]), ("fen", o["attr_fen"]), ("sog", o["attr_sog"]), ("gl", o["attr_goals"])):
                        x[f"{nm}_{p}_st{k}"] = arr[:, ti, k]
                for nm in ("pull_s", "n_pulls", "n_repulls", "first_pull_t", "first_pull_def", "pull_at_trail1", "trail1_seen",
                           "n_ret_ga", "n_ret_tie", "n_repull_after_ga"):
                    x[f"{nm}_{p}"] = o[nm][:, ti]
            for k in (5, 6):
                for c in range(7):
                    x[f"toi_{k}_{c}"] = o["toi_st_sc"][:, k, c]
            x["toi_en_s"] = o["pull_s"].sum(1)
        else:
            x["toi_en_s"] = 0
        extras.append(pd.DataFrame(x))
        print(now(), f"seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    pd.concat(parts, ignore_index=True).to_parquet(out / f"part_{a.seed0:04d}.parquet", index=False)
    pd.concat(extras, ignore_index=True).to_parquet(out / f"extra_{a.seed0:04d}.parquet", index=False)
    meta = dict(tag=tag, pull=a.pull, seed0=a.seed0, nseeds=a.nseeds, fold=2, season=TEST, sealed_touched=False,
                stand_in=[str(m) for m in o["stand_in"]], attr_model=str(o["attr_model"][0]), goal_model=str(o["goal_model"][0]),
                oracle_goalie=str(o["oracle_goalie"][0]),
                pull_model=str(o["pull_model"][0]) if a.pull == "on" else "none",
                pull_stand_in=[str(m) for m in o["pull_stand_in"]] if a.pull == "on" else [],
                pull_info=pinfo, delayed_penalty="no engine state (INV-70)")
    (out / f"meta_{a.seed0:04d}.json").write_text(json.dumps(meta, default=float, indent=1))
    print(now(), "done", flush=True)


def _concat(out, pat):
    return pd.concat([pd.read_parquet(f) for f in sorted(out.glob(pat))], ignore_index=True)


def cmd_grade(a):
    """G3 / G2 (A7 grader), G1 + G5-G7 (eval_gates with the EN goals and the strength_toi extension), the EN table."""
    tag = TAGS[a.pull]
    out = ROOT / "results" / tag
    for m in sorted(out.glob("meta_*.json")):                 # the A7 grader reads meta["info"]["parity"]
        d = json.loads(m.read_text())
        if "info" not in d:
            d["info"] = {"parity": {k: v for k, v in ((d.get("pull_info") or {}).get("parity") or {}).items()}}
            m.write_text(json.dumps(d, indent=1, default=float))
    G = load_mod("g3v4", "run_shot_attribute_g3_v4.py")
    G.DATE = f"{tag}_2026-10-21"
    G.BANNER = ("> **EG-R1 part A closed loop (Lane H8a), goalie pull " + a.pull.upper() + ".** Engine default set (D43 / "
                "INV-63): L1x-as, C1s ORACLE GOALIE, STAND-INS block B0 / miss S0t" + (", pull P1 + EN cascade (EN attempt and "
                "EN goal levels STAND-IN)" if a.pull == "on" else ", no goalie pull") + ". No delayed-penalty state (INV-70); "
                "OT = stage-1 3v3, shootout 50 / 50 stub; no rebounds. Report text produced by the SL-R7 grader.")
    G.cmd_grade(argparse.Namespace(tag=tag))
    s = _concat(out, "part_*.parquet")
    x = _concat(out, "extra_*.parquet")
    gm = pd.read_parquet(out / "games.parquet")
    if a.pull == "on":
        en = x[["game_id", "seed"]].assign(home_en_goals=x.gl_h_st6, away_en_goals=x.gl_a_st6)
    else:
        en = x[["game_id", "seed"]].assign(home_en_goals=0, away_en_goals=0)
    gm = gm.drop(columns=[c for c in ("home_en_goals", "away_en_goals") if c in gm.columns]).merge(en, on=["game_id", "seed"])
    gm.to_parquet(out / "games.parquet", index=False)
    st = x[["game_id", "seed", *TOI_COLS, "toi_en_s", "played_s", "ppo_home", "ppo_away", "pen_home", "pen_away", "pim",
            *[c for c in x.columns if c.startswith(("n_minor", "n_double", "n_major", "n_coinc", "minors_"))], "coinc_4v4"]]
    st.to_parquet(out / "strength_toi.parquet", index=False)
    spec5 = importlib.util.spec_from_file_location("evalgates", ROOT / "scripts" / "eval_gates.py")
    EV = importlib.util.module_from_spec(spec5)
    spec5.loader.exec_module(EV)
    rep5 = ROOT / f"docs/tests/gates_g1g5g7_{tag}_2026-10-21.md"
    EV.main(["--results", str(out), "--season", str(TEST), "--out", str(rep5)])
    rep5RS = ROOT / f"docs/tests/gates_g1g5g7_{tag}_RS_2026-10-21.md"
    EV.main(["--results", str(out), "--season", str(TEST), "--segment", "RS", "--out", str(rep5RS)])
    if a.pull == "on":
        en_table(x, out)


def en_table(x, out):
    """EN table: sim (RS, regulation window) vs actual by the same detection rule (non-DP, engine-rule episodes)."""
    from nhl_sim.data.load import load_events
    from nhl_sim.end_game import pull as PL
    D = ROOT / "data/processed/end_game"
    paths, ep = pd.read_parquet(D / "pull_paths_v1_20242025.parquet"), pd.read_parquet(D / "pull_episodes_v1_20242025.parquet")
    act = PL.actual_stats(paths, ep)
    gt = load_games([TEST], columns=["game_id", "game_type"])
    x = x.merge(gt, on="game_id")
    rs = x[x.game_type == 2]
    rs = rs[rs.game_id.isin(paths.game_id)]                     # games with goalie shifts (the actual's game set)
    n = len(rs)
    seen = np.concatenate([rs.trail1_seen_h, rs.trail1_seen_a])
    at1 = np.concatenate([rs.pull_at_trail1_h, rs.pull_at_trail1_a])
    ft = np.concatenate([rs.first_pull_t_h, rs.first_pull_t_a])
    fd = np.concatenate([rs.first_pull_def_h, rs.first_pull_def_a])
    sim = dict(pulled_s_per_game=float((rs.pull_s_h + rs.pull_s_a).sum() / n),
               share_trail1_pulled=float((seen & at1).sum() / seen.sum()),
               first_median_trail1=float(np.median(3600 - ft[(ft >= 0) & (fd == 1)])),
               first_median_trail2=float(np.median(3600 - ft[(ft >= 0) & (fd == 2)])),
               first_median_trail3=float(np.median(3600 - ft[(ft >= 0) & (fd == 3)])),
               repull_share=float((rs.n_repull_after_ga_h + rs.n_repull_after_ga_a).sum() / (rs.n_ret_ga_h + rs.n_ret_ga_a).sum()),
               pulls_per_game=float((rs.n_pulls_h + rs.n_pulls_a).sum() / n))
    ev = load_events([TEST], columns=["game_id", "game_type", "event", "period_type", "strength_state", "goalie_id"])
    ge = ev[(ev.event == "GOAL") & (ev.period_type != "SO") & (ev.game_type == 2)]
    ng_rs = int(gt[gt.game_type == 2].game_id.nunique())
    P = pd.read_parquet(D / "pulls_v1_20242025.parquet")
    Prs = P[P.game_type == 2]
    E = dict(
        en_against_goals_per_game=dict(sim=float((x.gl_h_st6 + x.gl_a_st6).sum() / len(x)),
                                       actual_G7_target=None),
        en_against_goals_per_game_RS=dict(sim=float((rs.gl_h_st6 + rs.gl_a_st6).sum() / n),
                                          actual_pbp=float((ge.strength_state == "EN_AGAINST").sum() / ng_rs),
                                          actual_no_goalie_id=float(ge.goalie_id.isna().sum() / ng_rs)),
        en_for_goals_per_game_RS=dict(sim=float((rs.gl_h_st5 + rs.gl_a_st5).sum() / n),
                                      actual_pbp=float((ge.strength_state == "EN_FOR").sum() / ng_rs)),
        en_attempts_per_game_RS=dict(sim_ef=float((rs.att_h_st5 + rs.att_a_st5).sum() / n),
                                     sim_ea=float((rs.att_h_st6 + rs.att_a_st6).sum() / n)),
        dp_missing=dict(dp_pulled_s_per_game=float(Prs[Prs.dp_overlap].dur.sum() / ng_rs),
                        dp_goals_for_in=int(Prs[Prs.dp_overlap].cause.eq("goal_for").sum()),
                        note="delayed-penalty pulls: absent from the engine (INV-70)"),
    )
    gates = dict(pulled_time=dict(sim=sim["pulled_s_per_game"], actual=act["pulled_s_per_game"],
                                  rel=sim["pulled_s_per_game"] / act["pulled_s_per_game"] - 1,
                                  status="PASS" if abs(sim["pulled_s_per_game"] / act["pulled_s_per_game"] - 1) <= 0.10 else "FAIL"),
                 trail1_share=dict(sim=sim["share_trail1_pulled"], actual=act["share_trail1_pulled"],
                                   pp=100 * (sim["share_trail1_pulled"] - act["share_trail1_pulled"]),
                                   status="PASS" if abs(sim["share_trail1_pulled"] - act["share_trail1_pulled"]) <= 0.03 else "FAIL"))
    res = dict(sim=sim, actual=act, en=E, gates_d45=gates, n_sim_rs_games=n, literal_actual_s_per_game=act["literal_s_per_game"])
    (out / "en_table.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--pull", choices=["on", "off"], default="on")
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    a = ap.parse_args()
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
