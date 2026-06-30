"""Tests for constraint validators."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from evolution.core.config import EvolutionConfig
from evolution.core.constraints import ConstraintValidator


@pytest.fixture
def validator() -> ConstraintValidator:
    config = EvolutionConfig()
    return ConstraintValidator(config)


class TestSizeConstraints:
    def test_skill_under_limit(self, validator: ConstraintValidator) -> None:
        result = validator._check_size("x" * 1000, "skill")
        assert result.passed

    def test_skill_over_limit(self, validator: ConstraintValidator) -> None:
        result = validator._check_size("x" * 20_000, "skill")
        assert not result.passed
        assert "exceeded" in result.message

    def test_tool_description_under_limit(self, validator: ConstraintValidator) -> None:
        result = validator._check_size("Search files by content", "tool_description")
        assert result.passed

    def test_tool_description_over_limit(self, validator: ConstraintValidator) -> None:
        result = validator._check_size("x" * 600, "tool_description")
        assert not result.passed

    def test_param_description_under_limit(self, validator: ConstraintValidator) -> None:
        result = validator._check_size("x" * 100, "param_description")
        assert result.passed

    def test_param_description_over_limit(self, validator: ConstraintValidator) -> None:
        result = validator._check_size("x" * 300, "param_description")
        assert not result.passed

    def test_unknown_type_uses_skill_default(self, validator: ConstraintValidator) -> None:
        # Default is max_skill_size (15000)
        result = validator._check_size("x" * 1000, "unknown_type")
        assert result.passed
        result = validator._check_size("x" * 16000, "unknown_type")
        assert not result.passed


class TestGrowthConstraints:
    def test_acceptable_growth(self, validator: ConstraintValidator) -> None:
        baseline = "x" * 1000
        evolved = "x" * 1100  # 10% growth
        result = validator._check_growth(evolved, baseline, "skill")
        assert result.passed

    def test_excessive_growth(self, validator: ConstraintValidator) -> None:
        baseline = "x" * 1000
        evolved = "x" * 1300  # 30% growth
        result = validator._check_growth(evolved, baseline, "skill")
        assert not result.passed

    def test_shrinkage_is_ok(self, validator: ConstraintValidator) -> None:
        baseline = "x" * 1000
        evolved = "x" * 800  # 20% smaller
        result = validator._check_growth(evolved, baseline, "skill")
        assert result.passed


class TestNonEmpty:
    def test_non_empty_passes(self, validator: ConstraintValidator) -> None:
        result = validator._check_non_empty("some content")
        assert result.passed

    def test_empty_fails(self, validator: ConstraintValidator) -> None:
        result = validator._check_non_empty("")
        assert not result.passed

    def test_whitespace_only_fails(self, validator: ConstraintValidator) -> None:
        result = validator._check_non_empty("   \n  ")
        assert not result.passed


class TestSkillStructure:
    def test_valid_skill(self, validator: ConstraintValidator) -> None:
        skill = "---\nname: test-skill\ndescription: A test skill\n---\n\n# Test\nContent here"
        result = validator._check_skill_structure(skill)
        assert result.passed

    def test_missing_frontmatter(self, validator: ConstraintValidator) -> None:
        skill = "# Test\nContent without frontmatter"
        result = validator._check_skill_structure(skill)
        assert not result.passed

    def test_missing_name(self, validator: ConstraintValidator) -> None:
        skill = "---\ndescription: A test skill\n---\n\n# Test"
        result = validator._check_skill_structure(skill)
        assert not result.passed

    def test_missing_description(self, validator: ConstraintValidator) -> None:
        skill = "---\nname: test-skill\n---\n\n# Test"
        result = validator._check_skill_structure(skill)
        assert not result.passed


class TestValidateAll:
    def test_valid_skill_passes_all(self, validator: ConstraintValidator) -> None:
        skill = "---\nname: test\ndescription: Test skill\n---\n\n# Procedure\n1. Do thing"
        results = validator.validate_all(skill, "skill")
        assert all(r.passed for r in results)
        assert any(r.constraint_name == "skill_structure" for r in results)

    def test_non_skill_skips_structure_check(self, validator: ConstraintValidator) -> None:
        results = validator.validate_all("some text", "tool_description")
        assert not any(r.constraint_name == "skill_structure" for r in results)

    def test_empty_skill_fails(self, validator: ConstraintValidator) -> None:
        results = validator.validate_all("", "skill")
        failed = [r for r in results if not r.passed]
        assert len(failed) > 0

    def test_includes_growth_when_baseline_provided(self, validator: ConstraintValidator) -> None:
        baseline = "original"
        evolved = "updated"
        results = validator.validate_all(evolved, "skill", baseline_text=baseline)
        assert any(r.constraint_name == "growth_limit" for r in results)


class TestRunTestSuite:
    def test_success(self, validator: ConstraintValidator) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "16 passed in 0.05s"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = validator.run_test_suite(Path("/tmp/repo"))
            assert result.passed
            assert "All tests passed" in result.message
            assert result.details is not None
            assert "16 passed" in result.details
            mock_run.assert_called_once()

    def test_failure(self, validator: ConstraintValidator) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Failing test output line 1\nline 2\nline 3\nline 4\nline 5"

        with patch("subprocess.run", return_value=mock_result):
            result = validator.run_test_suite(Path("/tmp/repo"))
            assert not result.passed
            assert "Test suite failed" in result.message
            assert result.details is not None
            assert "line 5" in result.details

    def test_timeout(self, validator: ConstraintValidator) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["cmd"], 300)):
            result = validator.run_test_suite(Path("/tmp/repo"))
            assert not result.passed
            assert "timed out" in result.message

    def test_generic_exception(self, validator: ConstraintValidator) -> None:
        with patch("subprocess.run", side_effect=RuntimeError("Unexpected error")):
            result = validator.run_test_suite(Path("/tmp/repo"))
            assert not result.passed
            assert "Failed to run tests" in result.message
            assert "Unexpected error" in result.message
