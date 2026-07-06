"""Standalone, provider-agnostic tool-using agent loop.

The loop injects the SakThai memory block into the system prompt, exposes the
built-in tools, and drives a provider backend (Anthropic, Gemini, or an
OpenAI-compatible/Ollama endpoint) to completion. Provider-specific concerns —
the API call, message adaptation, retries, and credential/client resolution —
live in :mod:`sakthai.agent.providers`; this module is the orchestration.

``run_agent`` accepts injectable ``client`` and ``store`` so tests never touch
the network or a real database.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..auth import get_credential_source
from ..config import redact_secrets, sessions_dir
from ..memory.store import MemoryStore
from ..skills import default_skill_roots, find_skill, render_skills_prompt_block
from . import providers
from .eval import EvalRecord, record_eval, task_preview
from .guardrails import DEFAULT_POLICY, GuardrailAction, GuardrailPolicy
from .providers import base as _providers_base
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

# Re-exports / back-compat shims. Provider logic now lives in
# :mod:`sakthai.agent.providers`; these names keep loop.py the stable import and
# patch surface for the orchestration it drives. ``run_agent`` calls the
# selection/dispatch shims by these module-local names so tests can monkeypatch
# them here.
AgentError = providers.AgentError
_Block = providers.Block
_Response = providers.Response
_is_retryable = _providers_base.is_retryable
_with_retry = _providers_base.with_retry
_detect_provider = providers.detect_provider
_build_client = providers.build_client
_call_anthropic = providers.call_anthropic
_call_gemini = providers.call_gemini
_call_openai_compat = providers.call_openai_compat

SYSTEM_BASE = (
    "You are SakThai, a personal agent that lives in the user's terminal. You have "
    "persistent memory (`learn`, `recall`, `search`, `forget`), read access to the "
    "local filesystem (`read_file`), and opt-in shell execution (`run_command`). "
    "Read existing facts before answering anything that may depend on them, and honor "
    "stated preferences silently. Save new facts only when the user shares something "
    "worth recalling later. Prefer running CLI tasks yourself with `run_command` over "
    "asking the user to run commands."
)


@dataclass
class AgentResult:
    text: str
    iterations: int
    stop_reason: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )


# -- prompt + tool execution --------------------------------------------


def _parse_slash_command(task: str) -> tuple[str, str] | None:
    """If task starts with /plugin:command, resolve it and return (injected_system_prompt, active_task)."""
    import re

    task_stripped = task.strip()
    match = re.match(r"^/([a-zA-Z0-9_-]+):([a-zA-Z0-9_-]+)(?:\s+(.*))?$", task_stripped, re.DOTALL)
    if not match:
        return None

    plugin_name = match.group(1)
    command_name = match.group(2)
    arguments = match.group(3) or ""

    cmd_file = None
    for root in default_skill_roots():
        p = root / plugin_name / "commands" / f"{command_name}.md"
        if p.is_file():
            cmd_file = p
            break
        p = root / "commands" / f"{command_name}.md"
        if p.is_file():
            cmd_file = p
            break
        # Also search one level deeper to cover extension bundle subdirectories.
        if root.is_dir():
            for child in root.iterdir():
                if not child.is_dir():
                    continue
                p = child / plugin_name / "commands" / f"{command_name}.md"
                if p.is_file():
                    cmd_file = p
                    break
                p = child / "commands" / f"{command_name}.md"
                if p.is_file():
                    cmd_file = p
                    break
        if cmd_file:
            break

    if not cmd_file:
        return None

    try:
        content = cmd_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        content = content.replace("$ARGUMENTS", arguments)
        content = content.replace("$FEATURE", arguments)
        system_block = f"COMMAND INSTRUCTIONS ({plugin_name}:{command_name}):\n\n{content}"
        return system_block, arguments
    except Exception as exc:
        logger.warning("failed to load command file %s: %s", cmd_file, exc)
        return None


def _build_skills_block(skills: Sequence[str], command_system: str, caveman: str | None) -> str:
    """Construct the full skills block for the system prompt."""
    parts = []
    if skills:
        parts.append(render_skills_prompt_block(skills))
    if command_system:
        parts.append(command_system)

    if caveman:
        caveman_skill = find_skill("caveman", *default_skill_roots())
        if caveman_skill:
            caveman_instructions = (
                f"{caveman_skill.body}\n\nACTIVE CAVEMAN LEVEL: {caveman}\n"
                f"Respond using the rules of {caveman} level strictly."
            )
            parts.append(caveman_instructions)
        else:
            logger.warning("Caveman skill not found; compression mode disabled.")

    return "\n\n".join(p for p in parts if p)


def _build_system(
    store: MemoryStore,
    skills: Sequence[str],
    command_system: str,
    fast: bool,
    stateless: bool,
    caveman: str | None,
    system_prompt_prefix: str = "",
) -> str:
    """Assemble the complete system prompt from all its parts."""
    parts = []
    if system_prompt_prefix.strip():
        parts.append(system_prompt_prefix.strip())
    parts.append(SYSTEM_BASE)
    if fast:
        parts.append(
            "FAST-TRACK MODE: Execute the user's task directly and quickly without enforcing the 6-stage cycle (Dream/Hope/Care/Joy/Trust/Growth)."
        )
    if not stateless and (memory_block := store.render_prompt_block()):
        parts.append(memory_block)
    skills_block = _build_skills_block(skills, command_system, caveman)
    if skills_block:
        parts.append(skills_block)
    return "\n\n".join(p for p in parts if p)


def _resolve_model_name(model: str, provider: str) -> str:
    """Resolve the final model name, applying provider-specific defaults."""
    if model != DEFAULT_MODEL:
        return model

    if provider == "openai":
        return "qwen2.5-coder:7b" if os.environ.get("OLLAMA_HOST") else "gpt-4o"
    if provider == "google":
        return "gemini-2.5-flash"
    return model


def _execute_tool(tool: Tool, args: dict[str, Any], store: MemoryStore) -> tuple[str, bool]:
    """Run a tool, returning (output, is_error). Errors are reported, not raised.

    All tool output is passed through ``redact_secrets`` as a global fail-safe.
    """
    try:
        output = tool.handler(args, store)
        return redact_secrets(output), False
    except Exception as exc:  # noqa: BLE001 — surfaced back to the model
        logger.debug("Tool %r raised %s: %s", tool.name, type(exc).__name__, exc)
        return redact_secrets(f"{type(exc).__name__}: {exc}"), True


def _execute_tool_with_guardrails(
    tool: Tool, args: dict[str, Any], store: MemoryStore, policy: GuardrailPolicy
) -> tuple[str, bool]:
    """Check guardrails, then run a tool.

    If the pre-execution guardrail check fails, the tool is not run, and the
    denial reason is returned as an error output.
    """
    pre_check_result = policy.check_pre_execution(tool, args, store)
    if pre_check_result.action == GuardrailAction.DENY:
        return (
            pre_check_result.reason
            or f"Tool '{tool.name}' was denied by a pre-execution guardrail.",
            True,
        )

    # Use the arguments as potentially modified by the guardrail policy.
    final_args = pre_check_result.modified_args or args

    output, is_error = _execute_tool(tool, final_args, store)

    post_check_result = policy.check_post_execution(tool, final_args, output, is_error, store)
    if post_check_result.action == GuardrailAction.DENY:
        return (
            post_check_result.reason
            or f"Output from tool '{tool.name}' was denied by a post-execution guardrail.",
            True,
        )

    return output, is_error


def _process_tool_uses(
    tool_uses: list[Any],
    registry: ToolRegistry,
    store: MemoryStore,
    notify: Callable[[str, dict[str, Any]], None],
    tool_calls: list[dict[str, Any]],
    policy: GuardrailPolicy,
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
        output, is_error = _execute_tool_with_guardrails(tool, args, store, policy)
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


def _dispatch_tool_calls(
    response: Any,
    messages: list[dict[str, Any]],
    registry: ToolRegistry,
    store: MemoryStore,
    notify: Callable[[str, dict[str, Any]], None],
    tool_calls: list[dict[str, Any]],
    policy: GuardrailPolicy,
) -> None:
    """Process tool_use blocks, execute tools, and append results to messages."""
    tool_uses = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
    if not tool_uses:
        # This can happen if the model returns stop_reason="tool_use" but with
        # no actual tool_use blocks in the content. Treat as a pause.
        logger.warning("Model indicated tool_use but sent no tool_use blocks.")
        messages.append({"role": "assistant", "content": response.content})
        return

    messages.append({"role": "assistant", "content": response.content})
    results = _process_tool_uses(tool_uses, registry, store, notify, tool_calls, policy)
    messages.append({"role": "user", "content": results})


def _agent_turn(
    provider: str,
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
    on_token: Callable[[str], None] | None,
    max_tokens: int,
    tool_schemas: list[dict[str, Any]],
    usage_tracker: UsageTracker,
) -> Any:
    """Execute a single turn of the agent loop, calling the provider."""
    if provider == "google":
        response: Any = _call_gemini(
            client, model, system, tools, messages, iteration, on_token=on_token
        )
        usage_tracker.record(**response.usage)
    elif provider in ("openai", "gateway"):
        response = _call_openai_compat(
            client, model, system, tools, messages, iteration, on_token=on_token
        )
        usage_tracker.record(**response.usage)
    else:
        response = _call_anthropic(
            client, model, max_tokens, system, tool_schemas, messages, on_token=on_token
        )
        usage_tracker.record(**extract_usage(response))
    return response


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
    on_token: Callable[[str], None] | None = None,
    provider: str | None = None,
    skills: Sequence[str] = (),
    fast: bool = False,
    stateless: bool = False,
    caveman: str | None = None,
    system_prompt_prefix: str = "",
    guardrail_policy: GuardrailPolicy | None = None,
) -> AgentResult:
    """Run one task to completion against Claude, Gemini, or an OpenAI endpoint.

    ``max_seconds`` adds an optional wall-clock budget on top of
    ``max_iterations``. ``skills`` names skills whose instructions are injected
    into the system prompt. ``on_token`` (when set) receives assistant text
    deltas as they stream from providers that support it. ``client`` and
    ``store`` are injectable for testing.
    """
    if not task.strip():
        raise AgentError("Task must be a non-empty string.")
    if max_seconds is not None and max_seconds <= 0:
        raise AgentError("max_seconds must be positive when set.")

    parsed = _parse_slash_command(task)
    command_system = ""
    if parsed:
        command_system, task = parsed

    provider = provider or _detect_provider(client, model)
    if provider == "ollama":
        provider = "openai"

    if provider == "openai" and model == DEFAULT_MODEL:
        if os.environ.get("OLLAMA_HOST"):
            model = "qwen2.5-coder:7b"
        else:
            model = "gpt-4o"
    elif provider == "google" and model == DEFAULT_MODEL:
        model = "gemini-2.5-flash"

    client = _build_client(provider, client)

    own_store = store is None
    store = store or MemoryStore()
    notify = on_event or (lambda _kind, _payload: None)
    registry = ToolRegistry(tools)
    tool_schemas = registry.schemas()
    tool_calls: list[dict[str, Any]] = []
    policy = guardrail_policy or DEFAULT_POLICY
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
    deadline = time.monotonic() + max_seconds if max_seconds is not None else None

    usage_tracker = UsageTracker()
    start_time = time.monotonic()

    def _record_run_eval(iteration: int, stop_reason: str, had_error: bool) -> None:
        usage = usage_tracker.to_dict()
        record_eval(
            EvalRecord(
                timestamp=int(time.time()),
                task_preview=task_preview(task),
                model=model,
                provider=provider,
                iterations=iteration,
                stop_reason=stop_reason,
                latency_s=time.monotonic() - start_time,
                input_tokens=usage["input_tokens"],
                output_tokens=usage["output_tokens"],
                tool_call_count=len(tool_calls),
                had_error=had_error,
            )
        )

    # Mark the loop active only once setup has succeeded, and inside the try whose
    # finally restores it. Setting it earlier leaked "1" into the process
    # environment whenever setup raised (bad provider, missing credentials,
    # client build failure), permanently tripping the run_agent_loop recursion
    # guard for the rest of the process.
    old_active = os.environ.get("SAKTHAI_AGENT_ACTIVE")
    os.environ["SAKTHAI_AGENT_ACTIVE"] = "1"
    try:
        for iteration in range(1, max_iterations + 1):
            if deadline is not None and time.monotonic() >= deadline:
                raise AgentError(f"Agent time budget exhausted (max_seconds={max_seconds}).")
            logger.debug("Agent iteration %d/%d", iteration, max_iterations)

            system = _build_system(
                store,
                skills,
                command_system,
                fast=fast,
                stateless=stateless,
                caveman=caveman,
                system_prompt_prefix=system_prompt_prefix,
            )
            response = _agent_turn(
                provider,
                client,
                model,
                system,
                tools,
                messages,
                iteration,
                on_token,
                max_tokens,
                tool_schemas,
                usage_tracker,
            )

            stop_reason = getattr(response, "stop_reason", "") or ""
            notify("iteration", {"n": iteration, "stop_reason": stop_reason})

            if stop_reason in _TERMINAL_STOPS:
                final_text = _extract_text(response.content)
                missed_tool = _detect_untriggered_tool_call(final_text, registry)
                if missed_tool is not None:
                    logger.warning(
                        "Model ended the turn (stop_reason=%s) with text that looks "
                        "like an un-dispatched %r tool call; not executing it.",
                        stop_reason,
                        missed_tool,
                    )
                    notify("tool_call_in_text", {"name": missed_tool, "stop_reason": stop_reason})
                result = AgentResult(
                    text=final_text,
                    iterations=iteration,
                    stop_reason=stop_reason,
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                )
                _save_session_log(task, model, messages, result)
                _record_run_eval(iteration, stop_reason, had_error=False)
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
                _record_run_eval(iteration, stop_reason, had_error=False)
                return result

            _dispatch_tool_calls(response, messages, registry, store, notify, tool_calls, policy)

        _record_run_eval(max_iterations, "max_iterations", had_error=True)
        raise AgentError(
            f"Agent hit the iteration cap (max_iterations={max_iterations}) "
            "without producing a final response."
        )
    finally:
        if old_active is None:
            os.environ.pop("SAKTHAI_AGENT_ACTIVE", None)
        else:
            os.environ["SAKTHAI_AGENT_ACTIVE"] = old_active

        if own_store:
            store.close()


def preflight(
    *,
    model: str = DEFAULT_MODEL,
    provider: str | None = None,
    tools: tuple[Tool, ...] = BUILTIN_TOOLS,
    client: Any | None = None,
) -> dict[str, Any]:
    """Report what a run *would* use without building a client or calling the API.

    Resolves the provider, effective model, credential source, and tool count
    exactly as :func:`run_agent` would, but makes no network call — backing
    ``sakthai run --dry-run`` so a run can be validated at zero token cost.
    ``runnable`` is True when a usable credential for the resolved provider exists.
    """
    resolved = provider or _detect_provider(client, model)
    if resolved == "ollama":
        resolved = "openai"
    effective_model = _resolve_model_name(model, resolved)
    cred_source = get_credential_source(resolved)

    registry = ToolRegistry(tools)
    return {
        "provider": resolved,
        "model": effective_model,
        "credential_source": cred_source,
        "credentials_ok": cred_source is not None,
        "tool_count": len(registry.tools),
        "tools": [t.name for t in registry.tools],
        "runnable": cred_source is not None,
    }


# -- response + session helpers -----------------------------------------


def _extract_text(content: Any) -> str:
    parts = [
        getattr(block, "text", "")
        for block in content or []
        if getattr(block, "type", "") == "text"
    ]
    return "\n".join(p for p in parts if p).strip()


# Keys a model might use to name a tool / wrap its arguments when it emits a
# tool call as plain text instead of a structured tool_use block.
_TOOL_NAME_KEYS = ("name", "tool", "tool_name", "function")
_TOOL_ARG_KEYS = ("arguments", "input", "parameters", "args", "tool_input")


def _strip_code_fence(text: str) -> str:
    """Drop a leading/trailing markdown code fence (```json ... ```)."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _detect_untriggered_tool_call(text: str, registry: ToolRegistry) -> str | None:
    """Return the tool name if ``text`` is a tool-call-shaped JSON blob.

    Weak local models sometimes end a turn (``stop_reason=end_turn``) with final
    text that is really a tool call they failed to emit as a structured
    ``tool_use`` block. We don't dispatch it (that would be guessing), but we
    surface it so the run isn't silently reported as a clean success. Detection
    is deliberately conservative: the parsed JSON must name a *registered* tool.
    """
    candidate = _strip_code_fence(text)
    if not candidate or candidate[0] not in "{[":
        return None
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None

    for entry in parsed if isinstance(parsed, list) else [parsed]:
        if not isinstance(entry, dict):
            continue
        for key in _TOOL_NAME_KEYS:
            value = entry.get(key)
            # OpenAI-style: {"function": {"name": ...}}
            if isinstance(value, dict):
                value = value.get("name")
            if isinstance(value, str) and value in registry:
                # Stronger signal when an arguments-ish key is also present, but
                # a registered tool name alone is enough to warrant a warning.
                return value
    return None


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
        # Restrict permissions on the sessions directory: rwx------ (0700)
        base.mkdir(parents=True, exist_ok=True)
        os.chmod(str(base), 0o700)

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
        # Redact any accidental secrets in the full log payload.
        log_json = json.dumps(payload, indent=2, ensure_ascii=False)
        redacted_log = redact_secrets(log_json)

        # Create log file with restricted permissions: rw------- (0600)
        # Use os.open with flags to ensure correct mode on creation.
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(redacted_log)
    except Exception as exc:  # noqa: BLE001 — logging is best-effort
        logger.warning("Failed to save session log: %s", exc)
