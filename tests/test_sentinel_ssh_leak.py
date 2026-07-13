import unittest

from sakthai.agent.guardrails import _is_sensitive_path


class TestSSHLeakRepro(unittest.TestCase):
    def test_relative_sensitive_paths(self):
        # These are currently NOT blocked if they don't start with / or ~ or contain ..
        sensitive_relative_paths = [
            ".ssh/id_rsa",
            ".ssh/config",
            ".aws/credentials",
            ".aws/config",
            ".bash_history",
            ".zsh_history",
            ".python_history",
            ".netrc",
            ".npmrc",
            ".pypirc",
        ]
        for path in sensitive_relative_paths:
            with self.subTest(path=path):
                self.assertTrue(
                    _is_sensitive_path(path), f"Relative path {path!r} should be blocked"
                )

    def test_absolute_sensitive_user_paths(self):
        # This is already blocked by _CRITICAL_ROOTS check if it starts with /home
        self.assertTrue(_is_sensitive_path("/home/user/.ssh/id_rsa"))

        # But this might not be if /root is not in _CRITICAL_ROOTS or if it's just /.ssh
        self.assertTrue(_is_sensitive_path("/.ssh/id_rsa"))


if __name__ == "__main__":
    unittest.main()
