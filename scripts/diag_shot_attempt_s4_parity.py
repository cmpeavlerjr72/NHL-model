"""INV-36 parity: the G2-path stage-1 loader (run_shot_attempt_g2.stage1_tables('lc2t2') + simulate(per_team_types=True),
no attempts) must reproduce Lane L2's G1 run (results/ss_lc2_g1_H3_T2) on a fixed seed set (seeds 0-7)."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src"))
import run_shot_attempt_g2 as G
import run_strength_state_g1_v5 as V
from nhl_sim.data.load import load_games
from nhl_sim.engine.rules import era_for_season
from nhl_sim.engine.sim import simulate

tables, games, _ = G.stage1_tables("lc2t2")
gt = load_games([G.TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
o = simulate(tables, games, gt.game_type.to_numpy(), 8, era_for_season(G.TEST), seed0=0, per_team_types=True)
g, s = V.to_frames(o, games)
ref_g = pd.read_parquet("results/ss_lc2_g1_H3_T2/games.parquet"); ref_g = ref_g[ref_g.seed < 8]
ref_s = pd.read_parquet("results/ss_lc2_g1_H3_T2/strength_toi.parquet"); ref_s = ref_s[ref_s.seed < 8]
res = {}
for nm, a, b in (("games", g, ref_g), ("strength_toi", s, ref_s)):
    k = ["game_id", "seed"]
    a = a.sort_values(k).reset_index(drop=True); b = b.sort_values(k).reset_index(drop=True)
    cols = [c for c in b.columns if c in a.columns]
    same = all(np.array_equal(a[c].to_numpy(), b[c].to_numpy()) for c in cols if c not in ("home_en_goals", "away_en_goals"))
    res[nm] = dict(rows=len(a), ref_rows=len(b), cols=len(cols), bit_identical=bool(same))
print(json.dumps(res))
Path("results/sa_r3_g2_A3gc_lc2t2").mkdir(parents=True, exist_ok=True)
Path("results/sa_r3_g2_A3gc_lc2t2/parity_g1.json").write_text(json.dumps(res))
assert all(v["bit_identical"] and v["rows"] == v["ref_rows"] for v in res.values())
