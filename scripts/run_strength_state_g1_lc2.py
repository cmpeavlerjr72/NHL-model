"""SS-R3c (INV-31): closed-loop G1 + decomposition for the LC-1 re-levelled stage-1 arm (H3''c or H2''c) with the
selected type arm T2 (SS-R5, dff868d / 9b299f3). Reuses Lane P2's scripts unchanged by re-pointing their module
globals (their files are not modified):
  run_strength_state_g1_v5.py   RES -> results/strength_state_lc2, R5D -> results/strength_state_r3c/r5 (a private
                                copy of T2_fold2.json; the hazard-table cache there is this arm's, never SS-R5's)
  diag_strength_state_g1_decomp_v5.py   R3 -> results/strength_state_lc2 (D14 decomposition + the PP-opportunities-
                                conferred spread ratios by own taken / opponent drawn quintile, RS and all games)

    run_strength_state_g1_v3c.py g1     --arm H3 [--seeds 200 --workers 4]   -> results/ss_lc2_g1_<arm>_T2/
    run_strength_state_g1_v3c.py decomp --arm H3
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

LC2D = Path("results/strength_state_lc2")


def main():
    cmd, rest = sys.argv[1], sys.argv[2:]
    arm = rest[rest.index("--arm") + 1] if "--arm" in rest else "H3"
    tag = f"ss_lc2_g1_{arm}_T2"
    if cmd == "g1":
        import run_strength_state_g1_v5 as G
        G.RES = LC2D
        G.R5D = LC2D / "r5"
        G.R5D.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path("results/strength_state_r5") / "T2_fold2.json", G.R5D / "T2_fold2.json")
        sys.argv = [sys.argv[0], *rest, "--type-arm", "T2", "--tag", tag,
                    "--report", f"docs/tests/gates_g1_{tag}_2026-10-16.md"]
        G.main()
    elif cmd == "decomp":
        import diag_strength_state_g1_decomp_v5 as D
        D.R3 = LC2D
        sys.argv = [sys.argv[0], *rest, "--tag", tag]
        D.main()
    else:
        raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
