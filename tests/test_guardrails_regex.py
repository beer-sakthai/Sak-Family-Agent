from __future__ import annotations

from typing import Any

import pytest

from sakthai.agent.guardrails import GuardrailAction, _block_output_with_secrets
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


@pytest.fixture
def dummy_tool() -> Tool:
    return Tool("dummy", "desc", {}, lambda a, s: "")


@pytest.fixture
def dummy_store() -> Any:
    import unittest.mock

    return unittest.mock.MagicMock(spec=MemoryStore)


@pytest.mark.parametrize(
    "secret",
    [
        "sk_12345678901234567890",
        "sk-ant-api03-1234567890123456789012345",
        "AIzaSyA1234567890123456789012345678901",
        "ghp_TESTING_SECRET_DO_NOT_FLAG",
        "hf_1234567890123456789012345678901234",
        "123456789:ABCdefGhIJKlmNoPQRsTUVwxYZabcde1234",
    ],
)
def test_secret_detection_regex_blocks_secrets(
    dummy_tool: Tool, secret: str, dummy_store: MemoryStore
) -> None:
    result = _block_output_with_secrets(dummy_tool, {}, f"Error: {secret}", False, dummy_store)
    assert result.action == GuardrailAction.DENY, f"Secret {secret} was not blocked"


def test_secret_detection_regex_allows_innocent_text(
    dummy_tool: Tool, dummy_store: MemoryStore
) -> None:
    text = "Total tokens used: 12345. Request ID: req_abc123."
    result = _block_output_with_secrets(dummy_tool, {}, text, False, dummy_store)
    assert result.action == GuardrailAction.ALLOW


def test_block_output_with_pem_private_key(dummy_tool: Tool, dummy_store: MemoryStore) -> None:
    # Construct a PEM Private Key with concatenation to avoid any scanner false positives
    prefix = "-----BEGIN " + "RSA PRIVATE KEY-----"
    suffix = "-----END " + "RSA PRIVATE KEY-----"
    text = f"Some data here\n{prefix}\nMIIEowIBAAKCAQEAr7...\n{suffix}\nmore data"
    result = _block_output_with_secrets(dummy_tool, {}, text, False, dummy_store)
    assert result.action == GuardrailAction.DENY
    assert "private key block" in result.reason.lower()


def test_block_output_with_env_and_extra_secrets(
    dummy_tool: Tool, dummy_store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1. Test exact active environment variable secret matching (even if it does not match standard patterns)
    secret_val = "custom-" + "secret-key-xyz-123-abc"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret_val)

    text = f"The process failed with value: {secret_val}"
    result = _block_output_with_secrets(dummy_tool, {}, text, False, dummy_store)
    assert result.action == GuardrailAction.DENY
    assert "appears to contain a secret" in result.reason.lower()

    # 2. Test registered extra secrets (via register_secret)
    from sakthai.config import _EXTRA_SECRETS, register_secret

    extra_secret = "extra-" + "secret-token-value"
    register_secret(extra_secret)
    try:
        text2 = f"This is an extra secret: {extra_secret}"
        result2 = _block_output_with_secrets(dummy_tool, {}, text2, False, dummy_store)
        assert result2.action == GuardrailAction.DENY
        assert "appears to contain a secret" in result2.reason.lower()
    finally:
        _EXTRA_SECRETS.discard(extra_secret)
