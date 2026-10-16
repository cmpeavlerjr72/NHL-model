# INV-36: G2 for A3g-c on the re-levelled stage-1 incumbent H3''-LC2 + T2 (Lane S4, 2026-10-16)

- Brief: `docs/briefs/lane_S4_g2_confirm_2026-10-16.md`. Condition: D19. Full G2 tables, decompositions, per-team table: `docs/tests/gates_g2_sa_r3_g2_A3gc_lc2t2_2026-10-16.md`.
- Results (gitignored): `results/sa_r3_g2_A3gc_lc2t2/`. Attempt table cache: `results/shot_attempt_r3/att_lam_A3g-c_fold2.npy`.
- Setup: stage 1 = H3''-LC2 + T2 (Lane L2's cached `results/strength_state_lc2/r5/lam_H3_fold2.npy` and `types_T2_fold2.npy`, read-only; `simulate(per_team_types=True)`); stage 3 = A3g-c (b_c = 50); goals from the labelled league stub (as SA-R2/R3); no goalie pull; shootout skipped; 1398 games x 200 seeds. No gates.yaml, model-artifact or engine change.

## Verdict against the D19 condition

**Condition met.** Every non-3v3 cell is PASS (or UNDERPOWERED where labelled), the attempts-per-team-game decomposition is CLEAN (RS, overall, PO), and the per-state decomposition is CLEAN for 5v5, PP, PK and 4v4 (RS and overall). 4v4 passes (RS +2.82%, overall +2.58%, tolerance 3%) and closed-loop responsiveness passes. 3v3 is listed, gates at stage 8 (D19). The PM rules.

Things the PM should weigh:
- 4v4 RS +2.82% is inside the 3% line by 0.18 points. Offline A3g-c was +1.5% on 4v4; the closed loop adds about 1.3 points (per-60 decomposition of +1.37: hazard level +0.84, score mix +0.14, remainder +0.39; all the same sign, so no compensation). The 100-seed value is within 0.031 per 60 and also PASS.
- Playoffs: everything is UNDERPOWERED. The PO per-state decomposition marks PK as FAIL (+1.32 per 60 vs tolerance 0.40; sim 14.63 vs actual 13.32). That is a thin cell, labelled underpowered, not a gate result.

## Parity (stage-1 wiring)

`scripts/run_shot_attempt_g2.py` gained a default-off `--stage1 lc2t2` (additive; existing options unchanged). `scripts/diag_shot_attempt_s4_parity.py` runs the G2-path loader plus `simulate(per_team_types=True)` with no attempts, seeds 0-7, and compares to Lane L2's G1 outputs (`results/ss_lc2_g1_H3_T2`): `games` (11,184 rows, 6 cols) and `strength_toi` (11,184 rows, 28 cols) are **bit-identical**. Output: `results/sa_r3_g2_A3gc_lc2t2/parity_g1.json`.

## Clock (EDT)

| step | start | end |
|---|---|---|
| lane start | 09:51:40 | |
| parity | 09:52:11 | 09:52:46 |
| attempt table A3g-c (25 s) + block 0 | 09:52:52 | 09:58:37 |
| blocks 50 / 100 / 150 (parallel, 4 processes total) | about 09:53:30 | 09:59:06 |
| grade | 09:59:26 | 09:59:27 |

Measured about 6.3 s per seed per process; four blocks of 50 seeds took about 6 min wall, under the 15-min box rule. No box request filed.

## G2 table (per 60 unless stated; tolerance 3%)

| cell | RS | overall | PO |
|---|---|---|---|
| 5v5 | 58.56 vs 58.35, +0.35% PASS | +0.43% PASS | +1.65% UNDERPOWERED |
| PP | -0.49% PASS | -0.30% PASS | +2.44% UNDERPOWERED |
| PK | -2.14% PASS | -1.37% PASS | +9.88% UNDERPOWERED |
| 4v4 | **50.00 vs 48.62, +2.82% PASS** | +2.58% PASS | -0.95% UNDERPOWERED |
| 3v3 | 58.13 vs 55.23, +5.25% FAIL, **listed, gates at stage 8 (D19)** | +5.24% FAIL, same label | no actual 3v3 |
| EN-for / EN-against | UNREACHABLE (stage 8) | UNREACHABLE | UNREACHABLE |
| attempts / team-game | 58.92 vs 59.48, -0.94% PASS | -0.95% PASS | -1.08% UNDERPOWERED |
| score buckets -1 / 0 / +1 | -2.78% / +0.39% / +0.97% PASS | -2.67% / +0.58% / +0.92% PASS | UNDERPOWERED |
| score buckets <=-3, -2, +2, >=+3 | UNDERPOWERED | UNDERPOWERED | UNDERPOWERED |
| team-game SD (reported) | 9.91 vs 11.61 | 10.11 vs 11.86 | 12.13 vs 14.61 |
| home-away corr (reported) | -0.23 vs -0.41 | -0.19 vs -0.37 | |

## Decompositions (attempts per team-game, tolerance 1.78)

| component | RS | overall | PO |
|---|---:|---:|---:|
| hazard level | +0.18 | +0.25 | +1.36 |
| EN unreachable | -1.69 | -1.69 | -1.71 |
| state visits | +0.97 | +0.91 | -0.14 |
| score visits | +0.04 | +0.04 | +0.04 |
| remainder | -0.07 | -0.08 | -0.23 |
| verdict | CLEAN | CLEAN | CLEAN (UNDERPOWERED) |

By state per 60 (RS): 5v5 CLEAN (+0.20), PP CLEAN (-0.49), PK CLEAN (-0.31), 4v4 CLEAN (+1.37 vs tol 1.46), 3v3 FAIL (+2.90 vs tol 1.66; hazard level +2.98; listed). Overall shows the same pattern.

## Closed-loop responsiveness (overall, 5v5, quintile spread ratio, band 0.8-1.2)

- Own ES attempts-for rating: 1.135 (95% CI 0.996..1.313) PASS. Sim per 60 by quintile 53.6 / 56.6 / 59.0 / 60.4 / 64.2 against actual 54.3 / 56.5 / 58.3 / 59.6 / 63.7.
- Opponent ES attempts-against rating: 1.122 (0.973..1.329) PASS.
- Per team (all UNDERPOWERED): correlation of for 0.93, against 0.94.

## 100 vs 200 seeds

Every status is identical in RS, PO and overall. Largest per-60 move in a powered RS cell: 0.044 (PP); 4v4 0.031; 3v3 0.005. (PO 3v3 moves 11.5 per 60 but has no actual and is UNDERPOWERED.)

## EN watch item (D17, reported, not gated)

EN attempts are unreachable: -1.69 per team-game (RS and overall), offset by +0.97 / +0.91 of extra 5v5 time. Unchanged from SA-R3.

## Comparison with SA-R3 (A3g on H3'' + T2, old level)

Thin cells improve: 4v4 +4.42% -> +2.82%, 3v3 +6.62% -> +5.25%. 5v5, PP, PK and per team-game are within 0.3 points. Responsiveness is the same (1.135 / 1.122).

## HF push (step 4): NOT DONE

`scripts/hf_sync_data.py push` takes `--dirs` (whole bulk dirs such as `results`) only; `--only` applies to pull, and there is no per-subdirectory restriction. A push would upload every other lane's in-progress `results/` files, so per the brief it was not run. Resume (for the PM or Lane O): `.venv/Scripts/python.exe scripts/hf_sync_data.py push --dirs results`.

## Proposed text for the PM

D20 candidate: "INV-36 closed. G2 for A3g-c on H3''-LC2 + T2 meets the D19 condition (RS 4v4 +2.82%, 3v3 +5.25% listed for stage 8). Stage-3 A3g-c becomes CONFIRMED-INCUMBENT (provisional); the 3v3 attempt hazard stays with INV-35."
