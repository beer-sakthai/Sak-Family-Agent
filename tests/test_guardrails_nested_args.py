from __future__ import annotations

import pytest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore(":memory:")


@pytest.fixture
def test_tool() -> Tool:
    return Tool("test_tool", "A dummy tool for testing nested args", {}, lambda _a, _s: "ok")


def test_nested_list_sensitive(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that a list containing a sensitive path is blocked."""
    args = {"files": ["safe.txt", "/etc/shadow", "other.txt"]}
    result = DEFAULT_POLICY.check_pre_execution(test_tool, args, store)
    assert result.action == GuardrailAction.DENY
    assert "Access to sensitive path" in result.reason
    assert "/etc/shadow" in result.reason


def test_nested_dict_sensitive(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that a dict containing a sensitive path in its values or keys is blocked."""
    args_val = {"config": {"path": "/etc/passwd"}}
    result_val = DEFAULT_POLICY.check_pre_execution(test_tool, args_val, store)
    assert result_val.action == GuardrailAction.DENY
    assert "/etc/passwd" in result_val.reason

    args_key = {"config": {"/etc/passwd": "value"}}
    result_key = DEFAULT_POLICY.check_pre_execution(test_tool, args_key, store)
    assert result_key.action == GuardrailAction.DENY
    assert "/etc/passwd" in result_key.reason


def test_json_serialized_dict_sensitive(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that a JSON-serialized dict string containing a sensitive path is blocked."""
    args = {"config_str": '{"path": "/etc/shadow", "verbose": true}'}
    result = DEFAULT_POLICY.check_pre_execution(test_tool, args, store)
    assert result.action == GuardrailAction.DENY
    assert "Access to sensitive path" in result.reason
    assert "/etc/shadow" in result.reason


def test_json_serialized_list_sensitive(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that a JSON-serialized list string containing a sensitive path is blocked."""
    args = {"paths_str": '["safe_path.txt", "/etc/passwd"]'}
    result = DEFAULT_POLICY.check_pre_execution(test_tool, args, store)
    assert result.action == GuardrailAction.DENY
    assert "Access to sensitive path" in result.reason
    assert "/etc/passwd" in result.reason


def test_json_serialized_safe(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that safe JSON-serialized strings are allowed."""
    args = {"config_str": '{"path": "safe.txt", "verbose": false}'}
    result = DEFAULT_POLICY.check_pre_execution(test_tool, args, store)
    assert result.action == GuardrailAction.ALLOW


def test_malformed_json_treated_as_string(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that malformed JSON is treated as a normal string and checked properly."""
    # This malformed JSON contains a sensitive path, so standard string checking should still catch it.
    args = {"config_str": '{"path": "/etc/shadow", "invalid_json": '}
    result = DEFAULT_POLICY.check_pre_execution(test_tool, args, store)
    # Even if JSON parsing fails, the string itself contains "/etc/shadow" which matches _is_sensitive_path
    # due to split-delimiting or normpath logic.
    assert result.action == GuardrailAction.DENY
    assert "/etc/shadow" in result.reason


def test_deeply_nested_json(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that nested JSON within dictionaries or lists is recursively checked."""
    args = {
        "outer": {"inner_json_string": '{"deep_list": ["safe.txt", {"target": "/etc/shadow"}]}'}
    }
    result = DEFAULT_POLICY.check_pre_execution(test_tool, args, store)
    assert result.action == GuardrailAction.DENY
    assert "/etc/shadow" in result.reason


def test_quoted_sensitive_path(test_tool: Tool, store: MemoryStore) -> None:
    """Verify that a sensitive path wrapped in quotes is successfully stripped and blocked."""
    args = {"file_path": '"/etc/shadow"'}
    result = DEFAULT_POLICY.check_pre_execution(test_tool, args, store)
    assert result.action == GuardrailAction.DENY
    assert "/etc/shadow" in result.reason

    args_single = {"file_path": "'/etc/shadow'"}
    result_single = DEFAULT_POLICY.check_pre_execution(test_tool, args_single, store)
    assert result_single.action == GuardrailAction.DENY
    assert "/etc/shadow" in result_single.reason
