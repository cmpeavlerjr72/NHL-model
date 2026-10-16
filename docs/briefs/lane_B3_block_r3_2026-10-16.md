# Lane B3 brief: SB-R3, diagnosis of the block-rating over-response, then response-side arms (offline only)

Model: Opus. Why not Sonnet: step 0 is subtle diagnosis of a compensation-style failure. The fitted response holds on fold 1 and breaks on fold 2 in three stages, and D27 already misread its cause once.
Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L24, L27-L34.
Spec (binding): `docs/models/block/experiments.md`, section **SB-R3**. Context: D27, D29; `docs/tests/block_sb_r1_2026-10-16.md`, `docs/tests/block_sb_r2_2026-10-16.md` and their code (`scripts/train_block_v2.py`, `grade_block_v2.py`, `src/nhl_sim/block/`).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Lane A4 (stage 4) may still be editing `sim.py` and shot_attribute files. Do not touch them or its processes. Write new versioned files only.

Steps:
1. Run step 0 (diagnosis). Write it into the report and commit it before fitting any step-1 arm.
2. Run step 1: arms B1, B1p, B1m, B2p.
3. Run the blind fold-2 grade, bias checks, responsiveness, the fold-1 band for the selected arm, and the decision.
4. Report `docs/tests/block_sb_r3_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

If the diagnosis shows the spec's arms cannot address the cause, still run them as written. Then state the cause plainly and propose (not run) what would address it.

Message to the PM: under 400 words.
