"""SL-R7 (Lane A7): records the flag-off parity fixture from the PRE-change engine. The engine source is read from git
at --commit (default 80f0b2e, Lane E2 engine_c1s) and loaded as a separate module, so the working-tree sim.py may
already carry the change. Cases: tests/engine/l1xas_parity_cases.py (attr["l1x"] absent in every case).

    diag_engine_l1xas_parity_fixture.py [--commit 80f0b2e] [--out tests/fixtures/sim_l1xas_flag_parity.json]
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "engine"))
import l1xas_parity_cases as C  # noqa: E402
import t2_parity_cases as T2  # noqa: E402
from nhl_sim.engine.rules import ERA_2015  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default="80f0b2e")
    ap.add_argument("--out", default="tests/fixtures/sim_l1xas_flag_parity.json")
    a = ap.parse_args()
    src = subprocess.run(["git", "show", f"{a.commit}:src/nhl_sim/engine/sim.py"], capture_output=True, text=True,
                         check=True, cwd=ROOT).stdout
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sim_pre.py"
        p.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("nhl_sim.engine.sim_pre", p)
        SIM = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(SIM)
    res = {"source": f"engine/sim.py at {a.commit} (git show), era ERA_2015", "cases": {}}
    for name in C.CASES:
        if name.startswith("real") and not C.real_available():
            print("skip", name, "(results absent)")
            continue
        out = C.run(SIM, name, ERA_2015)
        res["cases"][name] = T2.digest(out)
        print(name, "unfinished", out["unfinished"], "goals", int(out["score"].sum()), flush=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print("wrote", a.out)
