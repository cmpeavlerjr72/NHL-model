# Lane C brief: port the HF data sync script (INV-9)

Model: Sonnet. Core cap: 1. Rules: `docs/ops/worker_rules_2026-10-15.md` and `CLAUDE.md` (read both first).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Goal

`scripts/hf_sync_data.py` for NHL-Model: push/pull/status of the gitignored bulk dirs to the private HF dataset `mvpeav/nhl-sim-data`, ported from `C:\Users\devuser\CBB-clean-sheet\scripts\hf_sync_data.py` (read-only source; do not modify the CBB repo).

## Steps

1. Read the CBB script and any doc it references (e.g. its `.env.example`, `docs/ops` notes on HF sync) to understand: token resolution (env, then `.env`, never printed), wave/retry upload logic, pull with staging, `status`, bulk keys for large artifact dirs.
2. Port it: `REPO_ID = "mvpeav/nhl-sim-data"`; sync keys `raw` (`data/raw/`), `results` (`results/`), and a placeholder `engine_inputs` key for future model-artifact dirs over 20 MB (document it, empty is fine). Drop CBB-specific keys. Keep the CLI shape (`push`, `pull`, `status`, `--dirs`, `--max-attempts`). Add `.env.example` with `HF_TOKEN=` (no value).
3. Tests: `tests/test_hf_sync_data.py`, offline only (mock `HfApi`): token never appears in logs/exceptions, key -> path mapping, pull refuses to overwrite a newer local file unless `--force` (if CBB has that behaviour; otherwise test what CBB guarantees).
4. Smoke test against the real dataset WITHOUT touching Lane A's live pull: run `status`; then push a tiny probe file `results/_sync_probe/probe.txt`, verify it via `status`/`list_repo_files`, pull it into a temp dir and compare bytes, then delete the probe from the remote and locally. Do NOT push `data/raw` (Lane A is still writing it; the PM will run the first raw push after Lane A reports).
5. Add a short "Bulk data sync" section to `docs/ops/hf_sync.md` (usage, keys, token handling).
6. Commit only your files, push, verify with `git ls-remote origin main`.

## Out of scope

Pushing real data, editing PM-owned docs, touching `src/nhl_sim/clients`, `scripts/pull_*`, or anything Lane A or Lane B owns.

## Report

Under 400 words: tests run and result, smoke-test evidence (file listed, bytes matched, probe deleted), commit hash, exact command the PM should run for the first raw push.
