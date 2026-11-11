"""Consistency guards for the six Sak Family persona SOUL files.

The six SOULs are hand-edited and have drifted before (missing siblings,
stale model lines, two personas claiming the same lane, references to tools
that do not exist in ``BUILTIN_TOOLS``). These tests parse the SOULs and
``personas/README.md`` and fail whenever the family stops telling one story,
so the drift cannot silently regress.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import click
import pytest
import yaml

from sakthai.agent.tools import BUILTIN_TOOLS
from sakthai.cli import main as cli_main
from sakthai.config import persona_model_defaults

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"

# slug -> display name used inside SOUL prose
PERSONAS: dict[str, str] = {
    "sakthai": "SakThai",
    "sakking": "SakKing",
    "saktan": "SakTan",
    "saksee": "SakSee",
    "saksit": "SakSit",
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
def test_soul_does_not_misstate_its_default_model(slug: str) -> None:
    """A SOUL must not claim a default model its own config.yaml contradicts.

    PR #344 put every agent on local Ollama and this test once required each
    SOUL to say so; #1619 moved five of them to Hugging Face, which left a
    "Default Local Model: Ollama" footer that only SakTan's config still bears out.
    """
    text = soul_text(slug)
    provider, _model = persona_model_defaults(slug)
    if provider != "ollama":
        assert "Default Local Model: Ollama" not in text, (
            f"{slug}/SOUL.md claims Ollama, but its config.yaml uses {provider!r}"
        )
    for stale_model in ("llama3", "`qwen`"):
        assert stale_model not in text.lower(), (
            f"{slug}/SOUL.md names {stale_model!r} — pre-PR-#344 model drift"
        )


def test_financial_analysis_has_no_owner() -> None:
    """No active persona claims financial analysis (SakTan, which once held that lane, now keeps operations)."""
    owners = [slug for slug in PERSONAS if "Master of Financial Analysis" in soul_text(slug)]
    assert owners == [], f"finance role still claimed by: {owners}"


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


def soul_cli_lines(slug: str) -> list[str]:
    """Every ``sakthai ...`` command in the SOUL's code blocks, continuations joined."""
    lines: list[str] = []
    for block in re.findall(r"```[a-z]*\n(.*?)```", soul_text(slug), re.S):
        joined = re.sub(r"\\\n\s*", " ", block)
        lines += [
            line.strip() for line in joined.splitlines() if line.strip().startswith("sakthai ")
        ]
    return lines


@pytest.mark.parametrize("slug", sorted(PERSONAS))
def test_soul_cli_commands_parse_against_the_real_cli(slug: str) -> None:
    """Each ``sakthai`` command a SOUL tells its agent to run must exist and parse.

    Five SOULs once told agents to run ``sakthai search ... --tag a --tag b``,
    a command the CLI never had.
    """
    for line in soul_cli_lines(slug):
        command: click.Command = cli_main
        args = shlex.split(line)[1:]
        while isinstance(command, click.Group) and args and args[0] in command.commands:
            command = command.commands[args.pop(0)]
        assert not isinstance(command, click.Group), f"{slug}/SOUL.md: no such command: {line}"
        try:
            command.make_context("sakthai", args)
        except click.UsageError as exc:
            pytest.fail(f"{slug}/SOUL.md: `{line}` does not parse: {exc.format_message()}")


HERMES_SOULS: dict[str, Path] = {
    slug: REPO_ROOT
    / "infra"
    / "hermes-agents"
    / ("default" if slug == "sakthai" else f"profiles/{slug}")
    / "SOUL.md"
    for slug in PERSONAS
}


def security_rules(path: Path) -> str:
    """The ``## Security Rules`` section of a SOUL file, or "" if it has none."""
    text = path.read_text(encoding="utf-8")
    start = text.find("\n## Security Rules\n")
    if start == -1:
        return ""
    return text[start : text.find("\n---\n", start)]


@pytest.mark.parametrize("slug", sorted(PERSONAS))
def test_soul_carries_the_shared_security_rules(slug: str) -> None:
    """Every SOUL, and its Hermes profile copy, carries the same Security Rules.

    The SOUL is injected as the agent's system prompt, so it is the only place
    these rules reach the model: a persona without the section never hears
    them.
    """
    canonical = security_rules(PERSONAS_DIR / "sakthai" / "SOUL.md")
    assert canonical, "personas/sakthai/SOUL.md has no '## Security Rules' section"
    for path in (PERSONAS_DIR / slug / "SOUL.md", HERMES_SOULS[slug]):
        assert security_rules(path) == canonical, (
            f"{path.relative_to(REPO_ROOT)} Security Rules differ from personas/sakthai/SOUL.md"
        )


def test_shared_soul_lists_all_six_handles() -> None:
    """docs/SOUL.md (the shared family contract) must list all six bot handles."""
    text = (REPO_ROOT / "docs" / "SOUL.md").read_text(encoding="utf-8")
    missing = [f"@{slug}_agent_bot" for slug in PERSONAS if f"@{slug}_agent_bot" not in text]
    assert not missing, f"docs/SOUL.md missing handle(s): {missing}"


def test_shared_soul_roles_match_the_workspace_configs() -> None:
    """docs/SOUL.md's team table shows each persona's role from its own workspace.yaml.

    It once listed SakTan and SakJules as retired and named models no config used.
    """
    text = (REPO_ROOT / "docs" / "SOUL.md").read_text(encoding="utf-8")
    for slug in PERSONAS:
        workspace = yaml.safe_load(
            (PERSONAS_DIR / slug / "config" / "workspace.yaml").read_text(encoding="utf-8")
        )
        row = f"| `@{slug}_agent_bot` | {workspace['role']} |"
        assert row in text, f"docs/SOUL.md has no row {row!r}"


PERSONA_FILES = ("SOUL.md", "PLAN.md", "CYCLE.md", "MEMORY.md", "HANDOFF.md", "BACKPACK.md")


@pytest.mark.parametrize("slug", sorted(PERSONAS))
def test_persona_keeps_the_working_files_and_installs_nothing_at_runtime(slug: str) -> None:
    """Every persona carries the same six files, and none says to `npx -y` a package `@latest`.

    Only SakJules and SakSee had the five beside SOUL.md once, and both of their
    BACKPACK files listed `@latest` installs that their own Security Rule 5 forbids.
    """
    for name in PERSONA_FILES:
        path = PERSONAS_DIR / slug / name
        assert path.is_file(), f"personas/{slug}/{name} is missing"
        unpinned = re.findall(r"npx -y [\w@/.-]+@latest", path.read_text(encoding="utf-8"))
        assert not unpinned, f"personas/{slug}/{name} installs unpinned: {unpinned}"


def test_personas_readme_skill_counts_match_disk() -> None:
    """personas/README.md per-persona and total skill counts must match disk."""
    readme = (PERSONAS_DIR / "README.md").read_text(encoding="utf-8")
    listed = {
        name: int(count)
        for count, name in re.findall(r"Contains the (\d+) skills mapped to (\w+)", readme)
    }
    assert set(listed) == set(PERSONAS.values()), f"README lists counts for {sorted(listed)}"
    # Count skill directories, not directory entries: personas/sakthai/skills
    # also holds README.md, .gitignore and hf-topics-covered.json, and a bare
    # iterdir() counted those three as skills.
    actual = {
        name: sum(
            1
            for entry in (PERSONAS_DIR / slug / "skills").iterdir()
            if entry.is_dir() and (entry / "SKILL.md").is_file()
        )
        for slug, name in PERSONAS.items()
    }
    assert listed == actual, f"README counts {listed} != on-disk counts {actual}"

    total_match = re.search(r"collectively host \*\*(\d+) specialized skills", readme)
    assert total_match is not None, "README total-skill claim not found"
    assert int(total_match.group(1)) == sum(actual.values())
