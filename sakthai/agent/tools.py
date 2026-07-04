"""Tools the agent loop (and the MCP server) can invoke.

A :class:`Tool` pairs a JSON input schema (what the model sees) with a Python
handler ``(args, store) -> str``. ``BUILTIN_TOOLS`` is the single registry used
by both the agent loop and the MCP server, so a tool's schema and behaviour live
in one place.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from ..config import sakthai_home
from ..lead.capture import capture_lead as capture_lead_fact
from ..learn.ingest import ingest_document as ingest_document_facts
from ..memory.store import MemoryStore

MAX_FILE_READ_CHARS = 20_000  # read_file output cap
MAX_CMD_OUTPUT_CHARS = 20_000  # run_command output cap
_RECALL_LIMIT_MAX = 200  # cap on recall/search limit
_CMD_TIMEOUT_DEFAULT = 30.0
_CMD_TIMEOUT_MAX = 120.0


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any], MemoryStore], str]

    def schema(self) -> dict[str, Any]:
        """The model-facing tool definition."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


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


def _resolve_and_validate_path(path_str: str) -> Path:
    """Resolve a path and ensure it is a file within allowed roots."""
    candidate = Path(path_str).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{candidate} is not a regular file.") from exc
    except OSError as exc:
        raise FileNotFoundError(f"{candidate} could not be opened: {exc}") from exc

    if not resolved.is_file():
        raise FileNotFoundError(f"{resolved} is not a regular file.")

    if not _path_under_any_root(resolved, _allowed_read_roots()):
        raise PermissionError(
            f"{resolved} is outside the allowed roots. Add it to SAKTHAI_READ_ALLOW "
            "(os.pathsep-separated) to permit reading."
        )
    return resolved


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


def _run_command(args: dict[str, Any], store: MemoryStore) -> str:
    """Run a command (no shell) and return its output and exit code.

    Disabled unless ``SAKTHAI_SHELL_ALLOW`` is set, so a stray tool call cannot
    execute arbitrary code on a machine where the user has not opted in.
    """
    command = args.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("`command` is required and must be a non-empty string.")
    if not os.environ.get("SAKTHAI_SHELL_ALLOW"):
        raise PermissionError(
            "Shell execution is disabled. Set SAKTHAI_SHELL_ALLOW=1 to enable `run_command`."
        )
    try:
        timeout = float(args.get("timeout") or _CMD_TIMEOUT_DEFAULT)
    except (TypeError, ValueError):
        timeout = _CMD_TIMEOUT_DEFAULT
    timeout = max(1.0, min(timeout, _CMD_TIMEOUT_MAX))
    try:
        proc = subprocess.run(  # nosec B603 — shell=False, opt-in gated above
            shlex.split(command, posix=sys.platform != "win32"),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
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
        return f"Unexpected Error sending Telegram message: {exc}"


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


# -- registry ------------------------------------------------------------

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
    ),
    Tool(
        name="recall",
        description=(
            "List facts and observations currently stored in SakThai memory. Use to "
            "check what is already known before asking the user or answering a question "
            "that depends on prior context."
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
    ),
    Tool(
        name="search",
        description=(
            "Search SakThai facts and observations for matching substrings. Use when you "
            "need specific entries about a topic rather than a broad recall of everything."
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
            },
            "required": ["command"],
        },
        handler=_run_command,
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
                    "description": "Optional LLM provider backend (anthropic, google, openai, ollama).",
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
    ),
)


def tool_by_name(name: str) -> Tool | None:
    for tool in BUILTIN_TOOLS:
        if tool.name == name:
            return tool
    return None
