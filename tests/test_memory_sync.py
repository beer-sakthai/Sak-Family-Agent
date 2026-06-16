"""Tests for ``sakthai.memory.sync`` — HTTP and Git memory synchronisation.

These exercise the previously-untested sync surface reachable via
``sakthai memory sync``. The HTTP path is driven with a stubbed ``urlopen``;
the Git paths run against real local repositories (a bare repo stands in for
the remote), including the rejected-push auto-merge recovery.
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from sakthai.memory import sync
from sakthai.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def _isolate_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Detach git from host system/global config (e.g. mandatory commit signing)
    so the Git sync tests run hermetically and deterministically."""
    cfg = tmp_path / "gitconfig"
    # `init.defaultBranch=main` so bare remotes created here track `main`
    # (the branch `sync` pushes), matching modern git setups.
    cfg.write_text("[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
class _FakeResponse:
    """Minimal stand-in for the object returned by ``urlopen``."""

    def __init__(self, status: int, body: bytes = b"ok") -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _seed_fact(home: Path, value: str) -> None:
    """Insert one fact into the store that ``sync`` will read (home/memory.db)."""
    with MemoryStore(home / "memory.db") as store:
        store.add_fact(value)


def _facts_jsonl_for(value: str, tmp_path: Path) -> str:
    """Build a valid ``facts.jsonl`` body containing a single fact `value`."""
    db = tmp_path / "throwaway.db"
    with MemoryStore(db) as store:
        store.add_fact(value)
        snapshot = store.export_to_dict()
    return "\n".join(json.dumps(f, ensure_ascii=False) for f in snapshot["facts"]) + "\n"


# --------------------------------------------------------------------------- #
# sync_memory_via_http
# --------------------------------------------------------------------------- #
def test_sync_http_rejects_non_http_url(sakthai_home: Path) -> None:
    with pytest.raises(ValueError, match="must start with http"):
        sync.sync_memory_via_http("ftp://example.com/ingest")


def test_sync_http_success_posts_snapshot(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_fact(sakthai_home, "remember the milk")
    captured: dict[str, object] = {}

    def fake_urlopen(req: urllib.request.Request) -> _FakeResponse:
        captured["req"] = req
        return _FakeResponse(200)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = sync.sync_memory_via_http("https://example.com/ingest", api_key="s3cret")

    assert "Synced to HTTP endpoint" in result
    req = captured["req"]
    assert isinstance(req, urllib.request.Request)
    assert req.get_method() == "POST"
    assert req.has_header("Authorization")  # api_key → Bearer header
    payload = json.loads(req.data)  # type: ignore[arg-type]
    assert any(f["value"] == "remember the milk" for f in payload["facts"])


def test_sync_http_no_api_key_omits_auth_header(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_fact(sakthai_home, "anon")
    captured: dict[str, object] = {}

    def fake_urlopen(req: urllib.request.Request) -> _FakeResponse:
        captured["req"] = req
        return _FakeResponse(204)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = sync.sync_memory_via_http("https://example.com/ingest")
    assert "Synced to HTTP endpoint" in result
    assert not captured["req"].has_header("Authorization")  # type: ignore[union-attr]


def test_sync_http_non_2xx_wrapped_as_runtime_error(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_fact(sakthai_home, "x")
    monkeypatch.setattr("urllib.request.urlopen", lambda req: _FakeResponse(500, b"boom"))
    with pytest.raises(RuntimeError, match="Failed to sync"):
        sync.sync_memory_via_http("https://example.com/ingest")


def test_sync_http_network_error_wrapped(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_fact(sakthai_home, "x")

    def boom(req: urllib.request.Request) -> _FakeResponse:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(RuntimeError, match="Failed to sync"):
        sync.sync_memory_via_http("https://example.com/ingest")


# --------------------------------------------------------------------------- #
# sync_memory_to_git — local
# --------------------------------------------------------------------------- #
def test_sync_git_local_only(sakthai_home: Path) -> None:
    _seed_fact(sakthai_home, "local fact")
    result = sync.sync_memory_to_git()

    assert result == "Synced locally to Git repository."
    assert (sakthai_home / ".git").is_dir()
    facts = (sakthai_home / "facts.jsonl").read_text(encoding="utf-8")
    assert "local fact" in facts
    assert (sakthai_home / "observations.jsonl").exists()
    # The committed tree carries the exported jsonl.
    tracked = _git(sakthai_home, "ls-files")
    assert "facts.jsonl" in tracked
    assert "observations.jsonl" in tracked


def test_sync_git_removes_legacy_snapshot(sakthai_home: Path) -> None:
    _seed_fact(sakthai_home, "fact")
    (sakthai_home / "snapshot.json").write_text("{}", encoding="utf-8")
    sync.sync_memory_to_git()
    assert not (sakthai_home / "snapshot.json").exists()


def test_sync_git_no_changes_on_second_run(sakthai_home: Path) -> None:
    _seed_fact(sakthai_home, "fact")
    sync.sync_memory_to_git()
    assert sync.sync_memory_to_git() == "No changes to sync."


# --------------------------------------------------------------------------- #
# sync_memory_to_git — remote
# --------------------------------------------------------------------------- #
def test_sync_git_pushes_to_remote(sakthai_home: Path, tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(remote))

    _seed_fact(sakthai_home, "pushed fact")
    result = sync.sync_memory_to_git(str(remote))

    assert result == f"Synced to remote: {remote}"
    # Clone the remote back out and confirm the fact landed.
    clone = tmp_path / "verify"
    _git(tmp_path, "clone", str(remote), str(clone))
    assert "pushed fact" in (clone / "facts.jsonl").read_text(encoding="utf-8")


def test_sync_git_auto_merges_on_rejected_push(sakthai_home: Path, tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(remote))

    # 1. First sync establishes origin/main with fact A.
    _seed_fact(sakthai_home, "fact-A")
    sync.sync_memory_to_git(str(remote))

    # 2. A second clone advances the remote with a divergent fact B, so the
    #    next push from `home` will be rejected as non-fast-forward.
    other = tmp_path / "other"
    _git(tmp_path, "clone", str(remote), str(other))
    (other / "facts.jsonl").write_text(_facts_jsonl_for("fact-B", tmp_path), encoding="utf-8")
    _git(other, "add", "facts.jsonl")
    _git(other, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "remote change")
    _git(other, "push", "origin", "main")

    # 3. home adds fact C and syncs: push is rejected, auto-merge recovers.
    _seed_fact(sakthai_home, "fact-C")
    result = sync.sync_memory_to_git(str(remote))

    assert result == f"Auto-merged remote changes and synced to remote: {remote}"

    # The local store now holds all three facts (A, C kept; B merged in).
    with MemoryStore(sakthai_home / "memory.db") as store:
        values = {f.value for f in store.list_facts(limit=100)}
    assert {"fact-A", "fact-B", "fact-C"} <= values

    # And the merged result was pushed to the remote.
    final = tmp_path / "final"
    _git(tmp_path, "clone", str(remote), str(final))
    pushed = (final / "facts.jsonl").read_text(encoding="utf-8")
    assert "fact-A" in pushed and "fact-B" in pushed and "fact-C" in pushed
