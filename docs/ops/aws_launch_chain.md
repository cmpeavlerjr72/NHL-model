# AWS launch chain (Lane O, NHL-Model)

Ported from CBB `docs/ops/aws_launch_chain.md`, simplified: no Docker, no SSH, no key pair. Everything rides on EC2 user-data.

## Rules (CLAUDE.md Compute + worker rules)
- us-east-1, spot only (one-time, interruption = terminate), `InstanceInitiatedShutdownBehavior=terminate`. Cap $60 per session, stop launching at $50.
- Tags: `project=nhl-model`, `lane=O`, `request=<name>`. Only Lane O touches AWS.
- Backstop: user-data runs `shutdown -h +<max_minutes+8>` first thing; the runner also `shutdown -h now` on completion or failure; `run_box_request.py` terminates and verifies in a `finally`.
- Secrets: `HF_TOKEN` is read from env/`.env` on the operator machine and goes only into user-data. Never printed (script output scrubs it), never committed. The repo is public, so the clone needs no GitHub credential.
- Account/credentials: the existing `cfb-sweep` IAM user from the local AWS CLI profile. Default VPC and default security group (no inbound rules needed). No IAM instance profile / SSM (the user cannot list them), hence user-data transport.

## Pieces
- `scripts/run_box_request.py` (operator machine): parse request, pick type, launch, poll HF for `results/aws/<name>/_done.json` (and instance state), verify pushed files exist on HF, terminate, verify `terminated`, write `docs/ops/box_queue/done_<name>.md` (+ a pointer `done_req_<name>.md`), append `logs/aws_spend_O.jsonl`. `--smoke` runs the pytest smoke test; `--dry-run` prints plan only. Needs `boto3` + `huggingface_hub` in the operator Python.
- `scripts/box_bootstrap_v1.sh` (box, root): pins `OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=$(nproc)`, `dnf install python3.12`, venv, `pip install -e ".[<extras>]"` (default `sim,dev`), optional `hf_sync_data.py pull <inputs>`.
- `scripts/box_run_v1.sh` (box, root): runs the request command in the venv, uploads outputs and `request.log` (tail) to HF `mvpeav/nhl-sim-data` under `results/aws/<name>/<repo-relative path>`, uploads `_done.json` last, shuts down.
- AMI: latest Amazon Linux 2023 (kernel 6.1, x86_64) looked up at launch. Root volume 40 GB gp3.

## Instance sizing
`vcpu` rounds up to large/xlarge/2xlarge/4xlarge/8xlarge/12xlarge/16xlarge. `ram_gb <= 2*vcpu` -> c7i then c6i; `<= 4*vcpu` -> m7i/m6i; else r7i/r6i. First type with capacity wins.

## Request file (`docs/ops/box_queue/req_<lane>_<step>_<HHMM>.md`)
One `key: value` per line (a leading `- ` and backticks are tolerated):
```
command: python scripts/foo.py --seeds 200 --out results/foo_run
commit: <git sha, pushed to origin>      (default: origin/main HEAD)
inputs: --dirs raw --only 'nhl_api/pbp/**'   (args for hf_sync_data.py pull; inputs must be on HF or in git)
outputs: results/foo_run                  (files or dirs, repo-relative, space separated)
vcpu: 16
ram_gb: 32
max_minutes: 60
```
Result: `docs/ops/box_queue/done_<lane>_<step>_<HHMM>.md` (and `done_req_<lane>_<step>_<HHMM>.md`, a pointer). Outputs are on HF at `results/aws/<lane>_<step>_<HHMM>/<path>`; fetch with `hf_hub_download` or `hf_sync_data.py pull --dirs results --only 'aws/<name>/**'`.

Caveats: the box sees only committed + pushed code and HF/git inputs; uncommitted local files do not exist there. Rate-limited crawls are not moved to AWS.
