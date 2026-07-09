import unittest
from pathlib import Path
from personas.sakthai.sakthai.agent.guardrails import _block_dangerous_shell_commands, GuardrailAction
from personas.sakthai.sakthai.agent.tools import Tool
from personas.sakthai.sakthai.memory.store import MemoryStore

class TestGuardrailsBypass(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        self.tool = Tool(name="run_command", description="run", input_schema={}, handler=lambda x, y: "")

    def test_base64_exfiltration_bypass(self):
        # base64 is not in dangerous_binaries currently
        args = {"command": "base64 /etc/shadow"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "base64 /etc/shadow should be blocked")

    def test_python_interpreter_bypass(self):
        # python is in dangerous_binaries, but _is_sensitive_path might not catch it in a script string
        args = {"command": "python3 -c \"print(open('/etc/shadow').read())\""}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "python script reading sensitive file should be blocked")

    def test_globbing_bypass(self):
        # Using globbing to bypass path matching
        args = {"command": "bash -c 'cat /et??/passwd'"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY, "globbing to sensitive path should be blocked")

if __name__ == "__main__":
    unittest.main()
