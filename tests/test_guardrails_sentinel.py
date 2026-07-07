import pytest
from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore

@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")

@pytest.mark.parametrize("command", [
    "find -L /etc -delete",
    "find -H /var -delete",
    "find -P /root -delete",
    "find /etc -execdir rm {} +",
    "find /etc -ok rm {} \;",
    "find /etc -okdir rm {} \;",
    "xargs rm -rf /etc",
    "sudo xargs rm -rf /bin",
])
def test_hardened_bypasses_blocked(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert "blocked" in result.reason.lower()

def test_xargs_safe_allowed(run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": "xargs ls"}, store)
    assert result.action == GuardrailAction.ALLOW
