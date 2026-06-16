"""Tests for sakthai.memory.sync — HTTP and Git memory sync.

All tests are hermetic: subprocess.run and urllib.request.urlopen are mocked,
and SAKTHAI_HOME is redirected to a tmp dir via the sakthai_home fixture.
"""

from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from sakthai.memory.store import MemoryStore
from sakthai.memory.sync import sync_memory_to_git, sync_memory_via_http

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _http_response(status: int, body: bytes = b"ok") -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _cp(args: list[str], *, stdout: str = "", returncode: int = 0) -> CompletedProcess[str]:
    return CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr="")


def _git_mock(*, status_output: str = " M facts.jsonl", push_returncode: int = 0):
    """Return a subprocess.run side_effect that fakes all git operations."""
    push_calls: list[int] = []

    def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
        if args == ["git", "status", "--porcelain"]:
            return _cp(args, stdout=status_output)
        if len(args) >= 2 and args[1] == "push":
            push_calls.append(1)
            rc = push_returncode if len(push_calls) <= 1 else 0
            return _cp(args, returncode=rc)
        if len(args) >= 2 and args[1] == "remote":
            return _cp(args, stdout="")
        return _cp(args)

    return _run


# ---------------------------------------------------------------------------
# HTTP sync
# ---------------------------------------------------------------------------


class TestSyncMemoryViaHttp:
    def test_rejects_non_http_url(self, sakthai_home: Path) -> None:
        with pytest.raises(ValueError, match="http"):
            sync_memory_via_http("ftp://example.com/sync")

    def test_successful_200(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(200)):
            result = sync_memory_via_http("http://example.com/sync")
        assert "example.com" in result

    def test_successful_201(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(201)):
            result = sync_memory_via_http("http://example.com/sync")
        assert isinstance(result, str) and result

    def test_successful_204(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(204)):
            result = sync_memory_via_http("http://example.com/sync")
        assert isinstance(result, str) and result

    def test_server_error_raises(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(500, b"error")), pytest.raises(RuntimeError):
            sync_memory_via_http("http://example.com/sync")

    def test_bad_request_raises(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(400, b"bad request")), pytest.raises(RuntimeError):
            sync_memory_via_http("http://example.com/sync")

    def test_sends_bearer_api_key(self, sakthai_home: Path) -> None:
        captured: list[MagicMock] = []

        def _fake_open(req: MagicMock) -> MagicMock:
            captured.append(req)
            return _http_response(200)

        with patch("urllib.request.urlopen", side_effect=_fake_open):
            sync_memory_via_http("http://example.com/sync", api_key="secret-key")

        assert captured[0].get_header("Authorization") == "Bearer secret-key"

    def test_no_api_key_omits_auth_header(self, sakthai_home: Path) -> None:
        captured: list[MagicMock] = []

        def _fake_open(req: MagicMock) -> MagicMock:
            captured.append(req)
            return _http_response(200)

        with patch("urllib.request.urlopen", side_effect=_fake_open):
            sync_memory_via_http("http://example.com/sync")

        assert captured[0].get_header("Authorization") is None

    def test_payload_contains_facts(self, sakthai_home: Path) -> None:
        db_path = sakthai_home / "memory.db"
        with MemoryStore(db_path) as store:
            store.add_fact("test sync fact")

        captured: list[MagicMock] = []

        def _fake_open(req: MagicMock) -> MagicMock:
            captured.append(req)
            return _http_response(200)

        with patch("urllib.request.urlopen", side_effect=_fake_open):
            sync_memory_via_http("http://example.com/sync")

        payload = json.loads(captured[0].data.decode("utf-8"))
        assert "facts" in payload
        assert any("test sync fact" in f.get("value", "") for f in payload["facts"])

    def test_content_type_header_is_json(self, sakthai_home: Path) -> None:
        captured: list[MagicMock] = []

        def _fake_open(req: MagicMock) -> MagicMock:
            captured.append(req)
            return _http_response(200)

        with patch("urllib.request.urlopen", side_effect=_fake_open):
            sync_memory_via_http("http://example.com/sync")

        assert captured[0].get_header("Content-type") == "application/json"

    def test_network_error_raises_runtime_error(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")), pytest.raises(RuntimeError, match="Failed to sync"):
            sync_memory_via_http("http://example.com/sync")

    def test_https_url_accepted(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(200)):
            result = sync_memory_via_http("https://secure.example.com/sync")
        assert "secure.example.com" in result


# ---------------------------------------------------------------------------
# Git sync
# ---------------------------------------------------------------------------


class TestSyncMemoryToGit:
    def test_no_changes_returns_early(self, sakthai_home: Path) -> None:
        with patch("subprocess.run", side_effect=_git_mock(status_output="")):
            result = sync_memory_to_git()
        assert result == "No changes to sync."

    def test_local_sync_returns_success_message(self, sakthai_home: Path) -> None:
        with patch("subprocess.run", side_effect=_git_mock()):
            result = sync_memory_to_git()
        assert "Synced" in result or "locally" in result.lower()

    def test_remote_sync_includes_url_in_result(self, sakthai_home: Path) -> None:
        remote = "https://github.com/user/memory.git"
        with patch("subprocess.run", side_effect=_git_mock()):
            result = sync_memory_to_git(remote=remote)
        assert remote in result

    def test_writes_facts_jsonl(self, sakthai_home: Path) -> None:
        db_path = sakthai_home / "memory.db"
        with MemoryStore(db_path) as store:
            store.add_fact("hello world git sync")

        with patch("subprocess.run", side_effect=_git_mock()):
            sync_memory_to_git()

        facts_path = sakthai_home / "facts.jsonl"
        assert facts_path.exists()
        lines = [ln for ln in facts_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert any("hello world git sync" in ln for ln in lines)

    def test_writes_observations_jsonl(self, sakthai_home: Path) -> None:
        with patch("subprocess.run", side_effect=_git_mock()):
            sync_memory_to_git()

        obs_path = sakthai_home / "observations.jsonl"
        assert obs_path.exists()

    def test_removes_legacy_snapshot_json(self, sakthai_home: Path) -> None:
        legacy = sakthai_home / "snapshot.json"
        legacy.write_text("{}", encoding="utf-8")

        with patch("subprocess.run", side_effect=_git_mock()):
            sync_memory_to_git()

        assert not legacy.exists()

    def test_push_failure_triggers_conflict_resolution(self, sakthai_home: Path) -> None:
        with patch("subprocess.run", side_effect=_git_mock(push_returncode=1)):
            result = sync_memory_to_git(remote="https://github.com/user/repo.git")
        assert isinstance(result, str) and result

    def test_empty_store_writes_empty_jsonl(self, sakthai_home: Path) -> None:
        with patch("subprocess.run", side_effect=_git_mock(status_output="")):
            sync_memory_to_git()

        facts_path = sakthai_home / "facts.jsonl"
        assert facts_path.exists()
        assert facts_path.read_text(encoding="utf-8").strip() == ""

    def test_facts_jsonl_is_valid_json_per_line(self, sakthai_home: Path) -> None:
        db_path = sakthai_home / "memory.db"
        with MemoryStore(db_path) as store:
            store.add_fact("line one")
            store.add_fact("line two")

        with patch("subprocess.run", side_effect=_git_mock()):
            sync_memory_to_git()

        facts_path = sakthai_home / "facts.jsonl"
        lines = [ln for ln in facts_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2
        for ln in lines:
            parsed = json.loads(ln)
            assert "value" in parsed
