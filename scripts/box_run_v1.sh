#!/usr/bin/env bash
# Box runner (Lane O). Runs ON the box as root after box_bootstrap_v1.sh.
# Env in: HF_TOKEN, REQ_NAME, REQ_COMMAND_B64 (base64 shell command), REQ_OUTPUTS (space-separated paths relative to repo),
#         T_LAUNCH (epoch of instance start, optional)
# Runs the command, pushes outputs + log to HF dataset mvpeav/nhl-sim-data under results/aws/<REQ_NAME>/, writes _done.json last.
set -uo pipefail
cd "$(dirname "$0")/.."
. /etc/profile.d/nhl_threads.sh
. .venv/bin/activate
CMD=$(echo "$REQ_COMMAND_B64" | base64 -d)
T0=$(date +%s)
echo "[box_run] start $(date -u +%FT%TZ) cmd: $CMD"
bash -c "$CMD" > /tmp/request.log 2>&1
RC=$?
T1=$(date +%s)
echo "[box_run] cmd rc=$RC secs=$((T1-T0))"
tail -c 200000 /tmp/request.log > /tmp/request_tail.log
python - <<PYEOF
import json, os, glob, time, sys
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HF_TOKEN"])
repo = "mvpeav/nhl-sim-data"
name = os.environ["REQ_NAME"]
base = f"results/aws/{name}"
pushed, missing = [], []
for p in os.environ.get("REQ_OUTPUTS", "").split():
    files = [p] if os.path.isfile(p) else [f for f in glob.glob(p.rstrip("/") + "/**", recursive=True) if os.path.isfile(f)]
    if not files:
        missing.append(p); continue
    for f in files:
        for attempt in range(5):
            try:
                api.upload_file(path_or_fileobj=f, path_in_repo=f"{base}/{f}", repo_id=repo, repo_type="dataset")
                pushed.append(f); break
            except Exception as e:
                time.sleep(2 ** attempt)
        else:
            missing.append(f)
api.upload_file(path_or_fileobj="/tmp/request_tail.log", path_in_repo=f"{base}/request.log", repo_id=repo, repo_type="dataset")
done = {"name": name, "rc": $RC, "cmd_secs": $T1 - $T0, "t_launch": int(os.environ.get("T_LAUNCH") or 0),
        "t_cmd_start": $T0, "t_done": int(time.time()), "pushed": pushed, "missing": missing}
open("/tmp/_done.json", "w").write(json.dumps(done))
api.upload_file(path_or_fileobj="/tmp/_done.json", path_in_repo=f"{base}/_done.json", repo_id=repo, repo_type="dataset")
print("pushed", len(pushed), "missing", missing)
PYEOF
echo "[box_run] finished; shutting down"
shutdown -h now
