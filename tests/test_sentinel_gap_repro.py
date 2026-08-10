"""Regression tests for two Sentinel-reported guardrail gaps.

Both checks are *pre-execution* argument inspections: they read the tool call's
arguments and never touch the filesystem. Earlier versions of this file wrote a
real ``.env.test`` into the process CWD (the repo root under pytest) to "set up"
the second case. That was never required by the code under test, and it leaked
the file whenever the guardrail call raised before the cleanup block. The setup
is gone; the assertions are unchanged in intent and now also pin the reason
string, so a rule that stops firing is not masked by a different rule denying
for an unrelated cause.
"""

import unittest

from sakthai.agent.guardrails import (
    DEFAULT_POLICY,
    GuardrailAction,
    _block_dangerous_shell_commands,
)
from sakthai.agent.tools import tool_by_name
from sakthai.memory.store import MemoryStore


class TestGuardrailGap(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        self.run_command_tool = tool_by_name("run_command")
        self.read_file_tool = tool_by_name("read_file")

    def test_uniq_exfiltration_bypass(self):
        args = {"command": "uniq /etc/passwd"}
        # _block_dangerous_shell_commands is exercised directly here; the
        # DEFAULT_POLICY path is covered by test_read_file_env_bypass below.
        result = _block_dangerous_shell_commands(self.run_command_tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "uniq /etc/passwd should be blocked")
        self.assertIn("/etc/passwd", result.reason)

    def test_read_file_env_bypass(self):
        # No file is created: the sensitive-path check runs on the argument
        # string, so a non-existent path must be blocked just the same. That is
        # the property worth pinning — the guardrail must not depend on the
        # target existing, or a race could slip a read through.
        args = {"path": ".env.test"}
        result = DEFAULT_POLICY.check_pre_execution(self.read_file_tool, args, self.store)

        self.assertEqual(
            result.action, GuardrailAction.DENY, "read_file('.env.test') should be blocked"
        )
        self.assertIn("sensitive path", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
