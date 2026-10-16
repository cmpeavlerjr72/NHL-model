# SM-R1 step 1: miss-share level constructions and parity (Lane M, 2026-10-16)

Spec (binding): `docs/models/miss/experiments.md` SM-R1. Script: `scripts/exp_miss_smr1_step1.py`; library `src/nhl_sim/miss/`; level table `data/processed/miss/level_v1.parquet` (created_at < puck_drop asserted). Generated 2026-10-16 12:42:39.

S0 = recorded training-row miss rate per (cell x type x strength group), shrunk (K = 20 pseudo-attempts, a labelled construction choice, not tuned) + the level offset logit(s_asof) - logit(s_train) per level group (ES+EN, PP, PK) + ten (strength group x period type) intercepts fitted under the offset. Parity = S0 predicted minus actual miss share (pp) per training season, over graded rows (ES + PP + PK) and over ES; tolerance +/-0.3 pp. 2021-22 has no prior season and is shown, not judged. E: on fold 1 every training row is era 1, so E = no level there.

## Parity (pred - actual, pp)

|                           |     ES |   overall | judged   |
|:--------------------------|-------:|----------:|:---------|
| (1, 'E', 20212022)        |  0.836 |     0.833 | False    |
| (1, 'E', 20222023)        | -0.843 |    -0.83  | True     |
| (1, 'M0', 20212022)       |  0.836 |     0.833 | False    |
| (1, 'M0', 20222023)       | -0.843 |    -0.83  | True     |
| (1, 'M1_K2000', 20212022) |  0.323 |     0.342 | False    |
| (1, 'M1_K2000', 20222023) | -0.326 |    -0.34  | True     |
| (1, 'M1_K500', 20212022)  |  0.312 |     0.322 | False    |
| (1, 'M1_K500', 20222023)  | -0.314 |    -0.321 | True     |
| (1, 'M1_K8000', 20212022) |  0.377 |     0.407 | False    |
| (1, 'M1_K8000', 20222023) | -0.38  |    -0.406 | True     |
| (1, 'M2_H30', 20212022)   |  0.291 |     0.325 | False    |
| (1, 'M2_H30', 20222023)   | -0.294 |    -0.323 | True     |
| (1, 'M2_H60', 20212022)   |  0.299 |     0.324 | False    |
| (1, 'M2_H60', 20222023)   | -0.302 |    -0.323 | True     |
| (1, 'O', 20212022)        |  0.124 |     0.138 | False    |
| (1, 'O', 20222023)        | -0.125 |    -0.138 | True     |
| (1, 'none', 20212022)     |  0.836 |     0.833 | False    |
| (1, 'none', 20222023)     | -0.843 |    -0.83  | True     |
| (2, 'E', 20212022)        |  0.829 |     0.847 | False    |
| (2, 'E', 20222023)        | -0.76  |    -0.728 | True     |
| (2, 'E', 20232024)        | -0.076 |    -0.116 | True     |
| (2, 'M0', 20212022)       |  1.534 |     1.501 | False    |
| (2, 'M0', 20222023)       | -0.06  |    -0.082 | True     |
| (2, 'M0', 20232024)       | -1.481 |    -1.411 | True     |
| (2, 'M1_K2000', 20212022) |  0.447 |     0.488 | False    |
| (2, 'M1_K2000', 20222023) | -0.102 |    -0.096 | True     |
| (2, 'M1_K2000', 20232024) | -0.347 |    -0.389 | True     |
| (2, 'M1_K500', 20212022)  |  0.41  |     0.432 | False    |
| (2, 'M1_K500', 20222023)  | -0.117 |    -0.114 | True     |
| (2, 'M1_K500', 20232024)  | -0.295 |    -0.315 | True     |
| (2, 'M1_K8000', 20212022) |  0.573 |     0.632 | False    |
| (2, 'M1_K8000', 20222023) | -0.084 |    -0.084 | True     |
| (2, 'M1_K8000', 20232024) | -0.492 |    -0.545 | True     |
| (2, 'M2_H30', 20212022)   |  0.426 |     0.491 | False    |
| (2, 'M2_H30', 20222023)   | -0.058 |    -0.057 | True     |
| (2, 'M2_H30', 20232024)   | -0.369 |    -0.431 | True     |
| (2, 'M2_H60', 20212022)   |  0.424 |     0.478 | False    |
| (2, 'M2_H60', 20222023)   | -0.076 |    -0.07  | True     |
| (2, 'M2_H60', 20232024)   | -0.35  |    -0.405 | True     |
| (2, 'O', 20212022)        |  0.111 |     0.146 | False    |
| (2, 'O', 20222023)        | -0.038 |    -0.031 | True     |
| (2, 'O', 20232024)        | -0.073 |    -0.114 | True     |
| (2, 'none', 20212022)     |  2.03  |     1.983 | False    |
| (2, 'none', 20222023)     |  0.432 |     0.396 | True     |
| (2, 'none', 20232024)     | -2.469 |    -2.368 | True     |

## Summary over judged cells

| construction   | family   |   max_abs_pp | all_pass   |
|:---------------|:---------|-------------:|:-----------|
| none           | none     |        2.469 | False      |
| M0             | M0       |        1.481 | False      |
| E              | E        |        0.843 | False      |
| M1_K500        | M1       |        0.321 | False      |
| M1_K2000       | M1       |        0.389 | False      |
| M1_K8000       | M1       |        0.545 | False      |
| M2_H30         | M2       |        0.431 | False      |
| M2_H60         | M2       |        0.405 | False      |
| O              | O        |        0.138 | True       |

## Selection: **M1_K500** (fallback: smallest max |parity|, ties within 0.1 pp to the simpler construction (failure listed))

## Raw miss share by season (% of unblocked goalie-in attempts)

|   season |    ES |    PP |    PK |   n_gated |
|---------:|------:|------:|------:|----------:|
| 20212022 | 27.01 | 27.27 | 16.92 |    119056 |
| 20222023 | 28.43 | 28.55 | 17.92 |    119486 |
| 20232024 | 31.46 | 30.39 | 20.18 |    119651 |
| 20242025 | 34.67 | 32.34 | 20.91 |    116716 |

## Post / crossbar share by season (a post or crossbar shot is a miss in the NHL feed; data only)

|   season |   misses |   post_bar |   pct_of_misses |   pct_of_unblocked |   pct_of_misses_ES |   over_net_pct_of_misses |   missing_reason |
|---------:|---------:|-----------:|----------------:|-------------------:|-------------------:|-------------------------:|-----------------:|
| 20212022 |    32623 |       2041 |           6.256 |              1.679 |              5.902 |                    9.711 |                0 |
| 20222023 |    34519 |       2206 |           6.391 |              1.808 |              5.868 |                    9.395 |                0 |
| 20232024 |    38093 |       2381 |           6.25  |              1.944 |              5.693 |                    7.408 |                4 |
| 20242025 |    40943 |       3422 |           8.358 |              2.853 |              7.647 |                    5.583 |                0 |
