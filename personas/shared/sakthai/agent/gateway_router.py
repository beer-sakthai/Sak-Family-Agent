"""Multi-Agent Gateway Router & Intent Classifier.

Routes incoming prompts, Telegram messages, and API queries across the 6
Sak-Family personas based on query intent, specialized craft, tool requirements,
and persona charge levels.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class IntentCategory(StrEnum):
    """Categorized user intent for persona matching."""

    CORE_REASONING = "core_reasoning"
    CODING = "coding"
    ARCHITECTURE = "architecture"
    RESEARCH = "research"
    PRESENTATION = "presentation"
    COPYWRITING = "copywriting"
    AUTOMATION_CI = "automation_ci"
    OPERATIONS = "operations"
    GENERAL_CHAT = "general_chat"


@dataclass(frozen=True)
class IntentClassification:
    """Result of query intent analysis."""

    primary_intent: IntentCategory
    confidence: float
    detected_keywords: tuple[str, ...] = field(default_factory=tuple)
    tool_hints: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PersonaRouteResult:
    """Outcome of routing an incoming query to a target persona."""

    selected_persona: str
    intent: IntentClassification
    role_declaration: str
    charge_level: int
    fallback_chain: tuple[str, ...]
    routing_reason: str


# Canonical opening line declarations per persona
PERSONA_ROLES: Mapping[str, str] = {
    "sakthai": "**SakThai · Core Reasoning & Adaptive Coding.**",
    "sakking": "**SakKing · Architectural Vision & Strategic Design.**",
    "saksee": "**SakSee · Deep Research & Visual Intelligence.**",
    "saksit": "**SakSit · Creative Copywriting & Narrative Content.**",
    "sakjules": "**SakJules · Master of Automation & CI/CD.**",
    "saktan": "**SakTan · Daily Operations & Triage Master.**",
}

# Persona specialization keywords
_KEYWORD_PATTERNS: Mapping[IntentCategory, tuple[tuple[str, ...], float]] = {
    IntentCategory.AUTOMATION_CI: (
        (
            "ci",
            "cd",
            "github actions",
            "workflow",
            "docker",
            "pipeline",
            "deploy",
            "lint",
            "ruff",
            "bandit",
            "pr",
            "pull request",
            "build",
            "release",
            "scorecard",
            "subagent",
            "test failure",
            "fix ci",
        ),
        1.0,
    ),
    IntentCategory.RESEARCH: (
        (
            "research",
            "paper",
            "arxiv",
            "find",
            "search",
            "investigate",
            "compare models",
            "benchmark data",
            "dataset analysis",
            "literature",
            "scholar",
        ),
        0.95,
    ),
    IntentCategory.PRESENTATION: (
        (
            "slide",
            "slides",
            "powerpoint",
            "pptx",
            "marp",
            "presentation",
            "deck",
            "pitch",
            "visual diagram",
            "chart",
        ),
        0.95,
    ),
    IntentCategory.ARCHITECTURE: (
        (
            "architecture",
            "system design",
            "spec",
            "vision",
            "strategy",
            "roadmap",
            "plan",
            "high level",
            "comfyui",
            "framework design",
        ),
        0.9,
    ),
    IntentCategory.COPYWRITING: (
        (
            "copy",
            "copywriting",
            "headline",
            "marketing",
            "blog",
            "story",
            "article",
            "tweet",
            "post",
            "social media",
            "newsletter",
            "tone",
        ),
        0.9,
    ),
    IntentCategory.OPERATIONS: (
        (
            "schedule",
            "reminder",
            "today",
            "log",
            "diary",
            "quote",
            "price",
            "invoice",
            "triage",
            "daily task",
            "todo",
            "calendar",
        ),
        0.85,
    ),
    IntentCategory.CODING: (
        (
            "code",
            "function",
            "class",
            "bug",
            "refactor",
            "typecheck",
            "mypy",
            "pytest",
            "python",
            "typescript",
            "react",
            "api",
            "endpoint",
            "regex",
            "algorithm",
        ),
        0.85,
    ),
}

# Primary persona affinity per intent category
_INTENT_TO_PERSONA: Mapping[IntentCategory, str] = {
    IntentCategory.AUTOMATION_CI: "sakjules",
    IntentCategory.RESEARCH: "saksee",
    IntentCategory.PRESENTATION: "saksee",
    IntentCategory.ARCHITECTURE: "sakking",
    IntentCategory.COPYWRITING: "saksit",
    IntentCategory.OPERATIONS: "saktan",
    IntentCategory.CODING: "sakthai",
    IntentCategory.CORE_REASONING: "sakthai",
    IntentCategory.GENERAL_CHAT: "sakthai",
}

# Default fallback hierarchy if preferred persona has depleted charge (< 20%)
_DEFAULT_FALLBACK: Mapping[str, tuple[str, ...]] = {
    "sakthai": ("sakking", "sakjules", "saksee", "saksit", "saktan"),
    "sakking": ("sakthai", "saksee", "sakjules", "saksit", "saktan"),
    "saksee": ("sakthai", "sakking", "saksit", "sakjules", "saktan"),
    "saksit": ("sakthai", "saksee", "sakking", "saktan", "sakjules"),
    "sakjules": ("sakthai", "sakking", "saktan", "saksee", "saksit"),
    "saktan": ("sakjules", "sakthai", "saksit", "saksee", "sakking"),
}


def classify_intent(query: str) -> IntentClassification:
    """Classify user query into an intent category using heuristic token matching."""
    normalized = query.lower()
    best_intent = IntentCategory.GENERAL_CHAT
    best_score = 0.0
    matched_keywords: list[str] = []

    # Check explicit persona targeting tags (e.g., @sakjules, @saksee)
    persona_tag_match = re.search(r"@(?P<tag>sak(?:thai|king|see|sit|jules|tan))", normalized)
    if persona_tag_match:
        tag = persona_tag_match.group("tag")
        for intent, persona in _INTENT_TO_PERSONA.items():
            if persona == tag:
                return IntentClassification(
                    primary_intent=intent,
                    confidence=1.0,
                    detected_keywords=(f"@{tag}",),
                    tool_hints=(),
                )

    for intent, (keywords, weight) in _KEYWORD_PATTERNS.items():
        found = [kw for kw in keywords if kw in normalized]
        if found:
            # Score scales with number of matched keywords
            score = min(1.0, weight * (0.6 + 0.2 * len(found)))
            if score > best_score:
                best_score = score
                best_intent = intent
                matched_keywords = found

    if not matched_keywords:
        return IntentClassification(
            primary_intent=IntentCategory.CORE_REASONING,
            confidence=0.5,
            detected_keywords=(),
            tool_hints=(),
        )

    return IntentClassification(
        primary_intent=best_intent,
        confidence=best_score,
        detected_keywords=tuple(matched_keywords),
        tool_hints=(),
    )


def route_to_persona(
    query: str,
    charge_state: Mapping[str, int] | None = None,
    preferred_persona: str | None = None,
) -> PersonaRouteResult:
    """Select the optimal persona to handle the incoming query."""
    intent = classify_intent(query)
    effective_charge: dict[str, int] = {
        "sakthai": 100,
        "sakking": 100,
        "saksee": 100,
        "saksit": 100,
        "sakjules": 100,
        "saktan": 100,
    }
    if charge_state:
        effective_charge.update(charge_state)

    if preferred_persona and preferred_persona in PERSONA_ROLES:
        target = preferred_persona
        reason = f"Explicit user selection of @{preferred_persona}"
    else:
        target = _INTENT_TO_PERSONA.get(intent.primary_intent, "sakthai")
        reason = (
            f"Matched intent '{intent.primary_intent.value}' (confidence {intent.confidence:.2f})"
        )

    # Check charge threshold (Critical state < 20% triggers fallback)
    target_charge = effective_charge.get(target, 100)
    fallback_chain = _DEFAULT_FALLBACK.get(target, ("sakthai",))

    if target_charge < 20:
        for alternative in fallback_chain:
            if effective_charge.get(alternative, 0) >= 20:
                reason = (
                    f"Persona @{target} charge is critical ({target_charge}%); "
                    f"fell back to @{alternative} ({effective_charge.get(alternative)}%)"
                )
                target = alternative
                target_charge = effective_charge.get(alternative, 100)
                break

    role_decl = PERSONA_ROLES.get(target, PERSONA_ROLES["sakthai"])

    return PersonaRouteResult(
        selected_persona=target,
        intent=intent,
        role_declaration=role_decl,
        charge_level=target_charge,
        fallback_chain=fallback_chain,
        routing_reason=reason,
    )
