# INV-24 DRatings close-out (Lane O2, 2026-10-16)

Run 2026-10-16 09:28-09:40 -04:00.

## 1. Validation of `data/processed/lines_dratings_v1.parquet`

- 490,968 rows, 5,598 game_ids, 3 markets (ml / pl / total) x 163,656 rows each; one DRatings uuid per game_id.
- Every game_id is in `games.parquet`: 0 missing.
- No game on/after 2025-07-01: latest game_date_local 2025-06-17 (start_utc max 2025-06-18T00:21Z); 0 games >= 2025-07-01. 2025-26 and 2026-27 are absent, consistent with the seal.
- UTA->ARI remap flag (`dr_team_label_remapped`): 20,886 rows, 246 games.
- Per-season counts (games with a DR row / games in `games.parquet`):

| season | RS | PO |
|---|---|---|
| 2021-22 | 1312 / 1312 | 89 / 89 |
| 2022-23 | 1312 / 1312 | 88 / 88 |
| 2023-24 | 1312 / 1312 | 88 / 88 |
| 2024-25 | 1311 / 1312 | 86 / 86 |
| 2025-26, 2026-27 | 0 (out of scope) | 0 |

- The single missing 2024-25 game: **2024020984, OTT at CHI, 2025-03-05** (game_state OFF). The log reported 0 games without a page, so this game was never matched to a DRatings listing (likely absent from the site or postponed/relisted); not pursued.

## 2. HF sync (`hf_sync_data.py push --dirs raw`)

- Before: 5,877 raw files outstanding (6,209 total incl. results). Push finished 09:29:03-09:33:04, attempt 1, no failed dirs.
- After: raw local 36,537 / remote 36,534, 3 outstanding. These 3 are live-collector snapshots (`raw/live/{dkex,goalies,kalshi}/2026-10-16/*`) written while the push ran, not DRatings files; all `raw/dratings/*` are on remote. Zero DRatings outstanding.
- `results` shows 399 outstanding (other lanes' in-progress outputs and logs, e.g. `results/sa_r2_g2_A2g_r3`, plus `results/logs/dratings_pull_2026-10-15.log`); not in scope (`--dirs raw` only). Total outstanding 402.

## 3. Scheduled task

`NHL-Model-dratings-pull` was still registered (state Ready, not running). Unregistered at 09:28; verified gone.

## 4. SBRO vs DRatings puck-line sign mismatches (38 of 1,743 overlap games)

Overlap is 2021-22 (1,401) and 2022-23 (342) only; every game in both sources has |PL| = 1.5. Signs are of the AWAY line (+1.5 means home is the -1.5 favourite). "ML fav" uses each source's own home win probability (DR `dr_ml_home_bookmed`, SBRO `sbro_ml_home_nv`). Data: `lines_crosscheck_sbro_dratings_v1.csv`.

| game_id | date | home-away | DR PL (away) | SBRO PL (away) | DR ML p(home) | SBRO ML p(home) | final margin (home) | end | DR sign agrees w/ own ML fav | SBRO sign agrees w/ own ML fav |
|---|---|---|---|---|---|---|---|---|---|---|
| 2021020028 | 2021-10-16 | CBJ-SEA | +1.5 | -1.5 | 0.484 | 0.477 | +1 | OT | N | Y |
| 2021020029 | 2021-10-16 | NSH-CAR | +1.5 | -1.5 | 0.486 | 0.481 | -1 | REG | N | Y |
| 2021020068 | 2021-10-23 | TBL-COL | -1.5 | +1.5 | 0.511 | 0.507 | -1 | SO | N | Y |
| 2021020087 | 2021-10-25 | CAR-TOR | +1.5 | -1.5 | 0.522 | 0.523 | +3 | REG | Y | N |
| 2021020126 | 2021-10-30 | SJS-WPG | +1.5 | -1.5 | 0.452 | 0.442 | +1 | OT | N | Y |
| 2021020129 | 2021-10-31 | ANA-MTL | -1.5 | +1.5 | 0.522 | 0.523 | +2 | REG | N | Y |
| 2021020177 | 2021-11-07 | VAN-DAL | +1.5 | -1.5 | 0.489 | 0.488 | +3 | REG | N | Y |
| 2021020204 | 2021-11-11 | VGK-MIN | +1.5 | -1.5 | 0.460 | 0.460 | +1 | REG | N | Y |
| 2021020228 | 2021-11-14 | STL-EDM | +1.5 | -1.5 | 0.479 | 0.481 | -1 | REG | N | Y |
| 2021020245 | 2021-11-17 | LAK-WSH | -1.5 | +1.5 | 0.507 | 0.507 | -2 | REG | N | Y |
| 2021020343 | 2021-11-30 | DAL-CAR | -1.5 | +1.5 | 0.505 | 0.502 | +3 | REG | N | Y |
| 2021020369 | 2021-12-04 | DET-NYI | +1.5 | -1.5 | 0.500 | 0.500 | +1 | OT | N | Y |
| 2021020379 | 2021-12-05 | CBJ-SJS | +1.5 | -1.5 | 0.495 | 0.488 | +2 | REG | N | Y |
| 2021020468 | 2021-12-17 | STL-DAL | +1.5 | -1.5 | 0.483 | 0.473 | +3 | REG | N | Y |
| 2021020489 | 2022-02-10 | BUF-CBJ | +1.5 | -1.5 | 0.477 | 0.477 | -1 | OT | N | Y |
| 2021020530 | 2022-02-09 | DAL-NSH | +1.5 | -1.5 | 0.488 | 0.481 | +1 | REG | N | Y |
| 2021020613 | 2022-01-07 | STL-WSH | +1.5 | -1.5 | 0.500 | 0.488 | +4 | REG | N | Y |
| 2021020617 | 2022-01-08 | CAR-FLA | +1.5 | -1.5 | 0.484 | 0.479 | -1 | OT | N | Y |
| 2021020627 | 2022-01-08 | ANA-NYR | -1.5 | +1.5 | 0.505 | 0.514 | -3 | REG | N | Y |
| 2021020878 | 2022-03-04 | WPG-DAL | -1.5 | +1.5 | 0.532 | 0.542 | -1 | OT | N | Y |
| 2021020934 | 2022-03-12 | OTT-CHI | -1.5 | +1.5 | 0.507 | 0.512 | -3 | REG | N | Y |
| 2021021143 | 2022-04-09 | DET-CBJ | -1.5 | +1.5 | 0.540 | 0.544 | -1 | OT | N | Y |
| 2021021217 | 2022-04-18 | VAN-DAL | +1.5 | -1.5 | 0.500 | 0.500 | +4 | REG | N | Y |
| 2021021246 | 2022-04-22 | EDM-COL | -1.5 | +1.5 | 0.530 | 0.527 | +3 | REG | N | Y |
| 2021021273 | 2022-02-23 | MTL-BUF | -1.5 | +1.5 | 0.521 | 0.521 | +4 | REG | N | Y |
| 2021021302 | 2022-04-29 | NYR-WSH | +1.5 | -1.5 | 0.525 | 0.525 | +1 | REG | Y | N |
| 2021030164 | 2022-05-08 | STL-MIN | +1.5 | -1.5 | 0.488 | 0.488 | +3 | REG | N | Y |
| 2021030183 | 2022-05-06 | LAK-EDM | -1.5 | +1.5 | 0.416 | 0.417 | -6 | REG | Y | N |
| 2021030416 | 2022-06-26 | TBL-COL | -1.5 | +1.5 | 0.491 | 0.491 | -1 | REG | Y | N |
| 2022020050 | 2022-10-18 | CBJ-VAN | +1.5 | -1.5 | 0.500 | 0.500 | +1 | OT | N | Y |
| 2022020074 | 2022-10-22 | BOS-MIN | +1.5 | -1.5 | 0.501 | 0.488 | +1 | OT | Y | Y |
| 2022020096 | 2022-10-24 | VGK-TOR | -1.5 | +1.5 | 0.501 | 0.512 | +2 | REG | N | Y |
| 2022020099 | 2022-10-25 | NYR-COL | +1.5 | -1.5 | 0.500 | 0.500 | -1 | SO | N | Y |
| 2022020102 | 2022-10-25 | DET-NJD | +1.5 | -1.5 | 0.510 | 0.500 | -4 | REG | Y | Y |
| 2022020206 | 2022-11-08 | LAK-MIN | -1.5 | +1.5 | 0.515 | 0.512 | +1 | REG | N | Y |
| 2022020232 | 2022-11-12 | NSH-NYR | -1.5 | +1.5 | 0.516 | 0.521 | +1 | REG | N | Y |
| 2022020250 | 2022-11-15 | CBJ-PHI | +1.5 | -1.5 | 0.480 | 0.488 | +1 | OT | N | Y |
| 2022020299 | 2022-11-21 | SJS-OTT | +1.5 | -1.5 | 0.480 | 0.473 | +4 | REG | N | Y |

Findings:
- All 38 are near pick'em games (both ML probs 0.42-0.54 for 37 of 38; the exception is 2021030183 at 0.416/0.417). The favourite is ambiguous, which is where a -1.5 label is most likely to be mis-signed.
- SBRO's PL sign agrees with its own ML favourite in **34 of 38**; DRatings' PL sign agrees with its own ML favourite in **6 of 38**. The two ML sources name the same favourite in 36 of 38 games (disagree on 2: 2022020074, 2022020102, both at p~0.50-0.51).
- Reading: the 38 mismatches are overwhelmingly DRatings' PL sign being inconsistent with DRatings' own ML (and with SBRO's). That points to the DRatings PL "close mode" sign (mode across books of a +/-1.5 line, which flips with a coin-flip game across books) as the unreliable field, not SBRO. Caveat: 38 is 2.2% of the overlap and this checks internal consistency only; final margins (mean home +0.6, sd 2.4) carry no information on which sign is "right". No third source was fetched. The PM rules.
- Suggested handling for PM consideration: when using DRatings PL, derive the sign from DRatings ML favourite (or the PL price) rather than the mode of the line sign.
