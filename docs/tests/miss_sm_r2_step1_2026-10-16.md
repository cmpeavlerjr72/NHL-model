# SM-R2 step 1: tier-specific miss level constructions and parity (Lane M2, 2026-10-16)

Spec (binding): `docs/models/miss/experiments.md` SM-R2. Script `scripts/exp_miss_smr2_step1.py`; library `src/nhl_sim/miss/tier.py`; level table `data/processed/miss/level_tier_v2.parquet` (created_at < puck_drop asserted). Generated 2026-10-16 13:03:13.

Level cell = (ES+EN / PP / PK) x (high / medium / low danger tier of the location cell). M1 / M2 pseudo-attempts K are split over the three tiers of a group by the tier's share of the group's attempts in the prior season (a labelled construction choice implementing 'scaled by the tier's share of attempts'). S0t = recorded cell x type x group table (K = 20, as SM-R1) + tier level offset + ten (group x period type) intercepts. Parity = S0t predicted minus actual miss share (pp) per training season; judged = overall graded rows and each of 3 tiers, +/-0.5 pp, genuine-prior seasons only (2022-23 fold 1; 2022-23 and 2023-24 fold 2). ES and tier x group cells are reported in the long csv `results/miss_sm_r2/step1_parity_long.csv`. 'none' = training-pooled level (no as-of), E = era-pooled (not selectable, D35), O = oracle.

## Parity, judged scopes (pred - actual, pp)

|                           |   overall |     ES |   tier high |   tier medium |   tier low | judged   |
|:--------------------------|----------:|-------:|------------:|--------------:|-----------:|:---------|
| (1, 'E', 20212022)        |     0.833 |  0.836 |       1.213 |         0.584 |      0.936 | False    |
| (1, 'E', 20222023)        |    -0.83  | -0.843 |      -1.155 |        -0.594 |     -0.933 | True     |
| (1, 'M0', 20212022)       |     0.833 |  0.836 |       0.988 |         0.647 |      0.953 | False    |
| (1, 'M0', 20222023)       |    -0.83  | -0.843 |      -1.39  |        -0.521 |     -0.919 | True     |
| (1, 'M1_K2000', 20212022) |     0.34  |  0.323 |       0.136 |         0.152 |      0.582 | False    |
| (1, 'M1_K2000', 20222023) |    -0.339 | -0.325 |      -0.853 |         0.283 |     -0.726 | True     |
| (1, 'M1_K500', 20212022)  |     0.319 |  0.312 |       0.07  |         0.089 |      0.616 | False    |
| (1, 'M1_K500', 20222023)  |    -0.318 | -0.315 |      -0.868 |         0.339 |     -0.726 | True     |
| (1, 'M1_K8000', 20212022) |     0.407 |  0.376 |       0.295 |         0.25  |      0.589 | False    |
| (1, 'M1_K8000', 20222023) |    -0.405 | -0.379 |      -0.9   |         0.168 |     -0.755 | True     |
| (1, 'M2_H30', 20212022)   |     0.323 |  0.29  |       0.281 |         0.137 |      0.51  | False    |
| (1, 'M2_H30', 20222023)   |    -0.322 | -0.292 |      -0.696 |         0.15  |     -0.622 | True     |
| (1, 'M2_H60', 20212022)   |     0.323 |  0.298 |       0.214 |         0.138 |      0.53  | False    |
| (1, 'M2_H60', 20222023)   |    -0.322 | -0.3   |      -0.741 |         0.211 |     -0.661 | True     |
| (1, 'O', 20212022)        |     0.135 |  0.121 |       0.37  |        -0.073 |      0.248 | False    |
| (1, 'O', 20222023)        |    -0.135 | -0.122 |      -0.346 |         0.076 |     -0.254 | True     |
| (1, 'none', 20212022)     |     0.833 |  0.836 |       1.213 |         0.584 |      0.936 | False    |
| (1, 'none', 20222023)     |    -0.83  | -0.843 |      -1.155 |        -0.594 |     -0.933 | True     |
| (2, 'E', 20212022)        |     0.863 |  0.849 |       1.338 |         0.588 |      0.956 | False    |
| (2, 'E', 20222023)        |    -0.713 | -0.742 |      -0.926 |        -0.569 |     -0.771 | True     |
| (2, 'E', 20232024)        |    -0.146 | -0.113 |      -0.429 |        -0.015 |     -0.178 | True     |
| (2, 'M0', 20212022)       |     1.501 |  1.537 |       1.678 |         1.301 |      1.627 | False    |
| (2, 'M0', 20222023)       |    -0.082 | -0.059 |      -0.608 |         0.151 |     -0.111 | True     |
| (2, 'M0', 20232024)       |    -1.412 | -1.485 |      -1.041 |        -0.73  |     -2.114 | True     |
| (2, 'M1_K2000', 20212022) |     0.495 |  0.461 |       0.352 |         0.291 |      0.732 | False    |
| (2, 'M1_K2000', 20222023) |    -0.085 | -0.089 |      -0.496 |         0.448 |     -0.428 | True     |
| (2, 'M1_K2000', 20232024) |    -0.408 | -0.374 |      -0.937 |         0.025 |     -0.631 | True     |
| (2, 'M1_K500', 20212022)  |     0.439 |  0.425 |       0.252 |         0.19  |      0.732 | False    |
| (2, 'M1_K500', 20222023)  |    -0.101 | -0.104 |      -0.545 |         0.465 |     -0.462 | True     |
| (2, 'M1_K500', 20232024)  |    -0.336 | -0.323 |      -0.99  |         0.125 |     -0.548 | True     |
| (2, 'M1_K8000', 20212022) |     0.638 |  0.584 |       0.583 |         0.468 |      0.814 | False    |
| (2, 'M1_K8000', 20222023) |    -0.076 | -0.073 |      -0.475 |         0.414 |     -0.383 | True     |
| (2, 'M1_K8000', 20232024) |    -0.559 | -0.514 |      -0.861 |        -0.15  |     -0.828 | True     |
| (2, 'M2_H30', 20212022)   |     0.5   |  0.439 |       0.52  |         0.299 |      0.678 | False    |
| (2, 'M2_H30', 20222023)   |    -0.046 | -0.043 |      -0.313 |         0.339 |     -0.304 | True     |
| (2, 'M2_H30', 20232024)   |    -0.451 | -0.399 |      -0.67  |        -0.134 |     -0.664 | True     |
| (2, 'M2_H60', 20212022)   |     0.486 |  0.438 |       0.439 |         0.286 |      0.686 | False    |
| (2, 'M2_H60', 20222023)   |    -0.059 | -0.061 |      -0.372 |         0.386 |     -0.356 | True     |
| (2, 'M2_H60', 20232024)   |    -0.424 | -0.379 |      -0.773 |        -0.057 |     -0.643 | True     |
| (2, 'O', 20212022)        |     0.157 |  0.127 |       0.471 |        -0.072 |      0.261 | False    |
| (2, 'O', 20222023)        |    -0.012 | -0.016 |      -0.095 |         0.1   |     -0.085 | True     |
| (2, 'O', 20232024)        |    -0.144 | -0.111 |      -0.428 |        -0.013 |     -0.176 | True     |
| (2, 'none', 20212022)     |     1.983 |  2.03  |       2.187 |         1.51  |      2.351 | False    |
| (2, 'none', 20222023)     |     0.396 |  0.432 |      -0.104 |         0.355 |      0.605 | True     |
| (2, 'none', 20232024)     |    -2.368 | -2.469 |      -2.295 |        -1.888 |     -2.808 | True     |

## Summary over judged cells

| construction            | family   |   max_abs_pp | all_pass   |
|:------------------------|:---------|-------------:|:-----------|
| none                    | none     |        2.808 | False      |
| M0                      | M0       |        2.114 | False      |
| E (not selectable, D35) | E        |        1.155 | False      |
| M1_K500                 | M1       |        0.99  | False      |
| M1_K2000                | M1       |        0.937 | False      |
| M1_K8000                | M1       |        0.9   | False      |
| M2_H30                  | M2       |        0.696 | False      |
| M2_H60                  | M2       |        0.773 | False      |
| O                       | O        |        0.428 | True       |

## Selection: **M2_H30** (fallback: smallest max |parity|, ties within 0.1 pp to the simpler construction (failure listed))

## Raw miss share by season and tier (% of unblocked ES / PP / PK attempts)

|   season |   high |   medium |   low |
|---------:|-------:|---------:|------:|
| 20212022 |  24.93 |    27.55 | 26.7  |
| 20222023 |  26.75 |    28.89 | 28.02 |
| 20232024 |  28.96 |    31.06 | 31.57 |
| 20242025 |  30.92 |    33.64 | 35.26 |
