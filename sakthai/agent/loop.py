"""Standalone tool-using agent loop over the Claude or Gemini API.

The loop injects the SakThai memory block into the system prompt and exposes the
built-in tools from :mod:`sakthai.agent.tools`. The Anthropic and Gemini paths
are normalised to a common response shape (:class:`_Response` /
:class:`_Block`) so the iteration logic stays provider-agnostic.

``run_agent`` accepts injectable ``client`` and ``store`` so tests never touch
the network or a real database.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import anthropic
import httpx
import tenacity

from ..auth import (
    AuthError,
    anthropic_credential_source,
    openai_credential_source,
    resolve_anthropic_client,
)
from ..config import sessions_dir
from ..memory.store import MemoryStore
from ..skills import render_skills_prompt_block
from .registry import ToolRegistry
from .tools import BUILTIN_TOOLS, Tool
from .usage import UsageTracker, extract_usage

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 16000
DEFAULT_MAX_ITERATIONS = 12
DEFAULT_MAX_SECONDS: float | None = None  # opt-in wall-clock budget

# stop_reasons that end the loop with a final answer.
_TERMINAL_STOPS = frozenset({"end_turn", "max_tokens", "stop_sequence", "refusal"})

# Transient-failure retry policy for provider API calls. The wait constants are
# module-level so tests can zero them out to avoid real sleeps.
_RETRY_ATTEMPTS = 3
_RETRY_WAIT_MULTIPLIER = 0.5
_RETRY_WAIT_MAX = 8.0
_RETRYABLE_STATUS = frozenset({408, 409, 429, 500, 502, 503, 504})


def _is_retryable(exc: BaseException) -> bool:
    """True for transient API failures worth retrying (rate limit, 5xx, network)."""
    if isinstance(exc, anthropic.APIConnectionError | httpx.TransportError | OSError):
        return True
    # HTTP status surfaced differently across SDKs: anthropic uses ``status_code``,
    # google-genai uses ``code``, httpx exposes it on ``response``.
    status: Any = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(exc, "code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return isinstance(status, int) and status in _RETRYABLE_STATUS


def _with_retry(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call ``fn`` with exponential-backoff retries on transient failures.

    Non-retryable errors (bad request, auth, not found) propagate on the first
    attempt; the original exception is re-raised once attempts are exhausted.
    """
    retryer = tenacity.Retrying(
        retry=tenacity.retry_if_exception(_is_retryable),
        stop=tenacity.stop_after_attempt(_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=_RETRY_WAIT_MULTIPLIER, max=_RETRY_WAIT_MAX),
        reraise=True,
    )
    return retryer(fn, *args, **kwargs)


SYSTEM_BASE = (
    "You are SakThai, a personal agent that lives in the user's terminal. You have "
    "persistent memory (`learn`, `recall`, `search`, `forget`), read access to the "
    "local filesystem (`read_file`), and opt-in shell execution (`run_command`). "
    "Read existing facts before answering anything that may depend on them, and honor "
    "stated preferences silently. Save new facts only when the user shares something "
    "worth recalling later. Prefer running CLI tasks yourself with `run_command` over "
    "asking the user to run commands."
)


class AgentError(RuntimeError):
    """Raised when the loop cannot proceed (missing credential, API failure, …)."""


@dataclass
class AgentResult:
    text: str
    iterations: int
    stop_reason: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )


class _Block:
    """Normalised content block (text or tool_use) across providers."""

    def __init__(
        self,
        block_type: str,
        *,
        text: str = "",
        id: str = "",
        name: str = "",
        input: dict[str, Any] | None = None,
    ) -> None:
        self.type = block_type
        self.text = text
        self.id = id
        self.name = name
        self.input = input or {}


class _Response:
    """Normalised model response: a stop_reason plus a list of content blocks."""

    def __init__(
        self,
        stop_reason: str,
        content: list[Any],
        usage: dict[str, int] | None = None,
    ) -> None:
        self.stop_reason = stop_reason
        self.content = content
        self.usage = usage or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


# -- prompt + tool execution --------------------------------------------


def _build_system(store: MemoryStore, skills_block: str = "") -> str:
    parts = [SYSTEM_BASE]
    memory = store.render_prompt_block()
    if memory:
        parts.append(memory)
    if skills_block:
        parts.append(skills_block)
    return "\n\n".join(parts)


def _execute_tool(tool: Tool, args: dict[str, Any], store: MemoryStore) -> tuple[str, bool]:
    """Run a tool, returning (output, is_error). Errors are reported, not raised."""
    try:
        return tool.handler(args, store), False
    except Exception as exc:  # noqa: BLE001 — surfaced back to the model
        logger.debug("Tool %r raised %s: %s", tool.name, type(exc).__name__, exc)
        return f"{type(exc).__name__}: {exc}", True


def _process_tool_uses(
    tool_uses: list[Any],
    registry: ToolRegistry,
    store: MemoryStore,
    notify: Callable[[str, dict[str, Any]], None],
    tool_calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for use in tool_uses:
        tool = registry.get(use.name)
        if tool is None:
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": use.id,
                    "content": f"Unknown tool: {use.name}",
                    "is_error": True,
                }
            )
            notify("tool_error", {"name": use.name, "reason": "unknown"})
            continue
        args = dict(use.input or {})
        output, is_error = _execute_tool(tool, args, store)
        tool_calls.append({"name": use.name, "input": args, "is_error": is_error})
        notify("tool_call", {"name": use.name, "input": args, "is_error": is_error})
        results.append(
            {
                "type": "tool_result",
                "tool_use_id": use.id,
                "content": output,
                "is_error": is_error,
            }
        )
    return results


# -- provider selection + per-iteration calls ---------------------------


def _detect_provider(client: Any | None, model: str) -> str:
    """Choose a provider when the caller didn't.

    A Gemini model name or google-genai client → ``google``;
    an openai client or `openai`/`ollama`/`gpt` in model name → ``openai``;
    any other injected client → ``anthropic``;
    otherwise pick whichever credential is present in order: anthropic → google → openai.
    """
    client_module = client.__class__.__module__ if client is not None else ""
    if "google.genai" in client_module or "gemini" in model.lower():
        return "google"
    if "openai" in client_module:
        return "openai"
    if any(
        keyword in model.lower()
        for keyword in ("openai", "ollama", "gpt-", "qwen", "llama", "deepseek", "mistral")
    ):
        return "openai"
    if client is not None:
        return "anthropic"
    if anthropic_credential_source() is not None:
        return "anthropic"
    import os

    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "google"
    if openai_credential_source() is not None:
        return "openai"
    return "anthropic"


def _build_client(provider: str, client: Any | None) -> Any:
    if client is not None:
        return client
    if provider == "google":
        import os

        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise AgentError(
                "Missing credentials for Google Gemini (GEMINI_API_KEY or GOOGLE_API_KEY must be set)."
            )
        try:
            return genai.Client(api_key=api_key)
        except Exception as exc:
            raise AgentError(f"Failed to initialize Google Gemini client: {exc}") from exc
    if provider == "openai":
        import httpx

        from ..auth import resolve_openai_credentials

        try:
            api_base, api_key = resolve_openai_credentials()
        except AuthError as exc:
            raise AgentError(str(exc)) from exc
        return httpx.Client(
            base_url=api_base,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
    try:
        return resolve_anthropic_client()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc


def _call_anthropic(
    client: Any,
    model: str,
    max_tokens: int,
    system: str,
    tool_schemas: list[dict[str, Any]],
    messages: list[dict[str, Any]],
) -> Any:
    try:
        return _with_retry(
            client.messages.create,
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tool_schemas,
            messages=messages,
        )
    except (anthropic.APIError, OSError) as exc:
        logger.error("Anthropic API call failed: %s", exc)
        raise AgentError(f"Anthropic API call failed: {exc}") from exc


def _call_gemini(
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
) -> _Response:
    from google.genai import types

    declarations: list[Any] = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters=t.input_schema,  # type: ignore[arg-type]
                )
            ]
        )
        for t in tools
    ]
    try:
        raw = _with_retry(
            client.models.generate_content,
            model=model,
            contents=_to_gemini_contents(messages),
            config=types.GenerateContentConfig(system_instruction=system, tools=declarations),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Gemini API call failed: %s", exc)
        raise AgentError(f"Gemini API call failed: {exc}") from exc

    if not raw.candidates:
        raise AgentError("Gemini returned no candidates.")
    candidate = raw.candidates[0]
    blocks: list[Any] = []
    has_tool_call = False
    parts = (candidate.content.parts if candidate.content else None) or []
    for idx, part in enumerate(parts):
        if part.text:
            blocks.append(_Block("text", text=part.text))
        elif part.function_calls:
            has_tool_call = True
            for fc in part.function_calls:
                blocks.append(
                    _Block(
                        "tool_use",
                        id=f"call_{fc.name}_{iteration}_{idx}",
                        name=fc.name,
                        input=dict(fc.args or {}),
                    )
                )
    if has_tool_call:
        stop_reason = "tool_use"
    elif candidate.finish_reason == "MAX_TOKENS":
        stop_reason = "max_tokens"
    else:
        stop_reason = "end_turn"
    usage = extract_usage(raw)
    return _Response(stop_reason=stop_reason, content=blocks, usage=usage)


def _to_openai_messages(system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    openai_msgs: list[dict[str, Any]] = [{"role": "system", "content": system}]

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            openai_msgs.append({"role": role, "content": content})
        elif isinstance(content, list):
            if role == "assistant":
                text_content = ""
                tool_calls = []
                for block in content:
                    block_type = _block_field(block, "type")
                    if block_type == "text":
                        text_content += _block_field(block, "text")
                    elif block_type == "tool_use":
                        tool_calls.append(
                            {
                                "id": _block_field(block, "id"),
                                "type": "function",
                                "function": {
                                    "name": _block_field(block, "name"),
                                    "arguments": json.dumps(_block_field(block, "input", {})),
                                },
                            }
                        )
                item: dict[str, Any] = {"role": "assistant"}
                if text_content:
                    item["content"] = text_content
                else:
                    item["content"] = None
                if tool_calls:
                    item["tool_calls"] = tool_calls
                openai_msgs.append(item)
            else:
                for block in content:
                    block_type = _block_field(block, "type")
                    if block_type == "tool_result":
                        openai_msgs.append(
                            {
                                "role": "tool",
                                "tool_call_id": _block_field(block, "tool_use_id"),
                                "content": _block_field(block, "content"),
                            }
                        )
                    else:
                        text = _block_field(block, "text")
                        if text:
                            openai_msgs.append({"role": "user", "content": text})
    return openai_msgs


def _call_openai_compat(
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
) -> _Response:
    openai_tools = []
    for t in tools:
        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.input_schema,
                },
            }
        )

    openai_messages = _to_openai_messages(system, messages)

    payload: dict[str, Any] = {
        "model": model,
        "messages": openai_messages,
        "stream": False,
    }
    if openai_tools:
        payload["tools"] = openai_tools

    if hasattr(client, "post"):

        def _do_request() -> dict[str, Any]:
            resp = client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    elif hasattr(client, "chat") and hasattr(client.chat, "completions"):

        def _do_request() -> dict[str, Any]:
            raw = client.chat.completions.create(**payload)
            return raw.model_dump()  # type: ignore[no-any-return]

    else:
        raise AgentError(f"Unsupported client type: {type(client)}")

    try:
        data = _with_retry(_do_request)
    except Exception as exc:
        logger.error("OpenAI-compatible API call failed: %s", exc)
        raise AgentError(f"OpenAI-compatible API call failed: {exc}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise AgentError("OpenAI returned no choices.")
    choice = choices[0]
    message_data = choice.get("message") or {}
    content_text = message_data.get("content") or ""
    tool_calls_data = message_data.get("tool_calls") or []
    finish_reason = choice.get("finish_reason")

    blocks: list[Any] = []
    if content_text:
        blocks.append(_Block("text", text=content_text))

    has_tool_call = False
    for idx, tc in enumerate(tool_calls_data):
        fn = tc.get("function") or {}
        fn_name = fn.get("name")
        if not isinstance(fn_name, str):
            fn_name = ""
        fn_args_raw = fn.get("arguments") or "{}"
        if isinstance(fn_args_raw, str):
            try:
                fn_args = json.loads(fn_args_raw)
            except Exception:
                fn_args = {}
        else:
            fn_args = fn_args_raw

        has_tool_call = True
        tool_id = tc.get("id") or f"call_{fn_name}_{iteration}_{idx}"
        blocks.append(
            _Block(
                "tool_use",
                id=tool_id,
                name=fn_name,
                input=dict(fn_args or {}),
            )
        )

    if has_tool_call:
        stop_reason = "tool_use"
    elif finish_reason == "length":
        stop_reason = "max_tokens"
    else:
        stop_reason = "end_turn"

    usage = extract_usage(data)
    return _Response(stop_reason=stop_reason, content=blocks, usage=usage)


# -- main loop -----------------------------------------------------------


def run_agent(
    task: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    max_seconds: float | None = DEFAULT_MAX_SECONDS,
    tools: tuple[Tool, ...] = BUILTIN_TOOLS,
    store: MemoryStore | None = None,
    client: Any | None = None,
    on_event: Callable[[str, dict[str, Any]], None] | None = None,
    provider: str | None = None,
    skills: Sequence[str] = (),
) -> AgentResult:
    """Run one task to completion against Claude or Gemini.

    ``max_seconds`` adds an optional wall-clock budget on top of
    ``max_iterations``. ``skills`` names skills whose instructions are injected
    into the system prompt. ``client`` and ``store`` are injectable for testing.
    """
    if not task.strip():
        raise AgentError("Task must be a non-empty string.")
    if max_seconds is not None and max_seconds <= 0:
        raise AgentError("max_seconds must be positive when set.")

    import os

    old_active = os.environ.get("SAKTHAI_AGENT_ACTIVE")
    os.environ["SAKTHAI_AGENT_ACTIVE"] = "1"

    provider = provider or _detect_provider(client, model)
    if provider == "ollama":
        provider = "openai"

    if provider == "openai" and model == DEFAULT_MODEL:
        if os.environ.get("OLLAMA_HOST"):
            model = "qwen2.5-coder:7b"
        else:
            model = "gpt-4o"

    client = _build_client(provider, client)

    own_store = store is None
    store = store or MemoryStore()
    notify = on_event or (lambda _kind, _payload: None)
    registry = ToolRegistry(tools)
    tool_schemas = registry.schemas()
    tool_calls: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
    skills_block = render_skills_prompt_block(skills) if skills else ""
    deadline = time.monotonic() + max_seconds if max_seconds is not None else None

    usage_tracker = UsageTracker()
    try:
        for iteration in range(1, max_iterations + 1):
            if deadline is not None and time.monotonic() >= deadline:
                raise AgentError(f"Agent time budget exhausted (max_seconds={max_seconds}).")
            logger.debug("Agent iteration %d/%d", iteration, max_iterations)

            system = _build_system(store, skills_block)
            if provider == "google":
                response: Any = _call_gemini(client, model, system, tools, messages, iteration)
                usage_tracker.record(**response.usage)
            elif provider == "openai":
                response = _call_openai_compat(client, model, system, tools, messages, iteration)
                usage_tracker.record(**response.usage)
            else:
                response = _call_anthropic(
                    client, model, max_tokens, system, tool_schemas, messages
                )
                usage_tracker.record(**extract_usage(response))

            stop_reason = getattr(response, "stop_reason", "") or ""
            notify("iteration", {"n": iteration, "stop_reason": stop_reason})

            if stop_reason in _TERMINAL_STOPS:
                result = AgentResult(
                    text=_extract_text(response.content),
                    iterations=iteration,
                    stop_reason=stop_reason,
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                )
                _save_session_log(task, model, messages, result)
                return result

            if stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue

            if stop_reason != "tool_use":
                result = AgentResult(
                    text=_extract_text(response.content)
                    or f"(unexpected stop_reason={stop_reason!r})",
                    iterations=iteration,
                    stop_reason=stop_reason,
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                )
                _save_session_log(task, model, messages, result)
                return result

            tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
            messages.append({"role": "assistant", "content": response.content})
            results = _process_tool_uses(tool_uses, registry, store, notify, tool_calls)
            messages.append({"role": "user", "content": results})

        raise AgentError(
            f"Agent hit the iteration cap (max_iterations={max_iterations}) "
            "without producing a final response."
        )
    finally:
        import os

        if old_active is None:
            os.environ.pop("SAKTHAI_AGENT_ACTIVE", None)
        else:
            os.environ["SAKTHAI_AGENT_ACTIVE"] = old_active

        if own_store:
            store.close()


def _extract_text(content: Any) -> str:
    parts = [
        getattr(block, "text", "")
        for block in content or []
        if getattr(block, "type", "") == "text"
    ]
    return "\n".join(p for p in parts if p).strip()


# -- Gemini message adaptation ------------------------------------------


def _find_tool_name_by_id(messages: list[dict[str, Any]], tool_use_id: str) -> str:
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            block_type = getattr(block, "type", "") or (
                block.get("type", "") if isinstance(block, dict) else ""
            )
            if block_type != "tool_use":
                continue
            current = getattr(block, "id", "") or (
                block.get("id", "") if isinstance(block, dict) else ""
            )
            if current == tool_use_id:
                return getattr(block, "name", "") or (
                    block.get("name", "") if isinstance(block, dict) else ""
                )
    return "unknown"


def _block_field(block: Any, field_name: str, default: Any = "") -> Any:
    if isinstance(block, dict):
        return block.get(field_name, default)
    return getattr(block, field_name, default)


def _to_gemini_contents(messages: list[dict[str, Any]]) -> list[Any]:
    from google.genai import types

    contents = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        parts = []
        if isinstance(content, str):
            parts.append(types.Part(text=content))
        elif isinstance(content, list):
            for block in content:
                block_type = _block_field(block, "type")
                if block_type == "text":
                    parts.append(types.Part(text=_block_field(block, "text")))
                elif block_type == "tool_use":
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=_block_field(block, "name"),
                                args=dict(_block_field(block, "input", {}) or {}),
                            )
                        )
                    )
                elif block_type == "tool_result":
                    tool_use_id = _block_field(block, "tool_use_id")
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=_find_tool_name_by_id(messages, tool_use_id),
                                response={"result": _block_field(block, "content")},
                            )
                        )
                    )
        if any(getattr(p, "function_response", None) is not None for p in parts):
            gemini_role = "tool"
        elif role == "assistant":
            gemini_role = "model"
        else:
            gemini_role = "user"
        contents.append(types.Content(role=gemini_role, parts=parts))
    return contents


# -- session logging -----------------------------------------------------


def _serialize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if not isinstance(content, list):
            serialized.append({"role": role, "content": content})
            continue
        blocks: list[Any] = []
        for block in content:
            if not hasattr(block, "type"):
                blocks.append(block)
                continue
            entry: dict[str, Any] = {"type": block.type}
            for attr in ("text", "id", "name", "input"):
                value = getattr(block, attr, None)
                if value:
                    entry[attr] = value
            blocks.append(entry)
        serialized.append({"role": role, "content": blocks})
    return serialized


def _save_session_log(task: str, model: str, messages: list[Any], result: AgentResult) -> None:
    try:
        base = sessions_dir().resolve()
        base.mkdir(parents=True, exist_ok=True)
        target = (base / f"{int(time.time())}_{uuid.uuid4().hex}.json").resolve()
        target.relative_to(base)  # guard against traversal
        payload = {
            "timestamp": int(time.time()),
            "task": task,
            "model": model,
            "messages": _serialize_messages(messages),
            "usage": result.usage,
            "result": {
                "text": result.text,
                "iterations": result.iterations,
                "stop_reason": result.stop_reason,
                "tool_calls": result.tool_calls,
            },
        }
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 — logging is best-effort
        logger.warning("Failed to save session log: %s", exc)
