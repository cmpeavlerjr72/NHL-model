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
