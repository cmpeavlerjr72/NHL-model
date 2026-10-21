# Lane O4 brief: AWS operator, serve the box queue (session 2026-10-21)

Model: Sonnet. Core cap: 1 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` (Compute section) and `docs/ops/worker_rules_2026-10-21.md` (AWS bullet). Read both first. You are the only lane that touches AWS. The user approved AWS for this session (2026-10-21) with the standing $60 cap.
Chain (already built, use as is): `docs/ops/aws_launch_chain.md`, `scripts/box_bootstrap_v1.sh`, `scripts/box_run_v1.sh`, `scripts/run_box_request.py`. Prior operator reports: `docs/ops/aws_operator_O_2026-10-15.md`, `aws_operator_O2_2026-10-16.md`, `aws_operator_O3_2026-10-16.md` (read their incidents and the "notes for requesters").
Commit attribution line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`

## Hard limits

- us-east-1, **spot instances only**. Spend cap **$60** for the session; stop launching at $50. Track estimated spend (instance type x hours x spot price) in `logs/aws_spend_O.jsonl` and in your report.
- Tag every instance `project=nhl-model`, `lane=O4`. Self-termination backstop (`shutdown -h` after the job plus a max-lifetime timer, instance-initiated shutdown = terminate).
- Never leave an instance idle. Before you report, run `aws ec2 describe-instances --filters Name=tag:project,Values=nhl-model` and paste the output showing none running or pending.
- Secrets reach the box only through user-data or SSM at runtime; never printed, logged or committed. Touch only resources tagged `project=nhl-model` or ones you created.

## Clock (hard)

Run `Get-Date` at the start. Stop accepting new requests **4 hours** after your start time, or when the PM's stop file `docs/ops/box_queue/STOP_O4` appears, whichever is first. All instances terminated and verified, and the report committed, within 30 minutes after that.

## Steps

1. Start: `git pull --ff-only` is NOT allowed on the shared tree; read the queue from the working tree (requesters commit their request files locally before pushing, so the file is on disk). Verify the AWS CLI credentials work with a read-only `describe-instances` and confirm zero instances exist before you begin.
2. Serve the queue: check `docs/ops/box_queue/` for `req_*.md` without a matching `done_*.md` every 5 minutes (blocking in-turn waits of at most 10 minutes each). Requesters this session: Lane A7 (SL-R7 snapshots or closed loop) and Lane E2 (plumbing closed loop). Run each on a right-sized spot instance (c7i / c6i, sized from the request), at the request's pushed commit, inputs from git / HF, outputs back to HF under `results/aws/<name>/`, and write `done_<same name>.md` with timings and cost. Commit the queue files you write (explicit paths only), push, verify.
3. If a request cannot run (commit not pushed, input missing on HF), write `done_<name>.md` with status FAILED and the reason within 10 minutes, so the requester is not blocked silently.
4. If no request arrives before the cutoff, that is a normal outcome; report it.
5. Report `docs/ops/aws_operator_O4_2026-10-21.md`, commit, push, verify.

## Report to PM (under 300 words)

Requests served (with time saved vs the local projection), total spend, the pasted `describe-instances` proof of zero instances, incidents, commits.
