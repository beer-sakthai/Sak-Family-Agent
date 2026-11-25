"""Tests for PatchFlow scanners (Dependabot, Linter, TestFailure)."""

from __future__ import annotations

from services.patchflow.src.scanners.dependabot import DependabotScanner
from services.patchflow.src.scanners.linter import LinterScanner
from services.patchflow.src.scanners.test_failure import TestFailureScanner


class TestDependabotScanner:
    def test_parse_dependabot_json(self):
        sample = [
            {
                "number": 12,
                "dependency": {
                    "package": {"name": "aiohttp"},
                    "manifest_path": "pyproject.toml",
                },
                "security_advisory": {
                    "ghsa_id": "GHSA-xxxx-yyyy",
                    "cve_id": "CVE-2024-12345",
                    "summary": "Request smuggling vulnerability",
                    "severity": "high",
                },
            }
        ]
        findings = DependabotScanner.parse_alerts(sample)
        assert len(findings) == 1
        f = findings[0]
        assert f.source == "dependabot"
        assert f.file_path == "pyproject.toml"
        assert "CVE-2024-12345" in f.rule_id
        assert f.severity == "high"
        assert "aiohttp" in f.description


class TestLinterScanner:
    def test_parse_ruff(self):
        sample = [
            {
                "code": "F401",
                "message": "os imported but unused",
                "filename": "personas/sakthai/agent/eval.py",
                "location": {"row": 15, "column": 1},
            }
        ]
        findings = LinterScanner.parse_ruff(sample)
        assert len(findings) == 1
        assert findings[0].rule_id == "F401"
        assert findings[0].line_number == 15
        assert findings[0].source == "linter"

    def test_parse_bandit(self):
        sample = {
            "results": [
                {
                    "test_id": "B101",
                    "issue_text": "Use of assert detected",
                    "filename": "personas/sakthai/cli/status.py",
                    "line_number": 42,
                    "issue_severity": "LOW",
                }
            ]
        }
        findings = LinterScanner.parse_bandit(sample)
        assert len(findings) == 1
        assert findings[0].rule_id == "B101"
        assert findings[0].severity == "low"


class TestTestFailureScanner:
    def test_parse_pytest_trace(self):
        trace = (
            "FAILED tests/test_agent_eval.py::test_eval_metrics - AssertionError: expected 1.0 but got 0.0\n"
            "tests/test_agent_eval.py:88: in test_eval_metrics\n"
        )
        findings = TestFailureScanner.parse_pytest(trace)
        assert len(findings) == 1
        assert findings[0].file_path == "tests/test_agent_eval.py"
        assert findings[0].line_number == 88
        assert findings[0].source == "test_failure"
        assert "test_eval_metrics" in findings[0].description
