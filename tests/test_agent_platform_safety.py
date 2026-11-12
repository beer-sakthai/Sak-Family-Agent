# tests/test_agent_platform_safety.py
from sakthai.agent_platform.safety import DataLossGuardrail


def test_guardrail_allows_safe_command():
    guard = DataLossGuardrail()
    result = guard.inspect("git status && ls -la")
    assert not result.is_destructive
    assert not result.blocked
    assert result.reason == "Command verified safe"


def test_guardrail_blocks_destructive_shell_command():
    guard = DataLossGuardrail()
    result = guard.inspect("rm -rf /tmp/my_data")
    assert result.is_destructive
    assert result.blocked
    assert "destructive file deletion" in result.reason.lower()
    assert "/tmp/my_data" in result.impact


def test_guardrail_blocks_destructive_sql():
    guard = DataLossGuardrail()
    result = guard.inspect("DROP TABLE customers;")
    assert result.is_destructive
    assert result.blocked
    assert "destructive database operation" in result.reason.lower()


def test_guardrail_allows_with_explicit_approval_token():
    guard = DataLossGuardrail()
    command = "rm -rf .cache"
    token = guard.generate_approval_token(command)
    result = guard.verify_or_halt(command, approval_token=token)
    assert result.is_destructive
    assert not result.blocked
