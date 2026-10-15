# Lane O brief: AWS operator, port the box chain and serve the box queue

Model: Sonnet. Core cap: 1 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` (Compute section) and `docs/ops/worker_rules_2026-10-15.md` (AWS bullet, updated 18:55). Read both first. You are the only lane that touches AWS.
Reference to port (read-only): `C:\Users\devuser\CBB-clean-sheet\docs\ops\aws_launch_chain.md` and its `scripts/box_bootstrap_v1.sh`, `box_run_v3.sh`, `box_queue_v1.sh`, `run_aws_sweep.sh`. Mine the CBB LEARNINGS/postmortems for AWS incidents before you launch anything.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Hard limits

- us-east-1, **spot instances only**. Spend cap **$60** for the session. Track the estimated spend (instance type x hours x spot price) in your report, and stop launching at $50.
- Tag every instance `project=nhl-model`, `lane=O`. Use self-termination as a backstop: `shutdown -h` after the job plus a max-lifetime timer, with instance-initiated shutdown set to terminate.
- Never leave an instance idle. Before you report, run `aws ec2 describe-instances --filters Name=tag:project,Values=nhl-model` and paste the output showing that none is running or pending.
- Secrets: `HF_TOKEN` and any GitHub credential reach the box only through user-data or SSM at runtime. They are never printed, logged or committed. Only touch AWS resources tagged `project=nhl-model` or ones you created.

## Clock (hard)

Run `Get-Date` at the start. Stop accepting new box requests at **23:15 EDT**. All instances must be terminated and verified, and the report committed, by **23:45 EDT**.

## Steps (chained)

1. **Port the chain.**
   - Write `docs/ops/aws_launch_chain.md` for NHL-Model. It covers the AMI/bootstrap (Python 3.12, a clone of `cmpeavlerjr72/NHL-model` at a given commit, `pip install` from the repo, inputs pulled from HF `mvpeav/nhl-sim-data`, outputs pushed back to HF under `results/aws/<request>/`), and the thread env vars pinned to the vCPU count.
   - Write the scripts as `scripts/box_bootstrap_v1.sh`, `scripts/box_run_v1.sh` and `scripts/run_box_request.py`. The last one takes a request file, launches, waits, verifies the outputs on HF, terminates and verifies, and writes `done_<name>.md` with timings and cost.
2. **Smoke test.** Run the cheapest spot instance that runs `pytest` on the repo at HEAD and pushes a small output file to HF. Terminate it, verify, and record the cold-start to result time and the cost.
3. **Serve the queue.** Until 23:15, check `docs/ops/box_queue/` for `req_*.md` every 5 minutes (blocking in-turn waits of at most 10 min each).
   - Run each request on a right-sized spot instance (prefer c7i/c6i compute-optimised; size from the request's cores/RAM), and write its `done_*.md`.
   - Commit the queue files you write (explicit paths only) so the requester sees them.
   - If no request arrives by 23:15, that is a normal outcome; report it.
4. **Report.** Write `docs/ops/aws_operator_O_2026-10-15.md`, commit, push and verify.

## Report to PM (under 400 words)

Give the chain status, the smoke-test timing and cost, the requests served (with time saved vs the local projection), the total spend, the pasted `describe-instances` proof of zero running instances, incidents and commits.
