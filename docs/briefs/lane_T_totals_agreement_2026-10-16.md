# Lane T brief: LT-R1 / INV-25, price-adjusted totals agreement ESPN BET vs DRatings

Model: Sonnet. Core cap: 2 locally. You may NOT spawn sub-agents. No network: everything you need is on disk (`data/processed/lines_espn_core_v1.parquet`, `lines_dratings_v1.parquet` (v2 with flags may appear from Lane O3; totals are unaffected, so use v1), verified finals `verified_finals_v2`).
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first.
Spec (binding, do not change it): `docs/models/lines_totals/experiments.md`, section **LT-R1**. Context: D10, D11, D21 in `ARCHITECTURE_DECISIONS.md`; `docs/tests/lines_crosscheck_espn_dratings_2026-10-15.md`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Lanes A (stage 4) and O3 (lines flag + AWS) are running. Do not edit their files. Write new versioned scripts (`scripts/exp_totals_agreement_v1.py`) and outputs only.

Steps:
1. Explain '-68' first.
2. Build the conversion lookup from 2021-22 + 2022-23.
3. Run the agreement test and the calibration tables.
4. Apply the pass rule as written.

Report `docs/tests/lines_totals_lt_r1_2026-10-16.md`. Append a results block under LT-R1 in the same commit. Commit, push, verify with `git ls-remote`. Message to the PM: under 400 words.
