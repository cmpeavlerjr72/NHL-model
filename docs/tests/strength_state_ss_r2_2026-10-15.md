# SS-R2 strength-state / penalty hazard with the SS-R1 biases fixed, full report (Lane H2, INV-26), 2026-10-15

Spec: `docs/models/strength_state/experiments.md` SS-R2 and the D12 ruling (commit 77e93ef), run as written. Worker: Opus, core cap 6, no sub-agents. Clock: start 19:45 EDT; table build 19:50-19:51; fold-1 tune 19:53; fold-2 fits 19:54; grade and bias checks by 19:58. No AWS or box request (no closed-loop run was allowed, see step 5).

Detail files:
- `docs/tests/strength_state_ss_r2_grade_2026-10-15.md`: blind table, reveal, decision rule, secondary tables (H3' and H2').
- `docs/tests/strength_state_ss_r2_bias_2026-10-15.md`: the pre-registered bias checks for every arm, by month.

## Headline

1. **Change 1 works.** The share of fold-2 penalty-taking events in state 'other' falls from 6.36% (590) to 1.54% (143). The residual is trailing-team pulls (123 of the 143 are in the last 3 minutes of regulation, 17 in OT).
2. **Bake-off: H3' > H2' > H1' > H0'**, every step significant. **Offline winner H3'** (+0.084 nats/game over H2', SE 0.012, seed floor 0.0003).
3. **Bias checks FAIL for every arm.** The month check fails in January 2025 for all four arms (+10.5% to +11.2%, n = 224 games). H3' also fails the overall level check (+3.08%, tolerance 3%). The 'other' check passes for every arm.
4. **Closed-loop G1: NOT RUN.** Step 4 says an arm that fails a bias check gets no closed loop. Both the winner and the next simpler arm (H2') fail.
5. **SS-R1's large H3 lead was mostly the delayed-penalty artefact.** In SS-R1, 0.27 of H3's 0.42 nats/game lead over H2, and 0.36 of H2's 0.51 lead over H0, came from 'other'-state rows, which the sim never visits. In SS-R2 the leads are 0.084 and 0.262.

## Step 1: change 1, delayed-penalty state (`src/nhl_sim/strength_state/delayed.py`)

- `DELAYED_PENALTY` events belong to the penalised team. In 2024-25, all 3,252 signal windows ending in a PENALTY whistle end in a penalty on that team.
- **Window:** from the signal second up to (not including) the first whistle after it (STOPPAGE, GOAL, PENALTY, PERIOD_END, GAME_END). A penalty at second t is counted in the row holding t-1, so the penalty falls in the window.
- **Pre-signal goalie state:** taken from the code of the last event before the signal. The pbp sometimes stamps the signal itself with the post-pull code: 244 of 7,092 signals in 2023-25 show a pull that the previous event does not. A goalie already pulled before the signal (a trailing-team pull) stays pulled. Overlapping windows take the earliest signal. Only the goalie digits change; the skater counts stay the engine replay.
- **Tables:** `*_v2*` (v1 untouched); `season_rows(ev, delayed_fix=True)`.
- **Test:** `tests/test_delayed_penalty_state.py` (3 tests). The first checks that a penalty after a signal gets the pre-signal state (5v5, not 'other'), and that the window seconds become 5v5 exposure. The second checks that a trailing pull without a signal keeps 'other'. The third checks that a pull before the signal stays 'other'. Full suite: 88 passed.

| season | signal windows | goalie-state seconds changed | events in 'other' v1 | events in 'other' v2 | share v1 | share v2 |
|---|---|---|---|---|---|---|
| 2021-22 | 1,883 | 5,491 | 649 | 208 | 6.44% | 2.06% |
| 2022-23 | 2,320 | 5,765 | 689 | 175 | 6.69% | 1.70% |
| 2023-24 | 3,607 | 5,804 | 683 | 157 | 6.76% | 1.55% |
| 2024-25 | 3,485 | 4,588 | 590 | 143 | 6.36% | 1.54% |

How the windows end in 2024-25: PENALTY 3,252, GOAL 135, STOPPAGE 98. Signals were logged less often in 2021-22 (1,883), which is why the residual 'other' share is higher that season.

Residual 'other' events in 2024-25 (143):
- 75 have the opponent's goalie pulled and 68 the team's own goalie pulled.
- They line up with the score: when the opponent's goalie is out, the team is ahead in 68 of the 75.
- These wait for the stage-8 pull model.

## Step 2: changes 2 and 3 (`src/nhl_sim/strength_state/league_level.py`, `models_r2.py`)

**League level.** For each game:

level = log(((E + 2k r_prev) / (H + 2k)) / r_prev)

- E and H are the season's events and team-hours in games with an earlier game date.
- r_prev is the previous season's final rate per team-hour.
- `created_at` is 6 h after the previous game date's last puck drop, and `created_at < puck_drop` is asserted on every row (all pass).

**How every arm uses it.** The level is a fixed offset with coefficient 1, so mu = exposure x exp(level) x exp(arm terms); H0' = H0 cells x exp(level). Season dummies are removed. The GLM cells are strength state x period type, and H3' drops `season_f`.

**2021-22 has level 0.** No 2020-21 data exists, so there is no previous final rate. 2021-22 is a training season in both folds.

**Interpretation choice for the PM.** The spec defines the level as a ratio vs the previous season. The cells are pooled over the training seasons, so the absolute rate of the previous season enters only through that ratio. Training-season rates are close (3.55 / 3.63 / 3.57 per team-hour), so this matters little here.

**Frozen on fold 1 (H1' fold-1 LL over 18 grid points):** k = 50, w = 1.0, prior strength 1,800 team-minutes. **All three sit on a grid corner again**; the grid was not extended, because the spec fixes it. The spread across the grid is 0.011 nats/game. H3' uses num_leaves 7, min_data_in_leaf 800 and 429 rounds (`docs/models/strength_state/ss_r2_frozen_params.json`).

The 2024-25 level on the k = 50 path, as exp(level), month mean: Oct 1.03, Nov 1.02, Dec 0.98, Jan 0.95, Feb 0.93, Mar 0.92, Apr 0.92. r_prev = 3.568 per team-hour.

## Step 3: bake-off (fold 2, 1,398 games, 330,280 rows, 9,270 events)

`scripts/grade_strength_state.py --res results/strength_state_r2 --round SS-R2` (blind, hashed labels). The extension is backward-compatible: re-grading SS-R1 reproduces its report (identical up to line endings) and `winner.json` (byte-identical).

| arm | LL/game vs H0' | predicted events (actual 9,270) |
|---|---|---|
| H0' | 0 | 9,492 |
| H1' | +0.051 (SE 0.011) | 9,516 |
| H2' | +0.262 (SE 0.020) | 9,505 |
| H3' | +0.345 (SE 0.020) | 9,555 |

- Pairwise: H2' vs H1' +0.211 (0.018); H3' vs H2' +0.084 (0.012); H3' vs H1' +0.294 (0.018).
- The H3' seed floor is 0.00025. Every comparison clears 2 SE, and the H3' comparisons also clear the seed floor. **Literal rule: offline winner H3'**, runner-up H2'.
- Type: T1 is carried over from SS-R1 unchanged and not re-raced (its fold-2 json is copied for the closed loop).

LL gain by state, nats/game summed over the rows of each state:

| state | SS-R1 H3-H2 | SS-R1 H2-H0 | SS-R2 H3'-H2' | SS-R2 H2'-H0' |
|---|---|---|---|---|
| 5v5 | 0.121 | 0.167 | 0.058 | 0.256 |
| PP / PK / 4v4 / 3v3 | 0.029 | -0.014 | 0.006 | 0.003 |
| other | **0.272** | **0.357** | 0.019 | 0.003 |

Secondary evidence (grade file):
- Responsiveness slopes by own taken-rating quintile: H3' 0.87, H2' 0.77. By opponent drawn-rating quintile: H3' 0.93, H2' 0.82. Both arms slope.
- Per-team predicted-actual correlation: H3' 0.79, H2' 0.83. All 32 teams are UNDERPOWERED (82-105 team-games, min_cell_n 300).

## Step 4: pre-registered bias checks (`scripts/diag_strength_state_bias_r2.py`)

| arm | pred / actual overall | overall (+/-3%) | months failing (+/-8%, n >= 100 games) | 'other' raw share | 'other' net shortfall | 'other' (<= 1.5%) | all pass |
|---|---|---|---|---|---|---|---|
| H0' | 1.0240 | PASS | 1 (Jan +10.8%) | 1.54% | -0.30% | PASS | **FAIL** |
| H1' | 1.0265 | PASS | 1 (Jan +11.2%) | 1.54% | -0.29% | PASS | **FAIL** |
| H2' | 1.0254 | PASS | 1 (Jan +10.5%) | 1.54% | +0.10% | PASS | **FAIL** |
| H3' | 1.0308 | **FAIL** | 1 (Jan +10.8%) | 1.54% | -0.06% | PASS | **FAIL** |

H3' by month, predicted / actual:

| month | ratio | n games | status |
|---|---|---|---|
| Oct | 0.961 | 166 | PASS |
| Nov | 1.046 | 220 | PASS |
| Dec | 1.051 | 214 | PASS |
| Jan | 1.108 | 224 | FAIL |
| Feb | 1.075 | 122 | PASS |
| Mar | 1.020 | 234 | PASS |
| Apr | 1.000 | 172 | PASS |
| May | 0.897 | 40 | UNDERPOWERED |
| Jun | 0.840 | 6 | UNDERPOWERED |

- **Net shortfall measure.** The sim never visits 'other' but spends that clock time in the non-pulled state. The shortfall is actual 'other' events minus the arm's expected events on the same rows relabelled 5v5, over all events. The relabelling is an approximation. The raw share, 1.54%, is the upper bound and is just above 1.5%. If the PM reads the check as the raw share, every arm fails it too.
- **The January failure is a within-season dip.** Jan 2025 had 3.04 events per team-game, against a season-to-date rate near 3.4. The to-date level cannot anticipate it, because the high October rate lifts the to-date mean.
- **Seasonality repeats.** October is the highest month in every season (3.93 / 4.21 / 4.32 / 3.76 events per team-game against season means of 3.59 / 3.68 / 3.61 / 3.32), and mid-winter is lower.
- The miss is about 4 Poisson SE (about 1,364 events). It is not noise.

## Step 5: closed-loop G1: NOT RUN

The brief's step 4 ("If any fails, report it and do not run the closed loop on that arm") blocks H3' (the winner) and H2' (the next simpler arm); H1' and H0' fail too. Every cell is NOT RUN:

| cell | RS | PO | overall |
|---|---|---|---|
| TOI by strength state (5v5, PP, PK, 4v4, 3v3, 5v3) | NOT RUN (bias check failed) | NOT RUN | NOT RUN |
| PP opps / team-game (mean, SD, P(k)) | NOT RUN | NOT RUN | NOT RUN |
| PIM / game | NOT RUN | NOT RUN | NOT RUN |
| share of minors ended by a PP goal | NOT RUN | NOT RUN | NOT RUN |
| per-team PP opps | NOT RUN | NOT RUN | NOT RUN |
| 100 vs 200 seed check | NOT RUN | | |

Nothing here is compensated: no G1 number exists to be compensated. strength_state stays TESTING.

## Findings (proposed LEARNINGS text for the PM)

1. **A model can learn the delayed-penalty artefact offline.** In SS-R1, most of the H2-over-H0 and H3-over-H2 likelihood gains (70% and 65%) came from 'other'-state rows: the delayed-penalty goalie pull. The sim never reaches that state, so offline likelihood rewarded a signal the closed loop cannot use. Read an offline lead by state before trusting it.
2. **An in-season to-date level fixes the season level but not within-season seasonality.** October runs about 10-20% above the season mean every season, and mid-winter runs below it. A to-date level over-predicts the mid-winter months (Jan 2025 +11%).
3. **The fold-1 tuning corner repeats.** k = 50 is the smallest k (fastest tracking), and w = 1.0 means full carry-over. Both point the same way: the rating and level signals want less shrinkage than the grid allows.

## Recommended next experiment (proposal; the PM decides and pre-registers)

SS-R3: SS-R2 plus a pre-registered seasonality term shared by every arm. The candidates are month of season, or days since the season opener as a spline, fitted on the training seasons as a relative profile. The month check stays the gate. Possibly extend the k grid below 50 and the w grid's upper edge. The G1 closed loop for H3' and H2' would then run as specified (200 seeds is about 17 min locally, so it goes to the Lane O box queue).

## Resume / reproduce

```
.venv/Scripts/python.exe scripts/build_strength_state_tables.py --version v2 --delayed-fix --grid-w 0.7 0.85 1.0 --grid-b 1800 5400 --level-k 50 150 450
.venv/Scripts/python.exe scripts/train_strength_state_v2.py tune
.venv/Scripts/python.exe scripts/train_strength_state_v2.py fold2
.venv/Scripts/python.exe scripts/grade_strength_state.py --res results/strength_state_r2 --round SS-R2 --out docs/tests/strength_state_ss_r2_grade_2026-10-15.md
.venv/Scripts/python.exe scripts/diag_strength_state_bias_r2.py
```

G1 (only if the PM rules that an arm may proceed): `run_strength_state_g1.py` needs an SS-R2 path, with the level offset in `lookup.hazard_table` and `--res results/strength_state_r2`. It was not built, because no arm passed. PARTIAL: G1 is not run, by rule.

Incidents: none. AWS: not used, no box request.
