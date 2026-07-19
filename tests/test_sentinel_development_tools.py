import pytest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.mark.parametrize(
    "command",
    [
        "git config alias.x '!cat /etc/shadow'",
        "git -c alias.x='!cat /etc/shadow' x",
        "sqlite3 memory.db",
        "sqlite3 .import /etc/shadow table",
        "tsx -e \"require('fs').readFileSync('.env')\"",
        "ts-node -e \"require('fs').readFileSync('.env')\"",
    ],
)
def test_development_tools_bypass(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY, f"Command '{command}' should be blocked"
