"""Grade any sim output (docs/ops/sim_output_schema.md) against G1-G9 (docs/gates.yaml).

    eval_gates.py --results results/<tag> --season 20242025 [--out docs/tests/gates_<tag>_<date>.md]

Statuses: PASS / FAIL / UNDERPOWERED / NEEDS-INSTRUMENTATION per gate. G1-G4 and G8 need event/player-level output
and report NEEDS-INSTRUMENTATION until the event engine exists. Nothing here adjusts an engine.
"""
import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_reference  # noqa: E402
from nhl_sim.eval.gates import evaluate, load_sim_output, load_tolerances, real_games  # noqa: E402


def fmt(v):
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else (f"{v:.4f}" if isinstance(v, float) else str(v))


def report(tag, season, res, meta, segment, n_sim_rows):
    L = [f"# Gate report: {tag} (season {season}, segment {segment})", "",
         f"Generated {date.today().isoformat()} by `scripts/eval_gates.py`. Tolerances `docs/gates.yaml` (provisional). "
         f"Sim rows {n_sim_rows}. run_meta: {meta}", "", "| gate | status |", "|---|---|"]
    L += [f"| {g} | {r['status']} |" for g, r in res.items()]
    for g, r in res.items():
        L += ["", f"## {g}: {r['status']}", "", "| check | sim | real | tol | status | n | note |", "|---|---|---|---|---|---|---|"]
        for c in r["checks"]:
            L.append(f"| {c['check']} | {fmt(c['sim'])} | {fmt(c['real'])} | {c['tol']} | {c['status']} | {c['n']} | {c['note']} |")
    return L


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--season", required=True, type=int)
    ap.add_argument("--gates-config", default="docs/gates.yaml")
    ap.add_argument("--segment", default="all", choices=["all", "RS", "PO"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    sim, meta = load_sim_output(a.results)
    real = real_games(a.season)
    tg = load_reference(f"gate_targets_{a.season}")
    miss = set(real.game_id) - set(sim.game_id)
    if miss:
        print(f"WARNING: sim lacks {len(miss)} real games of the season; graded on the overlap")
    real = real[real.game_id.isin(sim.game_id)]
    res = evaluate(sim, real, tg, load_tolerances(a.gates_config), a.segment)
    tag = Path(a.results).name
    out = Path(a.out) if a.out else Path("docs/tests") / f"gates_{tag}_{date.today().isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report(tag, a.season, res, meta, a.segment, len(sim))) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print({g: r["status"] for g, r in res.items()})
    return res


if __name__ == "__main__":
    main()
