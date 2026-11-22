"""Automated Memory & Episodic Context Middleware for the SakThai Runtime Gateway."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ..agent_platform.safety import DataLossGuardrail
from ..config import persona_memory_db_path, redact_secrets
from ..memory.store import DEFAULT_FACT_LIMIT, DEFAULT_OBS_LIMIT, MemoryStore

logger = logging.getLogger(__name__)

PERSONA_LABELS: dict[str, dict[str, str]] = {
    "sakthai": {"name": "SakThai", "role": "Main Lead, HF Master, Orchestrator"},
    "sakking": {"name": "SakKing", "role": "General Assistant & Runner · Deputy 1"},
    "saksee": {"name": "SakSee", "role": "Web / Browser Specialist · Deputy 3"},
    "sakjules": {"name": "SakJules", "role": "GitHub, CI/CD & Automation"},
    "saksit": {"name": "SakSit", "role": "Social / Content Specialist"},
    "saktan": {"name": "SakTan", "role": "Daily Ops, Rhythm & Execution"},
}


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

    def get_all_shards_metadata(self) -> dict[str, Any]:
        """Return file size and record counts for all 6 persona SQLite memory shards."""
        shards: list[dict[str, Any]] = []
        total_facts = 0
        total_obs = 0
        total_bytes = 0

        for p, meta in PERSONA_LABELS.items():
            db_path = persona_memory_db_path(p)
            file_size = db_path.stat().st_size if db_path.exists() else 0
            total_bytes += file_size
            facts_count = 0
            obs_count = 0
            try:
                with self.store_factory(p) as store:
                    cur = store._conn.cursor()
                    facts_count = cur.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
                    obs_count = cur.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            except Exception as exc:
                logger.debug("Failed reading shard count for persona %s: %s", p, exc)

            total_facts += facts_count
            total_obs += obs_count
            shards.append(
                {
                    "persona": p,
                    "name": meta["name"],
                    "role": meta["role"],
                    "db_path": str(db_path),
                    "exists": db_path.exists(),
                    "size_bytes": file_size,
                    "facts_count": facts_count,
                    "observations_count": obs_count,
                }
            )

        return {
            "ok": True,
            "shards": shards,
            "total_shards": len(shards),
            "total_facts": total_facts,
            "total_observations": total_obs,
            "total_size_bytes": total_bytes,
        }

    def list_persona_facts(
        self,
        persona: str,
        kind: str | None = None,
        tag: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List persistent facts for a specific persona or merged across all shards."""
        p = persona.lower().strip()
        if p in ("all", "merged"):
            all_facts: list[dict[str, Any]] = []
            for sibling in PERSONA_LABELS:
                try:
                    with self.store_factory(sibling) as store:
                        facts = (
                            store.search_by_tag(tag, limit=limit)
                            if tag
                            else store.list_facts(limit=limit, kind=kind)
                        )
                        for f in facts:
                            all_facts.append(
                                {
                                    "id": f.id,
                                    "persona": sibling,
                                    "kind": f.kind,
                                    "key": f.key,
                                    "value": f.value,
                                    "tags": getattr(f, "tags", []) or [],
                                    "updated_at": f.updated_at,
                                    "created_at": f.created_at,
                                }
                            )
                except Exception as exc:
                    logger.debug("Failed listing facts for %s: %s", sibling, exc)
            all_facts.sort(key=lambda x: x["updated_at"], reverse=True)
            return {
                "ok": True,
                "persona": "merged",
                "count": len(all_facts[:limit]),
                "facts": all_facts[:limit],
            }

        if p not in PERSONA_LABELS and p != "default":
            return {"ok": False, "error": f"Unknown persona '{persona}'", "facts": []}

        target = p if p in PERSONA_LABELS else "sakthai"
        try:
            with self.store_factory(target) as store:
                facts = (
                    store.search_by_tag(tag, limit=limit)
                    if tag
                    else store.list_facts(limit=limit, kind=kind)
                )
                facts_data = [
                    {
                        "id": f.id,
                        "persona": target,
                        "kind": f.kind,
                        "key": f.key,
                        "value": f.value,
                        "tags": getattr(f, "tags", []) or [],
                        "updated_at": f.updated_at,
                        "created_at": f.created_at,
                    }
                    for f in facts
                ]
                return {
                    "ok": True,
                    "persona": target,
                    "count": len(facts_data),
                    "facts": facts_data,
                }
        except Exception as exc:
            return {"ok": False, "persona": target, "error": str(exc), "facts": []}

    def add_fact(
        self,
        persona: str,
        value: str,
        *,
        kind: str = "fact",
        key: str | None = None,
        tags: list[str] | None = None,
        approval_token: str | None = None,
    ) -> dict[str, Any]:
        """Safely record a new memory fact under DataLossGuardrail protection."""
        target = persona.lower().strip()
        if target not in PERSONA_LABELS and target != "default":
            return {"ok": False, "status": "error", "error": f"Unknown persona '{persona}'"}

        actual_target = target if target in PERSONA_LABELS else "sakthai"
        if not value or not isinstance(value, str) or not value.strip():
            return {
                "ok": False,
                "status": "error",
                "error": "Fact value must be a non-empty string",
            }

        guardrail = DataLossGuardrail()
        check = guardrail.verify_or_halt(value, approval_token=approval_token)
        if check.blocked:
            token = guardrail.generate_approval_token(value)
            return {
                "ok": False,
                "status": "blocked",
                "error": f"Destructive content detected: {check.reason}",
                "impact": check.impact,
                "approval_token": token,
            }

        try:
            with self.store_factory(actual_target) as store:
                clean_key = key.strip() if key else None
                fact_id = store.add_fact(
                    value=value.strip(),
                    kind=kind.strip() or "fact",
                    key=clean_key,
                    tags=tags or [],
                )
                fact = store.get_fact(fact_id)
                fact_dict = {
                    "id": fact_id,
                    "persona": actual_target,
                    "kind": fact.kind if fact else kind,
                    "key": fact.key if fact else clean_key,
                    "value": fact.value if fact else value,
                    "tags": (getattr(fact, "tags", []) or []) if fact else (tags or []),
                    "updated_at": fact.updated_at if fact else 0,
                    "created_at": fact.created_at if fact else 0,
                }
                return {
                    "ok": True,
                    "status": "created",
                    "persona": actual_target,
                    "fact": fact_dict,
                }
        except Exception as exc:
            return {"ok": False, "status": "error", "error": str(exc)}

    def delete_fact(
        self,
        persona: str,
        fact_id: int,
        *,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """Delete a fact from a persona's shard, requiring explicit confirmation."""
        target = persona.lower().strip()
        if target not in PERSONA_LABELS and target != "default":
            return {"ok": False, "status": "error", "error": f"Unknown persona '{persona}'"}

        actual_target = target if target in PERSONA_LABELS else "sakthai"
        if not confirmed:
            return {
                "ok": False,
                "status": "confirmation_required",
                "error": "Explicit confirmation required to delete fact (pass confirmed=True)",
                "fact_id": fact_id,
                "persona": actual_target,
            }

        try:
            with self.store_factory(actual_target) as store:
                existing = store.get_fact(fact_id)
                if existing is None:
                    return {
                        "ok": False,
                        "status": "not_found",
                        "error": f"Fact ID {fact_id} not found in {actual_target} shard",
                    }
                success = store.forget_fact(fact_id)
                return {
                    "ok": success,
                    "status": "deleted" if success else "failed",
                    "fact_id": fact_id,
                    "persona": actual_target,
                }
        except Exception as exc:
            return {"ok": False, "status": "error", "error": str(exc)}

    def preview_memory_context(
        self,
        persona: str,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Simulate dynamic memory prompt context injection for test queries."""
        target = persona.lower().strip()
        actual_target = target if target in PERSONA_LABELS else "sakthai"
        prompt_block = self.get_memory_context(actual_target, query=query, limit=limit)
        facts: list[Any] = []
        obs: list[Any] = []
        try:
            with self.store_factory(actual_target) as store:
                if query.strip():
                    facts, obs = store.search_memory(query.strip(), limit=limit)
                if not facts and not obs:
                    facts = store.list_facts(limit=limit)
                    obs = store.top_observations(limit=limit)
        except Exception as exc:
            logger.debug("Failed retrieving structured items for preview: %s", exc)

        return {
            "ok": True,
            "persona": actual_target,
            "query": query,
            "prompt_context": prompt_block,
            "facts_count": len(facts),
            "observations_count": len(obs),
            "facts": [
                {
                    "id": f.id,
                    "kind": f.kind,
                    "key": f.key,
                    "value": f.value,
                    "tags": getattr(f, "tags", []) or [],
                    "updated_at": f.updated_at,
                }
                for f in facts
            ],
            "observations": [
                {
                    "id": o.id,
                    "summary": o.summary,
                    "weight": o.weight,
                    "created_at": o.created_at,
                }
                for o in obs
            ],
        }
