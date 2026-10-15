"""Sync the gitignored bulk data dirs to/from the private HuggingFace dataset.

Source/target: https://huggingface.co/datasets/mvpeav/nhl-sim-data (PRIVATE)
Ported from CBB-clean-sheet/scripts/hf_sync_data.py (simplified: no
git-ignore-driven keys).

Keys (CLI `--dirs`) and the local directory each maps to (also the HF repo
prefix each is pushed under):
  raw           data/raw/              raw NHL API JSON (gitignored)
  results       results/               run outputs (gitignored)
  engine_inputs data/processed/models/engine_inputs/
                PLACEHOLDER for future model-artifact dirs over 20 MB (the
                CLAUDE.md rule: such dirs sync to HF instead of git). Empty
                / missing locally is fine; push skips it.

Token: HF_TOKEN from the environment, else from .env. Never printed; any
exception text is scrubbed of the token before logging.

Pull downloads into a staging dir, then moves files to their final place
(snapshot_download would otherwise nest them one directory too deep). Like
the CBB original, pull OVERWRITES same-named local files; it never deletes
local-only files.

Run: .venv/Scripts/python.exe scripts/hf_sync_data.py status
     .venv/Scripts/python.exe scripts/hf_sync_data.py push --dirs raw
     .venv/Scripts/python.exe scripts/hf_sync_data.py pull --dirs raw
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ID = "mvpeav/nhl-sim-data"
BULK_DIRS = ["raw", "results", "engine_inputs"]

# Local path of each key relative to the root it is rooted at.
_REL_ROOT = {
    "raw": Path("data") / "raw",
    "results": Path("results"),
    "engine_inputs": Path("data") / "processed" / "models" / "engine_inputs",
}

_SECRETS: set = set()


def _scrub(text: str) -> str:
    for s in _SECRETS:
        if s:
            text = text.replace(s, "***")
    return re.sub(r"hf_[A-Za-z0-9]{10,}", "hf_***", text)


def log(msg: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {_scrub(str(msg))}", flush=True)


def resolve_token() -> str:
    """HF_TOKEN from the environment, else from .env. Never printed."""
    tok = os.environ.get("HF_TOKEN", "").strip()
    if not tok:
        env_file = ROOT / ".env"
        if env_file.exists():
            env = dict(re.findall(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", env_file.read_text(), re.M))
            tok = env.get("HF_TOKEN", "").strip().strip("'\"")
    if not tok:
        sys.exit(
            "No HF_TOKEN. Set it in the environment or in .env (see .env.example).\n"
            "The token is a secret -- never committed, never uploaded."
        )
    _SECRETS.add(tok)
    return tok


def with_retry(label: str, fn, max_attempts: int = 0, base_sleep: int = 30) -> bool:
    """Run fn(), retrying on any exception. max_attempts=0 means forever.
    Backoff doubles up to a 10 min cap."""
    attempt = 0
    while True:
        attempt += 1
        try:
            fn()
            log(f"{label}: OK (attempt {attempt})")
            return True
        except KeyboardInterrupt:
            raise
        except Exception as e:
            if max_attempts and attempt >= max_attempts:
                log(f"{label}: GAVE UP after {attempt} attempts -- {type(e).__name__}: {str(e)[:200]}")
                return False
            sleep = min(base_sleep * (2 ** min(attempt - 1, 5)), 600)
            log(f"{label}: attempt {attempt} failed ({type(e).__name__}: {str(e)[:200]}) "
                f"-- retrying in {sleep}s")
            time.sleep(sleep)


def _root_for(d: str, dest_root: Path = ROOT) -> Path:
    """Local directory a bulk key resolves to, rooted at `dest_root`."""
    return dest_root / _REL_ROOT[d]


def _local_to_remote(d: str, rel_path: str) -> str:
    rel_path = rel_path.strip("/")
    return f"{d}/{rel_path}" if rel_path else d


def _remote_to_local_rel(d: str, remote_path: str) -> str:
    prefix = f"{d}/"
    if not remote_path.startswith(prefix):
        raise ValueError(f"{remote_path!r} does not start with expected prefix {prefix!r}")
    return remote_path[len(prefix):]


def _api(token: str):
    from huggingface_hub import HfApi
    return HfApi(token=token)


def remote_files(token: str) -> set:
    files = _api(token).list_repo_files(repo_id=REPO_ID, repo_type="dataset")
    return {f for f in files if not f.startswith(".")}


def local_files(dirs: list, dest_root: Path = ROOT) -> set:
    out = set()
    for d in dirs:
        root = _root_for(d, dest_root)
        if not root.is_dir():
            continue
        out |= {_local_to_remote(d, p.relative_to(root).as_posix())
                for p in root.rglob("*") if p.is_file()}
    return out


def missing_set(token: str, dirs: list, dest_root: Path = ROOT) -> set:
    """Local files not present on the remote (set difference, not a count)."""
    return local_files(dirs, dest_root) - remote_files(token)


def push(dirs: list, token: str, max_attempts: int, dest_root: Path = ROOT) -> None:
    log(f"push -> {REPO_ID} (private); dirs={dirs}")
    try:
        outstanding = missing_set(token, dirs, dest_root)
        log(f"outstanding before push: {len(outstanding)} files")
    except Exception as e:
        outstanding = None
        log(f"could not compute outstanding ({type(e).__name__}) -- uploading all")
    if outstanding is not None and not outstanding:
        log("already fully mirrored; nothing to do")
        status(token, dest_root=dest_root)
        return
    failed = []
    for d in dirs:
        root = _root_for(d, dest_root)
        if not root.is_dir() or not any(p.is_file() for p in root.rglob("*")):
            log(f"--- {d}: no local files under {root}, skipping")
            continue
        kwargs = dict(repo_id=REPO_ID, folder_path=str(root), repo_type="dataset",
                      path_in_repo=d, commit_message=f"sync {d}")
        log(f"--- {d}: uploading from {root}")
        ok = with_retry(f"push-{d}", lambda k=kwargs: _api(token).upload_folder(**k),
                        max_attempts=max_attempts)
        if not ok:
            failed.append(d)
    log(f"push finished; failed dirs: {failed or 'none'}")
    status(token, dest_root=dest_root)


def pull(dirs: list, token: str, max_attempts: int, dest_root: Path = ROOT,
         only: list = None) -> None:
    """Download each bulk dir into `_root_for(d, dest_root)` via a staging dir."""
    from huggingface_hub import snapshot_download

    log(f"pull <- {REPO_ID}; dirs={dirs}; dest_root={dest_root}"
        + (f"; only={only}" if only else ""))
    for d in dirs:
        patterns = [f"{d}/{p.lstrip('/')}" for p in only] if only else [f"{d}/**"]
        root = _root_for(d, dest_root)
        root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".hf_pull_staging_{d}_", dir=str(root)))
        moved = 0
        try:
            ok = with_retry(
                f"pull-{d}",
                lambda staging=staging, patterns=patterns: snapshot_download(
                    repo_id=REPO_ID, repo_type="dataset", local_dir=str(staging),
                    allow_patterns=patterns, token=token, max_workers=8),
                max_attempts=max_attempts)
            if not ok:
                log(f"pull-{d}: download did not complete; moving whatever was staged")
            staged_root = staging / d
            if staged_root.is_dir():
                for f in staged_root.rglob("*"):
                    if not f.is_file():
                        continue
                    rel = _remote_to_local_rel(d, f.relative_to(staging).as_posix())
                    dest = root / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(dest))
                    moved += 1
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        n = sum(1 for f in root.rglob("*") if f.is_file())
        log(f"  {d}: {n} files ({moved} moved this run)")


def status(token: str, show: int = 15, dest_root: Path = ROOT) -> None:
    remote = remote_files(token)
    missing = local_files(BULK_DIRS, dest_root) - remote
    log(f"remote {REPO_ID}: {len(remote)} files")
    for d in BULK_DIRS:
        loc = len(local_files([d], dest_root))
        miss = len([m for m in missing if m.startswith(d + "/")])
        rem = len([r for r in remote if r.startswith(d + "/")])
        flag = "  <-- INCOMPLETE" if miss else ""
        log(f"  {d:13s} local={loc:6d} remote={rem:6d} missing_on_remote={miss:6d}{flag}")
    for m in sorted(missing)[:show]:
        log(f"      missing: {m}")
    if len(missing) > show:
        log(f"      ... and {len(missing) - show} more")
    log(f"  TOTAL still to upload: {len(missing)} files")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("action", choices=["push", "pull", "status"])
    ap.add_argument("--dirs", nargs="+", default=BULK_DIRS, choices=BULK_DIRS,
                    help="subset of the bulk keys (default: all)")
    ap.add_argument("--max-attempts", type=int, default=0,
                    help="retries per dir; 0 = forever (default, for overnight runs)")
    ap.add_argument("--only", nargs="+", default=None,
                    help="pull only: glob patterns relative to each --dirs key")
    ap.add_argument("--dest-root", type=Path, default=None,
                    help="root the bulk dirs resolve under (default: the repo); "
                         "lets a verification run use a scratch directory")
    args = ap.parse_args(argv)
    token = resolve_token()
    dest_root = args.dest_root.resolve() if args.dest_root else ROOT
    if args.action == "status":
        status(token, dest_root=dest_root)
    elif args.action == "push":
        push(args.dirs, token, args.max_attempts, dest_root=dest_root)
    else:
        pull(args.dirs, token, args.max_attempts, dest_root=dest_root, only=args.only)


if __name__ == "__main__":
    main()
