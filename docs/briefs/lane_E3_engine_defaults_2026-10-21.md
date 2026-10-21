# Lane E3 brief: INV-63, switch the selected models on in the engine's default table set

Model: Sonnet. Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus D41-D43.
Context: `src/nhl_sim/engine/sim.py` (flags `attr["l1x"]`, the C1s goal flag, the stand-in flags), `src/nhl_sim/engine/c1s_tables.py`, `src/nhl_sim/shot_attribute/serve_l1xas.py`, `scripts/run_engine_c1s_v1.py`, Lane A7's closed-loop runner for SL-R7 (see `docs/tests/shot_attribute_sl_r7_2026-10-21.md` for the command), `docs/tests/engine_c1s_2026-10-21.md`, `docs/ops/sim_output_schema.md`, `tests/engine/`.
Commit attribution line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`

**Concurrency.** Lane B5 (blocks) does offline work and does not touch `sim.py` until your report commit lands; your commit message must contain `engine_defaults`. Lane Z reads data only. Do not touch block / goal / shot_attribute model files.

**What "default on" means.** The engine's default table builder (the one the closed-loop runners call with no flags) now serves: stage 1 H3''-LC2 + T2, stage 3 A3g-c, block B0 stand-in (INV-54 groups), stage 4 **L1x-as** (D43), miss S0t stand-in, goal **C1s** (oracle goalie, D40). The L0s stand-in and the xG_ref goal stub stay available behind their explicit flags for reproducibility of the 2026-10-16 loops, and nothing is deleted. The `stand_in` marker must still list block B0 and miss S0t; the `attr` stand-in label disappears from the default output because L0s is no longer served by default (keep the label on the explicit L0s path). The `oracle_goalie` marker stays.

Steps:
1. Record a fixture from the HEAD engine on the existing parity cases before any edit, as Lanes E / E2 / A7 did.
2. Make the default table set as above. Flag-off / explicit-flag paths must stay bit-identical to HEAD on the fixture. Add a test that the default set carries L1x-as and C1s (the output has no `attr` stand-in label and does have the `oracle_goalie` marker).
3. Run the 200-seed plumbing loop on fold 2 with the default set, with the same seeds as Lane A7's SL-R7 closed loop. The per-seed game outputs must be bit-identical to Lane A7's loop (same models, same seeds); prove it by hashing the part files, or explain exactly why not (a difference is a finding, not a shrug). Report G2, G3, the stage-5/6 table (SOG per 60, miss share, save %, goals per 60 by strength state), and G5-G7 labelled plumbing (stages 7-8 absent). Measure a 3-minute slice first; the previous loops took 6-7 min locally.
4. Update `docs/ops/sim_output_schema.md` (markers, the default set, the explicit flags) and the engine docstring.
5. Report `docs/tests/engine_defaults_2026-10-21.md`; ledger rows (shot_attribute: L1x-as served by default; goal: C1s served by default). Commit with `engine_defaults` in the message, push, verify with `git ls-remote origin main`.

Message to the PM: under 300 words. Lead with: fixture bit-identity (yes / no), loop bit-identity to Lane A7's (yes / no, and why if no), and the save % / goals per 60 line.
