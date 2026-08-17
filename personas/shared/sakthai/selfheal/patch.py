"""Code editor — apply proposed edits as one transaction, with a rollback.

The pipeline's whole safety story downstream of the patch depends on being able
to put the working tree back exactly as it was, so applying edits is all-or-
nothing: :func:`apply_edits` captures each file's original bytes before writing,
and either every edit lands or none do. If verification later fails, the caller
calls :meth:`PatchTransaction.rollback` and the tree is byte-identical again.

Edits are re-validated here even though the safety gate already checked them.
That is deliberate, not redundant: the gate ran against the tree as it was at
diagnosis time, and this is the last read before the write.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .models import ProposedEdit

logger = logging.getLogger(__name__)


class PatchError(RuntimeError):
    """Raised when a patch cannot be applied cleanly; the tree is left untouched."""


@dataclass
class PatchTransaction:
    """The set of files a patch rewrote, plus the bytes needed to undo it."""

    repo_root: Path
    originals: dict[Path, str] = field(default_factory=dict)
    applied: bool = False

    @property
    def changed_files(self) -> tuple[str, ...]:
        """Repo-relative posix paths this transaction rewrote."""
        return tuple(sorted(path.relative_to(self.repo_root).as_posix() for path in self.originals))

    def rollback(self) -> tuple[str, ...]:
        """Restore every rewritten file to its original content. Idempotent."""
        if not self.applied:
            return ()
        restored: list[str] = []
        for path, original in self.originals.items():
            try:
                path.write_text(original, encoding="utf-8")
                restored.append(path.relative_to(self.repo_root).as_posix())
            except OSError as exc:  # pragma: no cover — a write that succeeded rarely fails to undo
                logger.error("selfheal: failed to roll back %s: %s", path, exc)
        self.applied = False
        return tuple(sorted(restored))


def _resolve(edit_path: str, repo_root: Path) -> Path:
    """Resolve an edit's path inside ``repo_root``, refusing anything outside it."""
    root = repo_root.resolve()
    candidate = Path(edit_path)
    absolute = candidate if candidate.is_absolute() else root / candidate
    try:
        resolved = absolute.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise PatchError(f"{edit_path} resolves outside the repository") from exc
    if not resolved.is_file():
        raise PatchError(f"{edit_path} is not an existing file")
    return resolved


def apply_edits(edits: Sequence[ProposedEdit], repo_root: Path) -> PatchTransaction:
    """Apply every edit, or none of them.

    Raises :class:`PatchError` — after undoing any writes already made — when a
    path escapes the repository, a file is missing, or the search text is absent
    or ambiguous.
    """
    transaction = PatchTransaction(repo_root=repo_root.resolve())
    if not edits:
        raise PatchError("no edits to apply")

    try:
        for edit in edits:
            path = _resolve(edit.path, repo_root)
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise PatchError(f"cannot read {edit.path}: {exc}") from exc

            occurrences = content.count(edit.old)
            if occurrences != 1:
                raise PatchError(
                    f"search text appears {occurrences} times in {edit.path} — expected exactly one"
                )

            transaction.originals.setdefault(path, content)
            transaction.applied = True
            try:
                path.write_text(content.replace(edit.old, edit.new, 1), encoding="utf-8")
            except OSError as exc:
                raise PatchError(f"cannot write {edit.path}: {exc}") from exc
    except PatchError:
        transaction.rollback()
        raise

    return transaction
