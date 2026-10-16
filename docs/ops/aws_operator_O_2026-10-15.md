# Lane O AWS operator report, 2026-10-15

- Chain: `docs/ops/aws_launch_chain.md`, `scripts/box_bootstrap_v1.sh`, `scripts/box_run_v1.sh`, `scripts/run_box_request.py` (user-data transport, no Docker/SSH, AL2023 + python3.12, HF in/out under `results/aws/<name>/`). Working end to end.
- Smoke test (c7i.large spot, us-east-1a, pytest 85 passed, output pushed to HF and verified): cold start launch to command start 83 s, launch to result 93 s, ~$0.001. Three smoke launches in total (two exposed bugs, since fixed: missing `sim` extras; stale `_done.json` from a prior run of the same name). Total spend $0.0039.
- Requests served: none. `docs/ops/box_queue/` stayed empty through the 21:50 cutoff (PM clock change); no time-saved figure.
- Spend ledger: `logs/aws_spend_O.jsonl` (gitignored).
- Final `aws ec2 describe-instances --filters Name=tag:project,Values=nhl-model` at ~21:51: empty output (no instances running, pending or terminating). Each smoke instance was also verified `terminated` by the runner.
- Notes for requesters: box sees only pushed commits plus git/HF inputs; request format is in the chain doc; done file is `done_<lane>_<step>_<HHMM>.md` (plus pointer `done_req_...`). Operator machine needs `boto3` (pip-installed in system Python; not added to repo deps).
