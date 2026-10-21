"""INV-77 + G5b (Lane E4, 2026-10-21): paired-seed closed loops, fold 2 (2024-25), ORACLE GOALIE, pull and shootout OFF, on the
NEW engine DEFAULT set (`defaults.default_attr`: L1x-as, block B1a-as, miss S0t stand-in, goal C1s; `defaults.att_table`:
A3g-c with the 3v3 OT level ON). Arms: c1s = the default set; sap = the same with attr["goal"] replaced by C1s-sap
(`goal_r4_tables`, flag attr["goal"]["sc_game"]). Only attr["goal"] differs, so all RNG streams are aligned.
One simulate call per chunk writes BOTH the G3-format part file (results/engine_defaults_v2_<arm>) and Lane G4's
recording file (results/engine_defaults_v2_loop/<arm>/rec_*.npz: goal pre-scores, snapshots at 20/40/55/60:00).

    run_engine_defaults_v2.py sim --arm c1s --seed0 0 --nseeds 50 [--tag-suffix ""]
    run_engine_defaults_v2.py grade        -> G3 / G2 / G1-G7 reports per arm, and
                                              docs/tests/engine_defaults_g5b_2026-10-21.md (G5b, goal O/E, G4)
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = load_mod("g3v4", "run_shot_attribute_g3_v4.py")
R4 = load_mod("r4run", "run_engine_goal_r4_v1.py")
from nhl_sim.engine import defaults as DF  # noqa: E402
from nhl_sim.engine import sim as S  # noqa: E402

LOOP = ROOT / "results" / "engine_defaults_v2_loop"
REPORT = ROOT / "docs/tests/engine_defaults_g5b_2026-10-21.md"
BANNER = ("> **INV-77 closed loop, NEW engine DEFAULT table set** (Lane E4): stage 4 = L1x-as, block = B1a-as (SB-R5), "
          "3v3 OT attempt level ON (EG-R1 part B), goal = {goal} (ORACLE GOALIE, D8), miss S0t STAND-IN. Pull and shootout "
          "flags OFF (no goalie pull, 50/50 shootout stub; no rebounds). G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. "
          "(Report text produced by the SL-R7 grader.)")


def tag_of(arm, suffix=""):
    return f"engine_defaults_v2_{arm}{suffix}"


def cmd_sim(a):
    tag = tag_of(a.arm, a.tag_suffix)
    S._BaseGameState = S.GameState

    def build(games):
        attr, info = DF.default_attr(games)
        if a.arm == "sap":
            from nhl_sim.engine import c1s_tables as CT
            from nhl_sim.engine import goal_r4_tables as GR
            P = CT._goal_parts(games)
            goal, _ = GR.goal_r4_tables(games, P=P)
            par = GR.goal_r4_parity(games, goal, P, use_engine=True)
            print(G.now(), f"C1s-sap served vs offline: max |diff| {par['max_abs_diff']:.3e}", flush=True)
            if not par["max_abs_diff"] <= 1e-6:
                raise RuntimeError("served != offline")
            attr["goal"] = goal
            info["parity"]["goal_sap"] = par
        return attr, info

    G.build_attr = build
    G.BANNER = BANNER.format(goal="C1s-sap (G-R4, sc_game flag)" if a.arm == "sap" else "C1s (provisional, D40)")
    G.DATE = tag
    real_sim = S.simulate
    cache = {}

    def sim_wrap(tables, games, gtype, n, era, **kw):
        if "att" not in cache:
            cache["att"], cache["ainfo"] = DF.att_table(games)       # 3v3 OT level ON (default)
        tables = dict(tables, att_lam=cache["att"])
        Rr = R4.install_hook(S, len(games) * n)
        o = real_sim(tables, games, gtype, n, era, **kw)
        if "block_model" not in o or any(str(m).startswith("block:") for m in o["stand_in"]):
            raise RuntimeError("block is not served as B1a-as")
        out = LOOP / a.arm
        out.mkdir(parents=True, exist_ok=True)

        def cat(k):
            return np.concatenate(Rr[k]) if Rr[k] else np.zeros(0)
        np.savez_compressed(out / f"rec_{kw['seed0']:04d}.npz", game_id=np.asarray(games, np.int64), seed0=kw["seed0"], n_seeds=n,
                            game_idx=o["game_idx"], seed=o["seed"], score=o["score"], end_state=o["end_state"],
                            snap=Rr["snap"], g_idx=cat("g_idx"), g_team=cat("g_team"), g_t=cat("g_t"), g_pre=cat("g_pre"),
                            toi_sc=o["toi_st_sc"].sum(1).astype(np.int32), sog=o["attr_sog"], goals=o["attr_goals"],
                            goal_model=str(o["goal_model"][0]))
        return o

    G.simulate = sim_wrap
    ns = argparse.Namespace(tag=tag, seed0=a.seed0, nseeds=a.nseeds, chunk=a.chunk)
    G.cmd_sim(ns)


def cmd_grade(a):
    import json
    import pandas as pd
    for arm in ("c1s", "sap"):
        tag = tag_of(arm)
        G.BANNER = BANNER.format(goal="C1s-sap (G-R4, sc_game flag)" if arm == "sap" else "C1s (provisional, D40)")
        G.DATE = tag
        G.cmd_grade(argparse.Namespace(tag=tag))
        out = Path("results") / tag
        spec5 = importlib.util.spec_from_file_location("evalgates", ROOT / "scripts" / "eval_gates.py")
        EV = importlib.util.module_from_spec(spec5)
        spec5.loader.exec_module(EV)
        EV.main(["--results", str(out), "--season", "20242025", "--out", f"docs/tests/gates_g5g7_{tag}_2026-10-21.md"])
    R4.OUT = LOOP
    R4.REPORT = REPORT
    R4.cmd_grade(argparse.Namespace())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--arm", choices=["c1s", "sap"], default="c1s")
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag-suffix", default="")
    a = ap.parse_args()
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
