"""SL-R1 engine flag (shot attributes, default off): records the flag-off parity fixture from the PRE-change engine.

    diag_engine_attr_parity_fixture.py --sim <path to the pre-change sim.py> --commit <hash>
        [--out tests/fixtures/sim_attr_flag_parity.json]

Loads the given sim.py as a standalone module (`git show b024504:src/nhl_sim/engine/sim.py`), runs every case of
tests/engine/attr_parity_cases.py and writes the sha256 digest of every output array.
`tests/engine/test_sim_attr_flag.py` asserts the changed engine with the flag off reproduces them exactly.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "engine"))
import attr_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", default="tests/fixtures/sim_attr_flag_parity.json")
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("sim_pre_change", a.sim)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    res = {"source": f"engine/sim.py at {a.commit} (pre-change), era ERA_2015", "cases": {}}
    for name, (mk, per_team) in C.CASES.items():
        if name.startswith("real") and not C.real_available():
            print("skip", name, "(results absent)")
            continue
        t, g, gt, n, s0 = mk()
        out = mod.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=per_team)
        res["cases"][name] = T2.digest(out)
        print(name, "unfinished", out["unfinished"], "goals", int(out["score"].sum()))
    Path(a.out).write_text(json.dumps(res, indent=1))
    print("wrote", a.out)
