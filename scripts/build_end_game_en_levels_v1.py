"""EG-R1 part A step 3 (Lane H8a): EN table inventory and the labelled EN stand-in levels (as-of M1 K500) with their
per-season parity. -> data/processed/end_game/en_levels_v1.parquet, docs/tests/end_game_eg_r1_en_levels_2026-10-21.md"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.end_game import en  # noqa: E402

t0 = time.time()
L, info = en.en_levels()
L.to_parquet(ROOT / "data/processed/end_game/en_levels_v1.parquet", index=False)
P = en.parity(L)
doc = ["# EG-R1 part A step 3: EN table inventory and EN stand-in levels (Lane H8a, 2026-10-21)", "",
       f"Generated {time.strftime('%Y-%m-%d %H:%M:%S %z')} by `scripts/build_end_game_en_levels_v1.py` ({time.time() - t0:.0f} s). "
       "Written after the fold-2 pull selection (P1, D45).", "",
       "## Inventory (which served table carries EN-for st 5 / EN-against st 6)", "",
       "| stage | served table | EN states | served at EN |",
       "|---|---|---|---|",
       "| 3 attempts | A3g-c (G, 2, M, 5, 7) | none | STAND-IN: as-of M1 K500 attempt rate per EN state (below) |",
       "| block | B0 (G, 5, 2) | ES group pools EN in the B0 fit | ES group (index 0) |",
       "| 4 class | L1x-as on L0s | L0s state_pdf rows 5 / 6 | L0s baseline x ES-group M1 K500 level (L33; SL-R7 offline does the same) |",
       "| miss | S0t (G, 3, 2, 78) | ES group pools EN | ES group (rating group 0) |",
       "| goal EN-for | C1s | sg 5 EAF (5v5 level group) | C1s EAF with the defending starter (oracle) |",
       "| goal EN-against | none (no goalie) | - | STAND-IN: as-of M1 K500 goal per SOG on st-6 SOG (below) |", "",
       "Served-vs-offline parity of the EN rows of block / class / miss / EAF: `docs/tests/end_game_eg_r1_pull_2026-10-21.md` (engine step).", "",
       "## EN levels: per-season parity (predicted / actual; 2021-22 is burn-in, never judged)", "",
       P.to_markdown(index=False, floatfmt=".4f"), "",
       f"Season finals (per team-hour; goal share): {info}", "",
       "EN-for attempts per team-hour rise 132 -> 143 -> 158 across the training seasons; a season-to-date level shrunk to the previous "
       "final runs low under a trend (L27). EN-against attempts are about 900 per season (Poisson SE about 3.3%). The goal share at "
       "the empty net is 1.0 in the data (0 recorded saves; 1 non-goal st-6 SOG in 2022-23)."]
(ROOT / "docs/tests/end_game_eg_r1_en_levels_2026-10-21.md").write_text("\n".join(doc) + "\n", encoding="utf-8")
print(P.to_string())
