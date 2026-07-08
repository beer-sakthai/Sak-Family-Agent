"""Tests for sakthai.memory.sync — HTTP and Git memory sync.

All tests are hermetic: subprocess.run and urllib.request.urlopen are mocked,
and SAKTHAI_HOME is redirected to a tmp dir via the sakthai_home fixture.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sakthai.memory.store import MemoryStore
from sakthai.memory.sync import (
    _handle_git_conflict_and_push,
    pull_memory_from_git,
    sync_memory_to_git,
    sync_memory_via_http,
)

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


def _git_mock(*, status_output: str = " M facts.jsonl", push_returncode: int = 0) -> Any:
    """Return a subprocess.run side_effect that fakes all git operations."""
    push_calls: list[int] = []

    def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
        if len(args) >= 3 and args[:3] == ["git", "status", "--porcelain"]:
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
        assert isinstance(result, str) and result

    def test_successful_201(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(201)):
            result = sync_memory_via_http("http://example.com/sync")
        assert isinstance(result, str) and result

    def test_successful_204(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(204)):
            result = sync_memory_via_http("http://example.com/sync")
        assert isinstance(result, str) and result

    def test_server_error_raises(self, sakthai_home: Path) -> None:
        with (
            patch("urllib.request.urlopen", return_value=_http_response(500, b"error")),
            pytest.raises(RuntimeError),
        ):
            sync_memory_via_http("http://example.com/sync")

    def test_bad_request_raises(self, sakthai_home: Path) -> None:
        with (
            patch("urllib.request.urlopen", return_value=_http_response(400, b"bad request")),
            pytest.raises(RuntimeError),
        ):
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
        with (
            patch("urllib.request.urlopen", side_effect=OSError("connection refused")),
            pytest.raises(RuntimeError, match="Failed to sync"),
        ):
            sync_memory_via_http("http://example.com/sync")

    def test_https_url_accepted(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(200)):
            result = sync_memory_via_http("https://secure.example.com/sync")
        assert result == "Synced to HTTP endpoint: https://secure.example.com/sync"


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


# ---------------------------------------------------------------------------
# _handle_git_conflict_and_push (direct unit tests)
# ---------------------------------------------------------------------------


def _fact_dict(value: str) -> dict[str, Any]:
    """Minimal valid fact dict matching the format produced by export_to_dict."""
    now = int(time.time())
    return {
        "id": 1,
        "kind": "note",
        "key": None,
        "value": value,
        "source_session": None,
        "created_at": now,
        "updated_at": now,
        "tags": [],
    }


class TestHandleGitConflictAndPush:
    """Direct tests for the conflict-resolution / auto-merge path."""

    def test_returns_auto_merged_message(self, sakthai_home: Path) -> None:
        (sakthai_home / "facts.jsonl").write_text(
            json.dumps(_fact_dict("remote fact")) + "\n", encoding="utf-8"
        )
        (sakthai_home / "observations.jsonl").write_text("", encoding="utf-8")
        with patch("subprocess.run", side_effect=_git_mock()):
            result = _handle_git_conflict_and_push(sakthai_home, "https://example.com/repo.git")
        assert "Auto-merged" in result

    def test_merges_remote_facts_into_local_store(self, sakthai_home: Path) -> None:
        db_path = sakthai_home / "memory.db"
        with MemoryStore(db_path) as store:
            store.add_fact("local fact")
        (sakthai_home / "facts.jsonl").write_text(
            json.dumps(_fact_dict("remote fact")) + "\n", encoding="utf-8"
        )
        (sakthai_home / "observations.jsonl").write_text("", encoding="utf-8")
        with patch("subprocess.run", side_effect=_git_mock()):
            _handle_git_conflict_and_push(sakthai_home, "https://example.com/repo.git")
        with MemoryStore(db_path) as store:
            values = [f.value for f in store.list_facts()]
        assert "local fact" in values
        assert "remote fact" in values

    def test_merges_remote_observations_into_local_store(self, sakthai_home: Path) -> None:
        """Observations in observations.jsonl are parsed (line 160) and merged."""
        import time

        db_path = sakthai_home / "memory.db"
        now = int(time.time())
        obs_dict = {
            "id": 1,
            "summary": "remote observation summary",
            "evidence_session_id": None,
            "weight": 1.0,
            "confidence": 0.9,
            "created_at": now,
        }
        (sakthai_home / "facts.jsonl").write_text("", encoding="utf-8")
        (sakthai_home / "observations.jsonl").write_text(
            json.dumps(obs_dict) + "\n", encoding="utf-8"
        )
        with patch("subprocess.run", side_effect=_git_mock()):
            result = _handle_git_conflict_and_push(sakthai_home, "https://example.com/repo.git")

        assert isinstance(result, str)
        with MemoryStore(db_path) as store:
            observations = store.top_observations(limit=10)
        summaries = [o.summary for o in observations]
        assert "remote observation summary" in summaries

    def test_no_changes_after_merge_short_circuits(self, sakthai_home: Path) -> None:
        (sakthai_home / "facts.jsonl").write_text("", encoding="utf-8")
        (sakthai_home / "observations.jsonl").write_text("", encoding="utf-8")
        with patch("subprocess.run", side_effect=_git_mock(status_output="")):
            result = _handle_git_conflict_and_push(sakthai_home, "https://example.com/repo.git")
        assert "Merged remote" in result
        assert "no changes" in result.lower()

    def test_missing_jsonl_files_are_tolerated(self, sakthai_home: Path) -> None:
        with patch("subprocess.run", side_effect=_git_mock()):
            result = _handle_git_conflict_and_push(sakthai_home, "https://example.com/repo.git")
        assert isinstance(result, str) and result

    def test_blank_lines_in_jsonl_are_skipped(self, sakthai_home: Path) -> None:
        (sakthai_home / "facts.jsonl").write_text(
            "\n" + json.dumps(_fact_dict("actual fact")) + "\n\n", encoding="utf-8"
        )
        (sakthai_home / "observations.jsonl").write_text("\n\n", encoding="utf-8")
        with patch("subprocess.run", side_effect=_git_mock()):
            _handle_git_conflict_and_push(sakthai_home, "https://example.com/repo.git")
        with MemoryStore(sakthai_home / "memory.db") as store:
            values = [f.value for f in store.list_facts()]
        assert "actual fact" in values


# ---------------------------------------------------------------------------
# Additional git sync edge cases
# ---------------------------------------------------------------------------


class TestSyncMemoryToGitExtended:
    """Edge cases not covered by TestSyncMemoryToGit."""

    def test_remote_set_url_when_origin_already_exists(self, sakthai_home: Path) -> None:
        set_url_called: list[list[str]] = []

        def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
            if len(args) >= 3 and args[1:3] == ["remote", "set-url"]:
                set_url_called.append(args)
            if len(args) >= 3 and args[:3] == ["git", "status", "--porcelain"]:
                return _cp(args, stdout=" M facts.jsonl")
            if len(args) >= 2 and args[1] == "push":
                return _cp(args)
            if len(args) >= 2 and args[1] == "remote" and "set-url" not in args:
                # Simulate origin already present in the remote list
                return _cp(args, stdout="origin\n")
            return _cp(args)

        with patch("subprocess.run", side_effect=_run):
            sync_memory_to_git(remote="https://example.com/repo.git")

        assert set_url_called, "expected git remote set-url to be called"

    def test_git_init_called_when_dot_git_absent(self, sakthai_home: Path) -> None:
        init_called: list[bool] = []

        def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
            if len(args) >= 2 and args[:2] == ["git", "init"]:
                init_called.append(True)
            if len(args) >= 3 and args[:3] == ["git", "status", "--porcelain"]:
                return _cp(args, stdout="")
            if len(args) >= 2 and args[1] == "remote":
                return _cp(args, stdout="")
            return _cp(args)

        assert not (sakthai_home / ".git").exists()
        with patch("subprocess.run", side_effect=_run):
            sync_memory_to_git()

        assert init_called, "expected git init to be called when .git is absent"

    def test_git_init_skipped_when_dot_git_exists(self, sakthai_home: Path) -> None:
        (sakthai_home / ".git").mkdir()
        init_called: list[bool] = []

        def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
            if len(args) >= 2 and args[:2] == ["git", "init"]:
                init_called.append(True)
            if len(args) >= 3 and args[:3] == ["git", "status", "--porcelain"]:
                return _cp(args, stdout="")
            if len(args) >= 2 and args[1] == "remote":
                return _cp(args, stdout="")
            return _cp(args)

        with patch("subprocess.run", side_effect=_run):
            sync_memory_to_git()

        assert not init_called, "git init should not be called when .git already exists"

    def test_http_202_status_accepted(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", return_value=_http_response(202)):
            result = sync_memory_via_http("https://example.com/sync")
        assert isinstance(result, str) and result

    def test_run_git_failure_raises(self, sakthai_home: Path) -> None:
        import subprocess

        from sakthai.memory.sync import _run_git
        # Pass check=True (default) to cause CompletedProcess error print
        with pytest.raises(subprocess.CalledProcessError):
            _run_git(["status", "--invalid-flag-nonexistent"], cwd=sakthai_home)

    def test_http_url_error(self, sakthai_home: Path) -> None:
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("reason")):
            with pytest.raises(RuntimeError, match="Failed to sync to"):
                sync_memory_via_http("https://example.com/sync")

    def test_http_generic_exception(self, sakthai_home: Path) -> None:
        with patch("urllib.request.urlopen", side_effect=Exception("oops")):
            with pytest.raises(RuntimeError, match="Failed to sync to"):
                sync_memory_via_http("https://example.com/sync")

    def test_sync_memory_to_git_diff_summary(self, sakthai_home: Path) -> None:
        diff_stdout = '+ {"kind": "note", "value": "fact"}\n+ {"summary": "obs"}\n'
        def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
            if "diff" in args:
                return _cp(args, stdout=diff_stdout)
            if "status" in args:
                return _cp(args, stdout=" M facts.jsonl")
            return _cp(args)

        commit_args_called = []
        def _run_with_commit_check(args: list[str], **kwargs: object) -> CompletedProcess[str]:
            if "commit" in args:
                commit_args_called.append(args)
            return _run(args, **kwargs)

        with patch("sakthai.memory.sync._run_git", side_effect=_run_with_commit_check):
            sync_memory_to_git()

        assert any("Learned 1 fact(s), 1 observation(s)." in cmd for cmd in commit_args_called)

    def test_pull_memory_git_absent_raises(self, sakthai_home: Path) -> None:
        with pytest.raises(RuntimeError, match="no local Git repository found"):
            pull_memory_from_git()

    def test_pull_memory_git_remote_operations(self, sakthai_home: Path) -> None:
        (sakthai_home / ".git").mkdir()

        # Test pulling with remote when origin is absent and present
        remote_calls = []
        def _run(args: list[str], **kwargs: object) -> CompletedProcess[str]:
            if "remote" in args:
                remote_calls.append(args)
                if "set-url" not in args and "add" not in args:
                    return _cp(args, stdout="origin" if len(remote_calls) > 1 else "")
            return _cp(args)

        # Mock merge to return some counts
        with (
            patch("sakthai.memory.sync._run_git", side_effect=_run),
            patch("sakthai.memory.sync._merge_remote_into_store", return_value=(2, 3))
        ):
            res1 = pull_memory_from_git(remote="https://example.com/repo.git")
            assert "Pulled from https://example.com/repo.git: merged 2 fact(s), 3 observation(s)" in res1

            res2 = pull_memory_from_git(remote="https://example.com/repo.git")
            assert "Pulled from https://example.com/repo.git" in res2

    def test_pull_memory_git_already_up_to_date(self, sakthai_home: Path) -> None:
        (sakthai_home / ".git").mkdir()
        with (
            patch("sakthai.memory.sync._run_git", return_value=_cp([])),
            patch("sakthai.memory.sync._merge_remote_into_store", return_value=(0, 0))
        ):
            res = pull_memory_from_git()
            assert "already up to date" in res
