# Worker rules, session 2026-10-21

PM-owned. Every lane brief points here. Carried over from 2026-10-16 with the changes marked **(2026-10-21)**. `CLAUDE.md` binds in full; this file adds session specifics.

## Model

**(2026-10-21)** The PM session runs on Fable today. That changes nothing for workers: you are running on Opus, Sonnet or Haiku, never Fable. You may not spawn sub-agents unless your brief grants it; if granted, pass `model: "sonnet"` or `model: "haiku"` explicitly.

## Python

Use `.venv/Scripts/python.exe` explicitly in every command. Never `python3`: on this box it is the Windows Store stub, and it hung a lane on 2026-10-16. Set `PYTHONIOENCODING=utf-8` for anything that prints non-ASCII.

## Clock

Real wall clock only: `Get-Date -Format "yyyy-MM-dd HH:mm:ss K"` at the start and before / after every compute or download step, logged in your report. Size long runs from a measured slice of at least 3 minutes, never a guess. Neither you nor the PM can estimate elapsed time otherwise.

## Waiting

Never end your turn while a job you started is still running. Wait in-turn with a blocking foreground wait (timeout at most 10 minutes, repeated). Before reporting, stop every background child you started so exactly one completion notice reaches the PM.

## Compute and network

- Home box, shared. Your core cap is in your brief.
- Network pulls: at most 4 concurrent requests to any one host, retry with exponential backoff, cache raw responses to disk, never re-fetch a cached file. Identify a polite User-Agent.
- AWS **(2026-10-21: approved again by the user for this session, $60 cap)**: **Lane O4 is the only OPERATOR** and the only lane that touches AWS (us-east-1, spot only, every instance terminated and the termination verified with `describe-instances` before Lane O4 reports).
  - Any other lane whose measured 3-minute slice projects a step longer than **15 minutes** locally does NOT run it on the home box. It writes a box request `docs/ops/box_queue/req_<lane>_<step>_<HHMM>.md` in the format of `docs/ops/aws_launch_chain.md`: the exact command, the git commit to run at (pushed), the inputs (on HF or in git), the outputs and where they go back (HF path), and the cores / RAM needed. Commit and push the request so Lane O4 sees it.
  - The requesting lane continues with whatever does not depend on the result, then waits in-turn (10-min waits) for `docs/ops/box_queue/done_<same name>.md`.
  - Rate-limited network pulls are NOT moved to AWS. Spreading a polite crawl over more IPs is not polite.
- Commit AND push (`git push origin main`), then verify with `git ls-remote origin main`. If a push is rejected because another lane pushed first, `git pull --ff-only` is not allowed on the shared tree either: report it to the PM.
- No orders, trades, or account actions on Kalshi, DraftKings, or any venue. Read-only market data only. Never print or commit credentials.

## Git on the shared tree

All lanes share one working tree on `main`. Stage ONLY your own files by explicit path. Never `git add -A`, `git add .`, `git commit -a`, `git stash`, `git pull --rebase`, `git reset`, `git checkout -- <file>`. Check `git diff --cached --stat` shows only your files before committing. Commit messages end with the attribution line given in your brief. `data/processed/schedule_weekly.parquet` is modified by the weekly pull task; leave it unstaged.

## Ownership

PM-owned, do not edit: `CLAUDE.md`, `PROJECT_STATUS.md`, `HANDOFF.md`, `ARCHITECTURE_DECISIONS.md`, `docs/FRAMEWORK_PLAN.md`, `docs/SIM_GUARDRAILS.md`, `docs/LEARNINGS.md`, `docs/BOARD.md`, `docs/gates.yaml`, anything in `docs/ops/worker_rules_*` or `docs/briefs/`. Propose text for them in your report. The one exception: a lane appends its results block under the "Results" line of its own round in `docs/models/<model>/experiments.md`, and adds its ledger row in `docs/models/change_ledger.md`, in the same commit as its report.

## Reporting

Full evidence goes to the doc path named in your brief, committed. Your final message to the PM is under 400 words: result per deliverable (with numbers and doc paths), what was NOT done or is PARTIAL (with the resume command), any incident you caused, the commit hashes, and the next step you recommend. Plain statements; do not present a partial or underpowered result as a finding. A lane that finishes early reports early; it does not invent extra scope.

## Process control

Before stopping any process, print its full command line (`Get-CimInstance Win32_Process -Filter "ProcessId=<pid>" | Select CommandLine`). Stop it only if that line names a script you launched in this lane. "It was python and I assumed it was mine" is the incident this rule prevents (Lane I stopped Lane H's replay diagnostic on 2026-10-15).

## Holdout discipline

Fold 2 (2024-25) is read only at the step the spec names, after every earlier table is committed. Nothing from 2025-26 is read (the seal is enforced in code; do not set `NHL_UNSEAL_2025`). Intermediate documents never print fold-2 numbers before the selection step (Lane G incident, 2026-10-16).
