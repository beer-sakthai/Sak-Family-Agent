from __future__ import annotations

import pytest

from sakthai.agent.guardrails import GuardrailAction, _block_output_with_secrets
from sakthai.agent.tools import Tool


@pytest.fixture
def dummy_tool() -> Tool:
    return Tool("dummy", "desc", {}, lambda a, s: "")


@pytest.mark.parametrize(
    "secret",
    [
        "sk_12345678901234567890",
        "sk-ant-api03-1234567890123456789012345",
        "AIzaSyA1234567890123456789012345678901",
        "ghp_TESTING_SECRET_DO_NOT_FLAG",
    ],
)
def test_secret_detection_regex_blocks_secrets(dummy_tool: Tool, secret: str) -> None:
    result = _block_output_with_secrets(dummy_tool, {}, f"Error: {secret}", False, None)
    assert result.action == GuardrailAction.DENY, f"Secret {secret} was not blocked"


def test_secret_detection_regex_allows_innocent_text(dummy_tool: Tool) -> None:
    text = "Total tokens used: 12345. Request ID: req_abc123."
    result = _block_output_with_secrets(dummy_tool, {}, text, False, None)
    assert result.action == GuardrailAction.ALLOW
