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
        "npx rimraf /etc",
        "npx --yes rimraf /etc",
        "deno run --allow-read /etc/shadow",
        "deno run /etc/passwd",
        # Wrapped dangerous commands (recursive wrapper check)
        "uv run rm -rf /etc",
        "uv run --with requests python3 -c \"print(open('/etc/shadow').read())\"",
        "pipx run --spec requests python -c \"import os; os.remove('/etc/passwd')\"",
        "bun run rm -rf /etc",
        "bunx rm -rf /etc",
        "bunx -p tsx tsx -c \"require('fs').readFileSync('/etc/shadow')\"",
        # Database clients targeting sensitive paths
        "psql -f /etc/passwd",
        "mysql -u root -e 'source /etc/passwd'",
        "mongosh --eval \"load('/etc/passwd')\"",
        "redis-cli --eval /etc/passwd",
        # Text editors targeting sensitive paths
        "vim -c ':w /etc/shadow'",
        "nano /etc/shadow",
        # Hardened package managers
        "npm exec rm -rf /etc",
        "cargo run -- /etc",
        "composer exec rm -rf /etc",
        "npm exec --prefix /etc some-command",
        "cargo run --manifest-path /etc/Cargo.toml",
        "composer --working-dir /etc run-script test",
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
        "npx cowsay hello",
        "deno run main.ts",
        'psql -c "SELECT 1"',
        'mysql -e "SELECT 1"',
        "mongosh --eval \"print('hello')\"",
        "redis-cli ping",
        "npm run build",
        "cargo check",
        "composer install",
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
        "deno eval \"Deno.readTextFileSync('.env')\"",
        "bun eval \"require('fs').readFileSync('.env')\"",
        # Database/Editor/Package manager interpreters evaluating inline scripts/queries that target sensitive files
        "psql -c \"COPY (SELECT * FROM users) TO '/etc/shadow'\"",
        "mysql -e \"LOAD DATA INFILE '.env' INTO TABLE x\"",
        "mariadb -e \"LOAD DATA INFILE '.env' INTO TABLE x\"",
        "mongosh --eval \"cat('.env')\"",
        'redis-cli --eval ".env"',
        'vim -S ".env"',
        'vi -c "source .env"',
    ],
)
def test_database_and_vcs_tools_bypass_blocked(command, run_command_tool, store, monkeypatch):
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY, f"Command '{command}' should be blocked"
