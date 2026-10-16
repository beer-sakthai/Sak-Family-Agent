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
    persona_mcp_config_path,
    persona_memory_db_path,
    persona_model_defaults,
)
from ..memory.store import MemoryStore
from .loop import AgentError, AgentResult, run_agent

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
    no_mcp: bool = False,
    client: Any = None,
    system_prompt: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Resolve default runtime arguments scoped to the target persona.

    Injects the persona's `SOUL.md` prefix, resolves default model/provider
    from `config.yaml`, scopes memory db to the persona shard if not injected,
    and sets up persona MCP manifest.
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

    mcp_config = persona_mcp_config_path(persona)
    resolved_mcp_config = mcp_config if mcp_config.is_file() else None

    return {
        "task": task,
        "persona": persona,
        "store": resolved_store,
        "provider": resolved_provider,
        "model": resolved_model,
        "skills": with_skills,
        "max_iterations": max_iterations or 8,
        "max_tokens": max_tokens,
        "no_mcp": no_mcp,
        "mcp_config": resolved_mcp_config,
        "client": client,
        "system_prompt": combined_prompt if combined_prompt else None,
        "verbose": verbose,
    }


def run_persona_task(
    persona: str,
    task: str,
    *,
    with_skills: Sequence[str] = (),
    max_iterations: int | None = None,
    max_tokens: int | None = None,
    max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
    store: MemoryStore | None = None,
    model: str | None = None,
    provider: str | None = None,
    no_mcp: bool = False,
    client: Any = None,
    verbose: bool = False,
) -> AgentResult:
    """Execute a task in-process under the scoped target persona.

    Guards against recursion cycles and nesting beyond ``max_depth``.
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
        no_mcp=no_mcp,
        client=client,
        verbose=verbose,
    )

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
    """Execute multiple persona tasks concurrently using ThreadPoolExecutor.

    Each task dict should contain:
      - 'persona': target persona name (str)
      - 'task': task prompt (str)
      - 'with_skills': optional Sequence[str]
      - 'max_iterations': optional int
      - 'max_tokens': optional int
      - 'model': optional str
      - 'provider': optional str
      - 'no_mcp': optional bool
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
        item_store = item.get("store") or store

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
            client=client,
            verbose=verbose,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_worker, t) for t in tasks]
        return [f.result() for f in futures]
