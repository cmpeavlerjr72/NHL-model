"""SL-R3 recording-era flag: records the parity fixture from the PRE-change engine (run BEFORE engine/state.py,
engine/rules.py or engine/sim.py are edited; the cases cover the stage-4 option off and the SL-R1 cdf path).

    diag_engine_era_parity_fixture.py --commit <hash> [--out tests/fixtures/sim_era_flag_parity.json]

`tests/engine/test_sim_era_flag.py` asserts the changed engine reproduces every digest exactly.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "engine"))
import attr_parity_cases as A  # noqa: E402
import era_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402
from nhl_sim.engine import sim as SIM  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", default="tests/fixtures/sim_era_flag_parity.json")
    a = ap.parse_args()
    res = {"source": f"engine at {a.commit} (pre-change, working tree clean for src/nhl_sim/engine), era ERA_2015",
           "cases": {}}
    for name, (mk, per_team) in C.CASES.items():
        if name.startswith("real") and not A.real_available():
            print("skip", name, "(results absent)")
            continue
        t, g, gt, n, s0 = mk()
        out = SIM.simulate(t, g, gt, n, ERA_2015, seed0=s0, per_team_types=per_team)
        res["cases"][name] = T2.digest(out)
        print(name, "unfinished", out["unfinished"], "goals", int(out["score"].sum()), flush=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print("wrote", a.out)
