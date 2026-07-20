from __future__ import annotations

import pytest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.mark.parametrize(
    "command",
    [
        # Direct targeting of sensitive paths (destructive/exfiltration binary block)
        "uv pip install --target /etc some-package",
        "pipx install --spec some-package /etc",
        "bun run /etc/shadow",
        "bunx --cwd /etc some-command",
        # Wrapped dangerous commands (recursive wrapper check)
        "uv run rm -rf /etc",
        "uv run --with requests python3 -c \"print(open('/etc/shadow').read())\"",
        "pipx run --spec requests python -c \"import os; os.remove('/etc/passwd')\"",
        "bun run rm -rf /etc",
        "bunx rm -rf /etc",
        "bunx -p tsx tsx -c \"require('fs').readFileSync('/etc/shadow')\"",
    ],
)
def test_dangerous_development_tools_blocked(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY, (
        f"Command '{command}' should be blocked but was allowed"
    )
    assert "blocked" in result.reason.lower() or "denied" in result.reason.lower()


@pytest.mark.parametrize(
    "command",
    [
        "uv run python -c \"print('hello')\"",
        "bun run index.ts",
        "bunx cowsay hello",
    ],
)
def test_safe_development_tools_allowed(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.ALLOW, (
        f"Command '{command}' should be allowed but was blocked: {result.reason}"
    )


@pytest.mark.parametrize(
    "command",
    [
        # Version-control and database tools with embedded file access
        "git config alias.x '!cat /etc/shadow'",
        "git -c alias.x='!cat /etc/shadow' x",
        "sqlite3 memory.db",
        "sqlite3 .import /etc/shadow table",
        # TypeScript runners evaluating inline scripts that read sensitive files
        "tsx -e \"require('fs').readFileSync('.env')\"",
        "ts-node -e \"require('fs').readFileSync('.env')\"",
    ],
)
def test_database_and_vcs_tools_bypass_blocked(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY, f"Command '{command}' should be blocked"
