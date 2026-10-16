# INV-38: DRatings puck-line sign flag (Lane O3, 2026-10-16 ~10:15 -04:00)

Artifacts: `scripts/build_lines_dratings_v2.py`, `tests/test_lines_dratings_v2.py` (3 pass), `data/processed/lines_dratings_v2.parquet` (v1 + 4 game-level bool columns, same 490,968 rows), `data/processed/lines_dratings_v2_pl_flags.csv` (one row per game with the inputs). v1 untouched; no sign rewritten.

Definitions. Close: PL favourite = sign of the modal AWAY close PL line (away +x means home favoured); ML favourite = book-median no-vig close home prob (same as the SBRO crosscheck). `pl_sign_suspect` = they differ; `pl_sign_ambiguous` = |p_home - 0.5| <= 0.005 (not suspect). Open version (`*_open`): modal away open PL line vs mean over groups of no-vig open ML. Missing inputs: none for close or open (0 games). 4 games have a modal close |PL| != 1.5 (2.5); classified by sign like the rest.

## Counts by season (5,598 games; season = game_id prefix)

| season | games | suspect (close) | ambiguous (close) | suspect (open) | ambiguous (open) |
|---|---|---|---|---|---|
| 2021-22 | 1401 | 36 | 54 | 36 | 30 |
| 2022-23 | 1400 | 22 | 46 | 24 | 46 |
| 2023-24 | 1400 | 19 | 46 | 22 | 41 |
| 2024-25 | 1397 | 14 | 36 | 30 | 43 |
| total | 5598 | 91 (1.6%) | 182 | 112 | 160 |

Close: 85 regular season, 6 playoff suspect. Suspect games sit at p_home 0.45-0.54 (mean 0.498), i.e. near pick'em. Close and open suspects overlap in only 8 games (104 open-only), so the open flag is not a proxy for the close flag; use the one matching the line being graded.

## Reproduction of the 38 SBRO-vs-DRatings mismatches
All 38 are in the table. 23 flagged suspect, 10 ambiguous, 5 not flagged. O2's "32 DR sign disagrees with own ML" = 23 suspect + 9 that fall inside the 0.5 pp pick'em band (now ambiguous); O2's "6 agree" = 5 not flagged + 1 ambiguous (2022020074, p=0.501). So 32 -> 23 is the pick'em carve-out, no other difference. Overall: 42 of the 1,743 overlap games are suspect (2.4%) vs 49 of 3,855 outside the overlap (1.3%); the flag is not confined to the overlap.

## Notes for the PM
- Excluding suspect AND ambiguous games from PL grading/CLV removes 273 games (4.9%); D21 says suspect only. Ambiguous games can still carry a wrong sign (9 of the 38 known mismatches are ambiguous), so I suggest PL grading treats ambiguous as excluded too, or reports both. Decision is yours.
- Parquet is 1.1 MB, tracked.
