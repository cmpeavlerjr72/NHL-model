# Lane S3 brief: SA-R3 (INV-32): thin-state attempt hazard, T2 merge into sim.py, G2 on H3''+T2

Model: Opus. Why not Sonnet: the T2 merge touches the engine core (bit-identical parity both ways) and the thin-state arms need judgment on a 25-team-hour cell where a wrong construction can pass by compensation.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first.
Spec (binding, do not change it): `docs/models/shot_attempt/experiments.md`, section **SA-R3** (committed 21fe71e). Context: SA-R2 report `docs/tests/shot_attempt_sa_r2_2026-10-15.md`, D17 in `ARCHITECTURE_DECISIONS.md`, engine sibling `src/nhl_sim/.../sim_ss_r5.py` (find it), SS-R5 report `docs/tests/strength_state_ss_r5_2026-10-15.md`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Concurrency

Lane L2 (LC-2, stage-1 level) runs at the same time and writes new strength_state level tables and trainer versions. Do not touch strength_state files except reading them; G2 uses stage 1 = H3'' + T2 on the OLD level (the incumbent at launch). Lane O serves the AWS box queue.

## Steps (chained)

1. Offline arms per the spec: A3g (reproduction), A3g-s, A3g-c (b_c tuned on fold 1), A2g-c, plus A3g seed 2 for the floor. New versioned trainer files; never overwrite SA-R2's.
2. Grade blind with the existing stage-3 grading script; thin-state bias table (fold 2 gate, fold 1 diagnostic) with cell SEs; selection per the decision rule.
3. Engine merge: T2 into `sim.py` behind a default-off flag, with both parity tests as pytest tests. Full test suite passes.
4. G2, 200 seeds, selected arm + A3g, stage 1 = H3'' + T2. Measure a 3-minute slice first; if the projected run exceeds 15 min, file a box request in `docs/ops/box_queue/` per the worker rules (inputs must be on HF or in git at a pushed commit) and wait in-turn for its `done_` file.
5. Report `docs/tests/shot_attempt_sa_r3_2026-10-16.md` (clock table, all tables, decompositions, labelled interpretation choices). Append a results block under SA-R3 in `experiments.md` and a ledger row in `docs/models/change_ledger.md` in the same commit. Commit, push, verify with `git ls-remote`.

If no arm passes in step 2, still do step 3, run G2 on A3g alone on H3''+T2, and report; the PM rules.

Message to the PM: under 400 words, per the worker rules.
