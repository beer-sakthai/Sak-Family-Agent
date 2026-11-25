"""Patch synthesizer generating surgical code corrections."""

from __future__ import annotations

import difflib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .scanners.finding import Finding


@dataclass
class PatchCandidate:
    """A generated patch candidate targeting a specific file and finding."""

    finding_id: str
    target_file: str
    original_content: str
    patched_content: str
    explanation: str
    unified_diff: str

    def to_dict(self) -> dict[str, Any]:
        """Convert patch candidate to dictionary representation."""
        return asdict(self)


class PatchGenerator:
    """Synthesizes code edits to remediate identified findings."""

    @staticmethod
    def generate_diff(original: str, patched: str, file_path: str = "target_file") -> str:
        """Produce a standardized unified diff representation."""
        orig_lines = original.splitlines(keepends=True)
        patched_lines = patched.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            patched_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
        return "".join(diff)

    @classmethod
    def create_candidate(
        cls,
        finding: Finding,
        original_content: str,
        patched_content: str,
        explanation: str,
    ) -> PatchCandidate:
        """Build and validate a PatchCandidate."""
        diff = cls.generate_diff(original_content, patched_content, finding.file_path)
        return PatchCandidate(
            finding_id=finding.id,
            target_file=finding.file_path,
            original_content=original_content,
            patched_content=patched_content,
            explanation=explanation,
            unified_diff=diff,
        )

    @staticmethod
    def apply_patch_to_disk(candidate: PatchCandidate, repo_root: Path | str) -> bool:
        """Write candidate patch content directly to file."""
        target = Path(repo_root) / candidate.target_file
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(candidate.patched_content, encoding="utf-8")
            return True
        except Exception:
            return False
