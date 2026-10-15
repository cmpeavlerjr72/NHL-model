# HF sync

## Bulk data sync

`scripts/hf_sync_data.py` mirrors the gitignored bulk dirs to the PRIVATE HuggingFace dataset `mvpeav/nhl-sim-data`. It is the way to get `data/raw` and `results` onto a second machine or AWS box (a `git clone` does not bring them). Ported from `CBB-clean-sheet/scripts/hf_sync_data.py`.

### Keys

| `--dirs` key | Local dir | HF prefix |
|---|---|---|
| `raw` | `data/raw/` | `raw/` |
| `results` | `results/` | `results/` |
| `engine_inputs` | `data/processed/models/engine_inputs/` | `engine_inputs/` |

`engine_inputs` is a placeholder for future model-artifact dirs over 20 MB (CLAUDE.md: those sync to HF, not git). It is empty today; push skips an empty or missing key. `data/processed` and `data/reference` are git-tracked and are not synced here.

### Usage

```
.venv/Scripts/python.exe scripts/hf_sync_data.py status
.venv/Scripts/python.exe scripts/hf_sync_data.py push --dirs raw
.venv/Scripts/python.exe scripts/hf_sync_data.py pull --dirs raw
.venv/Scripts/python.exe scripts/hf_sync_data.py pull --dirs raw --only 'nhl_api/boxscore/**'
```

- `status`: remote file count, and per key local / remote / missing-on-remote (set difference by path, not a count).
- `push`: computes the missing set first, does nothing if fully mirrored; otherwise `upload_folder` per key with retry and exponential backoff (cap 10 min). `--max-attempts N` bounds retries per key (default 0 = retry forever, for overnight runs). Push only adds or updates; it never deletes remote files.
- `pull`: downloads into a staging dir under the target, then moves files to their final place (so no extra `raw/raw/` nesting). It OVERWRITES same-named local files and never deletes local-only files. `--only` takes globs relative to each key; `--dest-root DIR` lands the pull in a scratch directory for verification.

### Token

`HF_TOKEN` is read from the environment, else from the gitignored `.env` (template: `.env.example`, no value). It is never printed: all log text and exception messages are scrubbed of the token (and any `hf_...` pattern). `.env.example` is force-added to git because `.gitignore` has `.env.*`.

### Tests and smoke test

`tests/test_hf_sync_data.py` is offline (HfApi mocked). The 2026-10-15 live smoke test pushed, listed, pulled (bytes matched) and deleted a probe file `results/_sync_probe/probe.txt` using scratch roots, without touching `data/raw`.

### First raw push (PM, after Lane A reports)

```
.venv/Scripts/python.exe scripts/hf_sync_data.py push --dirs raw
```
