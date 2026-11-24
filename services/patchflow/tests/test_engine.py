"""Tests for PatchFlowEngine and PREmitter under SakJules protocol."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from services.patchflow.src.engine import PatchFlowEngine
from services.patchflow.src.pr_emitter import PREmitter
from services.patchflow.src.scanners.finding import Finding


class TestPatchFlowEngine:
    def test_pr_emitter_sakjules_conventions(self):
        finding = Finding(
            id="vuln-01",
            source="dependabot",
            file_path="pyproject.toml",
            rule_id="GHSA-test-1234",
            description="Vulnerable dependency",
            severity="high",
        )
        from services.patchflow.src.generator import PatchCandidate

        cand = PatchCandidate(
            finding_id="vuln-01",
            target_file="pyproject.toml",
            original_content="",
            patched_content="",
            explanation="Bump version to secure release",
            unified_diff="",
        )
        payload = PREmitter.emit_pr_payload(finding, cand)
        assert payload.title == "fix(patchflow): remediate dependabot finding GHSA-test-1234"
        assert payload.auto_merge_allowed is False
        assert "SakJules · Master of Automation & CI/CD." in payload.body
        assert "Manual Merge Required" in payload.body

    def test_engine_end_to_end_success(self):
        with TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            target_file = repo_dir / "calc.py"
            target_file.write_text("def add(a, b): return a - b\n", encoding="utf-8")

            engine = PatchFlowEngine(repo_root=repo_dir)

            finding = Finding(
                id="pytest-01",
                source="test_failure",
                file_path="calc.py",
                rule_id="test_add",
                description="Expected a + b but got a - b",
                severity="high",
            )

            def synthesizer(f: Finding, orig: str) -> tuple[str, str]:
                return orig.replace("return a - b", "return a + b"), "Fix arithmetic sign"

            res = engine.process_finding(
                finding=finding,
                patch_synthesizer=synthesizer,
                test_runner=lambda: True,
            )

            assert res.success is True
            assert res.pr_payload is not None
            assert "fix(patchflow)" in res.pr_payload.title
            assert target_file.read_text(encoding="utf-8") == "def add(a, b): return a + b\n"
