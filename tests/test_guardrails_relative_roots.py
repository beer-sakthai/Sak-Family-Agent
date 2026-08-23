"""Regression tests for relative system-root path blocking (re-land of PR #380).

``_is_sensitive_path`` must treat a relative path whose first component names
a critical system root (``etc/passwd``) like its absolute counterpart, and
the ``.config``/``.npm``/``credentials`` additions to the sensitive
blocklists must be enforced.
"""

import unittest

from sakthai.agent.guardrails import (
    GuardrailAction,
    _block_dangerous_shell_commands,
    _is_sensitive_path,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


class TestRelativeSystemRoots(unittest.TestCase):
    def test_relative_critical_roots_are_sensitive(self):
        for path in (
            "etc/passwd",
            "Etc/passwd",
            "var/log/auth.log",
            "root/.profile",
            "proc/self/environ",
            "tmp/exfil.txt",
            "./etc/shadow",
        ):
            with self.subTest(path=path):
                self.assertTrue(_is_sensitive_path(path))

    def test_single_component_tmp_is_allowed(self):
        # Bare 'tmp' is a common safe local name (discovery tools, project
        # dirs); only subpaths are blocked.
        self.assertFalse(_is_sensitive_path("tmp"))
        self.assertTrue(_is_sensitive_path("tmp/x"))

    def test_ordinary_relative_paths_still_allowed(self):
        for path in ("src/main.py", "README.md", "etcetera/notes.txt"):
            with self.subTest(path=path):
                self.assertFalse(_is_sensitive_path(path))

    def test_new_sensitive_names(self):
        for path in (
            ".config/gh/hosts.yml",
            ".npm/_authToken",
            "credentials",
            "some/dir/credentials",
        ):
            with self.subTest(path=path):
                self.assertTrue(_is_sensitive_path(path))


class TestRelativeRootCommandBlocking(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore(":memory:")
        self.tool = Tool(
            name="run_command", description="run", input_schema={}, handler=lambda x, y: ""
        )

    def test_cat_relative_etc_passwd_blocked(self):
        args = {"command": "cat etc/passwd"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY)

    def test_cat_config_token_blocked(self):
        args = {"command": "cat .config/gh/hosts.yml"}
        result = _block_dangerous_shell_commands(self.tool, args, self.store)
        self.assertEqual(result.action, GuardrailAction.DENY)


if __name__ == "__main__":
    unittest.main()
