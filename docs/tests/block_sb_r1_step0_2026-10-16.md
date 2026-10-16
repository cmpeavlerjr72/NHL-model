# SB-R1 step 1: block-share level constructions and parity (Lane B, 2026-10-16)

Spec (binding): `docs/models/block/experiments.md` SB-R1. Script: `scripts/exp_block_sbr1_step1.py`; library: `src/nhl_sim/block/data.py`; level table `data/processed/block/level_v1.parquet` (created_at < puck_drop asserted).

B0 = one-hot (strength group x period type) + level offset logit(s_asof) - logit(s_train), coefficient 1, fit on the fold's training rows (ES level group also serves EN rows, labelled). Parity = B0 predicted minus actual block share (pp) per training season, over graded rows (ES + PP + PK) and over ES. Tolerance +/-0.3 pp. The first season (2021-22) has no prior and is shown, not judged. E: on fold 1 every training row is era 1, so E = no level there (era-2 test games fall back to the pooled training share).

Block share by season (all attempts): see section 'Raw block share'.

## Parity (pred - actual, pp)

|                           |     ES |   overall | judged   |
|:--------------------------|-------:|----------:|:---------|
| (1, 'E', 20212022)        |  0.823 |     0.786 | False    |
| (1, 'E', 20222023)        | -0.812 |    -0.768 | True     |
| (1, 'M0', 20212022)       |  0.823 |     0.786 | False    |
| (1, 'M0', 20222023)       | -0.812 |    -0.768 | True     |
| (1, 'M1_K2000', 20212022) |  0.141 |     0.156 | False    |
| (1, 'M1_K2000', 20222023) | -0.139 |    -0.152 | True     |
| (1, 'M1_K500', 20212022)  |  0.107 |     0.115 | False    |
| (1, 'M1_K500', 20222023)  | -0.105 |    -0.112 | True     |
| (1, 'M1_K8000', 20212022) |  0.216 |     0.238 | False    |
| (1, 'M1_K8000', 20222023) | -0.213 |    -0.232 | True     |
| (1, 'M2_H30', 20212022)   |  0.135 |     0.158 | False    |
| (1, 'M2_H30', 20222023)   | -0.133 |    -0.154 | True     |
| (1, 'M2_H60', 20212022)   |  0.133 |     0.151 | False    |
| (1, 'M2_H60', 20222023)   | -0.131 |    -0.147 | True     |
| (1, 'O', 20212022)        | -0.002 |    -0.001 | False    |
| (1, 'O', 20222023)        |  0.002 |     0.001 | True     |
| (1, 'none', 20212022)     |  0.823 |     0.786 | False    |
| (1, 'none', 20222023)     | -0.812 |    -0.768 | True     |
| (2, 'E', 20212022)        |  0.818 |     0.783 | False    |
| (2, 'E', 20222023)        | -0.817 |    -0.773 | True     |
| (2, 'E', 20232024)        |  0.009 |     0.008 | True     |
| (2, 'M0', 20212022)       |  1.477 |     1.42  | False    |
| (2, 'M0', 20222023)       | -0.158 |    -0.134 | True     |
| (2, 'M0', 20232024)       | -1.245 |    -1.205 | True     |
| (2, 'M1_K2000', 20212022) |  0.287 |     0.28  | False    |
| (2, 'M1_K2000', 20222023) |  0.011 |    -0.024 | True     |
| (2, 'M1_K2000', 20232024) | -0.282 |    -0.24  | True     |
| (2, 'M1_K500', 20212022)  |  0.239 |     0.213 | False    |
| (2, 'M1_K500', 20222023)  |  0.031 |    -0.013 | True     |
| (2, 'M1_K500', 20232024)  | -0.256 |    -0.188 | True     |
| (2, 'M1_K8000', 20212022) |  0.408 |     0.427 | False    |
| (2, 'M1_K8000', 20222023) | -0.017 |    -0.038 | True     |
| (2, 'M1_K8000', 20232024) | -0.37  |    -0.364 | True     |
| (2, 'M2_H30', 20212022)   |  0.247 |     0.272 | False    |
| (2, 'M2_H30', 20222023)   | -0.019 |    -0.035 | True     |
| (2, 'M2_H30', 20232024)   | -0.215 |    -0.222 | True     |
| (2, 'M2_H60', 20212022)   |  0.254 |     0.265 | False    |
| (2, 'M2_H60', 20222023)   | -0.006 |    -0.03  | True     |
| (2, 'M2_H60', 20232024)   | -0.234 |    -0.22  | True     |
| (2, 'O', 20212022)        | -0.006 |    -0.005 | False    |
| (2, 'O', 20222023)        | -0.004 |    -0.004 | True     |
| (2, 'O', 20232024)        |  0.01  |     0.008 | True     |
| (2, 'none', 20212022)     |  2.063 |     1.978 | False    |
| (2, 'none', 20222023)     |  0.428 |     0.422 | True     |
| (2, 'none', 20232024)     | -2.361 |    -2.263 | True     |

## Summary over judged cells

| construction   | family   |   max_abs_pp | all_pass   |
|:---------------|:---------|-------------:|:-----------|
| none           | none     |        2.361 | False      |
| M0             | M0       |        1.245 | False      |
| E              | E        |        0.817 | False      |
| M1_K500        | M1       |        0.256 | True       |
| M1_K2000       | M1       |        0.282 | True       |
| M1_K8000       | M1       |        0.37  | False      |
| M2_H30         | M2       |        0.222 | True       |
| M2_H60         | M2       |        0.234 | True       |
| O              | O        |        0.01  | True       |

## Selection: **M1_K500** (simplest passer)

## Raw block share by season (%, goalie-in attempts)

|   season |    ES |    PP |    PK |
|---------:|------:|------:|------:|
| 20212022 | 24.32 | 22.97 | 11.67 |
| 20222023 | 25.95 | 24.13 | 12.77 |
| 20232024 | 28.76 | 26.77 | 11.64 |
| 20242025 | 28.87 | 25.22 | 12.18 |
