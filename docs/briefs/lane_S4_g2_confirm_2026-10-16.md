# Lane S4 brief: INV-36, G2 for A3g-c on the re-levelled stage-1 incumbent

Model: Sonnet. Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first.
Context: D18 and D19 in `ARCHITECTURE_DECISIONS.md`; `docs/tests/shot_attempt_sa_r3_2026-10-16.md` (Lane S3, 3b68b8f; its G2 runner `scripts/run_shot_attempt_g2.py`); `docs/tests/strength_state_lc2_2026-10-16.md` (Lane L2, 3a17280; stage-1 level tables `league_level_v5_f{1,2}`, `scripts/run_strength_state_g1_lc2.py`).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Steps

1. Run G2 with stage 1 = H3''-LC2 + T2 (`per_team_types` on, LC-2 level tables) and stage 3 = A3g-c (b_c = 50), 200 seeds. Reuse the existing runners; if wiring stage 1's LC-2 level into the G2 path needs code, add it as a versioned script or a default-off option, with a parity test showing the stage-1 path reproduces Lane L2's G1 numbers on a fixed seed set. Do not change gates.yaml, model artifacts or the engine defaults. If a measured 3-minute slice projects over 15 min, file a box request (Lane O2 serves the queue until 17:00).
2. Report the full G2 table (RS, overall, playoffs labelled), the per-team-game and by-state decompositions, closed-loop responsiveness, 100-vs-200-seed stability, and the EN watch item, in the SA-R3 report format. The 3v3 cell is reported and labelled "listed, gates at stage 8 (D19)".
3. Verdict against the D19 condition: every non-3v3 cell PASS and CLEAN, 4v4 PASS closed-loop. Report it plainly; the PM rules.
4. Then push `results/` to HF for your own and Lane S3's outputs only (`hf_sync_data.py push` restricted to `results/shot_attempt*` and your G2 output dirs; check the script's options; if it cannot restrict, do not push and say so).
5. Report `docs/tests/shot_attempt_g2_inv36_2026-10-16.md`, a results block under the D19 ruling in `docs/models/shot_attempt/experiments.md`, a ledger row. Commit, push, verify with `git ls-remote`.

Message to the PM: under 400 words.
