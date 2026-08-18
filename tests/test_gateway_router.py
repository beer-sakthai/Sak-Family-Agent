"""Unit tests for Multi-Agent Gateway Router & Intent Classifier."""

from __future__ import annotations

from sakthai.agent.gateway_router import (
    PERSONA_ROLES,
    IntentCategory,
    classify_intent,
    route_to_persona,
)


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
