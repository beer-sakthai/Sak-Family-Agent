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
