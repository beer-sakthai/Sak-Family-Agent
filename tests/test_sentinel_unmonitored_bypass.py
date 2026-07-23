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
        # Modern Python & Node execution runners targeting sensitive files
        "poetry run rm -rf /etc",
        "poetry run -C /tmp rm -rf /etc",
        "pipenv run rm -rf /etc",
        "conda run rm -rf /etc",
        "conda run -n myenv rm -rf /etc",
        "conda run -p /tmp/env cat /etc/shadow",
        "pnpm exec rm -rf /etc",
        "pnpm --filter pkg exec rm -rf /etc",
        "pnpm -c /tmp exec rm -rf /etc",
        "yarn run rm -rf /etc",
        "yarn --cwd /tmp run rm -rf /etc",
        "poetry run cat /etc/shadow",
        "pipenv run cat /etc/shadow",
        "conda run cat /etc/shadow",
        "pnpm exec cat /etc/shadow",
        "yarn run cat /etc/shadow",
        'pnpm exec sh -c "cat /etc/shadow"',
        'yarn exec sh -c "cat /etc/shadow"',
        "conda run -n myenv -p /some/prefix --cwd /some/dir cat /etc/shadow",
        "poetry run -C /some/dir cat /etc/shadow",
        'pnpm exec --filter mypkg -c /some/dir sh -c "cat /etc/shadow"',
    ],
)
def test_unmonitored_binaries_bypass(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY, (
        f"Command '{command}' should be blocked but was allowed"
    )


@pytest.mark.parametrize(
    "command",
    [
        "poetry run pytest",
        "pipenv run python main.py",
        'conda run python -c "print(1)"',
        "conda run -n myenv python",
        "pnpm exec tsc",
        "pnpm --filter pkg exec lint",
        "yarn run build",
        "yarn --cwd docs run build",
        "pipenv run python -m unittest",
        "conda run python -c \"print('hello')\"",
        "pnpm exec eslint .",
        "yarn exec prettier --check .",
        "conda run -n myenv -p /some/prefix --cwd /some/dir python -c \"print('hello')\"",
        "poetry run -C /some/dir pytest",
        "pnpm exec --filter mypkg -c /some/dir eslint .",
    ],
)
def test_safe_unmonitored_binaries_allowed(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.ALLOW, (
        f"Command '{command}' should be allowed but was blocked: {result.reason}"
    )
