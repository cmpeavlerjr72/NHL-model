# Change ledger

Append-only. One row per status change, same commit as the experiments.md entry. LF line endings.

| Date | Model | From | To | Evidence | Commit |
|---|---|---|---|---|---|
| 2026-10-15 | control | - | OPEN | R1 pre-registered in control/experiments.md | 5d2ae4d |
| 2026-10-15 | control | OPEN | TESTING | R1 run and graded: winner A0, fails G5/G6/G7/G9 (bar for event engine); see docs/tests/control_r1_2026-10-15.md | (this commit) |
| 2026-10-15 | control | TESTING | CONFIRMED-INCUMBENT (yardstick A0) | D9; docs/tests/control_r1_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | - | OPEN | SS-R1 pre-registered in strength_state/experiments.md | (this commit) |
| 2026-10-15 | strength_state | OPEN | TESTING | SS-R1 run: offline H3/T1; G1 overall pass is compensated (level drift vs missing EN-state events); see docs/tests/strength_state_ss_r1_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | TESTING | TESTING (ruling) | D12: H3 not confirmed (compensated G1); SS-R2 pre-registered | 2b7ebe0 |
| 2026-10-15 | strength_state | TESTING | TESTING | SS-R2 run: offline H3'; bias checks fail in every arm (Jan 2025 month level; H3' overall +3.1%), G1 not run; see docs/tests/strength_state_ss_r2_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | TESTING | TESTING (ruling) | D13: SS-R2 all arms fail bias checks; SS-R3 pre-registered | (this commit) |
| 2026-10-15 | strength_state | TESTING | TESTING | SS-R3 run: offline H3''; fold-2 bias checks fail in every arm (Jan 2025 +8.3% to +9.0%; overall level now passes), fold 1 passes; G1 not run; see docs/tests/strength_state_ss_r3_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | TESTING | TESTING (ruling) | D14: H3''+T1 accepted with listed Jan-2025 bias, pending clean G1 (INV-28) | (this commit) |
| 2026-10-15 | strength_state | TESTING | TESTING | SS-R3 closed-loop G1 (INV-28): parity test passes; RS cells PASS for H3'' and H2''; D14 decomposition CLEAN (H3'' RS +0.061 PP opps, no component > 0.15); responsiveness slopes but over-steep; see docs/tests/strength_state_g1_ssr3_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | TESTING | CONFIRMED-INCUMBENT (provisional) | D15: G1 RS PASS, CLEAN (b513691); rating over-response INV-29 open | (this commit) |
| 2026-10-15 | shot_attempt | - | OPEN | SA-R1 pre-registered in shot_attempt/experiments.md | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | SS-R4 (INV-29 rating response) pre-registered | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | SS-R4 (INV-29): stop condition met (offline fold-1 spread ratio 0.81/0.85); arms not run; lead: T1 has no rating features; replay regression confirmed; see docs/tests/strength_state_ss_r4_2026-10-15.md | (this commit) |
| 2026-10-15 | shot_attempt | OPEN | TESTING | SA-R1 run: no arm eligible (every arm fails the fold-2 level, -5%; root cause the SS-R3 level anchoring, fold-1 diagnostic), offline A3 > A4 > A2; G2 not run by rule; see docs/tests/shot_attempt_sa_r1_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | SS-R4 stop (d01e082); SS-R5 type-model team terms pre-registered | (this commit) |
| 2026-10-15 | shot_attempt | OPEN | TESTING | SA-R1: no arm eligible (level defect, D16); SA-R2 pre-registered | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | D16: SS-R3c re-level pre-registered; D15 holds until it rules | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | SS-R5 (INV-29): T2 type arm (own+opp taken-rating) wins offline (+0.0031 nats/penalty, 2.9 SE over T1); closed loop RS cells PASS and CLEAN but spread ratio 1.19 / 1.25 (drawn outside [0.8,1.2]); gate not met, INV-29 open, D15 holds; see docs/tests/strength_state_ss_r5_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | SS-R5 (dff868d): type arm T1 -> T2; INV-29 open (drawn spread 1.25) | (this commit) |
| 2026-10-15 | shot_attempt | TESTING | TESTING | SA-R2 run: A3g selected (A2g next); fold-2 bias and responsiveness pass; G2 RS core cells PASS and CLEAN, 4v4 / 3v3 per-60 FAIL; see docs/tests/shot_attempt_sa_r2_2026-10-15.md | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | SS-R3c stopped at the LC-1 parity assertion (fold-1 train H0''c -2.1% / +2.0%); fold 2 not graded; D15 unchanged; see docs/tests/strength_state_ss_r3c_2026-10-15.md | (this commit) |
| 2026-10-15 | shot_attempt | TESTING | TESTING (ruling) | D17: A3g leads; G2 4v4/3v3 fail; SA-R3 next | (this commit) |
| 2026-10-15 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | D17: SS-R3c stopped at LC-1 parity; LC-2 next; H3''+T2 on old level | (this commit) |
| 2026-10-16 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | LC-2 pre-registered (INV-33): level constructions L2c/L2a/L2b vs L1, parity on genuine-prior seasons, then SS-R3c decision rule + INV-29 re-measure | (this commit) |
| 2026-10-16 | shot_attempt | TESTING | TESTING | SA-R3 pre-registered (INV-32): A3g-s / A3g-c / A2g-c thin-state arms; T2 merged into sim.py behind a flag; G2 on H3''+T2 | (this commit) |
| 2026-10-16 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional), PM to rule | LC-2 run (INV-33): no level passes 0.5% parity, L2b hl14 selected by fallback (max 0.93%); H3''-LC2 meets SS-R3c acceptance (bias, LL, G1 RS CLEAN); INV-29 point ratios 1.10-1.19; see docs/tests/strength_state_lc2_2026-10-16.md | (this commit) |
| 2026-10-16 | strength_state | CONFIRMED-INCUMBENT (provisional) | CONFIRMED-INCUMBENT (provisional) | D18: incumbent H3''+T2 (old level) -> H3''-LC2+T2 (L2b hl14 level, parity miss +0.93% listed); INV-29 closed (spread 1.10/1.11 RS, 1.13/1.19 all); see docs/tests/strength_state_lc2_2026-10-16.md (3a17280) | (this commit) |
| 2026-10-16 | shot_attempt | TESTING | TESTING | SA-R3 run (INV-32): no thin-state arm passes (3v3 fold-2 bias +4.2% to +6.8% in every arm; A3g-s fails D13 on 4v4); T2 merged into sim.py behind per_team_types (parity bit-identical); G2 A3g on H3''+T2: core cells PASS/CLEAN, 4v4/3v3 FAIL; PM rules | (this commit) |
