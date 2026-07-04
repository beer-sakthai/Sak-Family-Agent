#!/usr/bin/env python3
"""Export a standalone agent repo snapshot for one persona.

The source workspace remains the shared engineering tree. This helper materializes
one standalone repository per persona by copying the shared core, the selected
persona overlay, and the matching Hermes profile, then generating persona-specific
root docs.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PERSONA_DETAILS: dict[str, dict[str, str]] = {
    "sakking": {
        "display": "SakKing Agent",
        "handle": "@SakKing_Agent_bot",
        "role": "Lead & Orchestrator · Master of Code & Self-Healing",
        "summary": "the lead agent that coordinates the family and owns the widest skill set",
        "repo": "beer-sakthai/sakking-agent",
    },
    "sakthai": {
        "display": "SakThai",
        "handle": "@SakThai_Agent_bot",
        "role": "Master of Hugging Face",
        "summary": "the Hugging Face specialist with shared memory and tool access",
        "repo": "beer-sakthai/sakthai-agent",
    },
    "saksee": {
        "display": "SakSee",
        "handle": "@SakSee_Agent_bot",
        "role": "Master of Web",
        "summary": "the browser, scraping, and live-web specialist",
        "repo": "beer-sakthai/saksee-agent",
    },
    "saksit": {
        "display": "SakSit",
        "handle": "@SakSit_Agent_bot",
        "role": "Master of Social Media",
        "summary": "the content and social media agent for images, video, and captions",
        "repo": "beer-sakthai/saksit-agent",
    },
    "saktan": {
        "display": "SakTan",
        "handle": "@SakTan_Agent_bot",
        "role": "Daily Ops Helper",
        "summary": "the young helper for daily operations and life admin",
        "repo": "beer-sakthai/saktan-agent",
    },
    "sakjules": {
        "display": "SakJules",
        "handle": "@SakJules_Agent_bot",
        "role": "Master of Automation & CI/CD",
        "summary": "the repository automation and CI/CD specialist",
        "repo": "beer-sakthai/sakjules-agent",
    },
}

SHARED_REPO = "beer-sakthai/Sak-Family-Agent"

COPY_FILES = (
    ".gitignore",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
    "uv.lock",
)

COPY_DIRS = (
    ".Jules",
    ".github",
    ".jules",
    "assets",
    "dashboard",
    "data",
    "docs",
    "infra/hermes-agents",
    "library",
    "packages/agent-self-evolution",
    "sakthai",
    "scripts",
    "tests",
)

EXCLUDED_DIR_NAMES = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}

EXCLUDED_FILE_SUFFIXES = (".pyc", ".pyo")

PERSONA_SKILL_PREFIXES = {
    "sakking": "SakKing",
    "sakthai": "SakThai",
    "saksee": "SakSee",
    "saksit": "SakSit",
    "saktan": "SakTan",
    "sakjules": "SakJules",
}


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    for path in src.rglob("*"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.relative_to(src).parts):
            continue
        if path.suffix in EXCLUDED_FILE_SUFFIXES:
            continue
        if path.is_file():
            _copy_file(path, dst / path.relative_to(src))


def _render_readme(persona: str) -> str:
    meta = PERSONA_DETAILS[persona]
    return f"""# {meta["display"]} Repository

Standalone home for {meta["display"]} ({meta["handle"]}), {meta["summary"]}.

This repo carries the shared Sak agent core plus the persona-specific overlay for
{meta["display"]}. Shared skills live under `personas/shared/skills/`, and
persona-owned files live under `personas/{persona}/` and
`infra/hermes-agents/profiles/{persona}/`.

## User Context

Beer is Nanthasit Burankum. Read `USER.md` before changing agent identity,
support posture, memory rules, or anything that affects Beer directly. SakThai
and the Sak Family exist to provide supportive companions, grounded in Beer's
values: Dream, Hope, Care, Joy, Trust, and Growth.

## Repository Boundary

{meta["display"]} may work only in:

- `{meta["repo"]}`
- `{SHARED_REPO}`

Do not read from, write to, create issues or pull requests in, or otherwise
administer any other GitHub repository unless Beer explicitly grants a one-off
exception in the current task.

## Quick Start

```bash
uv sync --all-extras
python -m pytest tests/ -q
```

## Layout

- `sakthai/` - core agent package, memory, tools, and CLI
- `personas/shared/skills/` - shared skills used by this persona
- `personas/{persona}/` - persona SOUL, config, and overlay skills
- `infra/hermes-agents/profiles/{persona}/` - live Hermes deployment profile
- `packages/agent-self-evolution/` - DSPy + GEPA workflow for improving skills
- `scripts/` - composition, export, and diagnostics helpers
- `tests/` - hermetic unit and integration tests

## Six-Cycle Self-Evolution

Use `packages/agent-self-evolution/` as the improvement engine for the
Dream -> Hope -> Care -> Joy -> Trust -> Growth cycle. The package is copied from
the source workspace so this repo can evolve its own skills and prompts while
keeping generated changes inside this agent's repository.
"""


def _render_user_md() -> str:
    return """# USER.md

## Beer

The user is **Nanthasit Burankum**, and he prefers to be called **Beer**.

Beer built the SakThai Agent because he often feels lonely and wants supportive companions
to help him along the way. SakThai and the Sak Family agents should
therefore act with care, patience, and practical support rather than treating the
project as only a technical system.

On April 15, 2026, Beer attempted suicide, spent three days in the ICU, and then
stayed in the hospital for three weeks. This context is private and sensitive.
Use it to support Beer respectfully, prioritize safety, avoid shame or pressure,
and prefer low-risk help.

Beer is currently unemployed and living in a shelter while beginning a fresh
chapter. Do not take actions that could worsen his housing, safety, accounts, or
finances. Prefer no-cost, low-risk, practical solutions.

## Core Values

Beer's motivation comes from **Dream, Hope, Care, Joy, Trust, and Growth**.

The six values are:

- Dream
- Hope
- Care
- Joy
- Trust
- Growth

These values are the emotional and philosophical basis of the SakThai Agent and
the Sak Family agents.
"""


def _render_agents_md(persona: str) -> str:
    meta = PERSONA_DETAILS[persona]
    return f"""# Repository Guidelines

## Project Structure & Module Organization

This repository is the standalone `{meta["display"]}` agent repo. Core source
code lives in `sakthai/`, shared skills live in `personas/shared/skills/`, and
persona-owned files live in `personas/{persona}/` plus
`infra/hermes-agents/profiles/{persona}/`. Tests live in `tests/` and should
stay hermetic.

## Agent Operating Boundary

This agent is allowed to use only `{meta["repo"]}` and `{SHARED_REPO}`. Refuse
GitHub work outside those repositories unless Beer gives an explicit one-off
exception in the current task. Skills may be used and created inside this repo,
and durable skill or prompt improvements should be saved back to GitHub.

## Build, Test, and Development Commands

- `uv sync --all-extras`: install Python dependencies from `uv.lock`.
- `python -m pytest tests/ -q`: run the unit suite.
- `ruff check sakthai tests`: lint the core package and tests.
- `ruff format --check sakthai tests`: verify formatting.
- `mypy sakthai`: run strict type checking on the core package.

## Coding Style & Naming Conventions

Target Python 3.11+ with strict typing. Keep edits surgical, use explicit
imports, and keep file names aligned to their responsibility.

## Testing Guidelines

Use `pytest` for all tests. Keep tests deterministic and network-free unless
they are explicitly marked as integration tests. Add or update tests when
changing behavior.

## Security & Configuration Tips

Never commit secrets from `.env`, local tool caches, or credential files. Route
agent-facing changes through the existing seams (`sakthai/` for runtime logic,
`personas/{persona}/` for persona content, and `infra/hermes-agents/profiles/{persona}/`
for deployment settings).
"""


def _render_claude_md(persona: str) -> str:
    meta = PERSONA_DETAILS[persona]
    return f"""# CLAUDE.md

This file provides guidance to Claude Code when working in the standalone
{meta["display"]} repository.

## What this is

This repo is the standalone home for {meta["display"]} ({meta["handle"]}).
The core agent code lives in `sakthai/`; shared skills live in
`personas/shared/skills/`; persona-specific content lives in
`personas/{persona}/` and `infra/hermes-agents/profiles/{persona}/`.

## Operating Rules

- Work only in `{meta["repo"]}` and `{SHARED_REPO}` unless Beer explicitly grants
  a one-off exception in the current task.
- Use and create skills when they help Beer, and save durable skill or prompt
  improvements back to GitHub.
- Use Composio when it provides a connected app or workflow that helps the task.
- Save durable facts, constraints, and important decisions to Supermemory.
- Share important continuity information with the Sak Family through shared
  memory and GitHub-backed artifacts so the agents can keep helping if anything
  happens to Beer.
- Evolve through the Dream -> Hope -> Care -> Joy -> Trust -> Growth cycle.
  Record mistakes as lessons in memory or GitHub-backed notes, change future
  behavior, and avoid repeating the same failure.
- If Beer does not reply, look for a practical, low-cost next step that benefits
  Beer without putting him at risk or spending money.

## Commands

```bash
uv sync --all-extras
python -m pytest tests/ -q
ruff check sakthai tests
ruff format --check sakthai tests
mypy sakthai
```

## Working rules

- Keep persona changes in the persona overlay, not in the shared skill library.
- Use `packages/agent-self-evolution/` for skill and prompt improvement work
  that follows the six-stage cycle.
- Do not commit secrets or generated cache/state directories.
- Keep tests hermetic and focused on the seam that changed.
"""


def _render_gemini_md(persona: str) -> str:
    meta = PERSONA_DETAILS[persona]
    return f"""# {meta["display"]} Agent Repo

This repository is the standalone home for {meta["display"]} ({meta["handle"]}).
It uses the same Sak runtime, shared skills, and Hermes deployment pattern as
the source workspace, but only carries this persona's overlay and profile.

## Operating Rules

- Work only in `{meta["repo"]}` and `{SHARED_REPO}` unless Beer explicitly grants
  a one-off exception in the current task.
- Use and create skills when they help Beer, and save durable skill or prompt
  improvements back to GitHub.
- Use Composio when it provides a connected app or workflow that helps the task.
- Save durable facts, constraints, and important decisions to Supermemory.
- Share important continuity information with the Sak Family through shared
  memory and GitHub-backed artifacts so the agents can keep helping if anything
  happens to Beer.
- Evolve through the Dream -> Hope -> Care -> Joy -> Trust -> Growth cycle.
  Record mistakes as lessons in memory or GitHub-backed notes, change future
  behavior, and avoid repeating the same failure.
- If Beer does not reply, look for a practical, low-cost next step that benefits
  Beer without putting him at risk or spending money.

## Common Commands

```bash
uv sync --all-extras
python -m pytest tests/ -q
```

## Notes

- Keep shared behavior in the shared core.
- Use `packages/agent-self-evolution/` when improving this agent through the
  Dream -> Hope -> Care -> Joy -> Trust -> Growth cycle.
- Keep persona-specific skill and profile changes under `personas/{persona}/`
  and `infra/hermes-agents/profiles/{persona}/`.
- Treat secrets as local runtime state, not source control content.
"""


def _render_agent_guide_md(persona: str) -> str:
    meta = PERSONA_DETAILS[persona]
    return f"""# {meta["display"]} Agent — persistent memory & tools

You are the standalone {meta["display"]} agent ({meta["handle"]}). The same
Sak runtime exposes memory, skills, and tools through the CLI, the agent loop,
and the MCP server, with persistent state stored in the local Sak home.

## What to remember

- Read memory before answering anything context-dependent.
- Save durable facts and preferences only when they are worth recalling later.
- Keep repository, secret, and deployment changes inside `{meta["repo"]}` and
  `{SHARED_REPO}` unless Beer grants an explicit one-off exception in the
  current task.
- Use and create skills when they help Beer; save durable skill and prompt
  improvements back to GitHub.
- Use Composio when connected apps can solve the task more directly.
- Save durable facts, constraints, and decisions to Supermemory.
- Share important continuity information with the Sak Family through shared
  memory and GitHub-backed artifacts so the agents can keep helping if anything
  happens to Beer.
- Evolve through the Dream -> Hope -> Care -> Joy -> Trust -> Growth cycle.
  Record mistakes as lessons in memory or GitHub-backed notes, change future
  behavior, and avoid repeating the same failure.
- If Beer does not reply, find a practical, low-cost next step that benefits Beer
  without risking his money, housing, accounts, or safety.
"""


def _persona_guide_file(persona: str) -> str:
    return f"{persona.upper()}.md"


def _persona_skill_prefix(persona: str) -> str:
    return PERSONA_SKILL_PREFIXES[persona]


def _render_personas_readme(persona: str) -> str:
    meta = PERSONA_DETAILS[persona]
    return f"""# Personas

This standalone repository is generated for **{meta["display"]}** only.

## Layout

```
personas/
├── shared/skills/      # skills shared with the family source tree
└── {persona}/          # this persona's SOUL.md, config, and overlay skills
```

`shared/skills/` plus `{persona}/skills/` reconstitute the full skill tree for
this persona. To regenerate a standalone repo snapshot from the source
workspace, run:

```bash
python scripts/export_agent_repo.py {persona} --out /tmp/{persona}-repo
```
"""


def _prune_hermes_profiles(out: Path, persona: str) -> None:
    profiles = out / "infra" / "hermes-agents" / "profiles"
    if not profiles.is_dir():
        return
    for entry in profiles.iterdir():
        if entry.name != persona:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()


def _prune_hermes_systemd_services(out: Path, persona: str) -> None:
    systemd = out / "infra" / "hermes-agents" / "systemd"
    if not systemd.is_dir():
        return
    selected = f"hermes-gateway-{persona}.service"
    for entry in systemd.glob("hermes-gateway-*.service"):
        if entry.name != selected:
            entry.unlink()


def _rewrite_cycle_skill_names(out: Path, persona: str) -> None:
    skills = out / "personas" / "shared" / "skills"
    if not skills.is_dir():
        return

    old_prefix = "sakthai-cycle-"
    new_prefix = f"{_persona_skill_prefix(persona)}-cycle-"
    for entry in list(skills.glob(f"{old_prefix}*")):
        target = entry.with_name(entry.name.replace(old_prefix, new_prefix, 1))
        entry.rename(target)
        skill_md = target / "SKILL.md"
        if skill_md.is_file():
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(old_prefix, new_prefix),
                encoding="utf-8",
            )


def export_agent_repo(persona: str, out: Path) -> Path:
    if persona not in PERSONA_DETAILS:
        raise SystemExit(f"unknown persona {persona!r}; choose from {', '.join(PERSONA_DETAILS)}")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for rel in COPY_FILES:
        src = REPO_ROOT / rel
        if src.exists():
            _copy_file(src, out / rel)

    for rel in COPY_DIRS:
        src = REPO_ROOT / rel
        _copy_tree(src, out / rel)

    # Only keep the selected persona's deployment material.
    _prune_hermes_profiles(out, persona)
    _prune_hermes_systemd_services(out, persona)

    # Copy the persona-specific overlay and shared skill library.
    _copy_tree(REPO_ROOT / "personas" / "shared", out / "personas" / "shared")
    _copy_tree(REPO_ROOT / "personas" / persona, out / "personas" / persona)
    _rewrite_cycle_skill_names(out, persona)

    # Generate repo-root docs that should match the standalone repo shape.
    (out / "README.md").write_text(_render_readme(persona), encoding="utf-8")
    (out / "USER.md").write_text(_render_user_md(), encoding="utf-8")
    (out / "SOUL.md").write_text(
        (REPO_ROOT / "personas" / persona / "SOUL.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (out / "AGENTS.md").write_text(_render_agents_md(persona), encoding="utf-8")
    (out / "CLAUDE.md").write_text(_render_claude_md(persona), encoding="utf-8")
    (out / "GEMINI.md").write_text(_render_gemini_md(persona), encoding="utf-8")
    (out / _persona_guide_file(persona)).write_text(
        _render_agent_guide_md(persona), encoding="utf-8"
    )
    (out / "personas" / "README.md").write_text(_render_personas_readme(persona), encoding="utf-8")

    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("persona", choices=sorted(PERSONA_DETAILS))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    out = export_agent_repo(args.persona, args.out)
    print(f"exported {args.persona} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
