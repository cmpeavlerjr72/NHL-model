"""INV-63 (Lane E3): plumbing closed loop with the engine's DEFAULT table set (nhl_sim.engine.defaults.default_attr):
stage 1 H3''-LC2 + T2, stage 3 A3g-c, block B0 STAND-IN, stage 4 L1x-as, miss S0t STAND-IN, goal C1s, ORACLE GOALIE.
Same simulate/grade code as scripts/run_shot_attribute_g3_v4.py (Lane A7 SL-R7 loop); only the table builder is the
default one, so the per-seed outputs must be bit-identical to results/sl_r7_g3_L1xas. PLUMBING, NOT A GATE.

    run_engine_defaults_v1.py sim   --seed0 0 --nseeds 50 [--tag engine_defaults_v1]
    run_engine_defaults_v1.py grade [--tag engine_defaults_v1]
    run_engine_defaults_v1.py cmp   [--tag engine_defaults_v1] [--ref sl_r7_g3_L1xas]   (bit-identity of the part files)
"""
import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.engine import defaults as DF  # noqa: E402

spec = importlib.util.spec_from_file_location("g3v4", ROOT / "scripts" / "run_shot_attribute_g3_v4.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
G.build_attr = DF.default_attr
G.DATE = "engine_defaults_2026-10-21"
G.BANNER = ("> **INV-63 plumbing closed loop, engine DEFAULT table set.** Stage 4 = L1x-as (D42/D43), goal = C1s "
            "(provisional, D40), ORACLE GOALIE (D8). STAND-INS: block B0 (INV-54), miss S0t (D37). Stages 7-8 absent "
            "(no rebounds, no goalie pull; OT = stage-1 3v3 OT, shootout 50/50 stub). G3 gates overall / 5v5 / PP / PK; "
            "4v4 / 3v3 reported. G2 4v4 listed under INV-42, 3v3 under INV-35. (Report text produced by the SL-R7 "
            "grader; titles saying SL-R7 refer to the identical stack.)")


def sha_df(p):
    import pandas as pd
    df = pd.read_parquet(p)
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes() +
                          "|".join(df.columns).encode()).hexdigest()


def cmd_grade(a):
    import json
    import pandas as pd
    G.cmd_grade(a)
    out = Path("results") / a.tag
    m0 = json.loads(sorted(out.glob("meta_*.json"))[0].read_text())
    rm = out / "run_meta.json"
    rm.write_text(json.dumps({**json.loads(rm.read_text()), "stand_in": m0["stand_in"], "attr_model": m0["attr_model"],
                              "goal_model": m0["goal_model"], "oracle_goalie": m0["oracle_goalie"],
                              "engine_tag": "event_engine_defaults_inv63",
                              "gates": "NONE (plumbing; stages 7-8 absent)"}, indent=1, default=float))
    spec5 = importlib.util.spec_from_file_location("evalgates", ROOT / "scripts" / "eval_gates.py")
    EV = importlib.util.module_from_spec(spec5)
    spec5.loader.exec_module(EV)
    rep5 = Path("docs/tests/gates_g5g7_engine_defaults_2026-10-21.md")
    EV.main(["--results", str(out), "--season", "20242025", "--out", str(rep5)])
    s = pd.read_parquet(out / "games.parquet")
    es = s.end_state.value_counts()
    txt = rep5.read_text(encoding="utf-8").split("\n", 1)
    rep5.write_text(txt[0] + " -- PLUMBING, STAGES 7-8 ABSENT\n\n" + G.BANNER + "\n\n> **G5-G7 below are labelled plumbing, "
                    "stages 7-8 absent** (no rebounds, no goalie pull / EN goals, no OT / shootout model). Not gate results. "
                    f"End states over {len(s):,} sim games: " + ", ".join(f"{k} {v:,} ({v / len(s):.1%})"
                                                                         for k, v in es.items()) + "\n" + txt[1], encoding="utf-8")
    print("wrote", rep5)


def cmd_cmp(a):
    ok = True
    for p in sorted((Path("results") / a.tag).glob("part_*.parquet")):
        q = Path("results") / a.ref / p.name
        h1, h2 = sha_df(p), sha_df(q)
        f1, f2 = hashlib.sha256(p.read_bytes()).hexdigest(), hashlib.sha256(q.read_bytes()).hexdigest()
        print(p.name, "content", h1 == h2, "file", f1 == f2, h1[:12], h2[:12])
        ok &= h1 == h2
    print("BIT-IDENTICAL (content)" if ok else "DIFFERENT")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade", "cmp"])
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag", default="engine_defaults_v1")
    ap.add_argument("--ref", default="sl_r7_g3_L1xas")
    a = ap.parse_args()
    {"sim": G.cmd_sim, "grade": cmd_grade, "cmp": cmd_cmp}[a.cmd](a)
