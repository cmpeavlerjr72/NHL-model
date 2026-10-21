"""INV-60 plumbing closed loop (Lane E2 brief 2026-10-21). PLUMBING, NOT A GATE: nothing here gates. ORACLE GOALIE.

Engine (engine/sim.py, one engine, default-off flags):
  stage 1 = H3''-LC2 + T2 (D18; run_shot_attempt_g2.stage1_tables("lc2t2"), per_team_types=True)
  stage 3 = A3g-c (D20; cached results/shot_attempt_r3/att_lam_A3g-c_fold2.npy)
  block   = B0 STAND-IN with own 4v4 / 3v3 groups (INV-54; engine.c1s_tables.block_b0g_table)
  stage 4 = L0s STAND-IN levelled by M1 K500 (INV-57, D35; engine.c1s_tables.l0s_m1k500_tables)
  miss    = S0t STAND-IN (D37; engine.c1s_tables.miss_s0t_table)
  goal    = C1s (provisional, D40) per shot on goal, ORACLE GOALIE: the box-score starter faces every SOG (D8)
  no goalie pull (EN unreachable), no rebound model (stage 7), OT = the stage-1 engine's 3v3 OT with C1s goals,
  shootout = 50 / 50 stub (no OT / SO model, stage 8). Fold 2 (2024-25) games; the sealed season is not touched.
Before any seed runs, the engine-served values of all four components are checked against the offline fold-2
predictions (< 1e-6).

    run_engine_c1s_v1.py sim   --seed0 0 --nseeds 50 [--tag engine_c1s_plumbing_v1]
    run_engine_c1s_v1.py grade [--tag engine_c1s_plumbing_v1]
      -> docs/tests/gates_g2_engine_c1s_plumbing_2026-10-21.md, docs/tests/gates_g3_engine_c1s_plumbing_2026-10-21.md,
         docs/tests/engine_c1s_stage56_2026-10-21.md, docs/tests/gates_g5g7_engine_c1s_plumbing_2026-10-21.md
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.engine import c1s_tables as CT  # noqa: E402
from nhl_sim.engine.rules import era_for_season  # noqa: E402
from nhl_sim.engine.sim import simulate  # noqa: E402
from nhl_sim.eval import g2 as EG2  # noqa: E402
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402
from nhl_sim.shot_attempt import models as SAM  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE  # noqa: E402

TEST, LAST_TRAIN = 20242025, 20232024
ST5 = ("5v5", "PP", "PK", "4v4", "3v3")
SWAP5 = np.array([0, 2, 1, 3, 4])
DATE = "2026-10-21"
BANNER = ("> **PLUMBING RUN (INV-60). NOTHING HERE GATES. ORACLE GOALIE** (the box-score starter faces every shot on goal, "
          "D8; no in-game goalie change). Goal = **C1s (provisional, D40)**. STAND-INS: block B0 (own 4v4 / 3v3 groups, "
          "INV-54), stage-4 L0s (level M1 K500, INV-57), miss S0t (D37): flat, not adoptable; team-level and "
          "responsiveness readings that pass through them are not evidence about any model. Stages 7-8 absent (no "
          "rebounds, no goalie pull, no OT / shootout model: OT is the stage-1 engine's 3v3 OT, the shootout a 50 / 50 "
          "stub). G2 4v4 is listed under INV-42 and 3v3 under INV-35 (D26).")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def g2mod():
    mod = load_mod("g2run", "run_shot_attempt_g2.py")
    mod.RES = Path("results/shot_attempt_r3")
    mod.FROZEN = Path("docs/models/shot_attempt/sa_r3_frozen_params.json")
    mod.ROUND.update(TV="v2", LEVEL="sa_r3")
    return mod


def build_attr(games):
    t0 = time.time()
    sp, gm, linfo = CT.l0s_m1k500_tables(games)
    pl = CT.l0s_parity(games, sp, gm)
    pb, binfo = CT.block_b0g_table(games)
    pbp = CT.b0g_parity(games, pb, binfo)
    pm, minfo = CT.miss_s0t_table(games)
    pmp = CT.miss_parity(games, pm)
    P = CT._goal_parts(games)
    goal, ginfo = CT.goal_c1s_tables(games, P=P)
    pg = CT.goal_parity(games, goal, P)
    par = dict(l0s=pl, block=pbp, miss=pmp, goal=pg)
    for k, v in par.items():
        print(now(), f"{k} parity: max |diff| {v['max_abs_diff']:.3e} over {v['n_rows']:,} rows", flush=True)
    bad = {k: v["max_abs_diff"] for k, v in par.items() if not v["max_abs_diff"] <= 1e-6}
    if bad:
        raise RuntimeError(f"served != offline: {bad}")
    xg = np.load(Path("data/processed/shot_attribute/xg_ref_v1_f2.npy"))[:, :3]
    attr = dict(state_pdf=sp, game_mult=gm, p_block_game=pb, p_miss_game=pm, goal=goal, xg=xg, n_type=N_TYPE,
                stand_in=dict(CT.STAND_IN))
    print(now(), f"tables + parity {time.time() - t0:.0f}s", flush=True)
    return attr, dict(parity=par, l0s=linfo, block=binfo, miss=minfo, goal=ginfo)


def cmd_sim(a):
    out = Path("results") / a.tag
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", a.tag, a.seed0, a.nseeds, flush=True)
    G2 = g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"] = np.load(Path("results/shot_attempt_r3/att_lam_A3g-c_fold2.npy"))
    from nhl_sim.shot_attempt.lookup import goal_stub
    tables["p_goal"] = goal_stub(LAST_TRAIN)            # unused under the attr variant; required by the engine
    tables["attr"], info = build_attr(games)
    gt = load_games([TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    parts, marker, gmodel, oracle = [], None, None, None
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        o = simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(TEST), seed0=s0, per_team_types=True,
                     seasons=np.full(len(games), TEST))
        marker = [str(x) for x in o["stand_in"]]          # KeyError if the engine dropped a marker
        gmodel, oracle = str(o["goal_model"][0]), str(o["oracle_goalie"][0])
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
        arm="A3g-c", attr_arm="L0s STAND-IN (M1 K500)", round="INV-60 plumbing (oracle goalie)", stand_in=marker,
        goal_model=gmodel, oracle_goalie=oracle, stage1=G2.S1_LABEL["lc2t2"], stage3="A3g-c (D20)", stage4=CT.L0S_LABEL,
        block=CT.BLOCK_LABEL, miss=CT.MISS_LABEL, goal=CT.GOAL_LABEL, goalie="ORACLE GOALIE: box-score starter (D8)",
        goalie_pull="none (EN unreachable)", rebounds="none (stage 7 absent)",
        overtime="stage-1 engine 3v3 OT with C1s goals (no OT model, stage 8 absent)", shootout="50/50 stub",
        fold=2, season=TEST, sealed_touched=False, info=info, seed0=a.seed0, nseeds=a.nseeds, gates="NONE (plumbing)"),
        default=float))
    print(now(), "done", flush=True)


# --------------------------------------------------------------------------------------------- grading helpers
def team_view(s, pre):
    """(2n, 5) team-view arrays [home rows; away rows] of the per-state column family `pre`."""
    return np.concatenate([np.stack([s[f"{pre}_{p}_st{k}"].to_numpy() for k in range(5)], 1) for p in ("h", "a")])


def actual_rows():
    """Fold-2 attempt rows in reachable team-view states 0..4 (stage-4 attempt table)."""
    from nhl_sim.block import data as BD
    a = pd.read_parquet(BD.SA / f"attempt_attr_v1_{TEST}.parquet", columns=["game_id", "game_type", "team", "st", "event"])
    return a[a.st <= 4].reset_index(drop=True)


def _dv(a, b):
    return float(a) / float(b) if b else float("nan")


def stage56_tables(s):
    """Sim vs actual by team-view state: attempts, unblocked, SOG per 60, miss share, save %, goals per 60."""
    toi = np.stack([s[f"toi_{k}_{c}"].to_numpy() for k in range(5) for c in range(7)], 1).reshape(-1, 5, 7).sum(2)
    T = np.concatenate([toi, toi[:, SWAP5]])
    att, fen, sog, gl, gp = (team_view(s, x) for x in ("att", "fen", "sog", "gl", "gp"))
    gtyp = np.concatenate([s.game_type.to_numpy()] * 2)
    R = EG2.real_team_arrays(SAM.load_rows([TEST]))
    Ta = R["T"].sum(2)[:, :5]
    A = actual_rows()
    out = {}
    for nm, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        ms = np.ones(len(gtyp), bool) if f is None else gtyp == f
        mr = np.ones(len(R["game_type"]), bool) if f is None else R["game_type"] == f
        aa = A if f is None else A[A.game_type == f]
        recs = []
        for k in range(5):
            hs, ha = T[ms, k].sum() / 3600, max(Ta[mr, k].sum() / 3600, 1e-9)
            x = aa[aa.st == k]
            u_a = int(x.event.isin(["SHOT", "MISS", "GOAL"]).sum())
            sog_a = int(x.event.isin(["SHOT", "GOAL"]).sum())
            g_a = int((x.event == "GOAL").sum())
            u_s, sog_s, g_s, p_s = fen[ms, k].sum(), sog[ms, k].sum(), gl[ms, k].sum(), gp[ms, k].sum()
            rec = dict(state=ST5[k], n_sog_act=sog_a, sog60_sim=_dv(sog_s, hs), sog60_act=_dv(sog_a, ha),
                       miss_share_sim=1 - _dv(sog_s, u_s), miss_share_act=1 - _dv(sog_a, u_a),
                       sv_sim=1 - _dv(g_s, sog_s), sv_act=1 - _dv(g_a, sog_a), sv_c1s_expected=1 - _dv(p_s, sog_s),
                       g60_sim=_dv(g_s, hs), g60_act=_dv(g_a, ha))
            rec["sog60_rel"] = _dv(rec["sog60_sim"], rec["sog60_act"]) - 1
            rec["miss_pp"] = 100 * (rec["miss_share_sim"] - rec["miss_share_act"])
            rec["sv_pp"] = 100 * (rec["sv_sim"] - rec["sv_act"])
            rec["g60_rel"] = _dv(rec["g60_sim"], rec["g60_act"]) - 1
            if sog_a < 2000:
                rec["note"] = "UNDERPOWERED (n SOG < 2,000)"
            recs.append(rec)
        hs_all, ha_all = T[ms].sum() / 3600, Ta[mr].sum() / 3600
        u_a = int(aa.event.isin(["SHOT", "MISS", "GOAL"]).sum())
        sog_a, g_a = int(aa.event.isin(["SHOT", "GOAL"]).sum()), int((aa.event == "GOAL").sum())
        u_s, sog_s, g_s, p_s = fen[ms].sum(), sog[ms].sum(), gl[ms].sum(), gp[ms].sum()
        recs.append(dict(state="all reachable", n_sog_act=sog_a, sog60_sim=sog_s / hs_all, sog60_act=sog_a / ha_all,
                         miss_share_sim=1 - sog_s / u_s, miss_share_act=1 - sog_a / u_a, sv_sim=1 - g_s / sog_s,
                         sv_act=1 - g_a / sog_a, sv_c1s_expected=1 - p_s / sog_s, g60_sim=g_s / hs_all, g60_act=g_a / ha_all,
                         sog60_rel=(sog_s / hs_all) / (sog_a / ha_all) - 1,
                         miss_pp=100 * ((1 - sog_s / u_s) - (1 - sog_a / u_a)),
                         sv_pp=100 * ((1 - g_s / sog_s) - (1 - g_a / sog_a)), g60_rel=(g_s / hs_all) / (g_a / ha_all) - 1))
        out[nm] = pd.DataFrame(recs).set_index("state")
    return out


def goalie_tables(s, nseed):
    """Per-goalie save % (sim: SOG faced by the goalie as oracle starter, per seed; actual: SOG faced in net, states
    0..4) and the D32 goalie-decile R on sim goal rate vs actual per (game, defending team) with the starter's as-of
    rating."""
    from nhl_sim.goal import data as GD
    rows = pd.read_parquet(CT.G_RES / "fold2" / "fold2_rows.parquet", columns=["game_id", "team_id", "opp_id", "goalie_id",
                                                                                "sg", "y", "g_r"])
    rows = rows[rows.sg <= 4]
    act = rows.groupby("goalie_id").agg(sog_act=("y", "size"), ga_act=("y", "sum"))
    sog_h, sog_a = team_view(s, "sog")[:len(s)].sum(1), team_view(s, "sog")[len(s):].sum(1)
    gl_h, gl_a = team_view(s, "gl")[:len(s)].sum(1), team_view(s, "gl")[len(s):].sum(1)
    # home shots are faced by goalie_vs_h (the away starter); away shots by goalie_vs_a (the home starter)
    u = pd.DataFrame({"game_id": np.concatenate([s.game_id, s.game_id]),
                      "goalie_id": np.concatenate([s.goalie_vs_h, s.goalie_vs_a]),
                      "shooter_home": np.r_[np.ones(len(s), bool), np.zeros(len(s), bool)],
                      "sog": np.concatenate([sog_h, sog_a]), "ga": np.concatenate([gl_h, gl_a])})
    sim = u.groupby("goalie_id").agg(sog_sim=("sog", "sum"), ga_sim=("ga", "sum"))
    sim[["sog_sim", "ga_sim"]] = sim[["sog_sim", "ga_sim"]] / nseed
    G = act.join(sim, how="outer").fillna(0.0)
    G["sv_act"] = 1 - G.ga_act / G.sog_act.where(G.sog_act > 0)
    G["sv_sim"] = 1 - G.ga_sim / G.sog_sim.where(G.sog_sim > 0)
    G["sv_pp"] = 100 * (G.sv_sim - G.sv_act)
    big = G[G.sog_act >= 500].sort_values("sog_act", ascending=False)
    small = G[G.sog_act < 500]
    pooled = dict(n_goalies=int(len(small)), sog_act=float(small.sog_act.sum()), sog_sim=float(small.sog_sim.sum()),
                  sv_act=float(1 - small.ga_act.sum() / small.sog_act.sum()),
                  sv_sim=float(1 - small.ga_sim.sum() / max(small.sog_sim.sum(), 1e-9)))
    # R: units = (game, defending team), starter's as-of rating; actual on the starter's own SOG faced
    gu = u.groupby(["game_id", "goalie_id"]).agg(sog=("sog", "sum"), ga=("ga", "sum")).reset_index()
    au = rows.groupby(["game_id", "goalie_id"]).agg(sog_a=("y", "size"), ga_a=("y", "sum"), g_r=("g_r", "first")).reset_index()
    m = gu.merge(au, on=["game_id", "goalie_id"], how="inner")
    m = m[(m.sog > 0) & (m.sog_a > 0)]
    R = slope_ratio(m.ga / m.sog, m.ga_a / m.sog_a, m.g_r, m.sog_a, m.game_id, n_buckets=10, n_boot=1000,
                    pred_weights=m.sog)
    corr = float(np.corrcoef(big.sv_sim, big.sv_act)[0, 1]) if len(big) > 2 else float("nan")
    return big, pooled, R, corr, int(len(m))


def cmd_grade(a):
    out = Path("results") / a.tag
    s = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    if not ((s.stand_in == 1).all() and (s.oracle_goalie == 1).all()):
        raise ValueError("every part must carry the stand_in and oracle_goalie markers")
    gt = load_games([TEST], columns=["game_id", "game_type", "home_id", "away_id"])
    s = s.merge(gt[["game_id", "game_type"]], on="game_id")
    nseed = s.seed.nunique()
    metas = [json.loads(p.read_text()) for p in sorted(out.glob("meta_*.json"))]
    m0 = metas[0]
    par = m0["info"]["parity"]
    head = [f"Engine markers: stand_in {m0['stand_in']}; goal_model `{m0['goal_model']}`; oracle_goalie "
            f"`{m0['oracle_goalie']}`.", "",
            "Served-vs-offline parity before the seeds (max |diff|): " +
            "; ".join(f"{k} {v['max_abs_diff']:.2e} over {v['n_rows']:,} rows" for k, v in par.items()) + ".", ""]
    # ---- stage 5 / 6 tables
    T56 = stage56_tables(s)
    big, pooled, R, corr, n_units = goalie_tables(s, nseed)
    L = [f"# Stage 5b / 6 closed loop by strength state, INV-60 plumbing: {a.tag}, fold 2 (2024-25), "
         f"{s.game_id.nunique()} games x {nseed} seeds", "", BANNER, "",
         f"Generated {now()} by `scripts/run_engine_c1s_v1.py grade`.", "", *head,
         "Actual side: 2024-25 stage-4 attempt rows in reachable team-view states (5v5 / PP / PK / 4v4 / 3v3; EN excluded, "
         "unreachable). SOG = SHOT + GOAL, miss share = MISS / unblocked, save % = 1 - goals / SOG. TOI from the stage-3 "
         "rows (the G2 source). sv_c1s_expected = 1 - summed C1s probability / SOG in the sim (the model's own expectation "
         "on the sim's shots). Cells with n SOG < 2,000 UNDERPOWERED.", ""]
    for nm, Tb in T56.items():
        L += [f"## {nm}", "", Tb.to_markdown(floatfmt=".4f"), ""]
    L += [f"## Per goalie (>= 500 fold-2 SOG faced in states 0..4; {len(big)} goalies)", "",
          "sim = SOG faced as the ORACLE starter per seed (whole game), actual = SOG faced in net. Correlation of sim and "
          f"actual save % over these goalies: {corr:.3f}.", "",
          big[["sog_act", "sog_sim", "sv_act", "sv_sim", "sv_pp"]].to_markdown(floatfmt=".4f"), "",
          f"Pooled, goalies with < 500 SOG (UNDERPOWERED, {pooled['n_goalies']} goalies): actual {pooled['sog_act']:.0f} "
          f"SOG, sv {pooled['sv_act']:.4f}; sim {pooled['sog_sim']:.0f} SOG per seed, sv {pooled['sv_sim']:.4f}.", "",
          f"## Goalie-decile responsiveness (D32 slope R, goal rate per SOG; units = {n_units:,} (game, starter) pairs, "
          "deciles of the starter's as-of rating g_r, actual = the starter's own SOG faced, 1,000 game bootstrap)", "",
          f"R = {R['R']:.3f} (95% CI {R['ci'][0]:.3f}..{R['ci'][1]:.3f}; {'UNDERPOWERED' if R['underpowered'] else 'powered'}); "
          f"old Q5-Q1 {R['old_q5q1']:.3f}. Reference band [0.8, 1.2]; plumbing, not a gate.", "",
          R["table"].to_markdown(floatfmt=".5f"), ""]
    rep = Path(f"docs/tests/engine_c1s_stage56_{DATE}.md")
    rep.write_text("\n".join(L) + "\n", encoding="utf-8")
    summ = dict(stage56={k: v.reset_index().to_dict("records") for k, v in T56.items()},
                goalies=big.reset_index().to_dict("records"), pooled=pooled, goalie_R=dict(R=R["R"], ci=R["ci"],
                underpowered=R["underpowered"], old_q5q1=R["old_q5q1"]), goalie_sv_corr=corr,
                end_state=s.end_state.value_counts().to_dict(), parity=par)
    (out / "stage56_summary.json").write_text(json.dumps(summ, indent=1, default=float))
    print(now(), "wrote", rep, flush=True)
    # ---- G3 + per 60 (blocked / unblocked) through the stand-in runner's grader pieces
    SR = load_mod("standins_run", "run_engine_standins_v1.py")
    G3 = load_mod("g3v3", "run_shot_attribute_g3_v3.py")
    import yaml
    tol = yaml.safe_load(Path("docs/gates.yaml").read_text())
    rel, mix, min_n = float(tol["g3_xg_rel"]), float(tol["g3_mix_pp"]), int(tol["min_cell_n"])
    r, u = G3.actual_frame()
    S = G3.sim_long(s)
    A = G3.act_long(r, u)
    gi = gt.set_index("game_id")
    L = [f"# G3 by strength state + blocked / unblocked per 60, INV-60 plumbing loop: {a.tag}, fold 2 (2024-25), "
         f"{s.game_id.nunique()} games x {nseed} seeds", "", BANNER, "", f"Generated {now()} by `scripts/run_engine_c1s_v1.py`.",
         "", *head, f"Reference tolerances (not gating): g3_xg_rel {rel}, g3_mix_pp {mix}; cells with n < {min_n} actual "
         "unblocked attempts UNDERPOWERED. PASS / FAIL words are the gate code's labels, read as REFERENCE only.", ""]
    P60 = SR.per60_tables(s, gi)
    L += ["## Attempts, blocked and unblocked attempts per 60 by team-view state (sim vs actual)", ""]
    for nm, Tb in P60.items():
        L += [f"### {nm}", "", Tb.to_markdown(floatfmt=".4f"), ""]
    g3s = {"per60": {k: v.reset_index().to_dict("records") for k, v in P60.items()}}
    for nm, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        Ss = S if f is None else S[S.game_type == f]
        Aa = A if f is None else A[A.game_type == f]
        Tb, TT, TY, comp, tot, tl, verdict = G3.g3_tables(Ss, Aa, nseed, rel, mix, min_n)
        L += [f"## G3 {nm}", "", "### xG_ref per unblocked attempt by team-view state", "", Tb.to_markdown(floatfmt=".4f"), "",
              "### Location tier shares (%)", "", TT.to_markdown(floatfmt=".3f"), "",
              "### Type shares (%), reported", "", TY.set_index("type").to_markdown(floatfmt=".3f"), "",
              f"### Decomposition of xG per unblocked attempt (sim - actual {tot:+.5f}; reference tolerance {tl:.5f})", "",
              pd.Series(comp, name="xG per attempt").to_frame().to_markdown(floatfmt="+.5f"), "",
              f"- Reference verdict ({nm}; not a gate): {verdict}", ""]
        g3s[nm] = dict(states=Tb.reset_index().to_dict("records"), tiers=TT.reset_index().to_dict("records"),
                       decomposition=comp, verdict_reference=verdict)
    rep3 = Path(f"docs/tests/gates_g3_engine_c1s_plumbing_{DATE}.md")
    rep3.write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "g3_summary.json").write_text(json.dumps(g3s, indent=1, default=float))
    print(now(), "wrote", rep3, flush=True)
    # ---- G2 (writes games.parquet and run_meta.json)
    G2 = g2mod()
    rep2 = Path(f"docs/tests/gates_g2_engine_c1s_plumbing_{DATE}.md")
    G2.cmd_grade(argparse.Namespace(arm="A3g-c", tag=a.tag, round="SA-R3", stage1="lc2t2", report=str(rep2)))
    txt = rep2.read_text(encoding="utf-8").split("\n", 1)
    rep2.write_text(txt[0].replace("# G2 closed loop", "# G2 closed loop, INV-60 plumbing (oracle goalie)") + "\n\n" +
                    BANNER + "\n" + txt[1], encoding="utf-8")
    rm = out / "run_meta.json"
    rm.write_text(json.dumps({**json.loads(rm.read_text()), "stand_in": m0["stand_in"], "goal_model": m0["goal_model"],
                              "oracle_goalie": m0["oracle_goalie"], "engine_tag": "event_engine_c1s_inv60",
                              "gates": "NONE (plumbing; stages 7-8 absent)"}, indent=1, default=float))
    print(now(), "wrote", rep2, flush=True)
    # ---- G5-G7 through eval_gates (plumbing, stages 7-8 absent)
    EV = load_mod("evalgates", "eval_gates.py")
    rep5 = Path(f"docs/tests/gates_g5g7_engine_c1s_plumbing_{DATE}.md")
    EV.main(["--results", str(out), "--season", str(TEST), "--out", str(rep5)])
    txt = rep5.read_text(encoding="utf-8").split("\n", 1)
    es = s.end_state.value_counts()
    rep5.write_text(txt[0] + " -- PLUMBING, STAGES 7-8 ABSENT\n\n" + BANNER + "\n\n> **G5-G7 below are labelled plumbing, "
                    "stages 7-8 absent** (no rebounds model, no goalie pull / EN goals, no OT / shootout model). They are "
                    f"not gate results. End states over {len(s):,} sim games: " +
                    ", ".join(f"{k} {v:,} ({v / len(s):.1%})" for k, v in es.items()) + " (OT = stage-1 engine 3v3 OT "
                    "with C1s goals; SO = 50/50 stub).\n" + txt[1], encoding="utf-8")
    print(now(), "wrote", rep5, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag", default="engine_c1s_plumbing_v1")
    a = ap.parse_args()
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
