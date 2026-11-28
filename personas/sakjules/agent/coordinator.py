"""Multi-agent coordinator and task delegation manager.

Provides depth-bounded, cycle-safe in-process delegation between Sak Family personas.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from contextvars import ContextVar
from typing import Any

from ..config import (
    PERSONA_NAMES,
    PERSONAS_DIR,
    persona_memory_db_path,
    persona_model_defaults,
)
from ..memory.store import MemoryStore
from .loop import DEFAULT_UNATTENDED_MAX_SECONDS, AgentError, AgentResult, run_agent

logger = logging.getLogger(__name__)

DEFAULT_MAX_DELEGATION_DEPTH = 2

_DELEGATION_CHAIN: ContextVar[tuple[str, ...]] = ContextVar("delegation_chain", default=())


class DelegationError(AgentError):
    """Base error for multi-agent delegation failures."""


class DelegationDepthError(DelegationError):
    """Raised when delegation exceeds the maximum allowable nesting depth."""


class DelegationCycleError(DelegationError):
    """Raised when a circular delegation loop is detected (e.g. A -> B -> A)."""


def get_delegation_chain() -> tuple[str, ...]:
    """Return the active tuple of delegating persona names in the current context."""
    return _DELEGATION_CHAIN.get()


def get_delegation_depth() -> int:
    """Return current delegation nesting depth (0 = top-level orchestrator/user run)."""
    return len(_DELEGATION_CHAIN.get())


def resolve_persona_agent_kwargs(
    persona: str,
    task: str,
    *,
    with_skills: Sequence[str] = (),
    max_iterations: int | None = None,
    max_tokens: int | None = None,
    store: MemoryStore | None = None,
    model: str | None = None,
    provider: str | None = None,
    client: Any = None,
    system_prompt: str | None = None,
) -> dict[str, Any]:
    """Resolve ``run_agent`` keyword arguments scoped to the target persona.

    Injects the persona's `SOUL.md` prefix, resolves default model/provider
    from `config.yaml`, and scopes memory db to the persona shard if not
    injected. Every key returned is a ``run_agent`` parameter. The delegated
    run gets the built-in tools only; the persona's MCP manifest is not loaded.
    """
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    persona_dir = PERSONAS_DIR / persona
    soul_file = persona_dir / "SOUL.md"
    soul_prefix = soul_file.read_text(encoding="utf-8").strip() if soul_file.is_file() else ""

    combined_prompt = soul_prefix
    if system_prompt:
        combined_prompt = f"{soul_prefix}\n\n{system_prompt}" if soul_prefix else system_prompt

    default_provider, default_model = persona_model_defaults(persona)
    resolved_provider = provider or default_provider
    resolved_model = model or default_model

    resolved_store = store
    if resolved_store is None:
        db_path = persona_memory_db_path(persona)
        resolved_store = MemoryStore(db_path)

    kwargs: dict[str, Any] = {
        "task": task,
        "persona": persona,
        "store": resolved_store,
        "provider": resolved_provider,
        "model": resolved_model,
        "skills": with_skills,
        "max_iterations": max_iterations or 8,
        "client": client,
        "system_prompt_prefix": combined_prompt,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return kwargs


def run_persona_task(
    persona: str,
    task: str,
    *,
    with_skills: Sequence[str] = (),
    max_iterations: int | None = None,
    max_tokens: int | None = None,
    max_seconds: float | None = DEFAULT_UNATTENDED_MAX_SECONDS,
    max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
    store: MemoryStore | None = None,
    model: str | None = None,
    provider: str | None = None,
    no_mcp: bool = False,
    allow_mcp: bool = False,
    client: Any = None,
    verbose: bool = False,
) -> AgentResult:
    """Execute a task in-process under the scoped target persona.

    Guards against recursion cycles and nesting beyond ``max_depth``.
    ``max_seconds`` defaults to ``DEFAULT_UNATTENDED_MAX_SECONDS``: a delegated
    run has no one watching it; pass ``None`` to lift the budget.
    When ``allow_mcp=True`` and ``no_mcp=False``, connects the target persona's
    configured MCP servers during execution.
    """
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    current_chain = _DELEGATION_CHAIN.get()
    current_depth = len(current_chain)

    if current_depth >= max_depth:
        raise DelegationDepthError(
            f"Delegation depth {current_depth} reached maximum limit of {max_depth} (chain: {' -> '.join(current_chain)})"
        )

    if persona in current_chain:
        raise DelegationCycleError(
            f"Circular delegation detected: {' -> '.join(current_chain)} -> {persona}"
        )

    kwargs = resolve_persona_agent_kwargs(
        persona,
        task,
        with_skills=with_skills,
        max_iterations=max_iterations,
        max_tokens=max_tokens,
        store=store,
        model=model,
        provider=provider,
        client=client,
    )

    kwargs["max_seconds"] = max_seconds

    if allow_mcp and not no_mcp:
        import os

        from ..mcp.manager import connect_servers
        from .tools import BUILTIN_TOOLS

        mcp_config_backup = os.environ.get("SAKTHAI_MCP_CONFIG")
        try:
            os.environ.pop("SAKTHAI_MCP_CONFIG", None)
            with connect_servers(persona=persona, include_builtins=True) as mcp_tools:
                kwargs["tools"] = (*BUILTIN_TOOLS, *mcp_tools)
                new_chain = (*current_chain, persona)
                token = _DELEGATION_CHAIN.set(new_chain)
                try:
                    return run_agent(**kwargs)
                finally:
                    _DELEGATION_CHAIN.reset(token)
        except (ConnectionError, TimeoutError, ImportError) as mcp_exc:
            logger.warning(
                "Could not connect MCP servers for delegated persona %s: %s. Continuing without MCP.",
                persona,
                mcp_exc,
            )
        finally:
            if mcp_config_backup is not None:
                os.environ["SAKTHAI_MCP_CONFIG"] = mcp_config_backup

    new_chain = (*current_chain, persona)
    token = _DELEGATION_CHAIN.set(new_chain)
    try:
        return run_agent(**kwargs)
    finally:
        _DELEGATION_CHAIN.reset(token)


def run_parallel_persona_tasks(
    tasks: Sequence[dict[str, Any]],
    *,
    max_workers: int | None = None,
    max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
    store: MemoryStore | None = None,
    client: Any = None,
    verbose: bool = False,
) -> list[AgentResult]:
    """Execute multiple persona tasks concurrently using ThreadPoolExecutor with error isolation.

    Each task dict should contain:
      - 'persona': target persona name (str)
      - 'task': task prompt (str)
      - 'with_skills': optional Sequence[str]
      - 'max_iterations': optional int
      - 'max_tokens': optional int
      - 'model': optional str
      - 'provider': optional str
      - 'no_mcp': optional bool
      - 'allow_mcp': optional bool
    """
    if not tasks:
        return []

    import concurrent.futures

    workers = max_workers or min(len(tasks), 8)

    def _worker(item: dict[str, Any]) -> AgentResult:
        persona = str(item.get("persona", "sakthai"))
        task_str = str(item.get("task", ""))
        skills = item.get("with_skills", ())
        max_iters = item.get("max_iterations")
        max_toks = item.get("max_tokens")
        model = item.get("model")
        provider = item.get("provider")
        no_mcp = bool(item.get("no_mcp", False))
        allow_mcp = bool(item.get("allow_mcp", False))
        item_store = item.get("store") or store

        try:
            return run_persona_task(
                persona=persona,
                task=task_str,
                with_skills=skills,
                max_iterations=max_iters,
                max_tokens=max_toks,
                max_depth=max_depth,
                store=item_store,
                model=model,
                provider=provider,
                no_mcp=no_mcp,
                allow_mcp=allow_mcp,
                client=client,
                verbose=verbose,
            )
        except Exception as exc:
            logger.error("Delegated task for persona %s failed: %s", persona, exc)
            return AgentResult(
                text=f"Error executing delegated task for persona '{persona}': {exc}",
                tool_calls=[],
                iterations=0,
                stop_reason="error",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_worker, t) for t in tasks]
        return [f.result() for f in futures]


def aggregate_persona_results(results: Sequence[AgentResult]) -> dict[str, Any]:
    """Aggregate individual persona task results into a consolidated summary."""
    from .loop import _TERMINAL_STOPS

    total_tokens = sum(r.usage.get("total_tokens", 0) for r in results)
    total_tool_calls = sum(len(r.tool_calls) for r in results)
    successful = [r for r in results if r.stop_reason in _TERMINAL_STOPS]
    failed = [r for r in results if r.stop_reason not in _TERMINAL_STOPS]

    sections = []
    for i, r in enumerate(results, start=1):
        status_tag = "✓" if r.stop_reason != "error" else "✗"
        sections.append(f"### Subtask {i} [{status_tag} - {r.stop_reason}]\n{r.text.strip()}")

    return {
        "total_tasks": len(results),
        "successful_tasks": len(successful),
        "failed_tasks": len(failed),
        "total_tokens": total_tokens,
        "total_tool_calls": total_tool_calls,
        "summary_text": "\n\n".join(sections),
    }


def classify_intent_envelope(
    task: str,
    *,
    timeout_seconds: float = 3.0,
    forced_persona: str | None = None,
) -> dict[str, Any]:
    """Fast (<=3.0s) intent preflight delegation envelope for SakKing runner."""
    import time

    start = time.perf_counter()

    if forced_persona and forced_persona.strip().lower() in PERSONA_NAMES:
        chosen = forced_persona.strip().lower()
        return {
            "task": task,
            "recommended_persona": chosen,
            "confidence": 1.0,
            "should_delegate": chosen != "sakking",
            "specialist_domain": "forced",
            "matched_keywords": [],
            "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        }

    lower_task = task.lower()
    kw_map = {
        "sakthai": (
            "Hugging Face & ML Governance",
            (
                "hugging face",
                "hf",
                "hub",
                "model card",
                "safetensors",
                "dataset",
                "spaces",
                "gguf",
                "quantize",
                "nanotron",
            ),
        ),
        "saksee": (
            "Web Browsing & Frontend Automation",
            (
                "browser",
                "playwright",
                "scrape",
                "crawl",
                "web page",
                "frontend",
                "ui",
                "ux",
                "inspect element",
                "chrome",
            ),
        ),
        "sakjules": (
            "Automation, CI/CD & Workflows",
            (
                "ci/cd",
                "github action",
                "workflow",
                "pull request",
                "pr review",
                "lint",
                "bandit",
                "auto-merge",
                "pipeline",
            ),
        ),
        "saksit": (
            "Social Media, Content & Copywriting",
            (
                "social media",
                "twitter",
                "xurl",
                "instagram",
                "linkedin",
                "post",
                "copywriting",
                "milestone content",
                "announcement",
            ),
        ),
        "saktan": (
            "Daily Operations & Maintenance",
            (
                "wal",
                "vacuum",
                "heartbeat",
                "daemon",
                "drift",
                "daily ops",
                "maintenance",
                "cron job",
                "nightly",
            ),
        ),
    }

    best_persona = "sakking"
    best_score = 0.0
    best_domain = "General Execution & Technical Implementation"
    matched_kws: list[str] = []

    for p, (domain, keywords) in kw_map.items():
        matches = [kw for kw in keywords if kw in lower_task]
        if matches:
            score = min(1.0, 0.4 + 0.2 * len(matches))
            if score > best_score:
                best_score = score
                best_persona = p
                best_domain = domain
                matched_kws = matches

    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    should_delegate = (best_persona != "sakking") and (best_score >= 0.5)

    return {
        "task": task,
        "recommended_persona": best_persona,
        "confidence": round(best_score if should_delegate else 1.0, 2),
        "should_delegate": should_delegate,
        "specialist_domain": best_domain,
        "matched_keywords": matched_kws,
        "latency_ms": latency_ms,
    }


class SakKingIntentPreflight:
    """Preflight classifier for SakKing to identify delegation targets within 3.0s."""

    def __init__(self, timeout_seconds: float = 3.0) -> None:
        self.timeout_seconds = timeout_seconds

    def evaluate(self, task: str) -> dict[str, Any]:
        return classify_intent_envelope(task, timeout_seconds=self.timeout_seconds)
