"""SB-R5 (Lane B5): closed loop with the engine DEFAULT table set plus the block B1a-as flag
(nhl_sim.engine.defaults.b1aas_attr): stage 1 H3''-LC2 + T2, stage 3 A3g-c, block B1a-as (replaces B0), stage 4 L1x-as,
miss S0t STAND-IN, goal C1s, ORACLE GOALIE. Pull and shootout flags OFF. Same simulate / grade code as
scripts/run_engine_defaults_v1.py (Lane E3) and run_shot_attribute_g3_v4.py (Lane A7); only the table builder differs,
so every stream is paired with results/engine_defaults_v1.

    run_engine_b1aas_v1.py sim   --seed0 0 --nseeds 50 [--tag engine_b1aas_v1]
    run_engine_b1aas_v1.py grade [--tag engine_b1aas_v1] [--ref engine_defaults_v1]
        G3 / G2 re-check reports (A7 grader) + the SB-R5 block gates: blocked share by state vs actual (SB-R1 bands),
        blocked / unblocked attempts per 60 by state (in the G3 report), team-decile R on the sim block share (D32)
        -> docs/tests/gates_block_b1aas_engine_2026-10-21.md
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.block import data as BD  # noqa: E402
from nhl_sim.block import serve_b1aas as SB  # noqa: E402
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.engine import defaults as DF  # noqa: E402
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402

spec = importlib.util.spec_from_file_location("g3v4", ROOT / "scripts" / "run_shot_attribute_g3_v4.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
G.build_attr = DF.b1aas_attr
G.DATE = "engine_b1aas_2026-10-21"
G.BANNER = ("> **SB-R5 closed loop: engine DEFAULT table set + block B1a-as flag** (attr['block_b1aas'], replaces the B0 "
            "stand-in). Stage 4 = L1x-as, goal = C1s (provisional, D40), ORACLE GOALIE (D8), miss S0t STAND-IN. Pull and "
            "shootout flags OFF (stages 7-8 absent: no rebounds, no goalie pull; OT = stage-1 3v3 OT, shootout 50/50 stub). "
            "G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. (Report text produced by the SL-R7 grader.)")
REPORT = Path("docs/tests/gates_block_b1aas_engine_2026-10-21.md")
TEST = 20242025
ST = ("5v5", "PP", "PK", "4v4", "3v3")
GRP_OF_ST = np.array([0, 1, 2, 0, 0])


def _sim_long(tag):
    out = Path("results") / tag
    s = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    rows = []
    for p, ti in (("h", 0), ("a", 1)):
        for k in range(5):
            rows.append(pd.DataFrame({"game_id": s.game_id, "seed": s.seed, "team": ti, "st": k,
                                      "att": s[f"att_{p}_st{k}"], "fen": s[f"fen_{p}_st{k}"]}))
    L = pd.concat(rows, ignore_index=True)
    L["blk"] = L.att - L.fen
    return L, s.seed.nunique()


def _actual():
    r = pd.read_parquet(ROOT / "results/block_sb_r5/fold2_rows.parquet", columns=["game_id", "team", "st", "y"])
    r = r[r.st <= 4]
    return r.groupby(["game_id", "team", "st"]).agg(att=("y", "size"), blk=("y", "sum")).reset_index()


def block_gates(tag, ref):
    S, ns = _sim_long(tag)
    A = _actual()
    out = {"nseed": ns}
    rows = []
    for nm, tag_ in ((tag, "b1aas"), (ref, "ref B0'")):
        if not (Path("results") / nm).exists():
            continue
        X, n_ = _sim_long(nm)
        for cell, f in [("overall ES+PP+PK", lambda d: d.st <= 4)] + [(f"group {g}", (lambda g_: (lambda d: GRP_OF_ST[d.st] == g_))(gi))
                                                                       for gi, g in enumerate(("ES", "PP", "PK"))] + \
                [(f"state {s_}", (lambda k: (lambda d: d.st == k))(ki)) for ki, s_ in enumerate(ST)]:
            xs, xa = X[f(X)], A[f(A)]
            n = int(xa.att.sum())
            tol = 1.0 if cell.startswith("overall") else 1.5
            gated = cell.startswith("overall") or (cell.startswith("group") and n >= 2000)
            d = 100 * (xs.blk.sum() / xs.att.sum() - xa.blk.sum() / xa.att.sum())
            rows.append(dict(arm=tag_, cell=cell, n_actual=n, sim_pct=100 * xs.blk.sum() / xs.att.sum(),
                             act_pct=100 * xa.blk.sum() / xa.att.sum(), diff_pp=d, tol_pp=tol if gated else np.nan,
                             status=("PASS" if abs(d) <= tol else "FAIL") if gated else
                             ("UNDERPOWERED (reported)" if n < 2000 else "reported")))
    T = pd.DataFrame(rows)
    out["share"] = T.to_dict("records")
    # team-decile R on the sim block share (D32), ES units (game, shooting team); ratings = Ra ES (the served ratings)
    rt = pd.read_parquet(BD.OUT / "ratings_r4_Ra.parquet").set_index(["game_id", "team_id"])
    k = BD.wkey(0.7, 1000)
    g = load_games([TEST], columns=["game_id", "home_id", "away_id"]).set_index("game_id")
    es = [0, 3, 4]
    s = S[S.st.isin(es)].groupby(["game_id", "team"])[["att", "blk"]].sum()
    a = A[A.st.isin(es)].groupby(["game_id", "team"])[["att", "blk"]].sum()
    j = s.add_suffix("_s").join(a.add_suffix("_a"), how="inner").reset_index()
    j = j[(j.att_s > 0) & (j.att_a > 0)]
    tid = np.where(j.team == 0, g.home_id.reindex(j.game_id).to_numpy(), g.away_id.reindex(j.game_id).to_numpy())
    oid = np.where(j.team == 0, g.away_id.reindex(j.game_id).to_numpy(), g.home_id.reindex(j.game_id).to_numpy())
    own = rt[f"rf_es_{k}"].reindex(pd.MultiIndex.from_arrays([j.game_id, tid])).to_numpy()
    opp = rt[f"ra_es_{k}"].reindex(pd.MultiIndex.from_arrays([j.game_id, oid])).to_numpy()
    R = {}
    for nm, r_ in (("for", own), ("against", opp)):
        q = slope_ratio(j.blk_s / j.att_s, j.blk_a / j.att_a, r_, j.att_a, j.game_id, n_buckets=10, n_boot=1000,
                        pred_weights=j.att_s)
        R[nm] = dict(R=q["R"], ci=q["ci"], underpowered=q["underpowered"], old_q5q1=q["old_q5q1"], n_units=int(len(j)),
                     status=q["status"])
    out["R"] = R
    return T, R, out


def cmd_grade(a):
    G.cmd_grade(a)
    T, R, out = block_gates(a.tag, a.ref)
    gs = json.loads((Path("results") / a.tag / "g3_summary.json").read_text())
    rs = Path("results") / a.ref / "g3_summary.json"
    cmp = []
    if rs.exists():
        g0 = json.loads(rs.read_text())
        for x, y in zip(gs["g3_gate"], g0["g3_gate"]):
            cmp.append(dict(cell=x["cell"], check=x["check"], b1aas=x["value"], status=x["status"], ref=y["value"],
                            ref_status=y["status"], delta=x["value"] - y["value"]))
        for nm in ("for", "against"):
            cmp.append(dict(cell="ES", check=f"closed-loop xG R {nm}", b1aas=gs["closed_loop_R"][nm]["R"], status="reported",
                            ref=g0["closed_loop_R"][nm]["R"], ref_status="reported",
                            delta=gs["closed_loop_R"][nm]["R"] - g0["closed_loop_R"][nm]["R"]))
    m0 = json.loads(sorted((Path("results") / a.tag).glob("meta_*.json"))[0].read_text())
    share_ok = bool((T[(T.arm == "b1aas") & T.status.isin(["PASS", "FAIL"])].status == "PASS").all())
    r_ok = all(0.8 <= R[n]["R"] <= 1.2 for n in R)
    L = [f"# SB-R5 closed loop, block B1a-as: {a.tag}, fold 2 (2024-25), {out['nseed']} seeds", "", G.BANNER, "",
         f"Engine markers: block_model in meta `{m0.get('block_model', '')}`; stand_in {m0['stand_in']}; attr_model "
         f"`{m0['attr_model']}`; goal_model `{m0['goal_model']}`; oracle_goalie `{m0['oracle_goalie']}`.", "",
         "Served-vs-offline parity before the seeds (max |diff|): " + "; ".join(
             f"{k} {v['max_abs_diff']:.2e} over {v['n_rows']:,} rows" for k, v in m0["info"]["parity"].items()) + ".", "",
         "## Blocked share by team-view state, sim vs actual (SB-R1 bands: overall +/-1.0 pp, strength group +/-1.5 pp "
         "with n >= 2,000; states reported). `ref B0'` = the paired default-set loop (Lane E3, B0' stand-in), same seeds.", "",
         T.set_index(["arm", "cell"]).to_markdown(floatfmt=".3f"), "",
         f"- **Block share bands: {'PASS' if share_ok else 'FAIL'}** (b1aas arm)", "",
         "## Team-decile R on the sim block share (D32 slope ratio; ES units (game, shooting team); deciles of the "
         "shooting team's Ra ES blocked-against rating (for) / the defending team's Ra ES blocks-for rating (against); "
         "1,000 game bootstrap)", ""]
    for nm, v in R.items():
        L.append(f"- {nm}: R {v['R']:.3f} (95% CI {v['ci'][0]:.3f}..{v['ci'][1]:.3f}; "
                 f"{'UNDERPOWERED' if v['underpowered'] else 'powered'}), old Q5-Q1 {v['old_q5q1']:.3f}, {v['n_units']:,} units")
    L += [f"- **R in [0.8, 1.2]: {'PASS' if r_ok else 'FAIL'}**", "",
          "## G3 / closed-loop R vs the paired default-set loop (B0')", "",
          pd.DataFrame(cmp).to_markdown(index=False, floatfmt="+.4f") if cmp else "(reference loop absent)", "",
          f"- G3 (b1aas): **{'PASS' if gs['g3_pass'] else 'FAIL'}**. Full G3 / per-60 / G2 reports: "
          f"`docs/tests/gates_g3_sl_r7_L1xas_{G.DATE}.md`, `docs/tests/gates_g2_sl_r7_L1xas_{G.DATE}.md`.", ""]
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    out.update(share_pass=share_ok, R_pass=r_ok, g3_pass=gs["g3_pass"], g3_vs_ref=cmp)
    (Path("results") / a.tag / "block_gates.json").write_text(json.dumps(out, indent=1, default=float))
    print("wrote", REPORT, "share", share_ok, "R", {k: round(v["R"], 3) for k, v in R.items()}, "G3", gs["g3_pass"])


_sim0 = G.cmd_sim


def cmd_sim(a):
    _sim0(a)
    out = Path("results") / a.tag
    p = out / f"meta_{a.seed0:04d}.json"
    m = json.loads(p.read_text())
    m.update(block_model=SB.LABEL, block="B1a-as (SB-R5) on the B0' base; replaces the B0 STAND-IN", pull="OFF",
             shootout="OFF (50/50 stub)")
    p.write_text(json.dumps(m, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag", default="engine_b1aas_v1")
    ap.add_argument("--ref", default="engine_defaults_v1")
    a = ap.parse_args()
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
