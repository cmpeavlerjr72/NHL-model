"""D32 STAND-IN plumbing closed loop (Lane E brief 2026-10-16). PLUMBING, NOT A GATE: nothing here gates.

Engine (engine/sim.py, one engine, default-off flags):
  stage 1 = H3''-LC2 + T2 (D18; run_shot_attempt_g2.stage1_tables("lc2t2"), per_team_types=True)
  stage 3 = A3g-c (D20; cached results/shot_attempt_r3/att_lam_A3g-c_fold2.npy)
  block   = B0 STAND-IN (attr["p_block_game"]: SB-R1 B0 + M1 K500 as-of level; engine.standins.block_b0_table)
  stage 4 = L0s STAND-IN (attr["state_pdf"] + era_mult from GameState.rec_era; engine.standins.l0s_tables)
  goals   = LABELLED STUB: one draw at xG_ref (fold-2 table) per sampled cell x type x group
  no goalie pull (EN unreachable), shootout skipped. Fold 2 (2024-25) games; the sealed season is not touched.
Before any seed runs, the engine-served B0 / L0s values are checked against the offline fold-2 predictions (< 1e-6).

    run_engine_standins_v1.py sim   --seed0 0 --nseeds 50 [--tag standins_plumbing_v1]
    run_engine_standins_v1.py grade [--tag standins_plumbing_v1]
      -> docs/tests/gates_g2_standins_plumbing_2026-10-16.md (G2, all cells)
         docs/tests/gates_g3_standins_plumbing_2026-10-16.md (G3 by strength state; blocked / unblocked per 60)
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.engine import standins as SI  # noqa: E402
from nhl_sim.engine.rules import era_for_season  # noqa: E402
from nhl_sim.engine.sim import simulate  # noqa: E402
from nhl_sim.eval import g2 as EG2  # noqa: E402
from nhl_sim.shot_attempt import models as SAM  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE  # noqa: E402

TEST, LAST_TRAIN = 20242025, 20232024
ST5 = ("5v5", "PP", "PK", "4v4", "3v3")
SWAP5 = np.array([0, 2, 1, 3, 4])
BANNER = ("> **STAND-IN / PLUMBING RUN (D32). NOTHING HERE GATES.** Block = B0 STAND-IN (flat: strength group x period "
          "type + M1 K500 level); stage 4 = L0s STAND-IN (flat, level E from GameState.rec_era); goals = xG_ref STUB. "
          "Team-level and responsiveness readings are against flat stand-ins and are not evidence about any model. "
          "G2 4v4 is listed under INV-42 and 3v3 under INV-35 (D26).")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


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


def standin_attr(games):
    pbg, binfo = SI.block_b0_table(games)
    pb = SI.b0_parity(games, pbg)
    sp, em, linfo = SI.l0s_tables()
    pl = SI.l0s_parity(sp, em)
    print(now(), "B0 parity", pb, flush=True)
    print(now(), "L0s parity", {k: v for k, v in pl.items() if k.startswith(("n_rows", "max_abs_diff"))}, flush=True)
    if pb["max_abs_diff"] > 1e-6 or pl["max_abs_diff"] > 1e-6:
        raise RuntimeError(f"served != offline: B0 {pb}, L0s {pl}")
    xg = np.load(Path("data/processed/shot_attribute/xg_ref_v1_f2.npy"))[:, :3]
    attr = dict(state_pdf=sp, era_mult=em, p_block_game=pbg, xg=xg, n_type=N_TYPE, stand_in=dict(SI.STAND_IN))
    return attr, dict(b0_parity=pb, l0s_parity=pl, b0=binfo, l0s=linfo)


def cmd_sim(a):
    out = Path("results") / a.tag
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", a.tag, a.seed0, a.nseeds, flush=True)
    G2 = g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"] = np.load(Path("results/shot_attempt_r3/att_lam_A3g-c_fold2.npy"))
    from nhl_sim.shot_attempt.lookup import goal_stub
    tables["p_goal"] = goal_stub(LAST_TRAIN)            # unused under the attr variant; required by the engine
    t0 = time.time()
    tables["attr"], par = standin_attr(games)
    print(now(), f"stand-in tables + parity ({time.time() - t0:.0f}s)", flush=True)
    gt = load_games([TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    parts, marker = [], None
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        o = simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(TEST), seed0=s0, per_team_types=True,
                     seasons=np.full(len(games), TEST))
        marker = [str(x) for x in o["stand_in"]]          # KeyError if the engine dropped the marker
        es = np.array(["", "REG", "OT", "SO"])[o["end_state"]]
        if (es == "").any():
            raise RuntimeError("unfinished sims")
        cols = {"game_id": games[o["game_idx"]], "seed": o["seed"].astype(np.int32), "home_goals": o["score"][:, 0],
                "away_goals": o["score"][:, 1], "end_state": es,
                "home_win": np.where(es == "SO", o["so_home_win"], o["score"][:, 0] > o["score"][:, 1]),
                "played_s": o["played_s"], "stand_in": np.int8(1)}
        for p, ti in (("h", 0), ("a", 1)):
            for k in range(5):
                cols[f"att_{p}_st{k}"] = o["att_st"][:, ti, k]
                cols[f"fen_{p}_st{k}"] = o["attr_fen"][:, ti, k]
                cols[f"xg_{p}_st{k}"] = o["attr_xg"][:, ti, k].astype(np.float32)
                cols[f"gl_{p}_st{k}"] = o["attr_goals"][:, ti, k]
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
        arm="A3g-c", attr_arm="L0s STAND-IN", round="D32 stand-in plumbing", stand_in=marker,
        stage1=G2.S1_LABEL["lc2t2"], stage3="A3g-c (D20)", stage4=SI.ATTR_LABEL, block=SI.BLOCK_LABEL,
        goals="STUB: xG_ref (fold-2 table) per sampled cell x type x group", p_goal=tables["p_goal"].tolist(),
        goalie_pull="none (EN unreachable)", shootout="skipped", fold=2, season=TEST, sealed_touched=False,
        parity=par, seed0=a.seed0, nseeds=a.nseeds, gates="NONE (plumbing)"), default=float))
    print(now(), "done", flush=True)


# ------------------------------------------------------------------------------- blocked / unblocked per 60
def per60_tables(s, gt_of):
    """Sim vs actual attempts, blocked and unblocked attempts per 60 by team-view state (RS / PO / overall)."""
    toi = np.stack([s[f"toi_{k}_{c}"].to_numpy() for k in range(5) for c in range(7)], 1).reshape(-1, 5, 7).sum(2)
    att = np.concatenate([np.stack([s[f"att_{p}_st{k}"].to_numpy() for k in range(5)], 1) for p in ("h", "a")])
    fen = np.concatenate([np.stack([s[f"fen_{p}_st{k}"].to_numpy() for k in range(5)], 1) for p in ("h", "a")])
    T = np.concatenate([toi, toi[:, SWAP5]])                        # team-view seconds by state
    gtyp = np.concatenate([s.game_type.to_numpy()] * 2)
    R = EG2.real_team_arrays(SAM.load_rows([TEST]))
    Ta, Aa = R["T"].sum(2)[:, :5], R["A"].sum(2)[:, :5]
    rows = M.load_rows([TEST])
    rows = rows[rows.st <= 4]
    out = {}
    for nm, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        ms = np.ones(len(gtyp), bool) if f is None else gtyp == f
        mr = np.ones(len(R["game_type"]), bool) if f is None else R["game_type"] == f
        rr = rows if f is None else rows[rows.game_type == f]
        recs = []
        for k in range(5):
            hs, ha = T[ms, k].sum() / 3600, max(Ta[mr, k].sum() / 3600, 1e-9)
            x = rr[rr.st == k]
            b_a, u_a = int(x.blocked.sum()), int((~x.blocked).sum())
            a_s, f_s = att[ms, k].sum(), fen[ms, k].sum()
            rec = dict(state=ST5[k], toi_h_per_game_sim=hs / ms.sum() * 2, toi_h_per_game_act=ha / mr.sum() * 2,
                       att60_sim=a_s / hs, att60_act=Aa[mr, k].sum() / ha, att60_act_attr_rows=(b_a + u_a) / ha,
                       blk60_sim=(a_s - f_s) / hs, blk60_act=b_a / ha, unb60_sim=f_s / hs, unb60_act=u_a / ha,
                       blk_share_sim=1 - f_s / a_s, blk_share_act=b_a / (b_a + u_a) if b_a + u_a else np.nan, n_blocked_act=b_a, n_unblocked_act=u_a)
            for q in ("att60", "blk60", "unb60"):
                rec[f"{q}_rel"] = rec[f"{q}_sim"] / rec[f"{q}_act"] - 1 if rec[f"{q}_act"] > 0 else np.nan
            rec["blk_share_diff_pp"] = 100 * (rec["blk_share_sim"] - rec["blk_share_act"])
            recs.append(rec)
        out[nm] = pd.DataFrame(recs).set_index("state")
    return out


def cmd_grade(a):
    out = Path("results") / a.tag
    s = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    if not (s.stand_in == 1).all():
        raise ValueError("every part must carry the stand_in marker")
    gt = load_games([TEST], columns=["game_id", "game_type", "home_id", "away_id"])
    s = s.merge(gt[["game_id", "game_type"]], on="game_id")
    nseed = s.seed.nunique()
    metas = [json.loads(p.read_text()) for p in sorted(out.glob("meta_*.json"))]
    G3 = load_mod("g3v3", "run_shot_attribute_g3_v3.py")
    tol = yaml.safe_load(Path("docs/gates.yaml").read_text())
    rel, mix, min_n = float(tol["g3_xg_rel"]), float(tol["g3_mix_pp"]), int(tol["min_cell_n"])
    r, u = G3.actual_frame()
    S = G3.sim_long(s)
    A = G3.act_long(r, u)
    gi = gt.set_index("game_id")
    L = [f"# G3 by strength state + blocked / unblocked per 60, STAND-IN plumbing loop: {a.tag}, fold 2 (2024-25), "
         f"{s.game_id.nunique()} games x {nseed} seeds", "", BANNER, "",
         f"Generated {now()} by `scripts/run_engine_standins_v1.py`. Engine marker: {metas[0]['stand_in']}. Stage 1 = "
         "H3''-LC2 + T2; stage 3 = A3g-c; block = B0 STAND-IN; stage 4 = L0s STAND-IN (rule (b): unblocked attempts "
         "only); goals = xG_ref STUB. No goalie pull (EN UNREACHABLE; actual side restricted to 5v5 / PP / PK / 4v4 / "
         f"3v3), shootout skipped. Reference tolerances (not gating): g3_xg_rel {rel}, g3_mix_pp {mix}; cells with "
         f"n < {min_n} actual unblocked attempts UNDERPOWERED. PASS / FAIL words below are the gate code's labels, "
         "read as REFERENCE only.", "",
         f"Served-vs-offline parity before the seeds: B0 max |dp| {metas[0]['parity']['b0_parity']['max_abs_diff']:.2e} "
         f"over {metas[0]['parity']['b0_parity']['n_rows']:,} rows; L0s max |dP| "
         f"{metas[0]['parity']['l0s_parity']['max_abs_diff']:.2e} over {metas[0]['parity']['l0s_parity']['n_rows']:,} rows.", ""]
    P60 = per60_tables(s, gi)
    L += ["## Attempts, blocked and unblocked attempts per 60 by team-view state (sim vs actual)", "",
          "att60_act from the stage-3 attempt rows (the G2 source); att60_act_attr_rows from the stage-4 attempt rows "
          "(blocked / unblocked source), shown as a consistency check. TOI hours per game are per team.", ""]
    for nm, T in P60.items():
        L += [f"### {nm}", "", T.to_markdown(floatfmt=".4f"), ""]
    summ = {"per60": {k: v.reset_index().to_dict("records") for k, v in P60.items()}}
    for nm, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        Ss = S if f is None else S[S.game_type == f]
        Aa = A if f is None else A[A.game_type == f]
        T, TT, TY, comp, tot, tl, verdict = G3.g3_tables(Ss, Aa, nseed, rel, mix, min_n)
        L += [f"## G3 {nm}", "", "### xG_ref per unblocked attempt by team-view state", "", T.to_markdown(floatfmt=".4f"), "",
              "### Location tier shares (%)", "", TT.to_markdown(floatfmt=".3f"), "",
              "### Type shares (%), reported", "", TY.set_index("type").to_markdown(floatfmt=".3f"), "",
              f"### Decomposition of xG per unblocked attempt (sim - actual {tot:+.5f}; reference tolerance {tl:.5f})", "",
              pd.Series(comp, name="xG per attempt").to_frame().to_markdown(floatfmt="+.5f"), "",
              f"- Reference verdict ({nm}; not a gate): {verdict}", ""]
        summ[nm] = dict(states=T.reset_index().to_dict("records"), tiers=TT.reset_index().to_dict("records"),
                        types=TY.to_dict("records"), decomposition=comp, verdict_reference=verdict)
    ids_s = np.where(S.team == 0, gi.home_id.reindex(S.game_id).to_numpy(), gi.away_id.reindex(S.game_id).to_numpy())
    ids_a = np.where(A.team == 0, gi.home_id.reindex(A.game_id).to_numpy(), gi.away_id.reindex(A.game_id).to_numpy())
    PT = G3.per_team(S, A, ids_s, ids_a, min_n, rel, mix)
    L += [f"## Per team, against the FLAT stand-in (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual "
          f"{np.corrcoef(PT.xg_sim, PT.xg_act)[0, 1]:.2f}). Stage 4 is flat, so team variation in the sim comes only "
          "from strength-state and score paths.", "", PT.to_markdown(floatfmt=".4f"), "",
          "Responsiveness (D32 slope R) is not computed here: both stand-ins are flat by construction (R undefined / "
          "no slope), and the D32 helper is Lane R's.", ""]
    gl = s[["home_goals", "away_goals"]].sum(axis=1).mean()
    ga = A.gl.sum() / A.game_id.nunique()
    gen = u[u.st > 4].is_goal.sum() / A.game_id.nunique()
    L += [f"## Goals (reported; stub goal model): sim goals per game ex-shootout {gl:.3f}; actual goals per game in "
          f"reachable states {ga:.3f} (+ {gen:.3f} in EN states, unreachable in the sim)", ""]
    rep = Path("docs/tests/gates_g3_standins_plumbing_2026-10-16.md")
    rep.write_text("\n".join(L) + "\n", encoding="utf-8")
    summ["sim_goals_per_game"] = float(gl)
    summ["actual_goals_per_game_reachable"] = float(ga)
    (out / "g3_summary.json").write_text(json.dumps(summ, indent=1, default=float))
    print(now(), "wrote", rep, flush=True)
    G2 = g2mod()
    rep2 = Path("docs/tests/gates_g2_standins_plumbing_2026-10-16.md")
    G2.cmd_grade(argparse.Namespace(arm="A3g-c", tag=a.tag, round="SA-R3", stage1="lc2t2", report=str(rep2)))
    txt = rep2.read_text(encoding="utf-8").split("\n", 1)
    rep2.write_text(txt[0].replace("# G2 closed loop", "# G2 closed loop, STAND-IN plumbing (D32)") + "\n\n" + BANNER +
                    "\n" + txt[1], encoding="utf-8")
    rm = out / "run_meta.json"
    rm.write_text(json.dumps({**json.loads(rm.read_text()), "stand_in": metas[0]["stand_in"],
                              "engine_tag": "event_engine_standins_d32", "gates": "NONE (plumbing)"}, indent=1))
    print(now(), "wrote", rep2, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag", default="standins_plumbing_v1")
    a = ap.parse_args()
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
