"""Search across past agent session logs by content."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import sessions_dir as default_sessions_dir

_SNIPPET_RADIUS = 40


@dataclass(frozen=True)
class SessionMatch:
    """One session whose content matched the query."""

    session_id: str
    timestamp: float | None
    task: str
    matched_snippet: str


def _searchable_text(data: dict[str, Any]) -> str:
    """Flatten the searched parts of a session record into one string."""
    parts: list[str] = [str(data.get("task", ""))]
    result = data.get("result") or {}
    if isinstance(result, dict):
        parts.append(str(result.get("text", "")))
        for call in result.get("tool_calls", []) or []:
            if isinstance(call, dict):
                parts.append(str(call.get("name", "")))
                call_input = call.get("input")
                if call_input is not None:
                    parts.append(json.dumps(call_input, ensure_ascii=False, default=str))
    return "\n".join(parts)


def _snippet(haystack: str, term: str) -> str:
    """Return a short context window around the first occurrence of `term`."""
    lower = haystack.lower()
    idx = lower.find(term)
    if idx == -1:
        return haystack[: _SNIPPET_RADIUS * 2].replace("\n", " ")
    start = max(0, idx - _SNIPPET_RADIUS)
    end = min(len(haystack), idx + len(term) + _SNIPPET_RADIUS)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(haystack) else ""
    return (prefix + haystack[start:end].replace("\n", " ") + suffix).strip()


def search_sessions(
    query: str,
    limit: int = 20,
    sessions_dir: Path | None = None,
) -> list[SessionMatch]:
    """Search past session logs for `query` (case-insensitive AND of terms).

    Read-only: never writes to the sessions directory. Corrupt or unreadable
    files are skipped. Missing directory returns an empty list.
    """
    if not query or not query.strip():
        raise ValueError("`query` is required and must be a non-empty string.")

    directory = sessions_dir if sessions_dir is not None else default_sessions_dir()
    if not directory.is_dir():
        return []

    terms = query.strip().lower().split()
    matches: list[SessionMatch] = []
    for path in directory.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        text = _searchable_text(data)
        lower = text.lower()
        if all(term in lower for term in terms):
            timestamp = data.get("timestamp")
            matches.append(
                SessionMatch(
                    session_id=path.stem,
                    timestamp=float(timestamp) if isinstance(timestamp, (int, float)) else None,
                    task=str(data.get("task", "")),
                    matched_snippet=_snippet(text, terms[0]),
                )
            )

    matches.sort(key=lambda m: m.timestamp or 0, reverse=True)
    return matches[:limit]
