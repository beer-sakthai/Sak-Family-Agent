"""Repo inspector — resolve the files a failure implicates and read them safely.

CI logs name files the way the runner saw them: absolute paths under
``/home/runner/work/<repo>/<repo>/``, or relative to whatever directory the step
ran in. :func:`resolve_repo_path` maps those back onto the local checkout, and
:func:`gather_context` reads a bounded window around each implicated line.

Every read is containment-checked against the repository root. A log is
attacker-influenceable input — anyone who can make CI print a line can suggest a
path — so a frame pointing at ``/etc/shadow`` or ``../../.ssh/id_rsa`` resolves
to nothing rather than to a file.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..config import redact_secrets
from .models import FailureSignal, FileContext

logger = logging.getLogger(__name__)

# How many lines either side of an implicated line to show the diagnosis agent.
DEFAULT_RADIUS = 40
# Bounds on what one diagnosis prompt may carry.
MAX_FILES = 4
MAX_FILE_BYTES = 512_000


def _is_contained(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_repo_path(raw: str, repo_root: Path) -> Path | None:
    """Map a path as printed in a CI log onto a real file inside ``repo_root``.

    Tries the path as given, then drops leading components one at a time — that
    is what turns ``/home/runner/work/repo/repo/tests/test_x.py`` back into
    ``tests/test_x.py``. Returns ``None`` when nothing resolves to a regular file
    inside the repository, including when the path escapes it via symlink.
    """
    cleaned = raw.strip().replace("\\", "/").lstrip()
    if not cleaned:
        return None

    try:
        root = repo_root.resolve()
    except OSError:  # pragma: no cover — resolve on a live root effectively cannot fail
        return None

    parts = [part for part in Path(cleaned).parts if part not in ("/", ".", "..")]
    for start in range(len(parts)):
        candidate = root.joinpath(*parts[start:])
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if not _is_contained(resolved, root):
            continue
        if resolved.is_file():
            return resolved
    return None


def read_window(path: Path, line: int, radius: int = DEFAULT_RADIUS) -> tuple[int, int, str] | None:
    """Read ``radius`` lines either side of ``line``. ``None`` if unreadable or huge."""
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        logger.debug("selfheal: cannot read %s: %s", path, exc)
        return None
    if not lines:
        return None

    start = max(1, line - radius)
    end = min(len(lines), max(line, 1) + radius)
    return start, end, "\n".join(lines[start - 1 : end])


def gather_context(
    signal: FailureSignal,
    repo_root: Path,
    *,
    radius: int = DEFAULT_RADIUS,
    max_files: int = MAX_FILES,
) -> tuple[FileContext, ...]:
    """Collect source windows for a signal's frames, innermost frame first.

    The innermost frame is where the error was raised and is almost always the
    one worth fixing, so it leads; outer frames follow until ``max_files`` is
    reached. Frames that do not resolve inside the repository are skipped.
    """
    contexts: list[FileContext] = []
    seen: set[Path] = set()

    for frame in reversed(signal.frames):
        if len(contexts) >= max_files:
            break
        resolved = resolve_repo_path(frame.path, repo_root)
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        window = read_window(resolved, frame.line, radius)
        if window is None:
            continue
        start, end, text = window
        contexts.append(
            FileContext(
                path=resolved.relative_to(repo_root.resolve()).as_posix(),
                start_line=start,
                end_line=end,
                text=redact_secrets(text),
            )
        )
    return tuple(contexts)


def render_contexts(contexts: tuple[FileContext, ...]) -> str:
    """Render gathered context as a fenced block per file, for the diagnosis prompt."""
    if not contexts:
        return "(no repository context could be resolved for this failure)"
    chunks = [
        f"--- {ctx.path} (lines {ctx.start_line}-{ctx.end_line}) ---\n{ctx.text}"
        for ctx in contexts
    ]
    return "\n\n".join(chunks)
