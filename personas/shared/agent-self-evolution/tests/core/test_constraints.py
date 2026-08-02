"""Tests for constraint validators."""

from unittest.mock import MagicMock, patch

import pytest
from evolution.core.config import EvolutionConfig
from evolution.core.constraints import ConstraintValidator


@pytest.fixture
def validator():
    config = EvolutionConfig()
    return ConstraintValidator(config)


class TestSizeConstraints:
    def test_skill_under_limit(self, validator):
        result = validator._check_size("x" * 1000, "skill")
        assert result.passed

    def test_skill_over_limit(self, validator):
        result = validator._check_size("x" * 20_000, "skill")
        assert not result.passed
        assert "exceeded" in result.message

    def test_tool_description_under_limit(self, validator):
        result = validator._check_size("Search files by content", "tool_description")
        assert result.passed

    def test_tool_description_over_limit(self, validator):
        result = validator._check_size("x" * 600, "tool_description")
        assert not result.passed


class TestGrowthConstraints:
    def test_acceptable_growth(self, validator):
        baseline = "x" * 1000
        evolved = "x" * 1100  # 10% growth
        result = validator._check_growth(evolved, baseline, "skill")
        assert result.passed

    def test_excessive_growth(self, validator):
        baseline = "x" * 1000
        evolved = "x" * 1300  # 30% growth
        result = validator._check_growth(evolved, baseline, "skill")
        assert not result.passed

    def test_shrinkage_is_ok(self, validator):
        baseline = "x" * 1000
        evolved = "x" * 800  # 20% smaller
        result = validator._check_growth(evolved, baseline, "skill")
        assert result.passed


class TestNonEmpty:
    def test_non_empty_passes(self, validator):
        result = validator._check_non_empty("some content")
        assert result.passed

    def test_empty_fails(self, validator):
        result = validator._check_non_empty("")
        assert not result.passed

    def test_whitespace_only_fails(self, validator):
        result = validator._check_non_empty("   \n  ")
        assert not result.passed


class TestSkillStructure:
    def test_valid_skill(self, validator):
        skill = "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test\nContent here"
        result = validator._check_skill_structure(skill)
        assert result.passed

    def test_missing_frontmatter(self, validator):
        skill = "# Test\nContent without frontmatter"
        result = validator._check_skill_structure(skill)
        assert not result.passed

    def test_missing_name(self, validator):
        skill = "---\ndescription: A test skill\n---\n\n# Test"
        result = validator._check_skill_structure(skill)
        assert not result.passed

    def test_missing_description(self, validator):
        skill = "---\nname: test-skill\n---\n\n# Test"
        result = validator._check_skill_structure(skill)
        assert not result.passed


class TestValidateAll:
    def test_valid_skill_passes_all(self, validator):
        skill = "---\nname: test\ndescription: Test skill\n---\n\n# Procedure\n1. Do thing"
        results = validator.validate_all(skill, "skill")
        assert all(r.passed for r in results)

    def test_empty_skill_fails(self, validator):
        results = validator.validate_all("", "skill")
        failed = [r for r in results if not r.passed]
        assert len(failed) > 0


class TestRunTestSuite:
    @patch("subprocess.run")
    def test_run_test_suite_success(self, mock_run, validator):
        from pathlib import Path

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "16 passed in 0.07s"
        mock_run.return_value = mock_process

        result = validator.run_test_suite(Path("/mock/repo"))

        assert result.passed
        assert result.constraint_name == "test_suite"
        assert result.message == "All tests passed"
        assert result.details == "16 passed in 0.07s"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_test_suite_failure(self, mock_run, validator):
        from pathlib import Path

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = "FAILED tests/core/test_constraints.py::TestSizeConstraints::test_skill_over_limit\n1 failed, 15 passed in 0.08s"
        mock_run.return_value = mock_process

        result = validator.run_test_suite(Path("/mock/repo"))

        assert not result.passed
        assert result.constraint_name == "test_suite"
        assert result.message == "Test suite failed"
        assert "1 failed, 15 passed in 0.08s" in result.details
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_test_suite_timeout(self, mock_run, validator):
        import subprocess
        from pathlib import Path

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["pytest"], timeout=300)

        result = validator.run_test_suite(Path("/mock/repo"))

        assert not result.passed
        assert result.constraint_name == "test_suite"
        assert result.message == "Test suite timed out (300s)"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_test_suite_exception(self, mock_run, validator):
        from pathlib import Path

        mock_run.side_effect = RuntimeError("Something went wrong")

        result = validator.run_test_suite(Path("/mock/repo"))

        assert not result.passed
        assert result.constraint_name == "test_suite"
        assert "Failed to run tests: Something went wrong" in result.message
        mock_run.assert_called_once()
