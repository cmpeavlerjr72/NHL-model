# Worker rules, session 2026-10-15

PM-owned. Every lane brief points here. `CLAUDE.md` binds in full; this file adds session specifics.

## Model

You are running on Opus, Sonnet or Haiku, never Fable. You may not spawn sub-agents unless your brief grants it; if granted, pass `model: "sonnet"` or `model: "haiku"` explicitly.

## Clock

Real wall clock only: `Get-Date -Format "yyyy-MM-dd HH:mm:ss K"` at the start and before / after every compute or download step, logged in your report. Size long runs from a measured slice of at least 3 minutes, never a guess. Neither you nor the PM can estimate elapsed time otherwise.

## Waiting

Never end your turn while a job you started is still running. Wait in-turn with a blocking foreground wait (timeout at most 10 minutes, repeated). Before reporting, stop every background child you started so exactly one completion notice reaches the PM.

## Compute and network

- Home box, shared. Your core cap is in your brief.
- Network pulls: at most 4 concurrent requests to any one host, retry with exponential backoff, cache raw responses to disk, never re-fetch a cached file. Identify a polite User-Agent.
- AWS: approved by the user, but no lane this session is the operator; no lane launches instances today.
- Commit AND push (`git push origin main`), then verify with `git ls-remote origin main`. If a push is rejected because another lane pushed first, do not force or rebase: report it to the PM.
- No orders, trades, or account actions on Kalshi, DraftKings, or any venue. Read-only market data only. Never print or commit credentials.

## Git on the shared tree

All lanes share one working tree on `main`. Stage ONLY your own files by explicit path. Never `git add -A`, `git add .`, `git commit -a`, `git stash`, `git pull --rebase`, `git reset`, `git checkout -- <file>`. Check `git diff --cached --stat` shows only your files before committing. Commit messages end with the attribution line given in your brief.

## Ownership

PM-owned, do not edit: `CLAUDE.md`, `PROJECT_STATUS.md`, `HANDOFF.md`, `ARCHITECTURE_DECISIONS.md`, `docs/FRAMEWORK_PLAN.md`, `docs/SIM_GUARDRAILS.md`, `docs/LEARNINGS.md`, `docs/BOARD.md`, `docs/gates.yaml`, anything in `docs/ops/worker_rules_*` or `docs/briefs/`. Propose text for them in your report.

## Reporting

Full evidence goes to the doc path named in your brief, committed. Your final message to the PM is under 400 words: result per deliverable (with numbers and doc paths), what was NOT done or is PARTIAL (with the resume command), any incident you caused, the commit hashes, and the next step you recommend. Plain statements; do not present a partial or underpowered result as a finding. A lane that finishes early reports early; it does not invent extra scope.
