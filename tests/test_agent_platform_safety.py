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


def test_guardrail_blocks_git_reset_and_clean():
    guard = DataLossGuardrail()
    r1 = guard.inspect("git reset --hard HEAD~1")
    assert r1.is_destructive
    assert r1.blocked
    assert "reset" in r1.reason.lower()

    r2 = guard.inspect("git clean -fd")
    assert r2.is_destructive
    assert r2.blocked
    assert "untracked" in r2.reason.lower()


def test_guardrail_blocks_system_and_infra_destruction():
    guard = DataLossGuardrail()
    r1 = guard.inspect("mkfs.ext4 /dev/nvme0n1")
    assert r1.is_destructive
    assert r1.blocked

    r2 = guard.inspect("dd if=/dev/zero of=/dev/sda bs=1M")
    assert r2.is_destructive
    assert r2.blocked

    r3 = guard.inspect("terraform destroy -auto-approve")
    assert r3.is_destructive
    assert r3.blocked

    r4 = guard.inspect("kubectl delete namespace staging")
    assert r4.is_destructive
    assert r4.blocked
