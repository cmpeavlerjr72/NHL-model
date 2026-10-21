"""SL-R7 closed loop for the selected L1x-as (docs/models/shot_attribute/experiments.md SL-R7 / SL-R4 "Closed loop";
D42). G3 gates overall / 5v5 / PP / PK (4v4 / 3v3 reported with n); the G2 re-check lists 4v4 under INV-42 and 3v3
under INV-35, every other cell gates.

Engine (engine/sim.py at 80f0b2e + the attr["l1x"] flag): stage 1 = H3''-LC2 + T2 (D18), stage 3 = A3g-c (D20),
block = B0 STAND-IN with own 4v4 / 3v3 groups (INV-54), stage 4 = **L1x-as** (SL-R7: L0s M1 K500 + L1x-ot0 terms +
as-of Qa scale H45 P10000; shot_attribute.serve_l1xas), miss = S0t STAND-IN (D37), goal = C1s (provisional, D40),
ORACLE GOALIE (box-score starter, D8). No goalie pull (EN unreachable), no rebounds, OT = the stage-1 3v3 OT, SO 50/50
stub. Fold 2 (2024-25); the sealed season is not touched. Before any seed runs, the engine-served L1x-as rows are
checked against the offline fold-2 prediction (< 1e-6), together with E2's four component checks.

    run_shot_attribute_g3_v4.py sim   --seed0 0 --nseeds 50 [--tag sl_r7_g3_L1xas]
    run_shot_attribute_g3_v4.py grade [--tag sl_r7_g3_L1xas]
      -> docs/tests/gates_g3_sl_r7_L1xas_2026-10-21.md, docs/tests/gates_g2_sl_r7_L1xas_2026-10-21.md
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

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.engine import c1s_tables as CT  # noqa: E402
from nhl_sim.engine.rules import era_for_season  # noqa: E402
from nhl_sim.engine.sim import simulate  # noqa: E402
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute import serve_l1xas as SV  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE  # noqa: E402

TEST, LAST_TRAIN = 20242025, 20232024
DATE = "2026-10-21"
STAND_IN = {k: v for k, v in CT.STAND_IN.items() if k != "attr"}
BANNER = ("> **SL-R7 closed loop. Stage 4 = L1x-as (selected on fold 2, D42).** ORACLE GOALIE (the box-score starter faces "
          "every shot on goal, D8). Goal = C1s (provisional, D40). STAND-INS: block B0 (own 4v4 / 3v3 groups, INV-54), "
          "miss S0t (D37). Stages 7-8 absent (no rebounds, no goalie pull: EN unreachable; OT = the stage-1 engine's 3v3 "
          "OT, shootout a 50 / 50 stub). G3 gates overall / 5v5 / PP / PK; 4v4 and 3v3 are reported with n. G2 4v4 is "
          "listed under INV-42 and 3v3 under INV-35.")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_attr(games):
    t0 = time.time()
    sp, gm, linfo = CT.l0s_m1k500_tables(games)
    lx, xinfo = SV.l1xas_tables(games)
    pl = SV.l1xas_parity(games, sp, gm, lx)
    pb, binfo = CT.block_b0g_table(games)
    pbp = CT.b0g_parity(games, pb, binfo)
    pm, minfo = CT.miss_s0t_table(games)
    pmp = CT.miss_parity(games, pm)
    P = CT._goal_parts(games)
    goal, ginfo = CT.goal_c1s_tables(games, P=P)
    pg = CT.goal_parity(games, goal, P)
    par = dict(l1xas=pl, block=pbp, miss=pmp, goal=pg)
    for k, v in par.items():
        print(now(), f"{k} parity: max |diff| {v['max_abs_diff']:.3e} over {v['n_rows']:,} rows", flush=True)
    bad = {k: v["max_abs_diff"] for k, v in par.items() if not v["max_abs_diff"] <= 1e-6}
    if bad:
        raise RuntimeError(f"served != offline: {bad}")
    xg = np.load(Path("data/processed/shot_attribute/xg_ref_v1_f2.npy"))[:, :3]
    attr = dict(state_pdf=sp, game_mult=gm, l1x=lx, p_block_game=pb, p_miss_game=pm, goal=goal, xg=xg, n_type=N_TYPE,
                stand_in=dict(STAND_IN))
    print(now(), f"tables + parity {time.time() - t0:.0f}s", flush=True)
    return attr, dict(parity=par, l0s_level=linfo, l1xas=xinfo, block=binfo, miss=minfo, goal=ginfo)


def cmd_sim(a):
    out = Path("results") / a.tag
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", a.tag, a.seed0, a.nseeds, flush=True)
    E2 = load_mod("e2run", "run_engine_c1s_v1.py")
    G2 = E2.g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"] = np.load(Path("results/shot_attempt_r3/att_lam_A3g-c_fold2.npy"))
    from nhl_sim.shot_attempt.lookup import goal_stub
    tables["p_goal"] = goal_stub(LAST_TRAIN)
    tables["attr"], info = build_attr(games)
    gt = load_games([TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    parts = []
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        o = simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(TEST), seed0=s0, per_team_types=True,
                     seasons=np.full(len(games), TEST))
        marker, amodel = [str(x) for x in o["stand_in"]], str(o["attr_model"][0])
        gmodel, oracle = str(o["goal_model"][0]), str(o["oracle_goalie"][0])
        if any(m.startswith("attr:") for m in marker) or amodel != SV.LABEL:
            raise RuntimeError("stage 4 is not served as L1x-as")
        es = np.array(["", "REG", "OT", "SO"])[o["end_state"]]
        if (es == "").any():
            raise RuntimeError("unfinished sims")
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
        print(now(), f"seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    pd.concat(parts, ignore_index=True).to_parquet(out / f"part_{a.seed0:04d}.parquet", index=False)
    (out / f"meta_{a.seed0:04d}.json").write_text(json.dumps(dict(
        arm="A3g-c", attr_arm="L1x-as (SL-R7, H45 P10000)", round="SL-R7 closed loop (oracle goalie)", stand_in=marker,
        attr_model=amodel, goal_model=gmodel, oracle_goalie=oracle, stage1=G2.S1_LABEL["lc2t2"], stage3="A3g-c (D20)",
        stage4=SV.LABEL, block=CT.BLOCK_LABEL, miss=CT.MISS_LABEL, goal=CT.GOAL_LABEL,
        goalie="ORACLE GOALIE: box-score starter (D8)", goalie_pull="none (EN unreachable)", rebounds="none",
        overtime="stage-1 engine 3v3 OT with C1s goals", shootout="50/50 stub", fold=2, season=TEST,
        sealed_touched=False, info=info, seed0=a.seed0, nseeds=a.nseeds), default=float))
    print(now(), "done", flush=True)


def closed_loop_R(S, A):
    """Closed-loop ES responsiveness (reported): units (game, team), sim vs actual xG_ref per unblocked attempt over ES
    states, deciles of the own as-of Qa ES "for" / the opponent's Qa ES "against" (the L1x-as ratings); D32 slope R
    with game bootstrap, plus the old team-game Q5-Q1."""
    q = pd.read_parquet(M.SA / "sq_ratings_v2_f2.parquet", columns=["game_id", "team_id", "rf_es_Qa", "ra_es_Qa"])
    g = load_games([TEST], columns=["game_id", "home_id", "away_id"]).set_index("game_id")
    es = [0, 3, 4]
    s = S[S.st.isin(es)].groupby(["game_id", "team"])[["fen", "xg"]].sum()
    a = A[A.st.isin(es)].groupby(["game_id", "team"])[["fen", "xg"]].sum()
    j = s.add_suffix("_s").join(a.add_suffix("_a"), how="inner").reset_index()
    j = j[(j.fen_s > 0) & (j.fen_a > 0)]
    tid = np.where(j.team == 0, g.home_id.reindex(j.game_id).to_numpy(), g.away_id.reindex(j.game_id).to_numpy())
    oid = np.where(j.team == 0, g.away_id.reindex(j.game_id).to_numpy(), g.home_id.reindex(j.game_id).to_numpy())
    qi = q.set_index(["game_id", "team_id"])
    own = qi.rf_es_Qa.reindex(pd.MultiIndex.from_arrays([j.game_id, tid])).to_numpy()
    opp = qi.ra_es_Qa.reindex(pd.MultiIndex.from_arrays([j.game_id, oid])).to_numpy()
    out = {}
    for nm, r in (("for", own), ("against", opp)):
        R = slope_ratio(j.xg_s / j.fen_s, j.xg_a / j.fen_a, r, j.fen_a, j.game_id, n_buckets=10, n_boot=1000,
                        pred_weights=j.fen_s)
        out[nm] = dict(R=R["R"], ci=R["ci"], underpowered=R["underpowered"], old_q5q1=R["old_q5q1"], n_units=int(len(j)),
                       table=R["table"].round(6).reset_index().to_dict("records"))
    return out


def cmd_grade(a):
    out = Path("results") / a.tag
    s = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    gt = load_games([TEST], columns=["game_id", "game_type", "home_id", "away_id"])
    s = s.merge(gt[["game_id", "game_type"]], on="game_id")
    nseed = s.seed.nunique()
    m0 = json.loads(sorted(out.glob("meta_*.json"))[0].read_text())
    par = m0["info"]["parity"]
    G3 = load_mod("g3v3", "run_shot_attribute_g3_v3.py")
    E2 = load_mod("e2run", "run_engine_c1s_v1.py")
    SR = load_mod("standins_run", "run_engine_standins_v1.py")
    tol = yaml.safe_load(Path("docs/gates.yaml").read_text())
    rel, mix, min_n = float(tol["g3_xg_rel"]), float(tol["g3_mix_pp"]), int(tol["min_cell_n"])
    r, u = G3.actual_frame()
    S = G3.sim_long(s)
    A = G3.act_long(r, u)
    gi = gt.set_index("game_id")
    head = [f"Engine markers: attr_model `{m0['attr_model']}`; stand_in {m0['stand_in']}; goal_model `{m0['goal_model']}`; "
            f"oracle_goalie `{m0['oracle_goalie']}`.", "",
            "Served-vs-offline parity before the seeds (max |diff|): " +
            "; ".join(f"{k} {v['max_abs_diff']:.2e} over {v['n_rows']:,} rows" for k, v in par.items()) + ".", ""]
    L = [f"# G3 closed loop, SL-R7 L1x-as: {a.tag}, fold 2 (2024-25), {s.game_id.nunique()} games x {nseed} seeds", "",
         BANNER, "", f"Generated {now()} by `scripts/run_shot_attribute_g3_v4.py grade`.", "", *head,
         f"Tolerances g3_xg_rel {rel}, g3_mix_pp {mix}; cells with n < {min_n} actual unblocked attempts UNDERPOWERED. "
         "Gated cells: all reachable, 5v5, PP, PK (xG_ref per unblocked attempt and the three tier shares); 4v4 / 3v3 "
         "reported.", ""]
    summ = {}
    gate_rows = []
    for nm, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        Ss = S if f is None else S[S.game_type == f]
        Aa = A if f is None else A[A.game_type == f]
        T, TT, TY, comp, tot, tl, verdict = G3.g3_tables(Ss, Aa, nseed, rel, mix, min_n)
        T = T.copy()
        TT = TT.copy()
        for k in ("4v4", "3v3"):
            if k in T.index:
                T.loc[k, "status"] = f"reported ({T.loc[k, 'status']})"
        TT["status"] = [f"reported ({v})" if i[0] in ("4v4", "3v3") else v for i, v in zip(TT.index, TT.status)]
        L += [f"## {nm}", "", "### xG_ref per unblocked attempt by team-view state", "", T.to_markdown(floatfmt=".4f"), "",
              "### Location tier shares (%)", "", TT.to_markdown(floatfmt=".3f"), "",
              "### Type shares (%), reported", "", TY.set_index("type").to_markdown(floatfmt=".3f"), "",
              f"### Decomposition of xG per unblocked attempt (sim - actual {tot:+.5f}; tolerance {tl:.5f})", "",
              pd.Series(comp, name="xG per attempt").to_frame().to_markdown(floatfmt="+.5f"), "",
              f"- Decomposition verdict ({nm}): {verdict}", ""]
        if nm == "overall":
            for st in ("all reachable", "5v5", "PP", "PK"):
                gate_rows.append(dict(cell=st, check="xG per unblocked", value=float(T.loc[st, "rel"]), status=T.loc[st, "status"]))
                for tn in ("high", "medium", "low"):
                    row = TT.loc[(st, tn)]
                    gate_rows.append(dict(cell=st, check=f"tier {tn} pp", value=float(row.diff_pp), status=row.status))
            summ["decomposition_verdict"] = verdict
        summ[nm] = dict(states=T.reset_index().to_dict("records"), tiers=TT.reset_index().to_dict("records"),
                        types=TY.to_dict("records"), decomposition=comp, verdict=verdict)
    GT = pd.DataFrame(gate_rows)
    g3_pass = bool((GT.status == "PASS").all())
    L += ["## G3 gate (overall slice; all reachable / 5v5 / PP / PK)", "", GT.to_markdown(index=False, floatfmt="+.4f"), "",
          f"- **G3: {'PASS' if g3_pass else 'FAIL'}**", ""]
    P60 = SR.per60_tables(s, gi)
    L += ["## Attempts, blocked and unblocked attempts per 60 by team-view state (reported)", ""]
    for nm, Tb in P60.items():
        L += [f"### {nm}", "", Tb.to_markdown(floatfmt=".4f"), ""]
    ids_s = np.where(S.team == 0, gi.home_id.reindex(S.game_id).to_numpy(), gi.away_id.reindex(S.game_id).to_numpy())
    ids_a = np.where(A.team == 0, gi.home_id.reindex(A.game_id).to_numpy(), gi.away_id.reindex(A.game_id).to_numpy())
    PT = G3.per_team(S, A, ids_s, ids_a, min_n, rel, mix)
    CR = closed_loop_R(S, A)
    L += ["## Closed-loop ES responsiveness (reported; D32 slope R over (game, team) units, deciles of the as-of Qa ES "
          "rating; 1,000 game bootstrap)", ""]
    for nm, v in CR.items():
        L += [f"- {nm}: R {v['R']:.3f} (95% CI {v['ci'][0]:.3f}..{v['ci'][1]:.3f}; "
              f"{'UNDERPOWERED' if v['underpowered'] else 'powered'}), old Q5-Q1 {v['old_q5q1']:.3f}, {v['n_units']:,} units"]
    L += ["", f"## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual "
          f"{np.corrcoef(PT.xg_sim, PT.xg_act)[0, 1]:.2f}; {int(PT.would_pass_xg.sum())}/{len(PT)} within 3%, "
          f"{int(PT.would_pass_tiers.sum())}/{len(PT)} tiers within 1.5 pp)", "", PT.to_markdown(floatfmt=".4f"), ""]
    T56 = E2.stage56_tables(s)
    L += ["## Stage 5b / 6 by state (reported; stand-in miss, C1s goal, oracle goalie)", ""]
    for nm, Tb in T56.items():
        L += [f"### {nm}", "", Tb.to_markdown(floatfmt=".4f"), ""]
    rep = Path(f"docs/tests/gates_g3_sl_r7_L1xas_{DATE}.md")
    rep.write_text("\n".join(L) + "\n", encoding="utf-8")
    summ.update(g3_gate=GT.to_dict("records"), g3_pass=g3_pass, closed_loop_R=CR,
                per_team=dict(n_within_xg=int(PT.would_pass_xg.sum()), n_within_tiers=int(PT.would_pass_tiers.sum()),
                              n=len(PT), corr=float(np.corrcoef(PT.xg_sim, PT.xg_act)[0, 1])),
                stage56={k: v.reset_index().to_dict("records") for k, v in T56.items()}, parity=par,
                end_state=s.end_state.value_counts().to_dict())
    (out / "g3_summary.json").write_text(json.dumps(summ, indent=1, default=float))
    print(now(), "wrote", rep, "G3", "PASS" if g3_pass else "FAIL", flush=True)
    G2 = E2.g2mod()
    rep2 = Path(f"docs/tests/gates_g2_sl_r7_L1xas_{DATE}.md")
    G2.cmd_grade(argparse.Namespace(arm="A3g-c", tag=a.tag, round="SA-R3", stage1="lc2t2", report=str(rep2)))
    txt = rep2.read_text(encoding="utf-8").split("\n", 1)
    rep2.write_text(txt[0].replace("# G2 closed loop", "# G2 re-check, SL-R7 L1x-as closed loop (oracle goalie)") + "\n\n" +
                    BANNER + "\n" + txt[1], encoding="utf-8")
    print(now(), "wrote", rep2, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag", default="sl_r7_g3_L1xas")
    a = ap.parse_args()
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
