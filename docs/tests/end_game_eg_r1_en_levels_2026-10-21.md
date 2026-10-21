# EG-R1 part A step 3: EN table inventory and EN stand-in levels (Lane H8a, 2026-10-21)

Generated 2026-10-21 13:58:41 -0400 by `scripts/build_end_game_en_levels_v1.py` (1 s). Written after the fold-2 pull selection (P1, D45).

## Inventory (which served table carries EN-for st 5 / EN-against st 6)

| stage | served table | EN states | served at EN |
|---|---|---|---|
| 3 attempts | A3g-c (G, 2, M, 5, 7) | none | STAND-IN: as-of M1 K500 attempt rate per EN state (below) |
| block | B0 (G, 5, 2) | ES group pools EN in the B0 fit | ES group (index 0) |
| 4 class | L1x-as on L0s | L0s state_pdf rows 5 / 6 | L0s baseline x ES-group M1 K500 level (L33; SL-R7 offline does the same) |
| miss | S0t (G, 3, 2, 78) | ES group pools EN | ES group (rating group 0) |
| goal EN-for | C1s | sg 5 EAF (5v5 level group) | C1s EAF with the defending starter (oracle) |
| goal EN-against | none (no goalie) | - | STAND-IN: as-of M1 K500 goal per SOG on st-6 SOG (below) |

Served-vs-offline parity of the EN rows of block / class / miss / EAF: `docs/tests/end_game_eg_r1_pull_2026-10-21.md` (engine step).

## EN levels: per-season parity (predicted / actual; 2021-22 is burn-in, never judged)

|   season |   ef_pred_over_actual |   ef_n_attempts |   ea_pred_over_actual |   ea_n_attempts |   en_goal_pred_over_actual |   en_sog | judged   |
|---------:|----------------------:|----------------:|----------------------:|----------------:|---------------------------:|---------:|:---------|
| 20212022 |                0.9893 |            2596 |                0.9764 |             856 |                     1.0000 |      452 | False    |
| 20222023 |                0.9813 |            2686 |                0.9532 |             895 |                     1.0024 |      417 | True     |
| 20232024 |                0.9663 |            3241 |                1.0232 |             906 |                     0.9983 |      437 | True     |
| 20242025 |                1.0044 |            3587 |                0.9354 |            1133 |                     1.0000 |      516 | True     |

Season finals (per team-hour; goal share): {'ef': {'20212022': 131.88450791679603, '20222023': 142.68891938554162, '20232024': 158.0782831362029, '20242025': 153.48737697903294}, 'ea': {'20212022': 43.487341593519794, '20222023': 47.545265394661115, '20232024': 44.189732959395194, '20242025': 48.48095849379546}, 'en_goal': {'20212022': 1.0, '20222023': 0.9976019184652278, '20232024': 1.0, '20242025': 1.0}}

EN-for attempts per team-hour rise 132 -> 143 -> 158 across the training seasons; a season-to-date level shrunk to the previous final runs low under a trend (L27). EN-against attempts are about 900 per season (Poisson SE about 3.3%). The goal share at the empty net is 1.0 in the data (0 recorded saves; 1 non-goal st-6 SOG in 2022-23).
