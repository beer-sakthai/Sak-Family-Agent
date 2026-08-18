"""Unit tests for Multi-Agent Gateway Router & Intent Classifier."""

from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError

from sakthai.agent.gateway_router import (
    PERSONA_ROLES,
    IntentCategory,
    IntentClassification,
    classify_intent,
    route_to_persona,
)


def test_intent_classification_default_values() -> None:
    intent = IntentClassification(
        primary_intent=IntentCategory.CODING,
        confidence=0.9,
    )
    assert intent.primary_intent == IntentCategory.CODING
    assert intent.confidence == 0.9
    assert intent.detected_keywords == ()
    assert intent.tool_hints == ()


def test_intent_classification_custom_tuples() -> None:
    intent = IntentClassification(
        primary_intent=IntentCategory.RESEARCH,
        confidence=0.95,
        detected_keywords=("arxiv", "paper"),
        tool_hints=("web_search",),
    )
    assert intent.detected_keywords == ("arxiv", "paper")
    assert intent.tool_hints == ("web_search",)


def test_intent_classification_immutability() -> None:
    intent = IntentClassification(
        primary_intent=IntentCategory.GENERAL_CHAT,
        confidence=0.5,
    )
    with pytest.raises(FrozenInstanceError):
        intent.confidence = 0.8  # type: ignore[misc]


def test_intent_classification_equality() -> None:
    intent1 = IntentClassification(
        primary_intent=IntentCategory.AUTOMATION_CI,
        confidence=1.0,
        detected_keywords=("ci", "workflow"),
    )
    intent2 = IntentClassification(
        primary_intent=IntentCategory.AUTOMATION_CI,
        confidence=1.0,
        detected_keywords=("ci", "workflow"),
    )
    intent3 = IntentClassification(
        primary_intent=IntentCategory.AUTOMATION_CI,
        confidence=0.8,
        detected_keywords=("ci", "workflow"),
    )
    assert intent1 == intent2
    assert intent1 != intent3


def test_classify_intent_automation_ci() -> None:
    intent = classify_intent(
        "Can you fix the failing GitHub Actions CI workflow in our release pipeline?"
    )
    assert intent.primary_intent == IntentCategory.AUTOMATION_CI
    assert intent.confidence >= 0.8
    assert any("ci" in kw or "workflow" in kw for kw in intent.detected_keywords)


def test_classify_intent_research() -> None:
    intent = classify_intent(
        "Please research recent arXiv papers on multimodal tool calling benchmarks."
    )
    assert intent.primary_intent == IntentCategory.RESEARCH
    assert intent.confidence >= 0.8
    assert "arxiv" in intent.detected_keywords or "research" in intent.detected_keywords


def test_classify_intent_presentation() -> None:
    intent = classify_intent(
        "Create a PowerPoint presentation deck with visual slides for our pitch."
    )
    assert intent.primary_intent == IntentCategory.PRESENTATION
    assert intent.confidence >= 0.8


def test_classify_intent_copywriting() -> None:
    intent = classify_intent(
        "Draft a marketing blog post and social media headline for our launch."
    )
    assert intent.primary_intent == IntentCategory.COPYWRITING
    assert intent.confidence >= 0.8


def test_classify_intent_operations() -> None:
    intent = classify_intent("What is my schedule and daily tasks on the calendar for today?")
    assert intent.primary_intent == IntentCategory.OPERATIONS
    assert intent.confidence >= 0.8


def test_classify_intent_coding() -> None:
    intent = classify_intent(
        "Refactor this Python function to optimize the regex algorithm and pass mypy."
    )
    assert intent.primary_intent == IntentCategory.CODING
    assert intent.confidence >= 0.8


def test_classify_intent_explicit_persona_tag() -> None:
    intent = classify_intent("Hey @sakjules please inspect the docker build status")
    assert intent.primary_intent == IntentCategory.AUTOMATION_CI
    assert intent.confidence == 1.0
    assert "@sakjules" in intent.detected_keywords


def test_route_to_persona_standard() -> None:
    route = route_to_persona("Deploy this new release workflow to GitHub Actions")
    assert route.selected_persona == "sakjules"
    assert route.role_declaration == PERSONA_ROLES["sakjules"]
    assert route.charge_level == 100


def test_route_to_persona_fallback_on_critical_charge() -> None:
    # Depleted charge on sakjules -> fallback to sakthai
    charge_state = {"sakjules": 10, "sakthai": 95}
    route = route_to_persona(
        "Deploy this new release workflow to GitHub Actions", charge_state=charge_state
    )
    assert route.selected_persona == "sakthai"
    assert route.role_declaration == PERSONA_ROLES["sakthai"]
    assert "critical" in route.routing_reason.lower()


def test_route_to_persona_explicit_preference() -> None:
    route = route_to_persona("Write a poem", preferred_persona="sakking")
    assert route.selected_persona == "sakking"
    assert route.role_declaration == PERSONA_ROLES["sakking"]
    assert "Explicit user selection" in route.routing_reason


def test_all_persona_roles_have_declarations() -> None:
    for persona in ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan"):
        assert persona in PERSONA_ROLES
        assert PERSONA_ROLES[persona].startswith(f"**{persona.capitalize()[:3]}")


def test_classify_intent_architecture() -> None:
    intent = classify_intent(
        "Design the high level architecture and roadmap for our system design spec."
    )
    assert intent.primary_intent == IntentCategory.ARCHITECTURE
    assert intent.confidence >= 0.8
    assert "architecture" in intent.detected_keywords or "roadmap" in intent.detected_keywords


def test_classify_intent_unmatched_fallback_to_core_reasoning() -> None:
    intent = classify_intent("xyz 123 unrecognised input")
    assert intent.primary_intent == IntentCategory.CORE_REASONING
    assert intent.confidence == 0.5
    assert intent.detected_keywords == ()


def test_classify_intent_all_persona_tags() -> None:
    tags = [
        "@sakthai",
        "@sakking",
        "@saksee",
        "@saksit",
        "@sakjules",
        "@saktan",
    ]
    for tag in tags:
        intent = classify_intent(f"Please help me {tag}")
        assert intent.confidence == 1.0
        assert intent.detected_keywords == (tag,)


def test_route_to_persona_fallback_chain_all_depleted() -> None:
    # All personas depleted -> keeps primary target or last checked
    charge_state = {
        "sakjules": 5,
        "sakthai": 5,
        "sakking": 5,
        "saksee": 5,
        "saksit": 5,
        "saktan": 5,
    }
    route = route_to_persona("Fix CI build", charge_state=charge_state)
    assert route.selected_persona == "sakjules"
    assert route.charge_level == 5


def test_route_to_persona_invalid_preferred_persona() -> None:
    route = route_to_persona("Fix CI build", preferred_persona="invalid_persona_name")
    assert route.selected_persona == "sakjules"
    assert "Matched intent 'automation_ci'" in route.routing_reason
