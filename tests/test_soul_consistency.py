"""Consistency guards for the six Sak Family persona SOUL files.

The six SOULs are hand-edited and have drifted before (missing siblings,
stale model lines, two personas claiming the same lane, references to tools
that do not exist in ``BUILTIN_TOOLS``). These tests parse the SOULs and
``personas/README.md`` and fail whenever the family stops telling one story,
so the drift cannot silently regress.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sakthai.agent.tools import BUILTIN_TOOLS

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"

# slug -> display name used inside SOUL prose
PERSONAS: dict[str, str] = {
    "sakthai": "SakThai",
    "sakking": "SakKing",
    "saksee": "SakSee",
    "saksit": "SakSit",
    "saktan": "SakTan",
    "sakjules": "SakJules",
}

# Tool names from runtimes the family no longer uses; SOULs must reference
# the real BUILTIN_TOOLS / CLI surface instead.
PHANTOM_TOOL_NAMES = ("supermemory-search", "supermemory-save", "skill_manage")


def soul_text(slug: str) -> str:
    """Return the SOUL.md contents for a persona slug."""
    return (PERSONAS_DIR / slug / "SOUL.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("slug", sorted(PERSONAS))
def test_soul_names_all_five_siblings(slug: str) -> None:
    """Every SOUL must mention each of its five siblings by display name."""
    text = soul_text(slug)
    missing = [name for other, name in PERSONAS.items() if other != slug and name not in text]
    assert not missing, f"{slug}/SOUL.md never mentions sibling(s): {missing}"


@pytest.mark.parametrize("slug", sorted(PERSONAS))
def test_soul_follows_local_model_policy(slug: str) -> None:
    """All agents default to the free local Ollama model (PR #344 policy)."""
    text = soul_text(slug)
    assert "Ollama" in text, f"{slug}/SOUL.md does not mention Ollama"
    for stale_model in ("llama3", "`qwen`"):
        assert stale_model not in text.lower(), (
            f"{slug}/SOUL.md names {stale_model!r} — pre-PR-#344 model drift"
        )


def test_financial_analysis_has_one_owner() -> None:
    """Exactly one persona (SakTan, the SakFin role) owns financial analysis."""
    owners = [slug for slug in PERSONAS if "Master of Financial Analysis" in soul_text(slug)]
    assert owners == ["saktan"], f"finance role claimed by: {owners}"


@pytest.mark.parametrize("slug", sorted(PERSONAS))
def test_soul_references_only_real_tools(slug: str) -> None:
    """SOULs must not reference tools from runtimes the family no longer uses."""
    text = soul_text(slug)
    found = [name for name in PHANTOM_TOOL_NAMES if name in text]
    assert not found, f"{slug}/SOUL.md references phantom tool(s): {found}"


def test_memory_tools_exist_in_builtin_tools() -> None:
    """The memory tools the SOULs point agents at must exist in the runtime."""
    builtin_names = {tool.name for tool in BUILTIN_TOOLS}
    assert {"learn", "recall", "search"} <= builtin_names


def test_shared_soul_lists_all_six_handles() -> None:
    """docs/SOUL.md (the shared family contract) must list all six bot handles."""
    text = (REPO_ROOT / "docs" / "SOUL.md").read_text(encoding="utf-8")
    missing = [f"@{slug}_agent_bot" for slug in PERSONAS if f"@{slug}_agent_bot" not in text]
    assert not missing, f"docs/SOUL.md missing handle(s): {missing}"


def test_personas_readme_skill_counts_match_disk() -> None:
    """personas/README.md per-persona and total skill counts must match disk."""
    readme = (PERSONAS_DIR / "README.md").read_text(encoding="utf-8")
    listed = {
        name: int(count)
        for count, name in re.findall(r"Contains the (\d+) skills mapped to (\w+)", readme)
    }
    assert set(listed) == set(PERSONAS.values()), f"README lists counts for {sorted(listed)}"
    actual = {
        name: len(list((PERSONAS_DIR / slug / "skills").rglob("SKILL.md")))
        for slug, name in PERSONAS.items()
    }
    assert listed == actual, f"README counts {listed} != on-disk counts {actual}"

    total_match = re.search(r"collectively host \*\*(\d+) specialized skills", readme)
    assert total_match is not None, "README total-skill claim not found"
    assert int(total_match.group(1)) == sum(actual.values())
