"""Tests for scripts/code_scanning_analyses.py's handling of a huge history."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "code_scanning_analyses.py"


@pytest.fixture
def csa() -> ModuleType:
    spec = importlib.util.spec_from_file_location("code_scanning_analyses", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _endless_analyses(csa: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """Alerts fit on one page; the unfiltered analyses list never ends."""

    def fake_request(
        method: str, path: str, token: str, params: dict[str, Any] | None = None
    ) -> tuple[int, Any, str | None]:
        if "/alerts" in path:
            return 200, [{"number": 1, "tool": {"name": "CodeQL"}, "state": "open"}], None
        if params and params.get("tool_name") == "BinSkim":
            return 200, [{"id": 7, "tool": {"name": "BinSkim"}, "created_at": "2026-09-01"}], None
        return 200, [{"id": 1, "tool": {"name": "CodeQL"}}], "https://api.github.com/next"

    monkeypatch.setattr(csa, "_request", fake_request)
    monkeypatch.setattr(csa, "MAX_PAGES", 3)


def _args(tool: str | None) -> argparse.Namespace:
    return argparse.Namespace(repo="o/r", tool=tool, state="open", alerts=False, analyses=False)


def test_list_without_tool_survives_page_limit(
    csa: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _endless_analyses(csa, monkeypatch)

    assert csa.cmd_list(_args(None), "t") == 0

    out, err = capsys.readouterr()
    assert "Open code-scanning alerts on o/r: 1" in out
    assert "CodeQL" in out
    assert "exceeds 3 pages" in err


def test_list_with_tool_is_filtered_server_side(
    csa: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _endless_analyses(csa, monkeypatch)

    assert csa.cmd_list(_args("BinSkim"), "t") == 0

    out, _ = capsys.readouterr()
    assert "BinSkim" in out
    assert "2026-09-01" in out


def test_page_limit_is_still_an_api_error(csa: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    _endless_analyses(csa, monkeypatch)

    with pytest.raises(csa.ApiError, match="Refusing to page past 3 pages"):
        csa.fetch_analyses("o/r", "t")


def _two_bandit_categories(
    csa: ModuleType, monkeypatch: pytest.MonkeyPatch, deleted: list[str]
) -> None:
    """A live Bandit category plus a stale one left by an older workflow."""
    analyses = [
        {"id": 3, "tool": {"name": "Bandit"}, "category": "live", "created_at": "2026-10-04"},
        {"id": 2, "tool": {"name": "Bandit"}, "category": "stale", "created_at": "2026-08-18"},
        {"id": 1, "tool": {"name": "Bandit"}, "category": "stale", "created_at": "2026-08-01"},
    ]

    def fake_request(
        method: str, path: str, token: str, params: dict[str, Any] | None = None
    ) -> tuple[int, Any, str | None]:
        if method == "DELETE":
            deleted.append(path.rsplit("/", 1)[1])
            return 200, {}, None
        if "/alerts" in path:
            return 200, [], None
        return 200, analyses, None

    monkeypatch.setattr(csa, "_request", fake_request)


def test_list_with_tool_breaks_analyses_down_by_category(
    csa: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _two_bandit_categories(csa, monkeypatch, [])

    assert csa.cmd_list(_args("Bandit"), "t") == 0

    out, _ = capsys.readouterr()
    assert "--- Bandit by category ---" in out
    stale = next(line for line in out.splitlines() if line.startswith("stale"))
    assert "2" in stale and "2026-08-18" in stale


def test_delete_category_leaves_the_live_category_alone(
    csa: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    deleted: list[str] = []
    _two_bandit_categories(csa, monkeypatch, deleted)
    args = argparse.Namespace(repo="o/r", tool="Bandit", category="stale", apply=True)

    assert csa.cmd_delete(args, "t") == 0

    assert deleted == ["2", "1"]


def test_delete_unknown_category_deletes_nothing(
    csa: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    deleted: list[str] = []
    _two_bandit_categories(csa, monkeypatch, deleted)
    args = argparse.Namespace(repo="o/r", tool="Bandit", category="nope", apply=True)

    assert csa.cmd_delete(args, "t") == 1

    assert deleted == []


def test_delete_none_sentinel_selects_only_uncategorized(
    csa: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    deleted: list[str] = []
    analyses = [
        {"id": 9, "tool": {"name": "Bandit"}, "category": "live"},
        {"id": 8, "tool": {"name": "Bandit"}, "category": ""},
        {"id": 7, "tool": {"name": "Bandit"}},
    ]

    def fake_request(
        method: str, path: str, token: str, params: dict[str, Any] | None = None
    ) -> tuple[int, Any, str | None]:
        if method == "DELETE":
            deleted.append(path.rsplit("/", 1)[1])
            return 200, {}, None
        return 200, analyses, None

    monkeypatch.setattr(csa, "_request", fake_request)
    args = argparse.Namespace(repo="o/r", tool="Bandit", category=csa.NO_CATEGORY, apply=True)

    assert csa.cmd_delete(args, "t") == 0

    assert deleted == ["8", "7"]
