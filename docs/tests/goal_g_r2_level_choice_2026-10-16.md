# G-R2 step 1: level re-selection under D35 (Lane G2, 2026-10-16)

Written and committed BEFORE any refit. Input: the committed G-R1 training parity table (`docs/tests/goal_g_r1_step1_2026-10-16.md`, `results/goal_g_r1/step1.json`). No fold-2 number is used.

Rule (experiments.md G-R2, D35): E excluded; simplest passing family; within it the smallest max |parity| on genuine-prior training seasons.

| construction | family | max judged parity (pp) | pass |
|---|---|---|---|
| E | E | 0.054 | not selectable (D35) |
| M0 | M0 | 0.574 | no |
| M1 K500 | M1 | 0.240 | yes |
| M1 K2000 | M1 | 0.251 | yes |
| M1 K8000 | M1 | 0.295 | yes |
| M2 H30 / H60 | M2 | 0.219 / 0.226 | yes (more complex family) |

Family order M0 < M1 < M2: M0 fails, so the simplest passing family is M1. Smallest max |parity| in M1 is **K500 (0.240 pp)**. **Selected level: M1 K500.** (The M2 H30 minimum of 0.219 is in a more complex family and is not considered.)

Frozen from G-R1 and reused unchanged: cell tables, as-of rating tables (`ratings_{goalie,team}_v1_f{1,2}.parquet`, built from the G-R1 C0 expectation), fold-1 cells (goalie b3000 w0.5 s0.5 c -1.780; team b10000 w0.7 s1.0 c 1.954; `results/goal_g_r1/select.json`), C2 capacity (`gr1_frozen_params.json`: 15 leaves, min_data 800, 97 rounds, lr 0.05). Labelled: the rating tables and the coefficients c were estimated under level E offsets and are not re-derived (the spec freezes them). Outputs go to `results/goal_g_r2/`.
