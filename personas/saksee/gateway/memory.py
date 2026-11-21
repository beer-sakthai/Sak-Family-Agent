"""Automated Memory & Episodic Context Middleware for the SakThai Runtime Gateway."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ..config import persona_memory_db_path, redact_secrets
from ..memory.store import DEFAULT_FACT_LIMIT, DEFAULT_OBS_LIMIT, MemoryStore

logger = logging.getLogger(__name__)


def _default_store_factory(persona: str = "sakthai") -> MemoryStore:
    """Open a MemoryStore pointing to the persona's SQLite shard."""
    return MemoryStore(db_path=persona_memory_db_path(persona))


class GatewayMemoryManager:
    """Manages automatic memory context retrieval and episodic interaction logging."""

    def __init__(
        self,
        store_factory: Callable[[str], MemoryStore] | None = None,
    ) -> None:
        self.store_factory = store_factory or _default_store_factory

    def get_memory_context(
        self,
        persona: str,
        query: str = "",
        limit: int = 5,
    ) -> str:
        """Retrieve relevant memory facts and observations formatted for prompt injection."""
        try:
            with self.store_factory(persona) as store:
                facts: list[Any] = []
                obs: list[Any] = []
                if query.strip():
                    facts, obs = store.search_memory(query.strip(), limit=limit)

                # Fallback to recent facts/observations if query search yielded nothing
                if not facts and not obs:
                    facts = store.list_facts(limit=min(limit, DEFAULT_FACT_LIMIT))
                    obs = store.top_observations(limit=min(limit, DEFAULT_OBS_LIMIT))

                if not facts and not obs:
                    return ""

                lines = [
                    f"### Persistent Memory Context for {persona.capitalize()}",
                    "The following facts and observations from past interactions are relevant to this query:",
                ]
                for f in facts[:limit]:
                    key_label = f"{f.key} = " if f.key else ""
                    lines.append(f"- Fact [{f.kind}]: {key_label}{f.value}")
                for o in obs[:limit]:
                    lines.append(f"- Context: {o.summary}")

                return redact_secrets("\n".join(lines))
        except Exception as exc:
            logger.warning("Failed to retrieve memory context for persona %s: %s", persona, exc)
            return ""

    def record_turn(
        self,
        persona: str,
        user_prompt: str,
        assistant_response: str,
    ) -> bool:
        """Record an episodic conversation turn into the persona's memory store."""
        if not user_prompt.strip() or not assistant_response.strip():
            return False
        try:
            with self.store_factory(persona) as store:
                clean_prompt = redact_secrets(user_prompt.strip())[:200]
                clean_response = redact_secrets(assistant_response.strip())[:300]
                summary = f"User asked: {clean_prompt} | {persona.capitalize()} answered: {clean_response}"
                store.add_observation(
                    summary=summary,
                    weight=0.8,
                    confidence=0.7,
                )
                return True
        except Exception as exc:
            logger.warning("Failed to record conversation turn for persona %s: %s", persona, exc)
            return False

    def get_memory_stats(self, persona: str, limit: int = 10) -> dict[str, Any]:
        """Return memory statistics and recent facts for a persona."""
        try:
            with self.store_factory(persona) as store:
                facts = store.list_facts(limit=limit)
                obs = store.top_observations(limit=limit)
                return {
                    "ok": True,
                    "persona": persona,
                    "facts_count": len(facts),
                    "observations_count": len(obs),
                    "facts": [
                        {
                            "key": f.key,
                            "value": f.value,
                            "kind": f.kind,
                            "updated_at": f.updated_at,
                        }
                        for f in facts
                    ],
                    "observations": [
                        {
                            "summary": o.summary,
                            "weight": o.weight,
                            "created_at": o.created_at,
                        }
                        for o in obs
                    ],
                }
        except Exception as exc:
            logger.warning("Failed to get memory stats for persona %s: %s", persona, exc)
            return {
                "ok": False,
                "persona": persona,
                "error": str(exc),
                "facts_count": 0,
                "observations_count": 0,
                "facts": [],
                "observations": [],
            }
