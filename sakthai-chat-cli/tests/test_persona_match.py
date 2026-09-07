"""Tests for sakthai.agent.persona_match — keyword-based domain matching."""

from __future__ import annotations

from sakthai.agent.persona_match import PERSONA_DOMAINS, match_persona


def test_match_persona_returns_none_for_an_ordinary_message() -> None:
    assert match_persona("What's the weather like today?") is None


def test_match_persona_requires_at_least_two_keyword_hits() -> None:
    # "deploy" alone is one hit — below the threshold.
    assert match_persona("Can you deploy this for me?") is None


def test_match_persona_matches_sakjules_on_cicd_language() -> None:
    result = match_persona("The github actions pipeline keeps failing on deploy")
    assert result == ("sakjules", "CI/CD & automation")


def test_match_persona_matches_saksee_on_browser_automation_language() -> None:
    result = match_persona("Can you scrape this website and grab the url list?")
    assert result == ("saksee", "web & browser automation")


def test_match_persona_matches_saksit_on_social_media_language() -> None:
    result = match_persona("Write a post caption for instagram about our launch")
    assert result == ("saksit", "social & storytelling")


def test_match_persona_matches_sakking_on_task_language() -> None:
    result = match_persona("Remind me to schedule this task for tomorrow")
    assert result == ("sakking", "general tasks")


def test_persona_domains_excludes_sakthai_and_saktan() -> None:
    assert "sakthai" not in PERSONA_DOMAINS
    assert "saktan" not in PERSONA_DOMAINS


def test_match_persona_matches_sakjules_on_a_single_strong_keyword() -> None:
    # "ci/cd" alone is unambiguous enough to match without a second hit.
    result = match_persona("Can you repair our CI/CD?")
    assert result == ("sakjules", "CI/CD & automation")


def test_match_persona_matches_saksit_on_a_single_strong_keyword() -> None:
    result = match_persona("Can you help with our Instagram strategy?")
    assert result == ("saksit", "social & storytelling")


def test_match_persona_still_requires_two_hits_for_weak_only_keywords() -> None:
    # "workflow" is a weak sakjules keyword — one hit alone isn't enough.
    assert match_persona("Let's talk about our workflow sometime") is None
