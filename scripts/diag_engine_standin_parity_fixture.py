"""D32 stand-ins: records the parity fixture from the PRE-change engine (run BEFORE engine/sim.py is edited; the
cases run with both stand-in flags off: see tests/engine/standin_parity_cases.py).

    diag_engine_standin_parity_fixture.py --commit <hash> [--out tests/fixtures/sim_standin_flag_parity.json]

`tests/engine/test_sim_standins.py` asserts the changed engine reproduces every digest exactly.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "engine"))
import attr_parity_cases as A  # noqa: E402
import standin_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402
from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", default="tests/fixtures/sim_standin_flag_parity.json")
    a = ap.parse_args()
    res = {"source": f"engine at {a.commit} (pre-change, working tree clean for src/nhl_sim/engine), era ERA_2015",
           "cases": {}}
    for name in C.CASES:
        if name.startswith("real") and not A.real_available():
            print("skip", name, "(results absent)")
            continue
        out = C.run(SIM, name, ERA_2015)
        res["cases"][name] = T2.digest(out)
        print(name, "unfinished", out["unfinished"], "goals", int(out["score"].sum()), flush=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print("wrote", a.out)
