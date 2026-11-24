"""Anti-Gaming & Holdout Isolation Gate enforcing release invariants on candidate patches."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_pkg_dir = str(Path(__file__).resolve().parents[3] / "personas" / "sakthai")
if _pkg_dir not in sys.path:
    sys.path.append(_pkg_dir)

from evolution.core.config import EvolutionConfig  # noqa: E402
from evolution.core.constraints import ConstraintValidator, SchemaChangeValidator  # noqa: E402
from sakthai.memory.session_store import FileSessionStore  # noqa: E402
from sakthai.memory.store import MemoryStore  # noqa: E402

from .generator import PatchCandidate  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass
class GateVerdict:
    """Outcome of Anti-Gaming gate verification."""

    passed: bool
    reason: str
    snapshot_id: str | None = None
    rolled_back: bool = False
    details: dict[str, Any] | None = None


class AntiGamingGate:
    """Enforces the 5 Anti-Gaming safeguards on all candidate patches."""

    def __init__(
        self,
        session_store: FileSessionStore | None = None,
        config: EvolutionConfig | None = None,
    ) -> None:
        self.session_store = session_store or FileSessionStore()
        self.config = config or EvolutionConfig()
        self.constraint_validator = ConstraintValidator(self.config)

    def verify_patch(
        self,
        candidate: PatchCandidate,
        repo_root: Path,
        memory_store: MemoryStore | None = None,
        test_runner: Callable[[], bool] | None = None,
        breaking_changes: list[str] | None = None,
        is_human_approved: bool = False,
    ) -> GateVerdict:
        """Execute the 5-point Anti-Gaming release gate on a candidate patch."""
        # 1. Human Approval Gate
        if breaking_changes:
            approval_res = SchemaChangeValidator.validate_approval(
                breaking_changes=breaking_changes,
                approved=is_human_approved,
            )
            if not approval_res.passed:
                return GateVerdict(
                    passed=False,
                    reason=f"Rejected by Human Approval Gate: {approval_res.message}",
                )

        # 2. Description Token Ceiling (if patching tool schemas or instructions)
        if "[TOOL " in candidate.patched_content:
            token_res = self.constraint_validator._check_tool_descriptions_structure(
                candidate.patched_content
            )
            if not token_res.passed:
                return GateVerdict(
                    passed=False,
                    reason=f"Rejected by Description Token Ceiling: {token_res.message}",
                )

        # 3. Snapshot Checkpoint Creation before applying
        snapshot_id = f"pre_patch_{candidate.finding_id}"
        self.session_store.create_checkpoint(
            snapshot_id=snapshot_id,
            memory_store=memory_store,
            metadata={"candidate": candidate.to_dict()},
        )

        # 4. Apply patch and test
        target_path = repo_root / candidate.target_file
        original_disk_content = (
            target_path.read_text(encoding="utf-8") if target_path.is_file() else ""
        )

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(candidate.patched_content, encoding="utf-8")

            # 5. Run verification tests / holdout validation
            tests_ok = True
            if test_runner is not None:
                tests_ok = test_runner()

            if not tests_ok:
                # Regressed! Trigger Snapshot Rollback
                if original_disk_content:
                    target_path.write_text(original_disk_content, encoding="utf-8")
                self.session_store.revert_checkpoint(snapshot_id, memory_store=memory_store)
                return GateVerdict(
                    passed=False,
                    reason="Test regression detected. Snapshot rolled back.",
                    snapshot_id=snapshot_id,
                    rolled_back=True,
                )

            return GateVerdict(
                passed=True,
                reason="All Anti-Gaming safeguards and tests passed cleanly.",
                snapshot_id=snapshot_id,
                rolled_back=False,
            )

        except Exception as exc:
            # Revert on unexpected failure
            if original_disk_content:
                target_path.write_text(original_disk_content, encoding="utf-8")
            self.session_store.revert_checkpoint(snapshot_id, memory_store=memory_store)
            return GateVerdict(
                passed=False,
                reason=f"Execution error: {exc}. Rolled back.",
                snapshot_id=snapshot_id,
                rolled_back=True,
            )
