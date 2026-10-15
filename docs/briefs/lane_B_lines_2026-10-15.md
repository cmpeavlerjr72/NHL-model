# Lane B brief: lines, props and goalie-confirmation source audit (INV-3, INV-8)

Model: Sonnet. Core cap: 2. Rules: `docs/ops/worker_rules_2026-10-15.md` and `CLAUDE.md` (read both first).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Goal

Tell the PM, with evidence, where we get (a) historical NHL closing lines for 2021-22 -> 2025-26 backtests, (b) live game and prop markets on Kalshi and the DraftKings Predictions exchange (DKeX), (c) pregame starting-goalie confirmations with timestamps, and (d) whether third-party hockey data sites may be used. Research and small read-only probes only. No orders, no account actions, never print or commit credentials.

## Steps

1. **Reuse first.** Read how the sister projects already do this and record what transfers:
   - `C:\Users\devuser\cfb-props-sim\scripts\props_edge_dkex.py`, `kalshi_team_edges.py`, `lines_open.py`, `decision_policy.py`, the `DK_website data/` HAR captures, and `C:\Users\devuser\.claude\projects\C--Users-devuser-cfb-props-sim\memory\` notes on Kalshi / DKeX (read-only).
   - `C:\Users\devuser\CBB-clean-sheet` lines ingest (closing lines via CBBD) and `docs/postmortem/` notes on lines.
   - The existing Kalshi credential setup in `C:\Users\devuser\.kalshi` (do not print its contents; just find how the CFB code loads it).
2. **Kalshi NHL.** Using the existing read-only client pattern, list NHL series/markets currently open (game winner, totals, spreads, any player props), their contract structure (one-sided binaries? strikes?), fee schedule, depth/volume on a few markets, and whether historical prices/candles are retrievable for past games.
3. **DKeX NHL.** From the CFB code and HAR captures, determine whether NHL markets and player props are listed and how they are accessed. Do NOT attempt to log in. If a fresh HAR is required, say exactly which pages the user should capture.
4. **Historical closes.** Identify free or already-owned sources of NHL moneyline/puck line/total closes (and props if any) for 2021-26. For each candidate: coverage, books, timestamps (open/close), format, terms of use. Pull a small sample (one week) from the best candidate to prove format, if its terms allow.
5. **Goalie confirmations.** Candidate sources for projected/confirmed starting goalies with timestamps, live and historical. Note whether historical timestamps exist (needed for honest backtests).
6. **Third-party terms.** MoneyPuck, Natural Stat Trick, Evolving-Hockey, Hockey-Reference: terms of use / robots for automated access and ML use. Record verdicts.
7. Write `docs/ops/lines_sources_audit_2026-10-15.md` (findings, sample files paths, recommendation per need) and `docs/ops/data_sources.md` (one row per source: what, coverage, terms verdict, access method).

## Out of scope

Building production ingesters, modeling, any trading. Do not edit PM-owned docs.

## Report

Under 400 words per the worker rules: recommendation per need (a)-(d), blockers that need the user (e.g. a fresh DK HAR), commit hashes.
