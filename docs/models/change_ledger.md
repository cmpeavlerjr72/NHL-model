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
