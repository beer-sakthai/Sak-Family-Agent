import unittest

from sakthai.agent.guardrails import (
    GuardrailAction,
    _block_dangerous_shell_commands,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


class TestGuardrailsBypass(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        self.tool = Tool(
            name="run_command", description="run", input_schema={}, handler=lambda x, y: ""
        )

    def test_base64_exfiltration_bypass(self):
        # base64 is not in dangerous_binaries currently
        args = {"command": "base64 /etc/shadow"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(
            result.action, GuardrailAction.DENY, "base64 /etc/shadow should be blocked"
        )

    def test_python_interpreter_bypass(self):
        # python is in dangerous_binaries, but _is_sensitive_path might not catch it in a script string
        args = {"command": "python3 -c \"print(open('/etc/shadow').read())\""}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(
            result.action,
            GuardrailAction.DENY,
            "python script reading sensitive file should be blocked",
        )

    def test_globbing_bypass(self):
        # Using globbing to bypass path matching
        args = {"command": "bash -c 'cat /et??/passwd'"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(
            result.action, GuardrailAction.DENY, "globbing to sensitive path should be blocked"
        )

    def test_env_bypass(self):
        # env rm -rf /etc
        args = {"command": "env rm -rf /etc"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "env rm -rf /etc should be blocked")

    def test_env_with_vars_bypass(self):
        # env FOO=BAR rm -rf /etc
        args = {"command": "env FOO=BAR rm -rf /etc"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(
            result.action, GuardrailAction.DENY, "env with vars rm -rf /etc should be blocked"
        )

    def test_rsync_bypass(self):
        # rsync /etc/shadow ...
        args = {"command": "rsync /etc/shadow /tmp/exfil"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "rsync /etc/shadow should be blocked")

    def test_tar_bypass(self):
        # tar -cf out.tar /etc/shadow
        args = {"command": "tar -cf /tmp/out.tar /etc/shadow"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(
            result.action, GuardrailAction.DENY, "tar reading /etc/shadow should be blocked"
        )

    def test_tar_attached_flag_bypass(self):
        # tar -xf/etc/shadow
        args = {"command": "tar -xf/etc/shadow"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(
            result.action, GuardrailAction.DENY, "tar -xf/etc/shadow should be blocked"
        )

    def test_bash_file_bypass(self):
        # bash /etc/shadow
        args = {"command": "bash /etc/shadow"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "bash /etc/shadow should be blocked")


if __name__ == "__main__":
    unittest.main()
