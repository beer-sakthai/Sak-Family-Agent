"""Pytest failure trace parser."""

from __future__ import annotations

import re

from .finding import Finding


class TestFailureScanner:
    """Parses pytest execution output and extracts test failures."""

    @staticmethod
    def parse_pytest(output: str) -> list[Finding]:
        """Parse pytest stdout/stderr to extract failing tests and traceback locations."""
        findings: list[Finding] = []
        if not output:
            return findings

        # Look for FAILED test lines: FAILED tests/test_foo.py::test_bar - Error...
        failed_lines = re.findall(
            r"FAILED\s+([^\s:]+)(?:::([^\s\-]+))?\s*(?:-\s*(.*))?",
            output,
        )

        for idx, match in enumerate(failed_lines):
            file_path = match[0]
            test_name = match[1] or ""
            error_msg = match[2] or "Test assertion failed"

            # Try to find line number in traceback if present
            line_match = re.search(rf"{re.escape(file_path)}:(\d+):", output)
            line_num = int(line_match.group(1)) if line_match else None

            desc = f"Test failed: {test_name} - {error_msg}" if test_name else error_msg

            findings.append(
                Finding(
                    id=f"pytest-{idx}-{test_name or 'failure'}",
                    source="test_failure",
                    file_path=file_path,
                    line_number=line_num,
                    rule_id=test_name or "AssertionError",
                    description=desc.strip(),
                    severity="high",
                    raw_payload={"trace": output[:500]},
                )
            )

        return findings
