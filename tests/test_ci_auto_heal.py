# tests/test_ci_auto_heal.py
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from scripts.ci_auto_heal import (
    FailureCategory,
    classify_ci_failure,
    find_affected_tests,
    format_ci_failure_memory,
    format_ci_stalled_memory,
    heal_local_pipeline,
)


class TestCIAutoHealClassification(unittest.TestCase):
    def test_classify_lint_format_failure(self):
        sample_log = """
Run ruff check personas/sakthai tests
personas/sakthai/agent/tools.py:12:1: E501 line too long
Found 1 error.
"""
        category, root_cause = classify_ci_failure(sample_log)
        self.assertEqual(category, FailureCategory.LINT_FORMAT)
        self.assertIn("Ruff", root_cause)

    def test_classify_typecheck_failure(self):
        sample_log = """
Run mypy personas/sakthai
personas/sakthai/agent/tools.py:45: error: Incompatible return value type (got "int", expected "str") [return-value]
Found 1 error in 1 file (checked 180 source files)
"""
        category, root_cause = classify_ci_failure(sample_log)
        self.assertEqual(category, FailureCategory.TYPE_CHECK)
        self.assertIn("mypy", root_cause)

    def test_classify_unit_test_failure(self):
        sample_log = """
=================================== FAILURES ===================================
____________________________ test_memory_store_read ____________________________
tests/test_memory_store.py:34: AssertionError: expected 5 facts but found 4
FAILED tests/test_memory_store.py::test_memory_store_read - AssertionError: expected 5 facts but found 4
"""
        category, root_cause = classify_ci_failure(sample_log)
        self.assertEqual(category, FailureCategory.UNIT_TEST_FAILURE)
        self.assertIn("test_memory_store", root_cause)

    def test_classify_transient_network_failure(self):
        sample_log = """
curl: (28) Failed to connect to huggingface.co port 443 after 120000 ms: Connection timed out
ReadTimeoutError: HTTPSConnectionPool(host='router.huggingface.co', port=443): Read timed out.
"""
        category, root_cause = classify_ci_failure(sample_log)
        self.assertEqual(category, FailureCategory.FLAKY_NETWORK_TIMEOUT)
        self.assertIn("Connection timed out", root_cause)

    def test_classify_security_bandit_failure(self):
        sample_log = """
Run bandit -c pyproject.toml -r personas/sakthai
>> Issue: [B105:hardcoded_password_string] Possible hardcoded password: 'secret123'
   Severity: Low   Confidence: Medium
   CWE: CWE-259 (https://cwe.mitre.org/data/definitions/259.html)
   Location: personas/sakthai/auth.py:42:12
"""
        category, root_cause = classify_ci_failure(sample_log)
        self.assertEqual(category, FailureCategory.SECURITY_BANDIT)
        self.assertIn("Bandit", root_cause)


class TestCIAutoHealMemoryFormatting(unittest.TestCase):
    def test_format_ci_failure_memory(self):
        mem = format_ci_failure_memory(
            task="fix-auth",
            run_id="12345678",
            failure_type="test",
            root_cause="AssertionError in test_auth",
            fix_applied="mock token validation",
            attempt=1,
            timestamp="2026-11-26T18:00:00Z",
        )
        self.assertIn("CI FAILURE: sakjules", mem)
        self.assertIn("task: fix-auth", mem)
        self.assertIn("run-id: 12345678", mem)
        self.assertIn("failure-type: test", mem)
        self.assertIn("attempt: 1", mem)

    def test_format_ci_stalled_memory(self):
        mem = format_ci_stalled_memory(
            task="fix-auth",
            run_id="12345678",
            attempts=3,
            timestamp="2026-11-26T18:00:00Z",
        )
        self.assertIn("CI STALLED: sakjules", mem)
        self.assertIn("task: fix-auth", mem)
        self.assertIn("attempts: 3", mem)


class TestTargetedTestDiscovery(unittest.TestCase):
    def test_find_affected_tests_from_tests_dir(self):
        changed = ["tests/test_ci_auto_heal.py", "README.md"]
        affected = find_affected_tests(changed)
        self.assertIn("tests/test_ci_auto_heal.py", affected)

    def test_find_affected_tests_from_src_dir(self):
        changed = ["personas/sakthai/agent/tools.py"]
        with patch("pathlib.Path.is_file", return_value=True):
            affected = find_affected_tests(changed)
            self.assertTrue(
                any("test_tools.py" in str(t) or "test_agent_tools.py" in str(t) for t in affected)
            )


class TestLocalPipelineHealing(unittest.TestCase):
    @patch("scripts.ci_auto_heal.run_command")
    def test_heal_local_pipeline_clean(self, mock_cmd):
        mock_cmd.return_value = MagicMock(returncode=0, stdout="", stderr="")
        res = heal_local_pipeline(run_tests=False, dry_run=False)
        self.assertTrue(res.success)
        self.assertTrue(res.format_passed)
        self.assertTrue(res.lint_passed)


if __name__ == "__main__":
    unittest.main()
