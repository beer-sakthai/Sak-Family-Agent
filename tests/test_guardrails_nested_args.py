"""Unit tests for nested tool argument path validation in guardrails.

This file verifies that `_block_sensitive_path_args` correctly scans
nested data structures (lists, dicts, tuples, sets) recursively for
sensitive paths.
"""

from __future__ import annotations

import unittest

from sakthai.agent.guardrails import DEFAULT_POLICY, GuardrailAction
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


class TestGuardrailsNestedArgs(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore(":memory:")
        self.dummy_tool = Tool(
            name="dummy_tool",
            description="A dummy tool that takes any argument structure.",
            input_schema={},
            handler=lambda x, y: "success",
        )

    def test_safe_arguments_allowed(self) -> None:
        """Verify that benign nested arguments are allowed."""
        safe_args = {
            "configs": ["/safe/path1", "/safe/path2"],
            "metadata": {
                "owner": "test",
                "paths": {"input": "input.txt", "output": "output.txt"},
            },
            "tags": ("tag1", "tag2"),
            "sets": {"item1", "item2"},
        }
        result = DEFAULT_POLICY.check_pre_execution(self.dummy_tool, safe_args, self.store)
        self.assertEqual(result.action, GuardrailAction.ALLOW)

    def test_nested_list_blocked(self) -> None:
        """Verify that a sensitive path inside a nested list is blocked."""
        bad_args = {
            "configs": ["/safe/path1", "/etc/passwd"],
        }
        result = DEFAULT_POLICY.check_pre_execution(self.dummy_tool, bad_args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn("Access to sensitive path", result.reason or "")
        self.assertIn("/etc/passwd", result.reason or "")

    def test_nested_dict_blocked(self) -> None:
        """Verify that a sensitive path inside a nested dictionary value or key is blocked."""
        bad_args_val = {
            "metadata": {
                "paths": {"input": "input.txt", "output": ".env"},
            }
        }
        result = DEFAULT_POLICY.check_pre_execution(self.dummy_tool, bad_args_val, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn(".env", result.reason or "")

        bad_args_key = {
            "metadata": {
                ".env": "some_value",
            }
        }
        result = DEFAULT_POLICY.check_pre_execution(self.dummy_tool, bad_args_key, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn(".env", result.reason or "")

    def test_nested_tuple_and_set_blocked(self) -> None:
        """Verify that sensitive paths in tuples or sets are blocked."""
        bad_args_tuple = {
            "tags": ("tag1", "/etc/shadow"),
        }
        result = DEFAULT_POLICY.check_pre_execution(self.dummy_tool, bad_args_tuple, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn("/etc/shadow", result.reason or "")

        bad_args_set = {
            "sets": {"item1", "memory.db"},
        }
        result = DEFAULT_POLICY.check_pre_execution(self.dummy_tool, bad_args_set, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY)
        self.assertIn("memory.db", result.reason or "")


if __name__ == "__main__":
    unittest.main()
