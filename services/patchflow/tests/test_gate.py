"""Tests for AntiGamingGate in PatchFlow."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from evolution.core.config import EvolutionConfig

from sakthai.memory.session_store import FileSessionStore
from services.patchflow.src.gate import AntiGamingGate
from services.patchflow.src.generator import PatchCandidate


class TestAntiGamingGate:
    def test_gate_human_approval_rejection(self):
        gate = AntiGamingGate()
        cand = PatchCandidate(
            finding_id="f-1",
            target_file="test.py",
            original_content="",
            patched_content="",
            explanation="test",
            unified_diff="",
        )
        verdict = gate.verify_patch(
            candidate=cand,
            repo_root=Path("."),
            breaking_changes=["Deleted tool: 'critical_tool'"],
            is_human_approved=False,
        )
        assert verdict.passed is False
        assert "Human Approval Gate" in verdict.reason

    def test_gate_token_ceiling_rejection(self):
        cfg = EvolutionConfig(max_tool_desc_tokens=5)
        gate = AntiGamingGate(config=cfg)
        cand = PatchCandidate(
            finding_id="f-2",
            target_file="skills/tool.py",
            original_content="",
            patched_content="[TOOL test]\ndescription: This description definitely has more than five words and tokens\nparameters:\n  x: val\n",
            explanation="Token gaming attempt",
            unified_diff="",
        )
        verdict = gate.verify_patch(
            candidate=cand,
            repo_root=Path("."),
            breaking_changes=[],
            is_human_approved=True,
        )
        assert verdict.passed is False
        assert "Token Ceiling" in verdict.reason

    def test_gate_successful_and_regression_rollback(self):
        with TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            target = repo_dir / "app.py"
            target.write_text("def run():\n    return False\n", encoding="utf-8")

            session_store = FileSessionStore(checkpoints_dir=repo_dir / "checkpoints")
            gate = AntiGamingGate(session_store=session_store)

            cand = PatchCandidate(
                finding_id="f-success",
                target_file="app.py",
                original_content="def run():\n    return False\n",
                patched_content="def run():\n    return True\n",
                explanation="Fix boolean return",
                unified_diff="",
            )

            # Success case
            verdict_ok = gate.verify_patch(
                candidate=cand,
                repo_root=repo_dir,
                test_runner=lambda: True,
            )
            assert verdict_ok.passed is True
            assert target.read_text(encoding="utf-8") == "def run():\n    return True\n"

            # Failure / regression case triggers rollback!
            cand_bad = PatchCandidate(
                finding_id="f-regress",
                target_file="app.py",
                original_content="def run():\n    return True\n",
                patched_content="def run():\n    raise RuntimeError('boom')\n",
                explanation="Buggy edit",
                unified_diff="",
            )
            verdict_fail = gate.verify_patch(
                candidate=cand_bad,
                repo_root=repo_dir,
                test_runner=lambda: False,  # Simulated test suite failure
            )
            assert verdict_fail.passed is False
            assert verdict_fail.rolled_back is True
            # Verified file content was rolled back to original!
            assert target.read_text(encoding="utf-8") == "def run():\n    return True\n"
