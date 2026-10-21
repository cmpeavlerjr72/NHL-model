"""INV-77 (Lane E4): digest of the attr tables from `defaults.<builder>` on the fold-2 game list. Recorded from HEAD
(e848fa6, builder default_attr = B0 default) BEFORE the edit; the test compares `b0_attr` (explicit pre-INV-77 path) to it.
    diag_engine_defaults_v2_tables_fixture.py --builder default_attr --out tests/fixtures/sim_defaults_v2_tables.json
"""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def dig(x):
    h = hashlib.sha256()

    def rec(v, path=""):
        if isinstance(v, dict):
            for k in sorted(v, key=str):
                rec(v[k], f"{path}/{k}")
        else:
            a = np.ascontiguousarray(np.asarray(v))
            h.update(path.encode() + str(a.shape).encode() + str(a.dtype).encode())
            h.update(a.tobytes() if a.dtype != object else str(a.tolist()).encode())
    rec(x)
    return h.hexdigest()


def fold2_games():
    import pandas as pd
    return np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"]).game_id.unique())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--builder", default="default_attr")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from nhl_sim.engine import defaults as DF
    g = fold2_games()
    attr, _ = getattr(DF, a.builder)(g)
    res = {k: dig(v) for k, v in attr.items()}
    Path(a.out).write_text(json.dumps(dict(builder=a.builder, n_games=len(g), digests=res), indent=1))
    print(res)
