"""Offline tests for scripts/hf_sync_data.py (HfApi mocked, no network)."""
import importlib.util
from pathlib import Path
from unittest import mock

import pytest

SPEC = importlib.util.spec_from_file_location(
    "hf_sync_data", Path(__file__).resolve().parent.parent / "scripts" / "hf_sync_data.py")
hf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hf)

TOKEN = "hf_SECRETSECRETSECRET1234567890"


def test_repo_and_keys():
    assert hf.REPO_ID == "mvpeav/nhl-sim-data"
    assert hf.BULK_DIRS == ["raw", "results", "engine_inputs"]


def test_key_to_path_mapping(tmp_path):
    assert hf._root_for("raw", tmp_path) == tmp_path / "data" / "raw"
    assert hf._root_for("results", tmp_path) == tmp_path / "results"
    assert hf._root_for("engine_inputs", tmp_path) == tmp_path / "data/processed/models/engine_inputs"


def test_local_remote_roundtrip():
    r = hf._local_to_remote("raw", "pbp/2024/x.json")
    assert r == "raw/pbp/2024/x.json"
    assert hf._remote_to_local_rel("raw", r) == "pbp/2024/x.json"
    with pytest.raises(ValueError):
        hf._remote_to_local_rel("raw", "results/x")


def test_local_files_and_missing(tmp_path):
    (tmp_path / "data/raw/a").mkdir(parents=True)
    (tmp_path / "data/raw/a/f.json").write_text("1")
    (tmp_path / "results").mkdir()
    (tmp_path / "results/r.txt").write_text("2")
    assert hf.local_files(hf.BULK_DIRS, tmp_path) == {"raw/a/f.json", "results/r.txt"}
    with mock.patch.object(hf, "remote_files", return_value={"raw/a/f.json"}):
        assert hf.missing_set(TOKEN, hf.BULK_DIRS, tmp_path) == {"results/r.txt"}


def test_token_from_env_and_dotenv_never_printed(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HF_TOKEN", TOKEN)
    assert hf.resolve_token() == TOKEN
    monkeypatch.delenv("HF_TOKEN")
    (tmp_path / ".env").write_text(f"HF_TOKEN={TOKEN}\n")
    monkeypatch.setattr(hf, "ROOT", tmp_path)
    assert hf.resolve_token() == TOKEN
    assert TOKEN not in capsys.readouterr().out


def test_missing_token_exits_without_leak(monkeypatch, tmp_path):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setattr(hf, "ROOT", tmp_path)
    with pytest.raises(SystemExit) as e:
        hf.resolve_token()
    assert "HF_TOKEN" in str(e.value)


def test_exception_text_scrubbed_in_logs(capsys, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", TOKEN)
    hf.resolve_token()

    def boom():
        raise RuntimeError(f"401 for Bearer {TOKEN}")

    assert hf.with_retry("t", boom, max_attempts=1) is False
    out = capsys.readouterr().out
    assert TOKEN not in out and "GAVE UP" in out


def test_retry_succeeds_after_failures(monkeypatch):
    monkeypatch.setattr(hf.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise OSError("dns")

    assert hf.with_retry("t", flaky, max_attempts=5) is True
    assert calls["n"] == 3


def test_push_uses_prefix_and_skips_empty(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results/r.txt").write_text("2")
    api = mock.MagicMock()
    api.list_repo_files.return_value = []
    with mock.patch.object(hf, "_api", return_value=api):
        hf.push(["results", "engine_inputs"], TOKEN, 1, dest_root=tmp_path)
    api.upload_folder.assert_called_once()
    kw = api.upload_folder.call_args.kwargs
    assert kw["path_in_repo"] == "results" and kw["repo_id"] == hf.REPO_ID
    assert kw["repo_type"] == "dataset"


def test_push_noop_when_mirrored(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results/r.txt").write_text("2")
    api = mock.MagicMock()
    api.list_repo_files.return_value = ["results/r.txt"]
    with mock.patch.object(hf, "_api", return_value=api):
        hf.push(["results"], TOKEN, 1, dest_root=tmp_path)
    api.upload_folder.assert_not_called()


def test_pull_stages_strips_prefix_and_overwrites(tmp_path):
    """CBB guarantee: files land at root/<rel> (not root/<d>/<rel>), same-named
    local files are overwritten, local-only files are kept, staging is removed."""
    root = tmp_path / "results"
    root.mkdir()
    (root / "keep.txt").write_text("local-only")
    (root / "a.txt").write_text("old")

    def fake_snapshot(repo_id, repo_type, local_dir, allow_patterns, token, max_workers):
        assert allow_patterns == ["results/**"] and repo_id == hf.REPO_ID
        p = Path(local_dir) / "results" / "sub"
        p.mkdir(parents=True)
        (p / "b.txt").write_text("new-b")
        (Path(local_dir) / "results" / "a.txt").write_text("new-a")

    with mock.patch("huggingface_hub.snapshot_download", side_effect=fake_snapshot):
        hf.pull(["results"], TOKEN, 1, dest_root=tmp_path)
    assert (root / "sub/b.txt").read_text() == "new-b"
    assert (root / "a.txt").read_text() == "new-a"
    assert (root / "keep.txt").read_text() == "local-only"
    assert not (root / "results").exists()
    assert not [p for p in root.iterdir() if p.name.startswith(".hf_pull_staging")]


def test_pull_only_patterns(tmp_path):
    seen = {}

    def fake_snapshot(**kw):
        seen.update(kw)

    with mock.patch("huggingface_hub.snapshot_download", side_effect=fake_snapshot):
        hf.pull(["raw"], TOKEN, 1, dest_root=tmp_path, only=["pbp/**"])
    assert seen["allow_patterns"] == ["raw/pbp/**"]
