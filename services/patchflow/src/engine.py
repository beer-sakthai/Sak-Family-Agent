"""PatchFlow Engine orchestrating the automated remediation lifecycle."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .gate import AntiGamingGate, GateVerdict
from .generator import PatchCandidate, PatchGenerator
from .pr_emitter import PREmitter, PullRequestPayload
from .scanners.finding import Finding

logger = logging.getLogger(__name__)


@dataclass
class PatchExecutionResult:
    """Outcome of an end-to-end patching run on a finding."""

    finding: Finding
    candidate: PatchCandidate | None
    verdict: GateVerdict | None
    pr_payload: PullRequestPayload | None
    success: bool
    message: str


class PatchFlowEngine:
    """Automated patching engine coordinating detection, patching, gating, and PR creation."""

    def __init__(
        self,
        repo_root: Path | str,
        gate: AntiGamingGate | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.gate = gate or AntiGamingGate()

    def process_finding(
        self,
        finding: Finding,
        patch_synthesizer: Callable[[Finding, str], tuple[str, str]],
        test_runner: Callable[[], bool] | None = None,
        is_human_approved: bool = False,
        breaking_changes: list[str] | None = None,
    ) -> PatchExecutionResult:
        """Remediate a single finding through synthesis, anti-gaming gating, and PR preparation."""
        target_path = self.repo_root / finding.file_path
        if not target_path.is_file():
            return PatchExecutionResult(
                finding=finding,
                candidate=None,
                verdict=None,
                pr_payload=None,
                success=False,
                message=f"Target file '{finding.file_path}' does not exist on disk.",
            )

        original_code = target_path.read_text(encoding="utf-8")
        try:
            patched_code, explanation = patch_synthesizer(finding, original_code)
        except Exception as exc:
            return PatchExecutionResult(
                finding=finding,
                candidate=None,
                verdict=None,
                pr_payload=None,
                success=False,
                message=f"Patch synthesis failed: {exc}",
            )

        candidate = PatchGenerator.create_candidate(
            finding=finding,
            original_content=original_code,
            patched_content=patched_code,
            explanation=explanation,
        )

        verdict = self.gate.verify_patch(
            candidate=candidate,
            repo_root=self.repo_root,
            test_runner=test_runner,
            breaking_changes=breaking_changes,
            is_human_approved=is_human_approved,
        )

        if not verdict.passed:
            return PatchExecutionResult(
                finding=finding,
                candidate=candidate,
                verdict=verdict,
                pr_payload=None,
                success=False,
                message=f"Patch rejected by release gate: {verdict.reason}",
            )

        pr_payload = PREmitter.emit_pr_payload(
            finding=finding,
            candidate=candidate,
            verification_summary="Verified by PatchFlow Anti-Gaming release gates & unit tests.",
        )

        return PatchExecutionResult(
            finding=finding,
            candidate=candidate,
            verdict=verdict,
            pr_payload=pr_payload,
            success=True,
            message="Patch successfully verified and PR payload staged.",
        )
