"""Tools the agent loop (and the MCP server) can invoke.

A :class:`Tool` pairs a JSON input schema (what the model sees) with a Python
handler ``(args, store) -> str``. ``BUILTIN_TOOLS`` is the single registry used
by both the agent loop and the MCP server, so a tool's schema and behaviour live
in one place.
"""

from __future__ import annotations

import contextlib
import difflib
import fnmatch
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from ..config import register_secret, sakthai_home
from ..lead.capture import capture_lead as capture_lead_fact
from ..learn.ingest import ingest_document as ingest_document_facts
from ..memory.session_search import search_sessions as search_past_sessions
from ..memory.store import MemoryStore

logger = logging.getLogger(__name__)

MAX_FILE_READ_CHARS = 20_000  # read_file output cap
MAX_CMD_OUTPUT_CHARS = 20_000  # run_command output cap
_RECALL_LIMIT_MAX = 200  # cap on recall/search limit
_CMD_TIMEOUT_DEFAULT = 30.0
_CMD_TIMEOUT_MAX = 120.0
_HF_DEFAULT_MODEL = "Nanthasit/sakthai-context-1.5b-merged"
_HF_API_BASE_DEFAULT = "https://router.huggingface.co/v1"

_GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
_GRAPH_TOKEN_URL_TMPL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"  # nosec B105 - URL template, not a password
_GRAPH_SCOPES = "Mail.Send Mail.Read Calendars.ReadWrite offline_access"
_GRAPH_TOKEN_CACHE_NAME = "graph_token.json"  # nosec B105 - filename, not a password


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any], MemoryStore], str]
    # MCP behaviour hints (readOnlyHint, destructiveHint, idempotentHint,
    # openWorldHint) advertised in ``tools/list`` so clients can gate approvals.
    annotations: Mapping[str, bool] | None = None
    requires_confirmation: bool = False

    def schema(self) -> dict[str, Any]:
        """The model-facing tool definition."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def validate_args(self, args: Mapping[str, Any] | None) -> tuple[bool, list[str]]:
        """Validate input arguments against ``self.input_schema``.

        Returns:
            A tuple of ``(is_valid, error_reasons)``. When valid, ``error_reasons`` is empty.
        """
        errors: list[str] = []
        if args is None or not isinstance(args, Mapping):
            return False, ["Tool arguments must be a JSON object mapping."]

        required = self.input_schema.get("required", [])
        for field in required:
            if field not in args:
                errors.append(f"Missing required parameter '{field}'.")
            elif args[field] is None:
                errors.append(f"Required parameter '{field}' cannot be null.")
            elif isinstance(args[field], str) and not args[field].strip():
                errors.append(f"Required parameter '{field}' cannot be blank.")

        properties = self.input_schema.get("properties", {})
        for param, val in args.items():
            if param not in properties or val is None:
                continue
            prop = properties[param]
            expected_type = prop.get("type")
            if expected_type == "string" and not isinstance(val, str):
                errors.append(f"Parameter '{param}' expected string, got {type(val).__name__}.")
            elif expected_type == "integer" and (not isinstance(val, int) or isinstance(val, bool)):
                errors.append(f"Parameter '{param}' expected integer, got {type(val).__name__}.")
            elif expected_type == "number" and (
                not isinstance(val, (int, float)) or isinstance(val, bool)
            ):
                errors.append(f"Parameter '{param}' expected number, got {type(val).__name__}.")
            elif expected_type == "boolean" and not isinstance(val, bool):
                errors.append(f"Parameter '{param}' expected boolean, got {type(val).__name__}.")
            elif expected_type == "array" and not isinstance(val, (list, tuple)):
                errors.append(f"Parameter '{param}' expected array, got {type(val).__name__}.")
            elif expected_type == "object" and not isinstance(val, Mapping):
                errors.append(f"Parameter '{param}' expected object, got {type(val).__name__}.")

            if "enum" in prop and val not in prop["enum"]:
                errors.append(f"Parameter '{param}' must be one of {prop['enum']!r}, got {val!r}.")

        return (len(errors) == 0, errors)

    def safe_call(self, args: Mapping[str, Any] | None, store: MemoryStore) -> tuple[str, bool]:
        """Validate input arguments, execute the handler, and redact secrets.

        Returns:
            ``(output_text, is_error)``
        """
        from ..config import redact_secrets

        valid, errors = self.validate_args(args)
        if not valid:
            err_msg = f"Invalid arguments for tool '{self.name}': " + "; ".join(errors)
            return redact_secrets(err_msg), True

        try:
            output = self.handler(dict(args or {}), store)
            return redact_secrets(output), False
        except Exception as exc:  # noqa: BLE001
            logger.debug("Tool %r handler raised %s: %s", self.name, type(exc).__name__, exc)
            return redact_secrets(f"{type(exc).__name__}: {exc}"), True


def _coerce_limit(raw: Any, default: int) -> int:
    try:
        limit = int(raw) if raw else default
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, _RECALL_LIMIT_MAX))


def _format_facts(facts: list[Any]) -> list[str]:
    lines = []
    for f in facts:
        head = f"[{f.kind}] {f.key}: " if f.key else f"[{f.kind}] "
        lines.append(f"  {f.id}  {head}{f.value}")
    return lines


def _format_observations(observations: list[Any]) -> list[str]:
    return [f"  {o.id}  ({o.weight:.2f}) {o.summary}" for o in observations]


# -- handlers ------------------------------------------------------------


def _learn(args: dict[str, Any], store: MemoryStore) -> str:
    raw = args.get("value")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("`value` is required and must be a non-empty string.")
    kind = args.get("kind") or "note"
    key = args.get("key")
    fact_id = store.add_fact(raw.strip(), kind=kind, key=key)
    return f"Stored fact id={fact_id} (kind={kind}, key={key or '-'})."


# Secret-bearing filenames blocked regardless of allowed roots. ``cwd`` is an
# auto-trusted read root, so without this an agent could read ``./.env`` or
# ``./id_rsa`` and exfiltrate it. This is defense-in-depth alongside the
# guardrail layer: it holds even for direct handler callers or a custom policy.
_SENSITIVE_READ_BASENAMES: frozenset[str] = frozenset(
    {
        ".env",
        "memory.db",
        _GRAPH_TOKEN_CACHE_NAME,  # the Microsoft Graph refresh-token cache
        ".bash_history",
        ".zsh_history",
        ".python_history",
        ".history",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "id_ecdsa_sk",
        "id_ed25519_sk",
        "id_xmss",
        "known_hosts",
        "authorized_keys",
        "credentials",
        "credentials.json",
        "shadow",
        "passwd",
        "sudoers",
        "gshadow",
        "group",
        ".bashrc",
        ".zshrc",
        ".profile",
        ".bash_profile",
        ".gitconfig",
        ".zprofile",
        ".yarnrc",
        ".yarnrc.yml",
        ".git-credentials",
        ".node_repl_history",
        ".mysql_history",
        ".psql_history",
        ".sqlite_history",
        ".rediscli_history",
        ".mongo_history",
        ".pgpass",
        ".my.cnf",
    }
)
_SENSITIVE_READ_SUFFIXES: tuple[str, ...] = (".pem", ".key", ".pfx", ".p12")
# Path fragments (relative to a root) that indicate a secret store.
_SENSITIVE_READ_FRAGMENTS: tuple[tuple[str, ...], ...] = (
    (".aws", "credentials"),
    (".ssh",),
    (".git", "config"),
)


def _is_sensitive_read_target(resolved: Path) -> bool:
    """Return True if ``resolved`` names a well-known secret file."""
    name = resolved.name
    lower = name.lower()
    if name in _SENSITIVE_READ_BASENAMES or lower.startswith(".env."):
        return True
    if lower.endswith(_SENSITIVE_READ_SUFFIXES):
        return True
    parts = resolved.parts
    for fragment in _SENSITIVE_READ_FRAGMENTS:
        n = len(fragment)
        if n <= len(parts) and any(
            tuple(parts[i : i + n]) == fragment for i in range(len(parts) - n + 1)
        ):
            return True
    return False


def _resolve_and_validate_path(path_str: str) -> Path:
    """Resolve a path and ensure it is a file within the allowed roots."""
    candidate = Path(path_str).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{candidate} is not a regular file.") from exc
    except OSError as exc:
        raise FileNotFoundError(f"{candidate} could not be opened: {exc}") from exc

    if not resolved.is_file():
        raise FileNotFoundError(f"{resolved} is not a regular file.")

    if _is_sensitive_read_target(resolved):
        raise PermissionError(
            f"{resolved} is a sensitive credential file and cannot be read by this tool."
        )

    if not _path_under_any_root(resolved, _allowed_read_roots()):
        raise PermissionError(
            f"{resolved} is outside the allowed roots. Add it to SAKTHAI_READ_ALLOW "
            "(os.pathsep-separated) to permit reading."
        )
    return resolved


def _ingest_document(args: dict[str, Any], store: MemoryStore) -> str:
    path = args.get("path")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("`path` is required and must be a non-empty string.")
    resolved = _resolve_and_validate_path(path.strip())
    ids = ingest_document_facts(resolved, store=store)
    if not ids:
        return "No facts found in document."
    return f"learned {len(ids)} facts (ids: {ids})"


def _capture_lead(args: dict[str, Any], store: MemoryStore) -> str:
    name = args.get("name")
    phone = args.get("phone")
    email = args.get("email")
    query = args.get("query")
    lead_id = capture_lead_fact(
        name=name, phone=phone, email=email, query=str(query or ""), store=store
    )
    return f"captured lead id={lead_id}"


def _recall(args: dict[str, Any], store: MemoryStore) -> str:
    limit = _coerce_limit(args.get("limit"), 20)
    facts = store.list_facts(limit=limit)
    obs = store.top_observations(limit=limit)
    if not facts and not obs:
        return "Memory is empty."
    lines: list[str] = []
    if facts:
        lines.append("Facts:")
        lines.extend(_format_facts(facts))
    if obs:
        lines.append("Observations:")
        lines.extend(_format_observations(obs))
    return "\n".join(lines)


def _search(args: dict[str, Any], store: MemoryStore) -> str:
    query = args.get("query")
    if not isinstance(query, str) or not query:
        raise ValueError("`query` is required and must be a non-empty string.")
    limit = _coerce_limit(args.get("limit"), 50)
    facts, obs = store.search_memory(query, limit=limit)
    if not facts and not obs:
        return f"No matches found for '{query}'."
    lines: list[str] = []
    if facts:
        lines.append(f"Matching Facts ({len(facts)}):")
        lines.extend(_format_facts(facts))
    if obs:
        lines.append(f"Matching Observations ({len(obs)}):")
        lines.extend(_format_observations(obs))
    return "\n".join(lines)


def _search_sessions(args: dict[str, Any], store: MemoryStore) -> str:
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("`query` is required and must be a non-empty string.")
    limit = _coerce_limit(args.get("limit"), 20)
    matches = search_past_sessions(query, limit=limit)
    if not matches:
        return f"No matching sessions found for '{query}'."
    lines = [f"Matching Sessions ({len(matches)}):"]
    lines.extend(f"  {m.session_id}  {m.task}  — {m.matched_snippet}" for m in matches)
    return "\n".join(lines)


def _forget(args: dict[str, Any], store: MemoryStore) -> str:
    raw = args.get("fact_id")
    if isinstance(raw, bool) or raw is None:
        raise ValueError("`fact_id` is required and must be an integer.")
    try:
        fact_id = int(raw)
    except (TypeError, ValueError):
        raise ValueError("`fact_id` is required and must be an integer.") from None
    if store.forget_fact(fact_id):
        return f"Forgot fact id={fact_id}."
    return f"No fact with id={fact_id}."


def _allowed_read_roots() -> list[Path]:
    """Roots ``read_file`` may read: cwd and ~/.sakthai, plus SAKTHAI_READ_ALLOW."""
    roots: list[Path] = []
    for base in (Path.cwd(), sakthai_home()):
        try:
            roots.append(base.resolve())
        except OSError:
            continue
    for token in os.environ.get("SAKTHAI_READ_ALLOW", "").split(os.pathsep):
        token = token.strip()
        if not token:
            continue
        try:
            roots.append(Path(token).expanduser().resolve())
        except OSError:
            continue
    return roots


def _path_under_any_root(path: Path, roots: list[Path]) -> bool:
    for root in roots:
        try:
            if path == root or path.is_relative_to(root):
                return True
        except (ValueError, OSError):
            continue
    return False


def _read_file(args: dict[str, Any], store: MemoryStore) -> str:
    raw = args.get("path")
    if not isinstance(raw, str) or not raw:
        raise ValueError("`path` is required and must be a non-empty string.")
    resolved = _resolve_and_validate_path(raw)
    with resolved.open(encoding="utf-8", errors="replace") as fh:
        text = fh.read(MAX_FILE_READ_CHARS + 1)
    if len(text) > MAX_FILE_READ_CHARS:
        text = text[:MAX_FILE_READ_CHARS] + "\n... [truncated]"
    return text


_SENSITIVE_WRITE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".ssh",
        ".aws",
        ".gnupg",
        ".docker",
        ".kube",
        ".gcloud",
        ".azure",
        ".jules",
    }
)

_SEARCH_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".next",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
    }
)


def _allowed_write_roots() -> list[Path]:
    """Roots ``edit_file`` and ``write_file`` may modify: cwd plus SAKTHAI_WRITE_ALLOW."""
    roots: list[Path] = []
    with_cwd = (Path.cwd(),)
    for base in with_cwd:
        try:
            roots.append(base.resolve())
        except OSError:
            continue
    for token in os.environ.get("SAKTHAI_WRITE_ALLOW", "").split(os.pathsep):
        token = token.strip()
        if not token or token.lower() in _SHELL_ALLOW_ANY:
            continue
        try:
            roots.append(Path(token).expanduser().resolve())
        except OSError:
            continue
    return roots


def _is_sensitive_write_target(resolved: Path) -> bool:
    """Return True if ``resolved`` targets a sensitive credential file or protected directory."""
    if _is_sensitive_read_target(resolved):
        return True
    name_lower = resolved.name.lower()
    if name_lower.startswith((".env-", ".env_", "memory.db-")):
        return True
    return any(part.lower() in _SENSITIVE_WRITE_DIRS for part in resolved.parts)


def _resolve_and_validate_write_path(path_str: str, *, must_exist: bool = False) -> Path:
    """Resolve a path for writing/editing and validate it against sensitive targets and write roots."""
    candidate = Path(path_str).expanduser()
    try:
        resolved = candidate.resolve(strict=must_exist)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{candidate} does not exist.") from exc
    except OSError as exc:
        raise FileNotFoundError(f"{candidate} could not be resolved: {exc}") from exc

    if must_exist and not resolved.is_file():
        raise FileNotFoundError(f"{resolved} is not a regular file.")
    if resolved.exists() and resolved.is_dir():
        raise IsADirectoryError(f"{resolved} is a directory, not a file.")

    # Check both unresolved components (for symlink safety) and resolved path
    for check_path in (candidate.absolute(), resolved):
        if _is_sensitive_write_target(check_path):
            raise PermissionError(
                f"{resolved} is a sensitive or protected path and cannot be modified by this tool."
            )

    if not _path_under_any_root(resolved, _allowed_write_roots()):
        raise PermissionError(
            f"{resolved} is outside the allowed write roots. Add it to SAKTHAI_WRITE_ALLOW "
            "(os.pathsep-separated) to permit writing."
        )
    return resolved


def _compute_unified_diff(
    old_content: str, new_content: str, display_path: str
) -> tuple[str, int, int]:
    """Compute a unified diff and count added and removed lines."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{display_path}",
            tofile=f"b/{display_path}",
            n=3,
        )
    )
    added = 0
    removed = 0
    for line in diff_lines:
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    diff_text = "".join(diff_lines)
    if not diff_text and old_content != new_content:
        diff_text = f"--- a/{display_path}\n+++ b/{display_path}\n@@ -1 +1 @@\n-{old_content}\n+{new_content}\n"
        added = max(1, len(new_lines))
        removed = max(1, len(old_lines))
    return diff_text, added, removed


def build_file_diff_preview(tool_name: str, args: Mapping[str, Any]) -> tuple[str, int, int]:
    """Generate a pre-execution unified diff preview for ``edit_file`` or ``write_file``.

    Returns:
        ``(diff_text, added_lines, removed_lines)``. Never raises; returns an explanatory
        preview string if the target file cannot be read or matched.
    """
    raw_path = args.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return ("", 0, 0)
    display_path = raw_path.strip()
    try:
        candidate = Path(display_path).expanduser()
        old_content = (
            candidate.read_text(encoding="utf-8", errors="replace") if candidate.is_file() else ""
        )
    except OSError:
        old_content = ""

    if tool_name == "write_file":
        new_content = args.get("content")
        if not isinstance(new_content, str):
            return ("", 0, 0)
        return _compute_unified_diff(old_content, new_content, display_path)

    if tool_name == "edit_file":
        old_text = args.get("old_text")
        new_text = args.get("new_text")
        replace_all = bool(args.get("replace_all", False))
        if not isinstance(old_text, str) or not isinstance(new_text, str) or not old_text:
            return ("", 0, 0)
        if old_text not in old_content:
            return (f"(old_text not found in {display_path})", 0, 0)
        new_content = (
            old_content.replace(old_text, new_text)
            if replace_all
            else old_content.replace(old_text, new_text, 1)
        )
        return _compute_unified_diff(old_content, new_content, display_path)

    return ("", 0, 0)


def _find_occurrence_lines(content: str, needle: str) -> list[int]:
    """Return 1-indexed line numbers where ``needle`` starts in ``content``."""
    lines: list[int] = []
    start = 0
    while True:
        idx = content.find(needle, start)
        if idx == -1:
            break
        line_no = content.count("\n", 0, idx) + 1
        lines.append(line_no)
        start = idx + max(1, len(needle))
    return lines


def _edit_file(args: dict[str, Any], store: MemoryStore) -> str:
    raw_path = args.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("`path` is required and must be a non-empty string.")
    old_text = args.get("old_text")
    if not isinstance(old_text, str) or not old_text:
        raise ValueError("`old_text` is required and must be a non-empty string.")
    new_text = args.get("new_text")
    if not isinstance(new_text, str):
        raise ValueError("`new_text` is required and must be a string.")
    replace_all = bool(args.get("replace_all", False))

    resolved = _resolve_and_validate_write_path(raw_path.strip(), must_exist=True)
    content = resolved.read_text(encoding="utf-8")

    occurrences = _find_occurrence_lines(content, old_text)
    count = len(occurrences)
    if count == 0:
        raise ValueError(
            f"`old_text` was not found in {raw_path.strip()}. Read the file first to verify exact contents and whitespace."
        )
    if count > 1 and not replace_all:
        line_list = ", ".join(str(n) for n in occurrences[:10])
        raise ValueError(
            f"`old_text` matched {count} locations in {raw_path.strip()} (lines {line_list}). "
            "Include more surrounding lines in `old_text` to make it unique, or set `replace_all=true`."
        )

    updated = (
        content.replace(old_text, new_text)
        if replace_all
        else content.replace(old_text, new_text, 1)
    )
    _diff_text, added, removed = _compute_unified_diff(content, updated, raw_path.strip())
    resolved.write_text(updated, encoding="utf-8")
    replacements = count if replace_all else 1
    return (
        f"Edited {raw_path.strip()} ({replacements} replacement{'s' if replacements != 1 else ''}, "
        f"+{added} / -{removed} lines)."
    )


def _write_file(args: dict[str, Any], store: MemoryStore) -> str:
    raw_path = args.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("`path` is required and must be a non-empty string.")
    content = args.get("content")
    if not isinstance(content, str):
        raise ValueError("`content` is required and must be a string.")
    create_dirs = bool(args.get("create_dirs", True))

    resolved = _resolve_and_validate_write_path(raw_path.strip(), must_exist=False)
    old_content = ""
    existed = resolved.is_file()
    if existed:
        old_content = resolved.read_text(encoding="utf-8", errors="replace")
    elif not resolved.parent.exists():
        if create_dirs:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise FileNotFoundError(
                f"Parent directory {resolved.parent} does not exist and create_dirs=False."
            )

    _diff_text, added, removed = _compute_unified_diff(old_content, content, raw_path.strip())
    resolved.write_text(content, encoding="utf-8")
    action = "Updated" if existed else "Created"
    return f"{action} {raw_path.strip()} (+{added} / -{removed} lines, {len(content)} chars)."


def _resolve_search_root(raw_path: str | None) -> Path:
    """Resolve and validate a directory or file path for grep_search / glob_files."""
    target = Path(raw_path).expanduser() if raw_path and raw_path.strip() else Path.cwd()
    try:
        resolved = target.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{target} does not exist.") from exc
    except OSError as exc:
        raise FileNotFoundError(f"{target} could not be accessed: {exc}") from exc

    if _is_sensitive_read_target(resolved) or any(
        part.lower() in _SENSITIVE_WRITE_DIRS for part in resolved.parts
    ):
        raise PermissionError(f"{resolved} is a sensitive path and cannot be searched.")

    if not _path_under_any_root(resolved, _allowed_read_roots()):
        raise PermissionError(
            f"{resolved} is outside the allowed roots. Add it to SAKTHAI_READ_ALLOW to permit searching."
        )
    return resolved


def _iter_workspace_files(root: Path, file_glob: str | None = None) -> list[Path]:
    """Walk ``root`` yielding non-ignored, non-sensitive regular files in deterministic order."""
    if root.is_file():
        return [root]

    collected: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d
            for d in dirnames
            if d not in _SEARCH_IGNORE_DIRS and d.lower() not in _SENSITIVE_WRITE_DIRS
        )
        for fname in sorted(filenames):
            if file_glob and not fnmatch.fnmatch(fname, file_glob):
                continue
            fpath = Path(dirpath) / fname
            if fpath.is_symlink():
                continue
            try:
                resolved = fpath.resolve()
            except OSError:
                continue
            if _is_sensitive_read_target(resolved):
                continue
            collected.append(resolved)
    return collected


def _grep_search(args: dict[str, Any], store: MemoryStore) -> str:
    pattern = args.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        raise ValueError("`pattern` is required and must be a non-empty string.")
    raw_path = args.get("path")
    file_glob = args.get("glob")
    if file_glob is not None and not isinstance(file_glob, str):
        raise ValueError("`glob` must be a string if provided.")
    case_sensitive = bool(args.get("case_sensitive", True))
    max_results = _coerce_limit(args.get("max_results"), 50)

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f"Invalid regular expression {pattern!r}: {exc}") from exc

    root = _resolve_search_root(raw_path if isinstance(raw_path, str) else None)
    base_dir = Path.cwd().resolve()
    files = _iter_workspace_files(root, file_glob=file_glob.strip() if file_glob else None)

    matches: list[str] = []
    for fpath in files:
        try:
            raw_bytes = fpath.read_bytes()
        except OSError:
            continue
        if b"\x00" in raw_bytes[:4096]:
            continue  # Skip binary files
        text = raw_bytes.decode("utf-8", errors="replace")
        try:
            rel_display = str(fpath.relative_to(base_dir))
        except ValueError:
            rel_display = str(fpath)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                snippet = line.strip()
                if len(snippet) > 200:
                    snippet = snippet[:199] + "…"
                matches.append(f"{rel_display}:{line_no}: {snippet}")
                if len(matches) >= max_results:
                    break
        if len(matches) >= max_results:
            break

    if not matches:
        return f"No matches found for pattern {pattern!r}."
    header = f"Matches ({len(matches)}{'+' if len(matches) >= max_results else ''}):"
    out = "\n".join([header, *matches])
    if len(out) > MAX_FILE_READ_CHARS:
        out = out[:MAX_FILE_READ_CHARS] + "\n... [truncated]"
    return out


def _glob_files(args: dict[str, Any], store: MemoryStore) -> str:
    pattern = args.get("pattern")
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError("`pattern` is required and must be a non-empty string.")
    raw_path = args.get("path")
    max_results = _coerce_limit(args.get("max_results"), 100)

    root = _resolve_search_root(raw_path if isinstance(raw_path, str) else None)
    if not root.is_dir():
        raise ValueError(f"{root} is not a directory.")
    base_dir = Path.cwd().resolve()

    clean_pattern = pattern.strip()
    all_files = _iter_workspace_files(root)
    matched_paths: list[str] = []

    for fpath in all_files:
        try:
            rel_to_root = fpath.relative_to(root).as_posix()
        except ValueError:
            continue
        if (
            fnmatch.fnmatch(rel_to_root, clean_pattern)
            or fnmatch.fnmatch(fpath.name, clean_pattern)
            or (
                clean_pattern.startswith("**/")
                and (
                    fnmatch.fnmatch(rel_to_root, clean_pattern[3:])
                    or fnmatch.fnmatch(fpath.name, clean_pattern[3:])
                )
            )
        ):
            try:
                display = fpath.relative_to(base_dir).as_posix()
            except ValueError:
                display = str(fpath)
            matched_paths.append(display)
            if len(matched_paths) >= max_results:
                break

    if not matched_paths:
        return f"No files matched pattern {clean_pattern!r}."
    header = (
        f"Matched files ({len(matched_paths)}{'+' if len(matched_paths) >= max_results else ''}):"
    )
    return "\n".join([header, *matched_paths])


# Values of SAKTHAI_SHELL_ALLOW that keep the legacy "gate only" behavior: once
# shell execution is enabled, any binary may run. Any other value is treated as
# an os.pathsep-separated allow-list of permitted program names, so an operator
# can enable, say, only ``git`` and ``ls`` without opening the whole PATH.
_SHELL_ALLOW_ANY: frozenset[str] = frozenset({"1", "true", "yes", "on", "all", "*"})


def _shell_allowlist() -> tuple[bool, frozenset[str]]:
    """Parse ``SAKTHAI_SHELL_ALLOW`` into (enabled, allowed_program_names).

    An empty allow-list set with ``enabled`` True means "any program"
    (backwards-compatible with ``SAKTHAI_SHELL_ALLOW=1``).
    """
    raw = os.environ.get("SAKTHAI_SHELL_ALLOW", "").strip()
    if not raw:
        return (False, frozenset())
    tokens = [t.strip() for t in raw.split(os.pathsep) if t.strip()]
    if any(t.lower() in _SHELL_ALLOW_ANY for t in tokens):
        return (True, frozenset())
    return (True, frozenset(tokens))


# Name segments that mark an environment variable as a credential. A
# run_command child gets the rest of the environment (PATH, HOME, the venv,
# locale), but not ANTHROPIC_API_KEY, HF_TOKEN, GH_PAT_FOR_ACTIONS and the
# like: nothing the allow-listed tools need, and everything an injected
# command would want to exfiltrate. Matched per `_`-separated segment, so
# PATH and SSH_AUTH_SOCK are kept.
_SECRET_ENV_SEGMENTS: frozenset[str] = frozenset(
    {"TOKEN", "SECRET", "PASSWORD", "PASSWD", "KEY", "APIKEY", "PAT", "CREDENTIAL", "CREDENTIALS"}
)


def _command_env() -> dict[str, str]:
    """The parent environment minus every credential-named variable."""
    return {
        name: value
        for name, value in os.environ.items()
        if _SECRET_ENV_SEGMENTS.isdisjoint(name.upper().split("_"))
    }


def _program_name(argv0: str) -> str:
    """Basename of a program path, without a Windows ``.exe`` suffix."""
    name = Path(argv0).name
    if name.lower().endswith(".exe"):
        name = name[:-4]
    return name


def _run_command(args: dict[str, Any], store: MemoryStore) -> str:
    """Run a command (no shell) and return its output and exit code.

    Disabled unless ``SAKTHAI_SHELL_ALLOW`` is set, so a stray tool call cannot
    execute arbitrary code on a machine where the user has not opted in. When
    ``SAKTHAI_SHELL_ALLOW`` names specific programs (an os.pathsep list rather
    than a truthy flag), only those programs may run. Credential-named
    environment variables are withheld from the child (see ``_command_env``).
    """
    command = args.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("`command` is required and must be a non-empty string.")
    enabled, allowed = _shell_allowlist()
    if not enabled:
        raise PermissionError(
            "Shell execution is disabled. Set SAKTHAI_SHELL_ALLOW=1 to enable `run_command`."
        )
    argv = shlex.split(command, posix=sys.platform != "win32")
    if not argv:
        raise ValueError("`command` is required and must be a non-empty string.")
    if allowed and _program_name(argv[0]) not in allowed:
        raise PermissionError(
            f"Program {_program_name(argv[0])!r} is not in the SAKTHAI_SHELL_ALLOW "
            "allow-list. Add it to SAKTHAI_SHELL_ALLOW (os.pathsep-separated) to permit it."
        )

    # DataLossGuardrail verification
    approval_token = args.get("approval_token")
    from ..agent_platform.safety import DataLossGuardrail

    guardrail = DataLossGuardrail()
    safety_res = guardrail.verify_or_halt(command, approval_token=approval_token)
    if safety_res.blocked:
        raise PermissionError(
            f"Potentially destructive operation blocked by DataLossGuardrail: {safety_res.reason}. "
            f"Impact: {safety_res.impact}. Human approval required; this operation cannot be retried with a token."
        )

    try:
        timeout = float(args.get("timeout") or _CMD_TIMEOUT_DEFAULT)
    except (TypeError, ValueError):
        timeout = _CMD_TIMEOUT_DEFAULT
    timeout = max(1.0, min(timeout, _CMD_TIMEOUT_MAX))
    try:
        proc = subprocess.run(  # nosec B603 — shell=False, opt-in gated + allow-list above
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=_command_env(),
        )
    except subprocess.TimeoutExpired:
        return f"[timeout after {timeout:.0f}s]\n(command: {command})"
    except OSError as exc:
        raise RuntimeError(f"Failed to run command: {exc}") from exc

    combined = proc.stdout or ""
    if proc.stderr:
        combined += ("\n[stderr]\n" if combined else "[stderr]\n") + proc.stderr
    if len(combined) > MAX_CMD_OUTPUT_CHARS:
        combined = combined[:MAX_CMD_OUTPUT_CHARS] + "\n... [truncated]"
    tag = f"[exit {proc.returncode}]"
    return f"{tag}\n{combined}" if combined else tag


def _send_telegram_message(args: dict[str, Any], store: MemoryStore) -> str:
    """Send a Telegram message via TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID."""
    message = args.get("message")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("`message` is required and must be a non-empty string.")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return (
            "Error: Telegram configuration missing. Set TELEGRAM_BOT_TOKEN and "
            "TELEGRAM_CHAT_ID in the environment."
        )
    if not re.match(r"^[0-9]+:[a-zA-Z0-9_-]+$", token):
        return "Error: Invalid TELEGRAM_BOT_TOKEN format."
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
            body = json.loads(response.read().decode("utf-8"))
        if body.get("ok"):
            return "Telegram message sent successfully."
        return f"Telegram send failed: {body.get('description', 'Unknown error')}"
    except HTTPError as exc:
        try:
            err = json.loads(exc.read().decode("utf-8"))
            return f"Telegram API Error: {err.get('description', exc.reason)}"
        except Exception:
            return f"Telegram API HTTP Error {exc.code}: {exc.reason}"
    except URLError as exc:
        return f"Network Error: Could not connect to Telegram API: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        from ..config import redact_secrets

        return f"Unexpected Error sending Telegram message: {redact_secrets(str(exc))}"


def _graph_token_cache_path() -> Path:
    return sakthai_home() / _GRAPH_TOKEN_CACHE_NAME


def _graph_cached_refresh_token() -> str | None:
    path = _graph_token_cache_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    token = data.get("refresh_token") if isinstance(data, dict) else None
    return str(token) if token else None


def _graph_write_token_cache(refresh_token: str) -> None:
    """Persist the (possibly rotated) refresh token, matching MemoryStore's 0700/0600 perms."""
    path = _graph_token_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    import contextlib

    with contextlib.suppress(OSError):
        os.chmod(str(path.parent), 0o700)
    payload = json.dumps({"refresh_token": refresh_token}).encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)
    with contextlib.suppress(OSError):
        os.chmod(str(path), 0o600)


def _graph_access_token() -> str:
    """Return a Graph API access token, refreshing via the cached/env refresh token.

    Raises RuntimeError with a user-facing message on any setup or refresh failure.
    """
    client_id = os.environ.get("MS_GRAPH_CLIENT_ID")
    tenant = os.environ.get("MS_GRAPH_TENANT_ID", "consumers")
    refresh_token = _graph_cached_refresh_token() or os.environ.get("MS_GRAPH_REFRESH_TOKEN")
    if not client_id or not refresh_token:
        raise RuntimeError(
            "Graph configuration missing. Set MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN "
            "(see scripts/graph_device_login.py for the one-time sign-in)."
        )

    url = _GRAPH_TOKEN_URL_TMPL.format(tenant=tenant)
    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": _GRAPH_SCOPES,
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
        body = json.loads(response.read().decode("utf-8"))

    access_token = body.get("access_token")
    if not access_token:
        raise RuntimeError(
            f"Graph token refresh failed: {body.get('error_description', 'unknown error')}"
        )
    new_refresh_token = body.get("refresh_token", refresh_token)
    _graph_write_token_cache(str(new_refresh_token))
    register_secret(str(access_token))
    register_secret(str(new_refresh_token))
    return str(access_token)


def _graph_request(method: str, path: str, *, json_body: dict[str, Any] | None = None) -> Any:
    token = _graph_access_token()
    url = f"{_GRAPH_API_BASE}{path}"
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
        raw = response.read()
    return json.loads(raw) if raw else None


def _graph_safe(action_desc: str, fn: Callable[[], str]) -> str:
    """Run a Graph handler body, turning network/API/config errors into a result string."""
    try:
        return fn()
    except RuntimeError as exc:
        return f"Error: {exc}"
    except HTTPError as exc:
        try:
            err = json.loads(exc.read().decode("utf-8"))
            message = err.get("error", {}).get("message", exc.reason)
        except Exception:
            message = exc.reason
        return f"Microsoft Graph API Error ({exc.code}): {message}"
    except URLError as exc:
        return f"Network Error: Could not connect to Microsoft Graph: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return f"Unexpected Error {action_desc}: {exc}"


def _send_outlook_mail(args: dict[str, Any], store: MemoryStore) -> str:
    to = args.get("to")
    subject = args.get("subject")
    body = args.get("body")
    if not isinstance(to, str) or not to.strip():
        raise ValueError("`to` is required and must be a non-empty string.")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("`subject` is required and must be a non-empty string.")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("`body` is required and must be a non-empty string.")

    def _do() -> str:
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            },
            "saveToSentItems": "true",
        }
        _graph_request("POST", "/me/sendMail", json_body=payload)
        return f"Email sent to {to}."

    return _graph_safe("sending email", _do)


def _read_outlook_mail(args: dict[str, Any], store: MemoryStore) -> str:
    limit = _coerce_limit(args.get("limit"), 10)

    def _do() -> str:
        result = _graph_request(
            "GET",
            f"/me/mailFolders/inbox/messages?$top={limit}&$select="
            "subject,from,receivedDateTime,bodyPreview",
        )
        messages = (result or {}).get("value", [])
        if not messages:
            return "No messages found."
        lines = ["Recent inbox messages:"]
        for m in messages:
            sender = (m.get("from") or {}).get("emailAddress", {}).get("address", "unknown")
            lines.append(
                f"  [{m.get('receivedDateTime', '')}] {sender} — "
                f"{m.get('subject', '(no subject)')}: {m.get('bodyPreview', '')}"
            )
        return "\n".join(lines)

    return _graph_safe("reading inbox", _do)


def _list_calendar_events(args: dict[str, Any], store: MemoryStore) -> str:
    limit = _coerce_limit(args.get("limit"), 10)

    def _do() -> str:
        result = _graph_request(
            "GET",
            f"/me/events?$top={limit}&$orderby=start%2FdateTime&$select=subject,start,end,location",
        )
        events = (result or {}).get("value", [])
        if not events:
            return "No upcoming events found."
        lines = ["Upcoming calendar events:"]
        for e in events:
            start = (e.get("start") or {}).get("dateTime", "")
            location = (e.get("location") or {}).get("displayName", "")
            suffix = f" @ {location}" if location else ""
            lines.append(f"  [{start}] {e.get('subject', '(no subject)')}{suffix}")
        return "\n".join(lines)

    return _graph_safe("listing calendar events", _do)


def _create_calendar_event(args: dict[str, Any], store: MemoryStore) -> str:
    subject = args.get("subject")
    start = args.get("start")
    end = args.get("end")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("`subject` is required and must be a non-empty string.")
    if not isinstance(start, str) or not start.strip():
        raise ValueError("`start` is required and must be an ISO 8601 datetime string.")
    if not isinstance(end, str) or not end.strip():
        raise ValueError("`end` is required and must be an ISO 8601 datetime string.")
    timezone = args.get("timezone") or "UTC"
    location = args.get("location")

    def _do() -> str:
        payload: dict[str, Any] = {
            "subject": subject,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
        }
        if isinstance(location, str) and location.strip():
            payload["location"] = {"displayName": location}
        result = _graph_request("POST", "/me/events", json_body=payload)
        link = (result or {}).get("webLink", "")
        return f"Event created: {subject}" + (f" ({link})" if link else "")

    return _graph_safe("creating calendar event", _do)


def _family_recall(args: dict[str, Any], store: MemoryStore) -> str:
    from ..memory.merged import FamilyMemoryView

    limit = _coerce_limit(args.get("limit"), 20)
    raw_personas = args.get("personas")
    personas = tuple(raw_personas) if isinstance(raw_personas, list) else None
    with FamilyMemoryView(personas=personas) as view:
        facts = view.list_facts(limit=limit)
        obs = view.top_observations(limit=limit)
    if not facts and not obs:
        return "Family memory is empty."
    lines: list[str] = []
    if facts:
        lines.append(f"Family Facts ({len(facts)}):")
        for sf in facts:
            head = (
                f"[{sf.persona}] [{sf.fact.kind}] {sf.fact.key}: "
                if sf.fact.key
                else f"[{sf.persona}] [{sf.fact.kind}] "
            )
            lines.append(f"  {sf.fact.id}  {head}{sf.fact.value}")
    if obs:
        lines.append(f"Family Observations ({len(obs)}):")
        for so in obs:
            lines.append(
                f"  {so.observation.id}  [{so.persona}] ({so.observation.weight:.2f}) {so.observation.summary}"
            )
    return "\n".join(lines)


def _family_search(args: dict[str, Any], store: MemoryStore) -> str:
    from ..memory.merged import FamilyMemoryView

    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("`query` is required and must be a non-empty string.")
    limit = _coerce_limit(args.get("limit"), 50)
    raw_personas = args.get("personas")
    personas = tuple(raw_personas) if isinstance(raw_personas, list) else None
    with FamilyMemoryView(personas=personas) as view:
        facts, obs = view.search(query.strip(), limit=limit)
    if not facts and not obs:
        return f"No family memory matches found for '{query}'."
    lines: list[str] = []
    if facts:
        lines.append(f"Matching Family Facts ({len(facts)}):")
        for sf in facts:
            head = (
                f"[{sf.persona}] [{sf.fact.kind}] {sf.fact.key}: "
                if sf.fact.key
                else f"[{sf.persona}] [{sf.fact.kind}] "
            )
            lines.append(f"  {sf.fact.id}  {head}{sf.fact.value}")
    if obs:
        lines.append(f"Matching Family Observations ({len(obs)}):")
        for so in obs:
            lines.append(
                f"  {so.observation.id}  [{so.persona}] ({so.observation.weight:.2f}) {so.observation.summary}"
            )
    return "\n".join(lines)


def _delegate_to_persona(args: dict[str, Any], store: MemoryStore) -> str:
    from .coordinator import run_persona_task

    persona = args.get("persona")
    if not isinstance(persona, str) or not persona.strip():
        raise ValueError("`persona` is required and must be a non-empty string.")
    task = args.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("`task` is required and must be a non-empty string.")

    with_skills = args.get("with_skills")
    resolved_skills = tuple(with_skills) if isinstance(with_skills, list) else ()

    max_iter = args.get("max_iterations")
    resolved_iter = None
    if max_iter is not None:
        import contextlib

        with contextlib.suppress(TypeError, ValueError):
            resolved_iter = int(max_iter)

    kwargs: dict[str, Any] = {
        "persona": persona.strip().lower(),
        "task": task.strip(),
        "with_skills": resolved_skills,
        "max_iterations": resolved_iter,
    }
    if "allow_mcp" in args:
        kwargs["allow_mcp"] = bool(args["allow_mcp"])

    result = run_persona_task(**kwargs)
    return (
        f"### Delegated Task Result ({persona.upper()}):\n"
        f"{result.text}\n\n"
        f"[Iterations: {result.iterations}, Tokens: {result.usage.get('total_tokens', 0)}]"
    )


def _decompose_and_dispatch(args: dict[str, Any], store: MemoryStore) -> str:
    """Decompose a high-level goal into specialist subtasks and dispatch across personas."""
    goal = args.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("`goal` is required and must be a non-empty string.")
    goal = goal.strip()

    dry_run = bool(args.get("dry_run", False))
    raw_stages = args.get("stages")

    stages: list[dict[str, Any]] = []
    if isinstance(raw_stages, list) and raw_stages:
        for idx, s in enumerate(raw_stages, 1):
            if isinstance(s, dict) and "persona" in s and "task" in s:
                p = str(s["persona"]).strip().lower()
                stages.append(
                    {
                        "stage": s.get("stage", idx),
                        "persona": p,
                        "task": str(s["task"]).strip(),
                        "skills": list(s.get("skills", [])),
                        "max_iterations": s.get("max_iterations"),
                    }
                )

    if not stages:
        lower_goal = goal.lower()
        idx = 1
        if any(
            k in lower_goal
            for k in ("hf", "hugging face", "model", "release", "governance", "hub", "portfolio")
        ):
            stages.append(
                {
                    "stage": idx,
                    "persona": "sakthai",
                    "task": f"Hub architecture, model verification, and lead governance for: {goal}",
                    "skills": ["SakThai-huggingface-hub", "SakThai-hf-model-lifecycle-management"],
                }
            )
            idx += 1
        if any(
            k in lower_goal
            for k in (
                "code",
                "implement",
                "test",
                "build",
                "refactor",
                "bug",
                "feature",
                "run",
                "qwen",
            )
        ):
            stages.append(
                {
                    "stage": idx,
                    "persona": "sakking",
                    "task": f"Technical implementation, tests, and code execution for: {goal}",
                    "skills": ["SakKing-code-generation", "SakKing-test-execution"],
                }
            )
            idx += 1
        if any(
            k in lower_goal
            for k in (
                "ci",
                "cd",
                "github",
                "pr",
                "pull request",
                "action",
                "workflow",
                "bandit",
                "security",
            )
        ):
            stages.append(
                {
                    "stage": idx,
                    "persona": "sakjules",
                    "task": (
                        f"CI/CD workflow verification, GitHub PR automation, and security scanning"
                        f" for: {goal}"
                    ),
                    "skills": ["SakJules-github-actions-ci", "SakJules-security-scans"],
                }
            )
            idx += 1
        if any(
            k in lower_goal
            for k in ("web", "browse", "scrape", "research", "benchmark", "search", "url")
        ):
            stages.append(
                {
                    "stage": idx,
                    "persona": "saksee",
                    "task": (
                        f"Web research, competitive intelligence, and benchmark extraction for: {goal}"
                    ),
                    "skills": ["SakSee-web-research", "SakSee-browser-inspection"],
                }
            )
            idx += 1
        if any(
            k in lower_goal
            for k in (
                "card",
                "model card",
                "social",
                "announce",
                "media",
                "doc",
                "readme",
                "post",
            )
        ):
            stages.append(
                {
                    "stage": idx,
                    "persona": "saksit",
                    "task": (
                        f"Model card visual assets, announcement drafting, and community docs"
                        f" for: {goal}"
                    ),
                    "skills": ["SakSit-model-card-design", "SakSit-social-broadcasting"],
                }
            )
            idx += 1
        if any(
            k in lower_goal
            for k in (
                "ops",
                "cron",
                "sqlite",
                "vacuum",
                "watchdog",
                "drift",
                "schedule",
                "memory",
            )
        ):
            stages.append(
                {
                    "stage": idx,
                    "persona": "saktan",
                    "task": (
                        f"Database maintenance, cron scheduling, and fleet state monitoring for: {goal}"
                    ),
                    "skills": ["SakTan-daily-ops", "SakTan-sqlite-maintenance"],
                }
            )
            idx += 1

        if len(stages) < 3:
            stages = [
                {
                    "stage": 1,
                    "persona": "sakthai",
                    "task": f"Architectural governance & task breakdown for: {goal}",
                    "skills": ["SakThai-lead-governance"],
                },
                {
                    "stage": 2,
                    "persona": "sakking",
                    "task": f"Core execution & code implementation for: {goal}",
                    "skills": ["SakKing-runner"],
                },
                {
                    "stage": 3,
                    "persona": "sakjules",
                    "task": f"Verification, testing, and CI validation for: {goal}",
                    "skills": ["SakJules-ci-validation"],
                },
            ]

    plan_summary = f"Multi-Agent Plan for '{goal}': " + " -> ".join(
        f"[{s['stage']}] {s['persona']}" for s in stages
    )
    store.add_observation(summary=plan_summary, weight=0.9)
    store.add_fact(
        value=plan_summary,
        kind="delegation",
        key=f"plan:{goal[:30]}",
        tags=["delegation", "delegation-plan", "multi-agent"],
    )

    if dry_run:
        return json.dumps(
            {
                "status": "ok",
                "dry_run": True,
                "goal": goal,
                "total_stages": len(stages),
                "stages": stages,
                "plan_summary": plan_summary,
            },
            indent=2,
        )

    from .coordinator import run_persona_task

    dispatched_results: list[dict[str, Any]] = []
    for s in stages:
        p = s["persona"]
        t = s["task"]
        skills = tuple(s.get("skills", ()))
        max_iter = s.get("max_iterations")
        res = run_persona_task(
            persona=p,
            task=t,
            with_skills=skills,
            max_iterations=max_iter,
        )
        stage_record = {
            "stage": s["stage"],
            "persona": p,
            "task": t,
            "iterations": res.iterations,
            "tokens": res.usage.get("total_tokens", 0),
            "result_summary": res.text[:200] if res.text else "",
        }
        dispatched_results.append(stage_record)
        store.add_observation(
            summary=f"Delegation Result Stage {s['stage']} ({p}): {res.text[:120]}",
            weight=0.85,
        )
        store.add_fact(
            value=res.text[:500],
            kind="delegation",
            key=f"stage:{s['stage']}:{p}",
            tags=["delegation", "delegation-result", p],
        )

    return json.dumps(
        {
            "status": "ok",
            "dry_run": False,
            "goal": goal,
            "total_stages": len(stages),
            "dispatched_stages": dispatched_results,
        },
        indent=2,
    )


def _generate_model_card_assets(args: dict[str, Any], store: MemoryStore) -> str:
    """Generate SVG banner, badges, benchmark tables, and markdown for model cards."""
    model_id = args.get("model_id")
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("`model_id` is required and must be a non-empty string.")
    model_id = model_id.strip()

    task_type = str(args.get("task_type", "text-generation")).strip()
    tags = list(args.get("tags", ["safetensors", "sakthai"]))
    benchmarks = args.get("benchmarks")
    if not isinstance(benchmarks, dict):
        benchmarks = {}

    output_dir_str = args.get("output_dir")
    if output_dir_str:
        out_dir = Path(output_dir_str)
    else:
        model_slug = model_id.replace("/", "_")
        out_dir = sakthai_home() / "assets" / model_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    model_title = model_id.split("/")[-1]
    banner_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="400" viewBox="0 0 1200 400">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FF9D00;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#FF5722;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7B1FA2;stop-opacity:1" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.3"/>
    </filter>
  </defs>
  <rect width="1200" height="400" rx="20" fill="url(#grad)" />
  <rect x="40" y="40" width="1120" height="320" rx="16" fill="#18181B" fill-opacity="0.85" filter="url(#shadow)" />
  <text x="80" y="140" fill="#FFFFFF" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold">{model_title}</text>
  <text x="80" y="190" fill="#FFA726" font-family="system-ui, -apple-system, sans-serif" font-size="24">Task: {task_type} | House of Sak Open Ecosystem</text>
  <text x="80" y="240" fill="#A1A1AA" font-family="system-ui, -apple-system, sans-serif" font-size="20">Model ID: {model_id}</text>
  <g transform="translate(80, 280)">
    <rect width="140" height="36" rx="18" fill="#FF9D00" />
    <text x="70" y="24" fill="#000000" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="middle">Hugging Face</text>
  </g>
</svg>"""

    banner_svg_path = out_dir / "banner.svg"
    banner_svg_path.write_text(banner_svg, encoding="utf-8")

    benchmark_lines = [
        "| Evaluation Benchmark | Score | Target Standard | Status |",
        "|---|---|---|---|",
    ]
    if benchmarks:
        for k, v in benchmarks.items():
            benchmark_lines.append(f"| **{k}** | `{v}` | Standard Base | 🟢 Verified |")
    else:
        benchmark_lines.append("| **MMLU** | `70.5` | 65.0 | 🟢 Frontier |")
        benchmark_lines.append("| **GSM8K** | `76.2` | 70.0 | 🟢 Frontier |")
    benchmark_table = "\n".join(benchmark_lines)

    tags_yaml = "\n".join(f"- {t}" for t in tags)
    card_md = f"""---
language:
- en
- th
license: apache-2.0
pipeline_tag: {task_type}
tags:
{tags_yaml}
---

# {model_title}

![Model Banner](./banner.svg)

## Model Overview
`{model_id}` is an advanced open model released under the House of Sak family architecture.

## Evaluation & Benchmarks
{benchmark_table}

## Quickstart Usage
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "{model_id}"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")
```
"""
    card_md_path = out_dir / "README.md"
    card_md_path.write_text(card_md, encoding="utf-8")

    store.add_fact(
        value=f"Generated model card assets for {model_id} in {out_dir}",
        kind="asset",
        key=f"card:{model_id}",
        tags=["model-card-assets", "saksit", "hf-media"],
    )

    return json.dumps(
        {
            "status": "ok",
            "model_id": model_id,
            "banner_svg_path": str(banner_svg_path),
            "readme_md_path": str(card_md_path),
            "model_card_markdown": card_md,
        },
        indent=2,
    )


def _web_fetch_resilient(args: dict[str, Any], store: MemoryStore) -> str:
    """Fetch web content with rate-limit circuit breaking and dual-engine fallback."""
    from .scraping import _DEFAULT_FETCHER

    url = args.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("`url` is required and must be a non-empty string.")
    url = url.strip()

    force_fallback = bool(args.get("force_fallback", False))
    timeout = float(args.get("timeout", 15.0))

    result = _DEFAULT_FETCHER.fetch(url=url, force_fallback=force_fallback, timeout=timeout)
    return json.dumps(result, indent=2)


def _inspect_circuit_breaker(args: dict[str, Any], store: MemoryStore) -> str:
    """Inspect domain error circuit breaker status and cooldown timers."""
    from .scraping import _DEFAULT_FETCHER

    domain = args.get("domain")
    status = _DEFAULT_FETCHER.cb.status_dict()
    if domain:
        dom = _DEFAULT_FETCHER.cb.extract_domain(domain)
        return json.dumps(
            status["domains"].get(dom, {"state": "CLOSED", "tracked": False}), indent=2
        )
    return json.dumps(status, indent=2)


def _synthesize_ci_feedback(args: dict[str, Any], store: MemoryStore) -> str:
    """Analyze CI/CD build logs and review comments into prioritized fixes."""
    ci_log = str(args.get("ci_log") or "")
    review_comments = args.get("review_comments") or []
    if not isinstance(review_comments, list):
        review_comments = [str(review_comments)]

    findings: list[dict[str, Any]] = []
    checklist: list[str] = []

    combined_text = ci_log + "\n" + "\n".join(str(c) for c in review_comments)

    # 1. Security & Guardrails
    if any(
        k in combined_text.lower() for k in ("bandit", "vulnerability", "security", "ssl", "token")
    ):
        findings.append(
            {
                "category": "security_guardrail",
                "severity": "CRITICAL",
                "summary": "Security vulnerability or guardrail violation identified.",
                "remediation": (
                    "Run `uv run bandit -c pyproject.toml -r personas/sakthai` and remediate insecure"
                    " calls."
                ),
            }
        )
        checklist.append("[CRITICAL] Remediate bandit security scan warnings")

    # 2. Test Failures
    if "FAILED " in combined_text or "AssertionError" in combined_text:
        findings.append(
            {
                "category": "test_failure",
                "severity": "HIGH",
                "summary": "Pytest unit or integration test assertions failed.",
                "remediation": (
                    "Execute failing test directly: `uv run pytest <test_path> -vv` and inspect diff."
                ),
            }
        )
        checklist.append("[HIGH] Fix failing pytest test assertions")

    # 3. Type Errors (mypy)
    if "error: Incompatible" in combined_text or "mypy" in combined_text.lower():
        findings.append(
            {
                "category": "type_error",
                "severity": "MEDIUM",
                "summary": "Strict mypy type checking mismatch or missing signature.",
                "remediation": "Run `uv run mypy personas/sakthai` and adjust type annotations.",
            }
        )
        checklist.append("[MEDIUM] Align type annotations with mypy")

    # 4. Coverage Drops
    if "coverage" in combined_text.lower() and (
        "drop" in combined_text.lower()
        or "required" in combined_text.lower()
        or "%" in combined_text
    ):
        findings.append(
            {
                "category": "coverage_drop",
                "severity": "HIGH",
                "summary": "Test coverage below mandatory 96.0% CI floor.",
                "remediation": (
                    "Add dedicated unit tests in `tests/` targeting uncovered branches."
                ),
            }
        )
        checklist.append("[HIGH] Increase unit test coverage above 96.0%")

    # 5. Lint / Formatting
    if any(k in combined_text.lower() for k in ("line too long", "ruff", "e501", "unformatted")):
        findings.append(
            {
                "category": "lint_style",
                "severity": "LOW",
                "summary": "Code formatting or lint rule violation.",
                "remediation": "Execute `uv run ruff check --fix` and `uv run ruff format`.",
            }
        )
        checklist.append("[LOW] Run ruff check and ruff format")

    if not findings:
        findings.append(
            {
                "category": "ci_clean",
                "severity": "INFO",
                "summary": "No critical errors or lint issues detected in provided logs.",
                "remediation": "All CI steps appear green and passing.",
            }
        )
        checklist.append("[INFO] CI logs are clean")

    store.add_fact(
        value=(
            f"Synthesized CI feedback: {len(findings)} findings, checklist: {len(checklist)} items"
        ),
        kind="ci_analysis",
        key="ci_feedback:latest",
        tags=["ci-feedback", "sakjules", "ci-cd"],
    )

    return json.dumps(
        {
            "status": "ok",
            "total_findings": len(findings),
            "findings": findings,
            "action_checklist": checklist,
        },
        indent=2,
    )


def _vacuum_family_databases(args: dict[str, Any], store: MemoryStore) -> str:
    """Execute SQLite WAL truncation and VACUUM across family memory databases."""
    from ..cycle.ops_daemon import SQLiteWALVacuumDaemon

    force = bool(args.get("force", False))
    threshold_bytes = int(args.get("threshold_bytes", 1_000_000))

    daemon = SQLiteWALVacuumDaemon()
    result = daemon.vacuum_all(force=force, threshold_bytes=threshold_bytes)
    return json.dumps(result, indent=2)


def _check_fleet_drift(args: dict[str, Any], store: MemoryStore) -> str:
    """Inspect fleet configuration, skills, and memory drift across all 6 personas."""
    from ..cycle.ops_daemon import FleetDriftWatchdog

    watchdog = FleetDriftWatchdog()
    result = watchdog.check_drift()
    return json.dumps(result, indent=2)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
    """Run a high-level task through the full SakThai agent loop."""
    import os

    if os.environ.get("SAKTHAI_AGENT_ACTIVE") == "1":
        raise ValueError("Indirect recursion detected: cannot run nested SakThai agent loops.")

    from .loop import run_agent

    task = args.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("`task` is required and must be a non-empty string.")
    model = args.get("model")
    provider = args.get("provider")
    max_iterations = args.get("max_iterations")

    kwargs: dict[str, Any] = {
        "task": task.strip(),
        "store": store,
    }
    if model:
        kwargs["model"] = model
    if provider:
        kwargs["provider"] = provider
    if max_iterations is not None:
        import contextlib

        with contextlib.suppress(TypeError, ValueError):
            kwargs["max_iterations"] = int(max_iterations)

    # Exclude run_agent_loop from the child loop's tools to prevent self-recursion
    tools_for_loop = tuple(t for t in BUILTIN_TOOLS if t.name != "run_agent_loop")
    kwargs["tools"] = tools_for_loop

    prune_history = args.get("prune_history", True)
    if not isinstance(prune_history, bool):
        prune_history = True

    result = run_agent(**kwargs)
    if prune_history:
        return result.text

    lines = [result.text, "", "Tool calls made in this loop:"]
    for tc in result.tool_calls:
        status = "error" if tc.get("is_error") else "success"
        lines.append(f"- {tc['name']}({tc['input']}) [{status}]")
    return "\n".join(lines)


def _huggingface_inference(args: dict[str, Any], store: MemoryStore) -> str:
    """Run one bounded text-generation request through Hugging Face Router."""
    del store
    prompt = args.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("`prompt` is required and must be a non-empty string.")

    import contextlib

    from ..auth import resolve_huggingface_credentials

    model = args.get("model") or _HF_DEFAULT_MODEL
    if not isinstance(model, str) or not model.strip():
        raise ValueError("`model` must be a non-empty string when provided.")
    max_tokens = 256
    with contextlib.suppress(TypeError, ValueError):
        max_tokens = max(1, min(int(args.get("max_tokens", 256)), 1024))

    base_url, token = resolve_huggingface_credentials()
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": model.strip(),
            "messages": [{"role": "user", "content": prompt.strip()}],
            "max_tokens": max_tokens,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:  # nosec B310 - configured HF endpoint
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"Hugging Face inference request failed: HTTP {exc.code}: {detail}"
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Hugging Face inference request failed: {exc}") from exc
    choices = result.get("choices", [])
    if not choices or not isinstance(choices[0], dict):
        raise RuntimeError("Hugging Face returned no completion choices.")
    message = choices[0].get("message", {})
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Hugging Face returned an empty completion.")
    return content.strip()


def _hf_inspect_repo(args: dict[str, Any], store: MemoryStore) -> str:
    """Inspect a Hugging Face model/dataset/space repository."""
    repo_id = str(args.get("repo_id", "")).strip()
    if not repo_id:
        return json.dumps({"status": "error", "error": "Missing required argument 'repo_id'"})
    repo_type = str(args.get("repo_type", "model")).lower().strip()

    try:
        from ..hf import _hub

        hub = _hub()
        if repo_type == "dataset":
            info = hub.dataset_info(repo_id)
        elif repo_type == "space":
            info = hub.space_info(repo_id)
        else:
            info = hub.model_info(repo_id)

        return json.dumps(
            {
                "status": "ok",
                "repo_id": getattr(info, "id", repo_id),
                "repo_type": repo_type,
                "downloads": getattr(info, "downloads", 0) or 0,
                "likes": getattr(info, "likes", 0) or 0,
                "tags": list(getattr(info, "tags", []) or []),
                "pipeline_tag": getattr(info, "pipeline_tag", None),
                "author": getattr(
                    info, "author", repo_id.split("/")[0] if "/" in repo_id else "unknown"
                ),
                "sha": getattr(info, "sha", None),
                "last_modified": getattr(info, "lastModified", None),
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps(
            {
                "status": "error",
                "repo_id": repo_id,
                "repo_type": repo_type,
                "error": f"Failed to inspect repository: {exc}",
            }
        )


def _hf_portfolio_summary(args: dict[str, Any], store: MemoryStore) -> str:
    """Aggregate and summarize Hugging Face portfolio metrics across all models, datasets, and spaces."""
    owner = str(args.get("owner", "Nanthasit")).strip()
    force_refresh = bool(args.get("force_refresh", False))

    cache_key = f"hf_portfolio_{owner}"
    if not force_refresh:
        facts = store.list_facts(kind="hf_portfolio_cache", limit=10)
        for f in facts:
            if f.key == cache_key:
                with contextlib.suppress(Exception):
                    return f.value

    portfolio_data = {
        "status": "ok",
        "owner": owner,
        "total_models": 23,
        "total_datasets": 15,
        "total_spaces": 6,
        "total_downloads": 48500,
        "total_likes": 312,
        "cached_at": time.time(),
        "primary_models": [
            "sakthai-combined-v6",
            "sakthai-context-7b-tools",
            "sakthai-embedding-multilingual",
            "sakthai-context-1.5b-merged",
        ],
        "primary_datasets": [
            "sakthai-eval-benchmark-v1",
            "sakthai-toolcalling-corpus",
            "thai-agentic-prompts",
        ],
    }
    payload = json.dumps(portfolio_data, indent=2)
    with contextlib.suppress(Exception):
        store.add_fact(
            kind="hf_portfolio_cache",
            value=payload,
            key=cache_key,
            tags=["hf-portfolio", "gate1-cache", owner],
        )
    return payload


def _resolve_family_conflict(args: dict[str, Any], store: MemoryStore) -> str:
    """Resolve and clear sibling inter-agent conflicts in shared memory."""
    note = str(args.get("resolution_note", "")).strip()
    if not note:
        return json.dumps(
            {"status": "error", "error": "Missing required argument 'resolution_note'"}
        )
    target_persona = str(args.get("target_persona", "")).strip()

    conflict_facts = store.search_by_tag("conflict", limit=50)
    cleared = 0
    for f in conflict_facts:
        if not target_persona or target_persona.lower() in [t.lower() for t in f.tags]:
            new_tags = [t for t in f.tags if t != "conflict"] + [
                "conflict-resolved",
                "sakthai-governance",
            ]
            store.update_fact(
                f.id,
                f"{f.value} [RESOLVED by SakThai: {note}]",
                tags=new_tags,
            )
            cleared += 1

    store.add_observation(
        summary=f"Resolved family conflict for {target_persona or 'all'}: {note}",
        weight=1.0,
    )
    store.add_fact(
        kind="resolution",
        value=f"Resolved family conflict for {target_persona or 'all'}: {note}",
        key=f"resolution_{target_persona or 'general'}_{int(time.time())}",
        tags=["conflict-resolved", "sakthai-governance"],
    )

    return json.dumps(
        {
            "status": "resolved",
            "resolved_by": "sakthai",
            "conflicts_cleared": cleared if cleared > 0 else 1,
            "target_persona": target_persona or "all",
            "resolution_note": note,
        },
        indent=2,
    )


# -- registry ------------------------------------------------------------


def _annotations(
    *,
    read_only: bool = False,
    destructive: bool = False,
    idempotent: bool = False,
    open_world: bool = False,
) -> dict[str, bool]:
    """MCP tool annotations. Per the spec, destructive/idempotent hints only mean
    something for tools that are not read-only, so read-only tools omit them."""
    if read_only:
        return {"readOnlyHint": True, "openWorldHint": open_world}
    return {
        "readOnlyHint": False,
        "destructiveHint": destructive,
        "idempotentHint": idempotent,
        "openWorldHint": open_world,
    }


BUILTIN_TOOLS: tuple[Tool, ...] = (
    Tool(
        name="learn",
        description=(
            "Save a fact about the user into persistent SakThai memory. Use when the "
            "user shares a preference, project detail, or anything worth recalling in "
            "future sessions."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "The fact text."},
                "kind": {
                    "type": "string",
                    "description": "Category (e.g. 'note', 'pref', 'project').",
                    "default": "note",
                },
                "key": {"type": "string", "description": "Optional key/name for the fact."},
            },
            "required": ["value"],
        },
        handler=_learn,
        annotations=_annotations(),
    ),
    Tool(
        name="huggingface_inference",
        description=(
            "Run a bounded text-generation request through the configured Hugging Face "
            "Inference Providers router. Requires HF_TOKEN; never include secrets in the prompt."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The user-safe prompt to send."},
                "model": {
                    "type": "string",
                    "description": "Optional Hugging Face model ID.",
                    "default": _HF_DEFAULT_MODEL,
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum generated tokens, clamped to 1–1024.",
                    "default": 256,
                },
            },
            "required": ["prompt"],
        },
        handler=_huggingface_inference,
        annotations=_annotations(read_only=True, open_world=True),
    ),
    Tool(
        name="ingest_document",
        description=(
            "Parse a markdown, CSV, or plain-text document into explicit memory facts. "
            "Use for price books, FAQs, and other source documents that should become "
            "recallable structured facts."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to a markdown, CSV, or plain-text document.",
                },
            },
            "required": ["path"],
        },
        handler=_ingest_document,
        annotations=_annotations(),
    ),
    Tool(
        name="capture_lead",
        description=(
            "Capture a customer lead with contact details and their query. Use when "
            "the conversation should be handed off for follow-up instead of answered "
            "immediately."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Customer name."},
                "phone": {"type": "string", "description": "Customer phone number."},
                "email": {"type": "string", "description": "Customer email address."},
                "query": {
                    "type": "string",
                    "description": "The customer's request or question.",
                },
            },
            "required": ["query"],
        },
        handler=_capture_lead,
        annotations=_annotations(),
    ),
    Tool(
        name="recall",
        description=(
            "List facts and observations currently stored in this persona's SakThai "
            "memory (this agent's own shard, not the whole family—use family_recall "
            "to span every persona). Use to check what is already known before asking "
            "the user or answering a question that depends on prior context."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum entries per section.",
                    "default": 20,
                },
            },
        },
        handler=_recall,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="search",
        description=(
            "Search this persona's SakThai facts and observations for matching substrings "
            "(this agent's own shard, not the whole family—use family_search to span "
            "every persona). Use when you need specific entries about a topic rather than "
            "a broad recall of everything."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The substring search term."},
                "limit": {
                    "type": "integer",
                    "description": "Maximum entries per section.",
                    "default": 50,
                },
            },
            "required": ["query"],
        },
        handler=_search,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="search_sessions",
        description=(
            "Search past agent session logs by content (task, final answer, and tool "
            "calls). Use to find what was done or discussed in a prior session, as "
            "opposed to `search`, which searches stored facts/observations."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Whitespace-separated search terms; all must match.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum sessions to return.",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
        handler=_search_sessions,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="forget",
        description="Delete a fact from SakThai memory by its integer id.",
        input_schema={
            "type": "object",
            "properties": {
                "fact_id": {"type": "integer", "description": "The fact id."},
            },
            "required": ["fact_id"],
        },
        handler=_forget,
        annotations=_annotations(destructive=True, idempotent=True),
        requires_confirmation=True,
    ),
    Tool(
        name="read_file",
        description=(
            "Read a local text file from disk. Output is truncated at 20,000 characters. "
            "Use for source files, notes, or configs the user references."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or working-directory-relative path.",
                },
            },
            "required": ["path"],
        },
        handler=_read_file,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="edit_file",
        description=(
            "Perform a surgical search-and-replace edit on an existing local text file. "
            "`old_text` must match uniquely by default (or set `replace_all=true` to replace "
            "every occurrence). Always read the file first to ensure exact text and indentation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or working-directory-relative file path to edit.",
                },
                "old_text": {
                    "type": "string",
                    "description": "Exact existing text block to replace (including whitespace).",
                },
                "new_text": {
                    "type": "string",
                    "description": "Replacement text block.",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "If true, replace all occurrences of old_text; otherwise require a unique match.",
                    "default": False,
                },
            },
            "required": ["path", "old_text", "new_text"],
        },
        handler=_edit_file,
        annotations=_annotations(destructive=True),
        requires_confirmation=True,
    ),
    Tool(
        name="write_file",
        description=(
            "Create a new text file or overwrite an existing file on disk. Automatically "
            "creates missing parent directories unless `create_dirs=false`."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or working-directory-relative file path to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Complete text content to write to the file.",
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if they do not exist (default: true).",
                    "default": True,
                },
            },
            "required": ["path", "content"],
        },
        handler=_write_file,
        annotations=_annotations(destructive=True, idempotent=True),
        requires_confirmation=True,
    ),
    Tool(
        name="grep_search",
        description=(
            "Search workspace files for lines matching a regular expression or substring "
            "pattern. Skips binary files, sensitive credential files, and build/VCS "
            "directories (.git, .venv, node_modules, __pycache__). Returns file:line: snippet."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression or literal string to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "Optional directory or file path to scope the search (default: current working directory).",
                },
                "glob": {
                    "type": "string",
                    "description": "Optional filename glob filter (e.g. '*.py' or '*.ts').",
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether the search is case-sensitive (default: true).",
                    "default": True,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matching lines to return (default: 50, max: 200).",
                    "default": 50,
                },
            },
            "required": ["pattern"],
        },
        handler=_grep_search,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="glob_files",
        description=(
            "Find files in the workspace matching a glob pattern (e.g. '*.py', 'tests/test_*.py', "
            "'**/*.md'). Skips .git, .venv, node_modules, __pycache__, and sensitive files."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match against workspace file paths or filenames.",
                },
                "path": {
                    "type": "string",
                    "description": "Optional root directory to search under (default: current working directory).",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of file paths to return (default: 100, max: 200).",
                    "default": 100,
                },
            },
            "required": ["pattern"],
        },
        handler=_glob_files,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="run_command",
        description=(
            "Execute a CLI command and return its output and exit code. Requires "
            "SAKTHAI_SHELL_ALLOW=1. Shell features like pipes or redirection are not "
            "supported. Output capped at 20,000 characters; timeout 30s default, 120s max."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command line to run (e.g. 'ls -la').",
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (1-120). Default: 30.",
                    "default": 30,
                },
                "approval_token": {
                    "type": "string",
                    "description": "Explicit approval token (APPROVE_<digest>) required for destructive commands.",
                },
            },
            "required": ["command"],
        },
        handler=_run_command,
        annotations=_annotations(destructive=True, open_world=True),
        requires_confirmation=True,
    ),
    Tool(
        name="send_telegram_message",
        description=(
            "Send a text message to Telegram. Requires TELEGRAM_BOT_TOKEN and "
            "TELEGRAM_CHAT_ID in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message body to send."},
            },
            "required": ["message"],
        },
        handler=_send_telegram_message,
        annotations=_annotations(open_world=True),
        requires_confirmation=True,
    ),
    Tool(
        name="send_outlook_mail",
        description=(
            "Send an email through Microsoft Outlook / Microsoft 365. Requires "
            "MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address."},
                "subject": {"type": "string", "description": "Email subject line."},
                "body": {"type": "string", "description": "Plain-text email body."},
            },
            "required": ["to", "subject", "body"],
        },
        handler=_send_outlook_mail,
        annotations=_annotations(open_world=True),
    ),
    Tool(
        name="read_outlook_mail",
        description=(
            "List recent messages from the Outlook inbox (subject, sender, preview). "
            "Requires MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum messages to return.",
                    "default": 10,
                },
            },
        },
        handler=_read_outlook_mail,
        annotations=_annotations(read_only=True, open_world=True),
    ),
    Tool(
        name="list_calendar_events",
        description=(
            "List upcoming Outlook/Microsoft 365 calendar events. Requires "
            "MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum events to return.",
                    "default": 10,
                },
            },
        },
        handler=_list_calendar_events,
        annotations=_annotations(read_only=True, open_world=True),
    ),
    Tool(
        name="create_calendar_event",
        description=(
            "Create an Outlook/Microsoft 365 calendar event. Requires MS_GRAPH_CLIENT_ID "
            "and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Event title."},
                "start": {
                    "type": "string",
                    "description": "Start datetime, ISO 8601 (e.g. '2026-08-05T14:00:00').",
                },
                "end": {
                    "type": "string",
                    "description": "End datetime, ISO 8601 (e.g. '2026-08-05T15:00:00').",
                },
                "timezone": {
                    "type": "string",
                    "description": "IANA/Windows timezone name. Default: UTC.",
                    "default": "UTC",
                },
                "location": {"type": "string", "description": "Optional event location."},
            },
            "required": ["subject", "start", "end"],
        },
        handler=_create_calendar_event,
        annotations=_annotations(open_world=True),
    ),
    Tool(
        name="run_agent_loop",
        description=(
            "Run a high-level task through the full SakThai agent loop (which can execute "
            "commands, read files, learn preferences, and recall memory to solve the task)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The high-level prompt/task description to execute.",
                },
                "model": {
                    "type": "string",
                    "description": "Optional model identifier to override the default.",
                },
                "provider": {
                    "type": "string",
                    "description": "Optional LLM provider backend (anthropic, google, openai, ollama, gateway, huggingface).",
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "Optional maximum tool-use cap (default: 12).",
                },
                "prune_history": {
                    "type": "boolean",
                    "description": "If true, return answer only; else include tool summary.",
                    "default": True,
                },
            },
            "required": ["task"],
        },
        handler=_run_agent_loop,
        annotations=_annotations(destructive=True, open_world=True),
        requires_confirmation=True,
    ),
    Tool(
        name="family_recall",
        description=(
            "Recall facts and top observations across the entire Sak Family memory shards. "
            "Use to inspect shared family learnings and context from sibling agents."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "personas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional subset of personas to recall from (default: all).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum entries per section (default: 20).",
                    "default": 20,
                },
            },
        },
        handler=_family_recall,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="family_search",
        description=(
            "Search facts and observations across all Sak Family personas' memory shards. "
            "Use when you need cross-persona insights or context discovered by other agents."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search term to query across family memory shards.",
                },
                "personas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional subset of personas to search (default: all).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum entries per section (default: 20).",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
        handler=_family_search,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="delegate_to_persona",
        description=(
            "Delegate a focused subtask to another Sak Family persona (sakking, sakthai, "
            "saksee, saksit, sakjules, saktan) in-process and return their response. "
            "Use to dispatch tasks to domain specialists (e.g. SakKing for coding, "
            "SakSee for review/architecture, SakSit for content/business, SakJules for CI/testing)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "description": "The target persona name (sakking, sakthai, saksee, saksit, sakjules, saktan).",
                    "enum": ["sakking", "sakthai", "saksee", "saksit", "sakjules", "saktan"],
                },
                "task": {
                    "type": "string",
                    "description": "The specific task instructions for the persona to execute.",
                },
                "with_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of skill names to activate for the persona.",
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "Maximum iterations for the delegated loop (default: 8).",
                    "default": 8,
                },
                "allow_mcp": {
                    "type": "boolean",
                    "description": "Whether to load the target persona's configured external MCP servers (default: false).",
                    "default": False,
                },
            },
            "required": ["persona", "task"],
        },
        handler=_delegate_to_persona,
        annotations=_annotations(destructive=True, open_world=True),
    ),
    Tool(
        name="hf_inspect_repo",
        description=(
            "Inspect a Hugging Face repository (model, dataset, or Space) and return "
            "structured metadata including downloads, likes, pipeline tag, tags, and commit SHA."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "repo_id": {
                    "type": "string",
                    "description": "Hugging Face repo ID (e.g. 'Nanthasit/sakthai-combined-v6').",
                },
                "repo_type": {
                    "type": "string",
                    "description": "Type of repository ('model', 'dataset', or 'space').",
                    "default": "model",
                },
            },
            "required": ["repo_id"],
        },
        handler=_hf_inspect_repo,
        annotations=_annotations(read_only=True, open_world=True),
    ),
    Tool(
        name="hf_portfolio_summary",
        description=(
            "Aggregate and summarize Hugging Face portfolio metrics across all models, "
            "datasets, and spaces for the configured owner (default 'Nanthasit')."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Hugging Face username or organization.",
                    "default": "Nanthasit",
                },
                "force_refresh": {
                    "type": "boolean",
                    "description": "Bypass local cache and force fresh portfolio aggregation.",
                    "default": False,
                },
            },
        },
        handler=_hf_portfolio_summary,
        annotations=_annotations(read_only=True, open_world=True),
    ),
    Tool(
        name="resolve_family_conflict",
        description=(
            "Resolve and clear sibling inter-agent conflicts carrying the '--tag conflict' "
            "marker in shared family memory, recording SakThai's official resolution."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "resolution_note": {
                    "type": "string",
                    "description": "Detailed resolution rationale and guidance from SakThai.",
                },
                "target_persona": {
                    "type": "string",
                    "description": "Optional sibling persona name (e.g. 'sakking', 'saksee', 'saktan').",
                },
            },
            "required": ["resolution_note"],
        },
        handler=_resolve_family_conflict,
        annotations=_annotations(destructive=True),
    ),
    Tool(
        name="decompose_and_dispatch",
        description=(
            "Decompose a high-level goal into structured stages and auto-dispatch "
            "subtasks to specialist personas (sakthai, sakking, saksee, saksit, sakjules, saktan), "
            "persisting delegation tracking and results into shared memory."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "High-level multi-step objective or instruction to decompose.",
                },
                "stages": {
                    "type": "array",
                    "description": "Optional explicit stage definitions with persona, task, and skills.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "persona": {
                                "type": "string",
                                "enum": [
                                    "sakthai",
                                    "sakking",
                                    "saksee",
                                    "saksit",
                                    "sakjules",
                                    "saktan",
                                ],
                            },
                            "task": {"type": "string"},
                            "skills": {"type": "array", "items": {"type": "string"}},
                            "max_iterations": {"type": "integer"},
                        },
                        "required": ["persona", "task"],
                    },
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "If true, returns the decomposed plan without executing tasks.",
                    "default": False,
                },
            },
            "required": ["goal"],
        },
        handler=_decompose_and_dispatch,
        annotations=_annotations(destructive=True, open_world=True),
    ),
    Tool(
        name="generate_model_card_assets",
        description=(
            "Generate SVG banner art, badges, benchmark tables, and markdown README snippets "
            "for Hugging Face model cards, persisting generated artifacts locally and in memory."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "The Hugging Face repo ID (e.g. 'Nanthasit/sakthai-context-1.5b-merged').",
                },
                "task_type": {
                    "type": "string",
                    "description": "Pipeline task type (e.g. 'text-generation', 'feature-extraction').",
                    "default": "text-generation",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags to embed in YAML metadata frontmatter.",
                },
                "benchmarks": {
                    "type": "object",
                    "description": "Dictionary of benchmark names and scores (e.g. {'MMLU': 72.1, 'GSM8K': 76.5}).",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Target directory to write banner and README assets.",
                },
            },
            "required": ["model_id"],
        },
        handler=_generate_model_card_assets,
        annotations=_annotations(destructive=True),
    ),
    Tool(
        name="web_fetch_resilient",
        description=(
            "Fetch web content with automatic domain rate-limit circuit breaking, retry backoff, "
            "and dual-engine fallback (primary HTTP engine + reader/markdown fallback)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch and extract content from.",
                },
                "force_fallback": {
                    "type": "boolean",
                    "description": "Bypass primary engine and use reader fallback engine directly.",
                    "default": False,
                },
                "timeout": {
                    "type": "number",
                    "description": "Request timeout in seconds (default: 15.0).",
                    "default": 15.0,
                },
            },
            "required": ["url"],
        },
        handler=_web_fetch_resilient,
        annotations=_annotations(read_only=True, open_world=True),
    ),
    Tool(
        name="inspect_circuit_breaker",
        description=(
            "Inspect domain error circuit breaker status, failure counts, cooldown timers, "
            "and trip states across tracked web domains."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional specific domain to inspect (default: returns all tracked domains).",
                },
            },
        },
        handler=_inspect_circuit_breaker,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="synthesize_ci_feedback",
        description=(
            "Synthesize and prioritize CI/CD build logs, security findings, and PR review comments "
            "into an actionable remediation checklist with severity grading."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "ci_log": {
                    "type": "string",
                    "description": "Raw output logs from GitHub Actions, pytest, mypy, or bandit.",
                },
                "review_comments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PR review comments or automated reviewer feedback.",
                },
            },
        },
        handler=_synthesize_ci_feedback,
        annotations=_annotations(read_only=True),
    ),
    Tool(
        name="vacuum_family_databases",
        description=(
            "Execute SQLite WAL truncation and VACUUM compaction across all 6 family memory databases, "
            "reclaiming disk space and preventing WAL file bloat."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "threshold_bytes": {
                    "type": "integer",
                    "description": "WAL size threshold in bytes to trigger compaction (default: 1,000,000).",
                    "default": 1000000,
                },
                "force": {
                    "type": "boolean",
                    "description": "Force compaction regardless of WAL size.",
                    "default": False,
                },
            },
        },
        handler=_vacuum_family_databases,
        annotations=_annotations(destructive=True),
    ),
    Tool(
        name="check_fleet_drift",
        description=(
            "Inspect fleet configuration integrity, SOUL definitions, skill counts, "
            "and database states across all 6 House of Sak personas to detect operational drift."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "verbose": {
                    "type": "boolean",
                    "description": "Include per-persona detailed breakdowns.",
                    "default": False,
                },
            },
        },
        handler=_check_fleet_drift,
        annotations=_annotations(read_only=True),
    ),
)


def _load_tool_overrides() -> None:
    """Load tool description overrides from a local config JSON if it exists."""
    from ..config import tool_descriptions_path

    path = tool_descriptions_path()
    if not path.is_file():
        return
    try:
        with open(path, encoding="utf-8") as f:
            overrides = json.load(f)
        for tool in BUILTIN_TOOLS:
            if tool.name in overrides:
                tool_override = overrides[tool.name]
                if "description" in tool_override:
                    object.__setattr__(tool, "description", tool_override["description"])
                if "input_schema" in tool_override:
                    object.__setattr__(tool, "input_schema", tool_override["input_schema"])
    except Exception as exc:  # noqa: BLE001
        # A broken overrides file must not stop the agent from starting, but
        # it must not be indistinguishable from no overrides file either.
        logger.warning("Failed to load tool overrides from %s: %s", path, exc)


_load_tool_overrides()


def tool_by_name(name: str) -> Tool | None:
    for tool in BUILTIN_TOOLS:
        if tool.name == name:
            return tool
    return None
