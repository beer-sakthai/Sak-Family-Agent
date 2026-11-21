"""Keyword-based domain matching for the chat CLI.

Labels a reply with whichever Sak Family persona's domain best fits the
user's message — SakThai always generates the reply text; this only
affects how the reply panel is themed and labeled. See
docs/superpowers/specs/2026-07-25-persona-domain-match-design.md.
"""

from __future__ import annotations

MATCH_THRESHOLD = 2
STRONG_WEIGHT = 2
WEAK_WEIGHT = 1

# Each persona: (domain_label, strong_keywords, weak_keywords). A strong
# keyword is unambiguous enough to match alone (worth STRONG_WEIGHT, which
# equals MATCH_THRESHOLD); weak keywords need two combined hits. This split
# exists so an unambiguous phrase like "repair our CI/CD" matches on its own,
# while single common words (e.g. "task", "story") still require
# corroboration before labeling a reply.
PERSONA_DOMAINS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "sakking": (
        "general tasks",
        (),
        ("remind", "schedule", "task", "todo", "run this", "execute"),
    ),
    "saksee": (
        "web & browser automation",
        ("automate the web",),
        ("browser", "scrape", "website", "web page", "url"),
    ),
    "saksit": (
        "social & storytelling",
        ("social media", "instagram"),
        ("tweet", "caption", "story", "write a post"),
    ),
    "sakjules": (
        "CI/CD & automation",
        ("ci/cd", "github actions"),
        ("deploy", "pipeline", "workflow", "build fails"),
    ),
}


def match_persona(message: str) -> tuple[str, str] | None:
    """Score ``message`` against each persona's keywords (case-insensitive
    substring counts, strong keywords weighted higher than weak ones).
    Returns ``(persona_key, domain_label)`` for the highest scorer at or
    above :data:`MATCH_THRESHOLD`, or ``None`` if nothing clears it.
    """
    lowered = message.lower()
    best_persona: str | None = None
    best_domain = ""
    best_score = 0
    for persona, (domain, strong, weak) in PERSONA_DOMAINS.items():
        score = STRONG_WEIGHT * sum(1 for keyword in strong if keyword in lowered) + (
            WEAK_WEIGHT * sum(1 for keyword in weak if keyword in lowered)
        )
        if score > best_score:
            best_score = score
            best_persona = persona
            best_domain = domain
    if best_persona is not None and best_score >= MATCH_THRESHOLD:
        return best_persona, best_domain
    return None
