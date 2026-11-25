"""Tests for PatchFlow generator and unified diff creation."""

from __future__ import annotations

from services.patchflow.src.generator import PatchGenerator
from services.patchflow.src.scanners.finding import Finding


class TestPatchGenerator:
    def test_generate_diff(self):
        orig = "def hello():\n    return 'world'\n"
        patched = "def hello():\n    return 'sakthai'\n"
        diff = PatchGenerator.generate_diff(orig, patched, "hello.py")
        assert "--- a/hello.py" in diff
        assert "+++ b/hello.py" in diff
        assert "-    return 'world'" in diff
        assert "+    return 'sakthai'" in diff

    def test_create_candidate(self):
        finding = Finding(
            id="f-1",
            source="linter",
            file_path="src/main.py",
            rule_id="F401",
        )
        orig = "import os\nimport sys\n"
        patched = "import sys\n"
        cand = PatchGenerator.create_candidate(
            finding=finding,
            original_content=orig,
            patched_content=patched,
            explanation="Remove unused os import",
        )
        assert cand.finding_id == "f-1"
        assert cand.target_file == "src/main.py"
        assert "-import os" in cand.unified_diff
        assert cand.explanation == "Remove unused os import"
