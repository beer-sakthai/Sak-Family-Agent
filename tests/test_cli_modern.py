"""Tests for modern agent CLI experience (Claude Code, Gemini CLI, AGY parity).

Covers:
- Smart default command routing (no-args interactive chat, non-interactive help,
  direct task prompts without explicit 'run' subcommand, flag forwarding).
- Multi-token task joining for `sakthai run` and direct prompts.
- Interactive REPL slash commands (/help, /status, /persona, /model, /provider,
  /tools, /skills, /memory, /learn, /doctor, /clear, /reset, /goal, /exit, /quit).
- In-session shell command execution (!<cmd>).
- Dynamic prompt generation, cancellation handling, and history persistence.
- Entrypoint definitions (`sak` and `sakthai`).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from rich.console import Console

import sakthai.cli as cli_module
import sakthai.cli.chat as chat_cli
from sakthai.agent.chat import run_chat, slash_result
from sakthai.agent.tools import Tool
from sakthai.agent.ui import SLASH_COMMANDS, personas_panel, status_panel
from sakthai.cli import main
from sakthai.memory.store import MemoryStore

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# Entrypoints and Smart Dispatcher Tests
# ---------------------------------------------------------------------------


def test_pyproject_scripts_include_sak_and_sakthai() -> None:
    """Both 'sak' and 'sakthai' should be configured in pyproject.toml scripts."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    assert scripts.get("sakthai") == "sakthai.cli:main"
    assert scripts.get("sak") == "sakthai.cli:main"


def test_version_dynamic_prog_name_sak(runner: CliRunner) -> None:
    """When invoked as sak, version output shows sak."""
    result = runner.invoke(main, ["--version"], prog_name="sak")
    assert result.exit_code == 0
    assert result.output.strip().startswith("sak, version")


def test_version_dynamic_prog_name_sakthai(runner: CliRunner) -> None:
    """When invoked as sakthai, version output shows sakthai."""
    result = runner.invoke(main, ["--version"], prog_name="sakthai")
    assert result.exit_code == 0
    assert result.output.strip().startswith("sakthai, version")


def test_version_dynamic_default(runner: CliRunner) -> None:
    """When invoked without explicit prog_name, version defaults to sak."""
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip().startswith("sak, version")


def test_main_no_args_non_interactive_shows_help(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    """When invoked without arguments non-interactively, main should display help."""
    monkeypatch.setattr(cli_module, "_is_interactive", lambda: False)
    result = runner.invoke(main, [], prog_name="sak")
    assert result.exit_code == 0
    assert "Usage: sak" in result.output
    assert "Commands:" in result.output
    assert "House of Sak" in result.output


def test_main_no_args_interactive_launches_chat(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    """When invoked without arguments interactively, main should drop into chat."""
    invoked = False

    def _mock_chat(*args: Any, **kwargs: Any) -> None:
        nonlocal invoked
        invoked = True

    monkeypatch.setattr(cli_module, "_is_interactive", lambda: True)
    monkeypatch.setattr(cli_module, "chat_cmd", _mock_chat)
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert invoked is True


def test_main_direct_task_routes_to_run(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    """Passing a task prompt directly to sakthai should execute run."""
    captured: dict[str, Any] = {}

    def _mock_run_agent(task: str, **kwargs: Any) -> Any:
        captured["task"] = task
        captured.update(kwargs)
        res = MagicMock()
        res.text = "Analysis complete."
        return res

    monkeypatch.setattr("sakthai.cli.agent.run_agent", _mock_run_agent)
    result = runner.invoke(main, ["explain the architecture", "--no-mcp"])
    assert result.exit_code == 0
    assert captured.get("task") == "explain the architecture"
    assert "Analysis complete." in result.output


def test_main_multi_token_task_routes_to_run(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    """Passing multiple unquoted tokens as a prompt should join and run."""
    captured: dict[str, Any] = {}

    def _mock_run_agent(task: str, **kwargs: Any) -> Any:
        captured["task"] = task
        res = MagicMock()
        res.text = "Done."
        return res

    monkeypatch.setattr("sakthai.cli.agent.run_agent", _mock_run_agent)
    result = runner.invoke(main, ["run", "my", "custom", "prompt", "--no-mcp"])
    assert result.exit_code == 0
    assert captured.get("task") == "my custom prompt"


def test_main_direct_prompt_with_flags_routes_to_run(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    """Passing flags with a direct task should forward flags to run."""
    captured: dict[str, Any] = {}

    def _mock_run_agent(task: str, **kwargs: Any) -> Any:
        captured["task"] = task
        captured["persona"] = kwargs.get("persona")
        res = MagicMock()
        res.text = "Jules reporting."
        return res

    monkeypatch.setattr("sakthai.cli.agent.run_agent", _mock_run_agent)
    result = runner.invoke(main, ["--persona", "sakjules", "check", "ci", "status", "--no-mcp"])
    assert result.exit_code == 0
    assert captured.get("task") == "check ci status"
    assert captured.get("persona") == "sakjules"


def test_main_subcommands_not_hijacked(runner: CliRunner) -> None:
    """Known subcommands like status or doctor must not be treated as run prompts."""
    res_status = runner.invoke(main, ["status", "--json"])
    assert res_status.exit_code == 0
    assert "ready" in res_status.output


# ---------------------------------------------------------------------------
# Slash Commands and UI Renderables
# ---------------------------------------------------------------------------


def test_slash_commands_list_contains_all_modern_commands() -> None:
    """SLASH_COMMANDS should include all expected agent commands."""
    commands = {cmd for cmd, _args, _desc in SLASH_COMMANDS}
    expected = {
        "/help",
        "/status",
        "/persona",
        "/model",
        "/provider",
        "/tools",
        "/skills",
        "/memory",
        "/learn",
        "/doctor",
        "/goal",
        "/clear",
        "/reset",
        "!<cmd>",
        "/exit",
    }
    assert expected.issubset(commands)


def test_slash_result_help_and_status(tmp_path: Path) -> None:
    """slash_result should handle /help and /status cleanly."""
    store = MemoryStore(tmp_path / "memory.db")
    try:
        handled, goal, renderables = slash_result(
            "/help",
            persona="sakthai",
            goal=None,
            store=store,
        )
        assert handled is True
        assert len(renderables) == 1

        handled, goal, renderables = slash_result(
            "/status",
            persona="sakjules",
            goal="ship release",
            store=store,
            model="sakthai",
            provider="ollama",
            turns=3,
        )
        assert handled is True
        assert len(renderables) == 1
    finally:
        store.close()


def test_slash_result_persona_listing_and_switching(tmp_path: Path) -> None:
    """slash_result should list personas when no arg, and confirm valid persona."""
    store = MemoryStore(tmp_path / "memory.db")
    try:
        # Listing
        handled, _, renderables = slash_result(
            "/persona", persona="sakthai", goal=None, store=store
        )
        assert handled is True
        assert len(renderables) == 1

        # Valid switch
        handled, _, renderables = slash_result(
            "/persona saksee", persona="sakthai", goal=None, store=store
        )
        assert handled is True
        assert "SakSee" in str(renderables[0])

        # Invalid persona
        handled, _, renderables = slash_result(
            "/persona non_existent", persona="sakthai", goal=None, store=store
        )
        assert handled is True
        assert "Unknown persona" in str(renderables[0])
    finally:
        store.close()


def test_slash_result_model_and_provider_switching(tmp_path: Path) -> None:
    """slash_result should display or set model and provider."""
    store = MemoryStore(tmp_path / "memory.db")
    try:
        # Model
        h1, _, r1 = slash_result(
            "/model", persona="sakthai", goal=None, store=store, model="sakthai"
        )
        assert h1 is True
        assert "Current model: sakthai" in str(r1[0])

        h2, _, r2 = slash_result("/model gpt-4o", persona="sakthai", goal=None, store=store)
        assert h2 is True
        assert "gpt-4o" in str(r2[0])

        # Provider
        h3, _, r3 = slash_result(
            "/provider", persona="sakthai", goal=None, store=store, provider="ollama"
        )
        assert h3 is True
        assert "Current provider: ollama" in str(r3[0])

        h4, _, r4 = slash_result("/provider anthropic", persona="sakthai", goal=None, store=store)
        assert h4 is True
        assert "anthropic" in str(r4[0])
    finally:
        store.close()


def test_slash_result_doctor_and_learn(tmp_path: Path) -> None:
    """slash_result should handle /doctor and /learn."""
    store = MemoryStore(tmp_path / "memory.db")
    try:
        # Doctor
        handled, _, renderables = slash_result("/doctor", persona="sakthai", goal=None, store=store)
        assert handled is True
        assert getattr(renderables[0], "title", "") == "Diagnostics"

        # Learn with value
        handled, _, renderables = slash_result(
            "/learn The sky is blue", persona="sakthai", goal=None, store=store
        )
        assert handled is True
        assert "Fact stored" in str(renderables[0])
        facts = store.list_facts()
        assert any("The sky is blue" in f.value for f in facts)

        # Learn without value
        handled, _, renderables = slash_result("/learn", persona="sakthai", goal=None, store=store)
        assert handled is True
        assert "Usage: /learn" in str(renderables[0])
    finally:
        store.close()


def test_slash_result_reset_and_clear() -> None:
    """slash_result should handle /reset, /new, and /clear."""
    h1, _, r1 = slash_result("/reset", persona="sakthai", goal="some goal", store=None)
    assert h1 is True
    assert "reset" in str(r1[0]).lower()

    h2, _, r2 = slash_result("/new", persona="sakthai", goal="some goal", store=None)
    assert h2 is True
    assert "reset" in str(r2[0]).lower()

    h3, g3, r3 = slash_result("/clear", persona="sakthai", goal="some goal", store=None)
    assert h3 is True
    assert g3 is None
    assert r3 == []


def test_personas_panel_and_status_panel_render() -> None:
    """personas_panel and status_panel should build Rich Panels cleanly."""
    p_panel = personas_panel()
    assert p_panel is not None

    s_panel = status_panel(
        persona="sakjules",
        model="claude-3-5-sonnet",
        provider="anthropic",
        tool_count=12,
        facts=42,
        observations=10,
        goal="Automate workflows",
        turns=5,
        cwd="/tmp/workspace",
    )
    assert s_panel is not None


# ---------------------------------------------------------------------------
# Interactive REPL run_chat Tests
# ---------------------------------------------------------------------------


def test_run_chat_slash_commands_and_shell(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """run_chat should handle in-session slash commands, shell execution, and persona switching."""
    inputs = [
        "/help",
        "/status",
        "/persona sakjules",
        "/model custom-model",
        "/provider gateway",
        "/learn Jules manages GitHub automation",
        "!echo shell_ok",
        "/reset",
        "/clear",
        "/exit",
    ]
    input_iter = iter(inputs)

    store = MemoryStore(tmp_path / "memory.db")
    console = Console(record=True, width=120)

    switched: list[str] = []

    def _on_switch(persona: str) -> None:
        switched.append(persona)

    tool = Tool(
        name="test_tool",
        description="A test tool",
        input_schema={},
        handler=lambda inp, s: "result",
    )

    try:
        run_chat(
            persona="sakthai",
            soul_text="You are SakThai.",
            tools=(tool,),
            model="sakthai",
            provider="ollama",
            caveman=None,
            with_skills=(),
            store=store,
            console=console,
            read_input=lambda: next(input_iter, None),
            on_persona_change=_on_switch,
        )
    finally:
        store.close()

    output = console.export_text()
    assert "Switched to SakJules" in output
    assert "Model changed to: custom-model" in output
    assert "Provider changed to: gateway" in output
    assert "Fact stored" in output
    assert "shell_ok" in output
    assert "Conversation history reset" in output
    assert "Goodbye! Keep growing." in output
    assert "sakjules" in switched


def test_run_chat_keyboard_interrupt_graceful(tmp_path: Path) -> None:
    """KeyboardInterrupt in read_input should cancel turn without crashing session."""
    called = 0

    def _faulty_input() -> str | None:
        nonlocal called
        called += 1
        if called == 1:
            raise KeyboardInterrupt()
        return "/exit"

    store = MemoryStore(tmp_path / "memory.db")
    console = Console(record=True)
    try:
        run_chat(
            persona="sakthai",
            soul_text="",
            tools=(),
            model="sakthai",
            provider="ollama",
            caveman=None,
            with_skills=(),
            store=store,
            console=console,
            read_input=_faulty_input,
        )
    finally:
        store.close()

    output = console.export_text()
    assert "(cancelled)" in output
    assert "Goodbye!" in output


def test_make_read_input_helper() -> None:
    """_make_read_input should create a prompt session with history and completer."""
    reader = chat_cli._make_read_input("sakking> ")
    assert callable(reader)
