"""Log ingestor — turn a raw GitHub Actions job log into :class:`FailureSignal`\\ s.

This is the first stage of the self-healing pipeline and the only one that sees
unstructured text. It is deliberately dependency-free and pure: give it a string,
get back an ordered list of structured failures. Everything downstream (context
gathering, diagnosis, safety) works from those structures, never from raw log
text, so a log-format change is contained to this module.

Four checkers are understood, matching the ones ``ci.yml`` actually runs: pytest,
ruff, mypy, and bandit.
"""

from __future__ import annotations

import re

from .models import FailureSignal, LogFrame

# A single failure is worth ~a few hundred lines of log; a pathological run can
# emit thousands. Cap what we hand downstream so a broken job cannot balloon the
# diagnosis prompt.
MAX_SIGNALS = 10
MAX_FRAMES = 12
MAX_EXCERPT_LINES = 60

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")
_WORKFLOW_MARKER_RE = re.compile(r"^##\[[a-z]+\]")

# pytest, --tb=short:  "tests/test_x.py:12: in test_y"
_FRAME_SHORT_RE = re.compile(r"^(?P<path>[^\s:][^:]*\.py):(?P<line>\d+): in (?P<function>\S+)\s*$")
# pytest, --tb=long trailing location:  "tests/test_x.py:12: AssertionError"
_FRAME_LOCATION_RE = re.compile(
    r"^(?P<path>[^\s:][^:]*\.py):(?P<line>\d+):\s*(?P<error>[\w.]*)\s*$"
)
# CPython native traceback:  '  File "tests/test_x.py", line 12, in test_y'
_FRAME_NATIVE_RE = re.compile(
    r'^\s*File "(?P<path>[^"]+)", line (?P<line>\d+), in (?P<function>\S+)\s*$'
)

# pytest error lines are prefixed with "E" in column 0.
_ERROR_TYPED_RE = re.compile(
    r"^E\s+(?P<type>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit)):\s*(?P<message>.*)$"
)
_ERROR_BARE_RE = re.compile(r"^E\s+(?P<message>\S.*)$")

_SUMMARY_RE = re.compile(r"^(?:FAILED|ERROR)\s+(?P<nodeid>\S+)(?:\s+-\s+(?P<message>.*))?$")

_RUFF_RE = re.compile(
    r"^(?P<path>[^\s:][^:]*\.pyi?):(?P<line>\d+):(?P<col>\d+): "
    r"(?P<code>[A-Z]+\d+)\s+(?:\[\*\]\s+)?(?P<message>.*)$"
)
_MYPY_PREFIX_RE = re.compile(
    r"^(?P<path>[^\s:][^:]*\.pyi?):(?P<line>\d+):(?:\d+:)? error: (?P<rest>.*)$"
)
_BANDIT_ISSUE_RE = re.compile(r"^>>\s*Issue:\s*\[(?P<code>[^:\]]+):[^\]]*\]\s*(?P<message>.*)$")
_BANDIT_LOCATION_RE = re.compile(r"^\s*Location:\s*(?P<path>\S+?):(?P<line>\d+)(?::\d+)?\s*$")


def _is_failures_banner(line: str) -> bool:
    if line.startswith("===") and line.endswith("==="):
        return line.strip("=").strip() in ("FAILURES", "ERRORS")
    return False


def _is_banner(line: str) -> bool:
    if line.startswith("===") and line.endswith("==="):
        return bool(line.strip("=").strip())
    return False


def _extract_block_name(line: str) -> str | None:
    if line.startswith("___") and line.endswith("___"):
        trimmed = line.strip("_").strip()
        if trimmed:
            return trimmed
    return None


def normalise(text: str) -> list[str]:
    """Strip Actions timestamps, group markers and ANSI colour from a raw log."""
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = _TIMESTAMP_RE.sub("", raw)
        line = _ANSI_RE.sub("", line)
        line = _WORKFLOW_MARKER_RE.sub("", line)
        lines.append(line.rstrip())
    return lines


def _excerpt(lines: list[str], start: int, end: int) -> str:
    window = [line for line in lines[start:end] if line.strip()]
    if len(window) > MAX_EXCERPT_LINES:
        window = window[-MAX_EXCERPT_LINES:]
    return "\n".join(window)


def _parse_summary(lines: list[str]) -> dict[str, str]:
    """Map a test's short name to its full pytest node id, from the summary section."""
    node_ids: dict[str, str] = {}
    for line in lines:
        match = _SUMMARY_RE.match(line)
        if not match:
            continue
        node_id = match.group("nodeid")
        short = node_id.rsplit("::", 1)[-1]
        node_ids.setdefault(short, node_id)
    return node_ids


def _lookup_node_id(block_name: str, node_ids: dict[str, str]) -> str:
    """Resolve a FAILURES block header to its full node id.

    pytest writes the header dot-separated (``TestAdder.test_adds``) but the
    summary line ``::``-separated (``tests/t.py::TestAdder::test_adds``), so a
    class-based test only matches on its final component. Try the whole header
    first — a parametrised id can itself contain dots (``test_x[1.5]``).
    """
    return node_ids.get(block_name) or node_ids.get(block_name.rsplit(".", 1)[-1]) or block_name


def _failure_sections(lines: list[str]) -> list[tuple[int, int]]:
    """Index ranges of the ``=== FAILURES ===`` / ``=== ERRORS ===`` sections."""
    sections: list[tuple[int, int]] = []
    start: int | None = None
    for index, line in enumerate(lines):
        if _is_failures_banner(line):
            if start is not None:
                sections.append((start, index))
            start = index + 1
        elif start is not None and _is_banner(line):
            sections.append((start, index))
            start = None
    if start is not None:
        sections.append((start, len(lines)))
    return sections


def _split_blocks(lines: list[str], start: int, end: int) -> list[tuple[str, int, int]]:
    """Split one FAILURES section into ``(test name, start, end)`` per-test blocks."""
    headers: list[tuple[str, int]] = []
    for index in range(start, end):
        name = _extract_block_name(lines[index])
        if name is not None:
            headers.append((name, index))
    if not headers:
        return [("", start, end)]

    blocks: list[tuple[str, int, int]] = []
    for position, (name, index) in enumerate(headers):
        block_end = headers[position + 1][1] if position + 1 < len(headers) else end
        blocks.append((name, index + 1, block_end))
    return blocks


def _block_frames(lines: list[str], start: int, end: int) -> tuple[LogFrame, ...]:
    frames: list[LogFrame] = []
    for line in lines[start:end]:
        if (match := _FRAME_SHORT_RE.match(line)) or (match := _FRAME_NATIVE_RE.match(line)):
            frames.append(
                LogFrame(match.group("path"), int(match.group("line")), match.group("function"))
            )
        elif match := _FRAME_LOCATION_RE.match(line):
            frames.append(LogFrame(match.group("path"), int(match.group("line"))))
    return tuple(frames[-MAX_FRAMES:])


def _block_error(lines: list[str], start: int, end: int) -> tuple[str, str]:
    """The error type and message for one failure block, from its ``E`` lines."""
    error_type = ""
    message = ""
    for line in lines[start:end]:
        if match := _ERROR_TYPED_RE.match(line):
            error_type, message = match.group("type"), match.group("message").strip()
        elif not error_type and (match := _ERROR_BARE_RE.match(line)):
            body = match.group("message").strip()
            # A bare ``E   assert x == y`` is pytest's rewritten assertion.
            error_type = "AssertionError" if body.startswith("assert") else "Failure"
            message = body
    if not error_type:
        # No ``E`` line at all (e.g. a collection error): fall back to the
        # trailing location line, which names the exception type.
        for line in reversed(lines[start:end]):
            if (match := _FRAME_LOCATION_RE.match(line)) and match.group("error"):
                return match.group("error"), ""
    return error_type, message


def _parse_pytest(lines: list[str]) -> tuple[list[FailureSignal], set[int]]:
    node_ids = _parse_summary(lines)
    signals: list[FailureSignal] = []
    consumed: set[int] = set()

    for section_start, section_end in _failure_sections(lines):
        consumed.update(range(section_start, section_end))
        for name, start, end in _split_blocks(lines, section_start, section_end):
            error_type, message = _block_error(lines, start, end)
            if not error_type:
                continue
            signals.append(
                FailureSignal(
                    tool="pytest",
                    error_type=error_type,
                    message=message,
                    test_id=_lookup_node_id(name, node_ids),
                    frames=_block_frames(lines, start, end),
                    excerpt=_excerpt(lines, start, end),
                )
            )

    if signals:
        return signals, consumed

    # No FAILURES section survived (``-q`` with a truncated log, or a log that
    # only carries the summary). The summary lines alone still identify the
    # failing tests, which is enough to gather context and diagnose.
    for line in lines:
        if match := _SUMMARY_RE.match(line):
            node_id = match.group("nodeid")
            path = node_id.split("::", 1)[0]
            signals.append(
                FailureSignal(
                    tool="pytest",
                    error_type="TestFailure",
                    message=(match.group("message") or "").strip(),
                    test_id=node_id,
                    frames=(LogFrame(path, 1),) if path.endswith(".py") else (),
                    excerpt=line,
                )
            )
    return signals, consumed


def _parse_line_checkers(lines: list[str], skip: set[int]) -> list[FailureSignal]:
    """Parse the one-line-per-diagnostic checkers: ruff and mypy."""
    signals: list[FailureSignal] = []
    for index, line in enumerate(lines):
        if index in skip:
            continue
        if match := _RUFF_RE.match(line):
            signals.append(
                FailureSignal(
                    tool="ruff",
                    error_type=match.group("code"),
                    message=match.group("message").strip(),
                    frames=(LogFrame(match.group("path"), int(match.group("line"))),),
                    excerpt=line,
                )
            )
        elif match := _MYPY_PREFIX_RE.match(line):
            rest = match.group("rest").strip()
            code = "error"
            message = rest
            if rest.endswith("]") and " [" in rest:
                msg, code_part = rest.rsplit(" [", 1)
                if code_part.endswith("]") and re.match(r"^[a-z-]+\]$", code_part):
                    code = code_part[:-1]
                    message = msg
            signals.append(
                FailureSignal(
                    tool="mypy",
                    error_type=code,
                    message=message.strip(),
                    frames=(LogFrame(match.group("path"), int(match.group("line"))),),
                    excerpt=line,
                )
            )
    return signals


def _parse_bandit(lines: list[str], skip: set[int]) -> list[FailureSignal]:
    """Parse bandit's two-part output: an ``>> Issue:`` header then a ``Location:``."""
    signals: list[FailureSignal] = []
    pending: tuple[str, str] | None = None
    for index, line in enumerate(lines):
        if index in skip:
            continue
        if match := _BANDIT_ISSUE_RE.match(line):
            pending = (match.group("code"), match.group("message").strip())
        elif pending and (match := _BANDIT_LOCATION_RE.match(line)):
            code, message = pending
            signals.append(
                FailureSignal(
                    tool="bandit",
                    error_type=code,
                    message=message,
                    frames=(LogFrame(match.group("path"), int(match.group("line"))),),
                    excerpt=f"{code}: {message}",
                )
            )
            pending = None
    return signals


def _dedupe(signals: list[FailureSignal]) -> list[FailureSignal]:
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[FailureSignal] = []
    for signal in signals:
        frame = signal.primary_frame
        key = (
            signal.tool,
            signal.error_type,
            signal.test_id or signal.message,
            f"{frame.path}:{frame.line}" if frame else "",
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(signal)
    return unique


def parse_job_log(text: str) -> list[FailureSignal]:
    """Parse a CI job log into structured failures, most-specific checker first.

    Returns at most :data:`MAX_SIGNALS` signals, deduplicated. An empty list means
    the log carried no failure this module recognises — which the pipeline treats
    as "nothing to heal", never as "healed".
    """
    lines = normalise(text)
    pytest_signals, consumed = _parse_pytest(lines)
    signals = (
        pytest_signals + _parse_line_checkers(lines, consumed) + _parse_bandit(lines, consumed)
    )
    return _dedupe(signals)[:MAX_SIGNALS]
