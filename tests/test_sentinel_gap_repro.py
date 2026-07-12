import unittest
import os
from sakthai.agent.guardrails import GuardrailAction, _block_dangerous_shell_commands, DEFAULT_POLICY
from sakthai.agent.tools import Tool, tool_by_name
from sakthai.memory.store import MemoryStore

class TestGuardrailGap(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        self.run_command_tool = tool_by_name("run_command")
        self.read_file_tool = tool_by_name("read_file")

    def test_uniq_exfiltration_bypass(self):
        args = {"command": "uniq /etc/passwd"}
        # Currently _block_dangerous_shell_commands is called directly in some tests,
        # but DEFAULT_POLICY is what's used in practice.
        result = _block_dangerous_shell_commands(self.run_command_tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "uniq /etc/passwd should be blocked")

    def test_read_file_env_bypass(self):
        # Create a dummy .env file
        with open(".env.test", "w") as f:
            f.write("SECRET=123")

        # Check if DEFAULT_POLICY blocks it.
        # Currently it probably DOES NOT because _block_sensitive_path_args is missing.
        args = {"path": ".env.test"}
        result = DEFAULT_POLICY.check_pre_execution(self.read_file_tool, args, self.store)

        try:
            self.assertEqual(result.action, GuardrailAction.DENY, "read_file('.env.test') should be blocked")
        finally:
            if os.path.exists(".env.test"):
                os.remove(".env.test")

if __name__ == "__main__":
    unittest.main()
