"""Tests for scripts/code_scanning_analyses.py.

The script prunes GitHub code-scanning analyses whose producing workflow was
deleted — see ``docs/code-scanning-sweep-2026-08-12.md``. It lives under
``scripts/`` rather than in the installed package, so it is loaded here via
``importlib``, following ``tests/test_compose_persona.py``.

Every test stubs the single HTTP seam (``_request``); nothing here touches the
network.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "code_scanning_analyses.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("code_scanning_analyses", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mod() -> ModuleType:
    return _load_module()


def _analysis(analysis_id: int, tool: str, results: int = 1, created: str = "2026-07-03") -> dict:
    return {
        "id": analysis_id,
        "tool": {"name": tool},
        "created_at": created,
        "ref": "refs/heads/main",
        "category": None,
        "results_count": results,
        "deletable": True,
    }


def _alert(number: int, tool: str) -> dict:
    return {"number": number, "tool": {"name": tool}, "state": "open"}


# --------------------------------------------------------------------------
# pure helpers
# --------------------------------------------------------------------------


def test_tool_name_falls_back_when_absent(mod: ModuleType) -> None:
    assert mod._tool_name({"tool": {"name": "Codacy"}}) == "Codacy"
    assert mod._tool_name({"tool": {}}) == "(unknown)"
    assert mod._tool_name({}) == "(unknown)"


def test_group_by_tool_partitions_entries(mod: ModuleType) -> None:
    grouped = mod.group_by_tool([_alert(1, "Codacy"), _alert(2, "CodeQL"), _alert(3, "Codacy")])
    assert sorted(grouped) == ["Codacy", "CodeQL"]
    assert [a["number"] for a in grouped["Codacy"]] == [1, 3]


def test_message_reads_github_error_body(mod: ModuleType) -> None:
    assert mod._message({"message": "Resource not accessible by integration"}) == (
        "Resource not accessible by integration"
    )
    assert mod._message("plain") == "plain"


# --------------------------------------------------------------------------
# pagination
# --------------------------------------------------------------------------


def test_paginate_walks_until_a_short_page(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    pages = {
        1: [_analysis(i, "Codacy") for i in range(mod.PER_PAGE)],
        2: [_analysis(999, "Codacy")],
    }
    seen: list[int] = []

    def fake_request(method: str, path: str, token: str, params: dict[str, Any]) -> tuple[int, Any]:
        seen.append(params["page"])
        return 200, pages.get(params["page"], [])

    monkeypatch.setattr(mod, "_request", fake_request)
    out = mod._paginate("/x", "t", {})
    assert len(out) == mod.PER_PAGE + 1
    assert seen == [1, 2]


def test_paginate_raises_a_scope_hint_on_403(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        mod,
        "_request",
        lambda *a, **k: (403, {"message": "Resource not accessible by integration"}),
    )
    with pytest.raises(mod.ApiError) as excinfo:
        mod._paginate("/x", "t", {})
    # The hint is the whole point: a 403 here is always a token-scope problem.
    assert "Code scanning alerts" in str(excinfo.value)


def test_paginate_treats_404_as_empty(mod: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "_request", lambda *a, **k: (404, {"message": "Not Found"}))
    assert mod._paginate("/x", "t", {}) == []


def test_paginate_surfaces_other_errors(mod: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "_request", lambda *a, **k: (500, {"message": "boom"}))
    with pytest.raises(mod.ApiError, match="500"):
        mod._paginate("/x", "t", {})


# --------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------


def test_list_reports_a_tool_with_alerts_but_no_live_analysis(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(mod, "fetch_alerts", lambda *a: [_alert(1, "Codacy"), _alert(2, "Codacy")])
    monkeypatch.setattr(mod, "fetch_analyses", lambda *a, **k: [_analysis(10, "Codacy")])

    args = mod.build_parser().parse_args(["list"])
    assert args.func(args, "token") == 0

    out = capsys.readouterr().out
    assert "Open code-scanning alerts" in out
    assert "Codacy" in out
    assert "2026-07-03" in out


def test_list_can_dump_individual_analyses(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(mod, "fetch_alerts", lambda *a: [])
    monkeypatch.setattr(
        mod, "fetch_analyses", lambda *a, **k: [_analysis(10, "Codacy", results=15000)]
    )

    args = mod.build_parser().parse_args(["list", "--analyses"])
    assert args.func(args, "token") == 0
    assert "id=10" in capsys.readouterr().out


def test_list_says_so_when_nothing_is_reported(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(mod, "fetch_alerts", lambda *a: [])
    monkeypatch.setattr(mod, "fetch_analyses", lambda *a, **k: [])

    args = mod.build_parser().parse_args(["list"])
    assert args.func(args, "token") == 0
    assert "Nothing reported." in capsys.readouterr().out


# --------------------------------------------------------------------------
# alert state
# --------------------------------------------------------------------------


def test_fetch_alerts_filters_by_state(mod: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[dict] = []

    def fake_paginate(path: str, token: str, params: dict) -> list[dict]:
        seen.append(params)
        return []

    monkeypatch.setattr(mod, "_paginate", fake_paginate)
    mod.fetch_alerts("o/r", "t", "dismissed")
    assert seen == [{"state": "dismissed"}]


def test_fetch_alerts_sends_no_filter_for_all(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`all` must omit the parameter, not pass ``state=all``.

    The API has no ``all`` state; it returns every state when the parameter is
    absent. Sending ``state=all`` would be rejected rather than widened.
    """
    seen: list[dict] = []
    monkeypatch.setattr(mod, "_paginate", lambda p, t, params: seen.append(params) or [])
    mod.fetch_alerts("o/r", "t", "all")
    assert seen == [{}]


def test_list_prints_the_dismissal_reason(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A dismissed alert must be distinguishable from one a fix closed.

    Both simply stop appearing under `open`, which is how 29
    PinnedDependenciesID alerts left the dashboard with no matching diff.
    """
    dismissed = {
        "number": 15454,
        "tool": {"name": "Scorecard"},
        "state": "dismissed",
        "dismissed_reason": "won't fix",
        "rule": {"id": "PinnedDependenciesID", "severity": "medium"},
        "most_recent_instance": {"ref": "refs/heads/main", "location": {}},
    }
    monkeypatch.setattr(mod, "fetch_alerts", lambda *a: [dismissed])
    monkeypatch.setattr(mod, "fetch_analyses", lambda *a, **k: [])

    args = mod.build_parser().parse_args(["list", "--alerts", "--state", "dismissed"])
    assert args.func(args, "token") == 0
    out = capsys.readouterr().out
    assert "Dismissed code-scanning alerts" in out
    assert "state=dismissed (won't fix)" in out


def test_alert_state_omits_the_reason_when_there_is_none(mod: ModuleType) -> None:
    assert mod._alert_state({"state": "open"}) == "open"


# --------------------------------------------------------------------------
# delete
# --------------------------------------------------------------------------


def test_delete_without_apply_deletes_nothing(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        mod, "fetch_analyses", lambda *a, **k: [_analysis(10, "Codacy", results=9000)]
    )

    def fail(*a: Any, **k: Any) -> tuple[int, Any]:  # pragma: no cover - must not run
        raise AssertionError("dry run must not issue a DELETE")

    monkeypatch.setattr(mod, "_request", fail)

    args = mod.build_parser().parse_args(["delete", "--tool", "Codacy"])
    assert args.func(args, "token") == 0
    assert "Dry run." in capsys.readouterr().out


def test_delete_removes_newest_first(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        mod,
        "fetch_analyses",
        lambda *a, **k: [_analysis(10, "Codacy"), _analysis(30, "Codacy"), _analysis(20, "Codacy")],
    )
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def fake_request(method: str, path: str, token: str, params: dict[str, Any]) -> tuple[int, Any]:
        calls.append((method, path, params))
        return 200, {"next_analysis_url": None}

    monkeypatch.setattr(mod, "_request", fake_request)

    args = mod.build_parser().parse_args(["delete", "--tool", "Codacy", "--apply"])
    assert args.func(args, "token") == 0

    assert [c[0] for c in calls] == ["DELETE"] * 3
    assert [c[1].rsplit("/", 1)[-1] for c in calls] == ["30", "20", "10"]
    # confirm_delete is required for the final analysis of a set; sending it on
    # every call is what makes the loop safe to run in any order.
    assert all(c[2]["confirm_delete"] == "true" for c in calls)
    assert "Deleted 3 analysis/analyses" in capsys.readouterr().out


def test_delete_tolerates_an_already_deleted_analysis(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        mod, "fetch_analyses", lambda *a, **k: [_analysis(10, "Codacy"), _analysis(20, "Codacy")]
    )
    monkeypatch.setattr(
        mod,
        "_request",
        lambda m, p, t, params: (
            (404, {"message": "Not Found"}) if p.endswith("/10") else (200, None)
        ),
    )

    args = mod.build_parser().parse_args(["delete", "--tool", "Codacy", "--apply"])
    assert args.func(args, "token") == 0
    out = capsys.readouterr().out
    assert "already deleted" in out
    assert "Deleted 1 analysis/analyses" in out


def test_delete_stops_on_a_real_api_error(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(mod, "fetch_analyses", lambda *a, **k: [_analysis(10, "Codacy")])
    monkeypatch.setattr(mod, "_request", lambda *a, **k: (403, {"message": "nope"}))

    args = mod.build_parser().parse_args(["delete", "--tool", "Codacy", "--apply"])
    assert args.func(args, "token") == 1
    assert "nope" in capsys.readouterr().err


def test_delete_refuses_an_unknown_tool(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(mod, "fetch_analyses", lambda *a, **k: [])

    args = mod.build_parser().parse_args(["delete", "--tool", "Nope", "--apply"])
    assert args.func(args, "token") == 1
    assert "No analyses found" in capsys.readouterr().err


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def test_main_requires_a_token(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert mod.main(["list"]) == 2
    assert "Set GITHUB_TOKEN" in capsys.readouterr().err


def test_main_reports_api_errors_without_a_traceback(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "t")

    def boom(*a: Any, **k: Any) -> list[Any]:
        raise mod.ApiError("403 from /x: Resource not accessible by integration")

    monkeypatch.setattr(mod, "fetch_alerts", boom)
    assert mod.main(["list"]) == 1
    assert "Resource not accessible" in capsys.readouterr().err


def test_cleanup_workflow_never_interpolates_inputs_into_a_run_block() -> None:
    """`inputs.*` must reach the shell via env, not via ${{ }} inside `run:`.

    An input expanded into the script text of a `run:` step is a command
    injection sink — CodeQL's `actions/code-injection` rule. The workflow passes
    `tool` and `apply` through `env:` and dereferences them as shell variables,
    which is what keeps that query at zero.
    """
    workflow = REPO_ROOT / ".github" / "workflows" / "code-scanning-cleanup.yml"
    steps = yaml.safe_load(workflow.read_text())["jobs"]["cleanup"]["steps"]

    run_blocks = [step["run"] for step in steps if "run" in step]
    assert run_blocks, "expected the cleanup workflow to have run steps"
    for block in run_blocks:
        assert "${{" not in block, f"input interpolated into a run block: {block!r}"

    # And the values really are wired through, so the guard above is meaningful
    # rather than passing because nothing is passed at all.
    env_values = {v for step in steps for v in (step.get("env") or {}).values()}
    assert "${{ inputs.tool }}" in env_values
    assert "${{ inputs.apply }}" in env_values


def test_repo_defaults_to_this_repository(mod: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    reloaded = _load_module()
    args = reloaded.build_parser().parse_args(["list"])
    assert args.repo == "beer-sakthai/Sak-Family-Agent"
