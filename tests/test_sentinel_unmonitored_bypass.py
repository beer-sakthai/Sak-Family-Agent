import pytest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.mark.parametrize(
    "command",
    [
        "touch /etc/passwd",
        "git clone https://github.com/example/repo /root/.ssh",
        "npm install --prefix /etc some-package",
        "git init /etc",
        "mkdir /etc/test_dir",
        "pip install --target /root/.ssh some-package",
    ],
)
def test_unmonitored_binaries_bypass(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    # If these are currently bypassing, they will return ALLOW.
    # We WANT them to be blocked.
    assert result.action == GuardrailAction.DENY, (
        f"Command '{command}' should be blocked but was allowed"
    )
