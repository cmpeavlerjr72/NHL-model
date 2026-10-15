"""Lane O operator: run one box request on a spot instance (us-east-1) and write done_<name>.md.

Usage:
  python scripts/run_box_request.py docs/ops/box_queue/req_<lane>_<step>_<HHMM>.md
  python scripts/run_box_request.py --smoke            # pytest at HEAD + tiny HF output
Request file: lines of `key: value` (optionally `- key: value`, backticks ignored):
  command (required), commit (default origin/main HEAD), inputs (args for hf_sync_data.py pull, e.g. --dirs raw --only 'x/**'),
  outputs (space/comma separated repo-relative files or dirs), vcpu (default 2), ram_gb (default 2*vcpu), max_minutes (default 60),
  extras (pip extras, default sim,dev).
Flow: launch spot (terminate-on-shutdown, tagged project=nhl-model lane=O) -> user-data bootstraps, runs, pushes to HF
results/aws/<name>/ -> poll for _done.json -> verify outputs on HF -> terminate + verify -> write done md + spend ledger.
Secrets: HF_TOKEN from env/.env goes only into user-data; never printed.
"""
import argparse, base64, datetime as dt, json, os, re, subprocess, sys, time
from pathlib import Path
import boto3
from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
REGION = "us-east-1"
REPO_URL = "https://github.com/cmpeavlerjr72/NHL-model.git"
HF_REPO = "mvpeav/nhl-sim-data"
QUEUE = ROOT / "docs" / "ops" / "box_queue"
LEDGER = ROOT / "logs" / "aws_spend_O.jsonl"
SIZES = {2: "large", 4: "xlarge", 8: "2xlarge", 16: "4xlarge", 32: "8xlarge", 48: "12xlarge", 64: "16xlarge"}
KEYS = {"command", "commit", "inputs", "outputs", "vcpu", "ram_gb", "max_minutes", "extras"}


def token():
    t = os.environ.get("HF_TOKEN")
    if not t:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith("HF_TOKEN="):
                t = line.split("=", 1)[1].strip().strip("\"'")
    if not t:
        sys.exit("no HF_TOKEN")
    return t


def scrub(s, tok):
    return s.replace(tok, "***") if tok else s


def parse_request(path):
    d = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(?:[-*]\s*)?\**([a-z_]+)\**\s*:\s*(.+?)\s*$", line)
        if m and m.group(1) in KEYS:
            d[m.group(1)] = m.group(2).strip().strip("`")
    if "command" not in d:
        sys.exit("request has no `command:` line")
    return d


def pick_types(vcpu, ram_gb):
    vcpu = min((k for k in SIZES if k >= vcpu), default=64)
    fam = ["c7i", "c6i"] if ram_gb <= 2 * vcpu else (["m7i", "m6i"] if ram_gb <= 4 * vcpu else ["r7i", "r6i"])
    return [f"{f}.{SIZES[vcpu]}" for f in fam]


def user_data(tok, name, cmd, commit, inputs, outputs, extras, max_min, t_launch):
    b64 = base64.b64encode(cmd.encode()).decode()
    return f"""#!/bin/bash
exec > /var/log/nhl_box.log 2>&1
shutdown -h +{max_min + 8}
export HF_TOKEN='{tok}' REQ_NAME='{name}' REQ_COMMAND_B64='{b64}' REQ_OUTPUTS='{outputs}' REQ_INPUTS='{inputs}' REQ_EXTRAS='{extras}' T_LAUNCH='{t_launch}'
dnf install -y git >/dev/null 2>&1
cd /root && git clone {REPO_URL} nhl && cd nhl && git checkout -q {commit} || shutdown -h now
bash scripts/box_bootstrap_v1.sh || {{ echo bootstrap failed; shutdown -h now; }}
bash scripts/box_run_v1.sh
shutdown -h now
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("request", nargs="?")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tok = token()
    ec2 = boto3.client("ec2", region_name=REGION)
    head = subprocess.run(["git", "ls-remote", REPO_URL, "HEAD"], capture_output=True, text=True).stdout.split()[0]
    if a.smoke:
        name = "smoke_O"
        req = {"command": "mkdir -p results/_smoke; python -m pytest -q > /tmp/pt.log 2>&1; RC=$?; tail -5 /tmp/pt.log; (date -u +%FT%TZ; tail -3 /tmp/pt.log) > results/_smoke/smoke_out.txt; exit $RC",
               "outputs": "results/_smoke/smoke_out.txt", "vcpu": "2", "max_minutes": "20", "inputs": "", "extras": "sim,dev"}
    else:
        req = parse_request(a.request)
        name = re.sub(r"^req_", "", Path(a.request).stem)
    commit = req.get("commit", head)
    vcpu = int(req.get("vcpu", 2)); ram = int(req.get("ram_gb", 2 * vcpu)); max_min = int(req.get("max_minutes", 60))
    outputs = req.get("outputs", "").replace(",", " ")
    types = pick_types(vcpu, ram)
    t_launch = int(time.time())
    ud = user_data(tok, name, req["command"], commit, req.get("inputs", ""), outputs, req.get("extras", "sim,dev"), max_min, t_launch)
    imgs = ec2.describe_images(Owners=["amazon"], Filters=[{"Name": "name", "Values": ["al2023-ami-2023*-kernel-6.1-x86_64"]},
                                                           {"Name": "state", "Values": ["available"]}])["Images"]
    ami = sorted(imgs, key=lambda i: i["CreationDate"])[-1]["ImageId"]
    print(f"[{dt.datetime.now():%H:%M:%S}] request={name} commit={commit[:10]} types={types} ami={ami}")
    if a.dry_run:
        print("dry run; user-data bytes:", len(ud)); return
    try:  # clear a stale marker from an earlier run of the same name
        HfApi(token=tok).delete_file(f"results/aws/{name}/_done.json", repo_id=HF_REPO, repo_type="dataset")
    except Exception:
        pass
    iid = itype = None
    for t in types:
        try:
            r = ec2.run_instances(
                ImageId=ami, InstanceType=t, MinCount=1, MaxCount=1, UserData=ud,
                InstanceMarketOptions={"MarketType": "spot", "SpotOptions": {"SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}},
                InstanceInitiatedShutdownBehavior="terminate",
                BlockDeviceMappings=[{"DeviceName": "/dev/xvda", "Ebs": {"VolumeSize": 40, "VolumeType": "gp3", "DeleteOnTermination": True}}],
                MetadataOptions={"HttpTokens": "required"},
                TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "project", "Value": "nhl-model"}, {"Key": "lane", "Value": "O"},
                                                                           {"Key": "request", "Value": name}]}])
            iid = r["Instances"][0]["InstanceId"]; itype = t; break
        except Exception as e:
            print("launch failed", t, scrub(str(e), tok)[:200])
    if not iid:
        sys.exit("no capacity / launch failed on all types")
    t_start = time.time()
    print(f"[{dt.datetime.now():%H:%M:%S}] launched {iid} {itype}")
    api = HfApi(token=tok)
    done = None; status_note = ""
    deadline = t_start + (max_min + 15) * 60
    local = ROOT / "logs" / "_box_done"
    st = None
    try:
        while time.time() < deadline:
            time.sleep(15)
            try:
                p = api.hf_hub_download(HF_REPO, f"results/aws/{name}/_done.json", repo_type="dataset", local_dir=str(local), force_download=True)
                done = json.loads(Path(p).read_text())
                break
            except Exception:
                pass
            state = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]["State"]["Name"]
            if state in ("shutting-down", "terminated", "stopped"):
                status_note = f"instance went {state} without _done.json (spot interruption, bootstrap failure or max-lifetime)"
                break
        else:
            status_note = "timeout waiting for _done.json"
    finally:
        t_end = time.time()
        ec2.terminate_instances(InstanceIds=[iid])
        for _ in range(40):
            time.sleep(10)
            st = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]
            if st["State"]["Name"] == "terminated":
                break
    final_state = st["State"]["Name"]; az = st["Placement"]["AvailabilityZone"]
    ph = ec2.describe_spot_price_history(InstanceTypes=[itype], ProductDescriptions=["Linux/UNIX"], AvailabilityZone=az, MaxResults=1)["SpotPriceHistory"]
    price = float(ph[0]["SpotPrice"]) if ph else 0.0
    hours = (t_end - t_start) / 3600
    cost = price * hours + 40 * 0.08 / 730 * hours
    verified = []
    if done:
        listing = {f for f in api.list_repo_files(HF_REPO, repo_type="dataset") if f.startswith(f"results/aws/{name}/")}
        verified = [f for f in done["pushed"] if f"results/aws/{name}/{f}" in listing]
    ok = bool(done) and done["rc"] == 0 and not done["missing"] and len(verified) == len(done["pushed"])
    rec = {"name": name, "instance": iid, "type": itype, "az": az, "price_hr": price, "wall_s": round(t_end - t_start), "cost_usd": round(cost, 4), "ok": ok}
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    total = sum(json.loads(l)["cost_usd"] for l in LEDGER.read_text().splitlines() if l.strip())
    cold = (done["t_cmd_start"] - done["t_launch"]) if done else "n/a"
    lines = [f"# done {name}", "", f"- result: {'OK' if ok else 'FAILED'} {status_note}",
             f"- instance: {iid} {itype} spot {az}, commit {commit}", f"- final state: {final_state} (verified via describe-instances)",
             f"- launch to result seen: {round(t_end - t_start)} s; command secs: {done['cmd_secs'] if done else 'n/a'}; cold start (launch to command start): {cold} s",
             f"- command rc: {done['rc'] if done else 'n/a'}",
             f"- outputs on HF `{HF_REPO}` under `results/aws/{name}/`: {', '.join(verified) or 'none'}; missing: {done['missing'] if done else 'n/a'}",
             f"- log tail on HF: results/aws/{name}/request.log",
             f"- spot ${price:.4f}/h x {hours:.3f} h + EBS = ${cost:.3f}; session total so far ${total:.2f} (cap $60, stop launching at $50)"]
    text = "\n".join(lines) + "\n"
    if a.smoke:
        (ROOT / "logs").mkdir(exist_ok=True)
        (ROOT / "logs" / "smoke_done.md").write_text(text, encoding="utf-8")
    else:
        QUEUE.mkdir(parents=True, exist_ok=True)
        (QUEUE / f"done_{name}.md").write_text(text, encoding="utf-8")
        (QUEUE / f"done_req_{name}.md").write_text(f"See done_{name}.md\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
