# Lane A4 brief: SL-R4 (stage 4): L3c with EN on the baseline only and 4v4 / 3v3 strata, closed loop

Model: Opus. Why not Sonnet: it changes the engine's attribute-lookup strata, and it must stay bit-identical on the off path while routing EN rows around the booster. This is the same engine surface Lane A3 just changed.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L27-L33.
Spec (binding): `docs/models/shot_attribute/experiments.md`, section **SL-R4** (and its parents). Context: D26; `docs/tests/shot_attribute_sl_r3_2026-10-16.md` (9d92d31) and its code.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
Lane B (block decision, offline) runs concurrently. It reads the stage-3 rows and level code but does not edit the engine. Do not touch its files.

## Steps (chained)

1. Build L0s and L3c (new versioned files).
2. Run the in-sample check and the fold-1 D13 guard. Stop if either fails.
3. Run the blind fold-2 grade, bias checks, responsiveness and decision.
4. If L3c is selected, update the engine lookup (flag-off path bit-identical to HEAD) and run the closed loop with the gating as written. Run locally if it projects under 45 min; otherwise report it pending.
5. Report `docs/tests/shot_attribute_sl_r4_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

Message to the PM: under 400 words.
