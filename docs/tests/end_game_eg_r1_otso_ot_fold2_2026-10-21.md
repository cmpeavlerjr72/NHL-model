# EG-R1 part B: fold-2 parity and offline served bias of the 3v3 level (Lane H8b, 2026-10-21)

Read AFTER the training parity table and the selection were committed (e977e74). Fold 2 = 2024-25 regular season, 3v3 team-view rows, both teams. Parity is of the level alone (reported); the gate is the closed-loop G2 3v3 cell.

| season   | level    |   actual |   predicted |   parity |   team_hours |   games_with_3v3 |   per_team_hour_actual |   per_team_hour_pred |   goals |   poisson_se_rel | selected   | within_poisson_se   |
|:---------|:---------|---------:|------------:|---------:|-------------:|-----------------:|-----------------------:|---------------------:|--------:|-----------------:|:-----------|:--------------------|
| 2024-25  | M1_K500  |     1369 |     1386.56 |   0.0128 |      24.7867 |              262 |                55.2313 |              55.9397 |     163 |            0.027 | True       | True                |
| 2024-25  | M1_K2000 |     1369 |     1382.13 |   0.0096 |      24.7867 |              262 |                55.2313 |              55.7612 |     163 |            0.027 | False      | True                |
| 2024-25  | M2_H30   |     1369 |     1379.97 |   0.008  |      24.7867 |              262 |                55.2313 |              55.6737 |     163 |            0.027 | False      | True                |
| 2024-25  | E        |     1369 |     1380.45 |   0.0084 |      24.7867 |              262 |                55.2313 |              55.6933 |     163 |            0.027 | False      | True                |
| 2024-25  | O        |     1369 |     1369    |   0      |      24.7867 |              262 |                55.2313 |              55.2313 |     163 |            0.027 | False      | True                |

Offline served form on the same rows (A3g booster x exp(L_new - L_old) x exp(cell); the cell is the SA-R3 recipe refit on the fold-2 TRAINING rows with the own level in place; with the old level the same code reproduces the frozen A3g-c cell to 1e-12):

| arm                                   |   actual |   predicted |   bias |   per60_combined_pred |   per60_combined_actual |   poisson_se_rel |
|:--------------------------------------|---------:|------------:|-------:|----------------------:|------------------------:|-----------------:|
| A3g-c (shared ES level, cell -0.0133) |     1369 |     1442.87 | 0.054  |               116.423 |                 110.463 |            0.027 |
| own M1_K500 level, refit cell -0.0153 |     1369 |     1373.98 | 0.0036 |               110.865 |                 110.463 |            0.027 |

Training diagnostics of the refit cell: {"train_y": 4426.0, "train_mu_before_cell": 4494.847134201465, "mean_delta": 0.0022827214395051334}; frozen A3g-c cell -0.01334, refit cell -0.01526.

UNDERPOWERED note: about 1,370 attempts and 160 goals in the season; the Poisson count error is 2.7%.