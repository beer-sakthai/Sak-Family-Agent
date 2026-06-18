"""Commands to discover and inspect skills."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click

from ..config import LIBRARY_DIR, SKILLS_DIR, hermes_skills_dir
from ..hermes_skills import sync_hermes_skills
from ..skills import build_catalog, collect_skills, find_skill, validate_tree


@click.group()
def skills() -> None:
    """Discover and inspect SakThai skills."""


def _roots(source: str) -> tuple[Path, ...]:
    # Read the module-level dirs so tests can monkeypatch them.
    if source == "skills":
        return (SKILLS_DIR,)
    if source == "library":
        return (LIBRARY_DIR,)
    return (SKILLS_DIR, LIBRARY_DIR)


_SOURCE_OPTION = click.option(
    "--source",
    type=click.Choice(["all", "skills", "library"]),
    default="all",
    show_default=True,
    help="Which skill root(s) to scan.",
)


@skills.command("list")
@click.option("--category", default=None, help="Filter by category.")
@_SOURCE_OPTION
def skills_list(category: str | None, source: str) -> None:
    """List skills grouped by category."""
    catalog = build_catalog(*_roots(source))
    if category:
        catalog = [g for g in catalog if g["category"] == category]
    if not catalog:
        click.echo(f"no skills in category '{category}'" if category else "(no skills found)")
        return

    total = sum(g["count"] for g in catalog)
    click.secho(
        f"{total} skill(s) across {len(catalog)} categor{'y' if len(catalog) == 1 else 'ies'}\n",
        bold=True,
    )
    for group in catalog:
        entries: list[dict[str, Any]] = group["skills"]
        name_w = max(max(len(str(s["name"])) for s in entries), 4)
        click.secho(f"{group['category']}  ({group['count']})", fg="cyan", bold=True)
        for s in entries:
            desc = str(s["description"] or "")
            if len(desc) > 60:
                desc = desc[:59] + "…"
            click.echo(f"  {str(s['name']):<{name_w}}  {str(s['version'] or ''):<8}  {desc}")
        click.echo()


@skills.command("show")
@click.argument("name")
def skills_show(name: str) -> None:
    """Show full metadata and body of skill NAME."""
    skill = find_skill(name, *_roots("all"))
    if skill is None:
        raise click.ClickException(f"skill '{name}' not found")

    def _fmt(values: list[str] | None) -> str:
        return ", ".join(values) if values else "(none)"

    source = "library" if LIBRARY_DIR in skill.path.parents else "skills"
    click.echo(f"name:      {skill.name}")
    click.echo(f"category:  {skill.category or '(none)'}")
    click.echo(f"version:   {skill.version or '(none)'}")
    click.echo(f"source:    {source}")
    click.echo(f"platforms: {_fmt(skill.platforms)}")
    click.echo(f"tags:      {_fmt(skill.tags)}")
    click.echo(f"related:   {_fmt(skill.related_skills)}")
    click.echo(f"path:      {skill.path}")
    if skill.body:
        click.echo()
        click.echo(skill.body)


@skills.command("validate")
@_SOURCE_OPTION
def skills_validate(source: str) -> None:
    """Validate skill frontmatter; exit 1 if any errors are found."""
    roots = _roots(source)
    errors = validate_tree(*roots)
    if not errors:
        click.echo(f"ok  {len(collect_skills(*roots))} skills validated")
        return
    for path, message in errors:
        click.echo(f"error: {path}: {message}")
    click.echo(f"\n{len(errors)} error(s) found")
    sys.exit(1)


@skills.command("create")
@click.argument("name")
@click.option("--category", default="general", help="Skill category.")
@click.option("--description", default="A new SakThai skill.", help="Skill description.")
def skills_create(name: str, category: str, description: str) -> None:
    """Scaffold a new skill directory with a template SKILL.md under skills/."""
    slug = name.lower().replace("_", "-").replace(" ", "-")
    skill_dir = SKILLS_DIR / slug
    if skill_dir.exists():
        raise click.ClickException(f"skill directory '{skill_dir}' already exists")
    skill_dir.mkdir(parents=True, exist_ok=True)
    template = f"""---
name: {slug}
category: {category}
description: {description}
version: 1.0.0
platforms:
  - python
  - shell
metadata:
  sakthai:
    tags:
      - custom
    related_skills: []
---

# {name}

Describe how this skill works and its instructions here.
"""
    (skill_dir / "SKILL.md").write_text(template, encoding="utf-8")
    click.secho(f"created skill template → {skill_dir / 'SKILL.md'}", fg="green")


@skills.command("sync-hermes")
@click.option(
    "--hermes-home",
    "hermes_root",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Hermes skills dir (default: $HERMES_HOME/skills or ~/.hermes/skills).",
)
@click.option("--dry-run", is_flag=True, help="Report what would change without writing.")
def skills_sync_hermes(hermes_root: Path | None, dry_run: bool) -> None:
    """Import skills Hermes has learned into skills/ as sakthai- skills."""
    source = hermes_root if hermes_root is not None else hermes_skills_dir()
    if not source.is_dir():
        raise click.ClickException(f"Hermes skills dir not found: {source}")
    outcome = sync_hermes_skills(source, SKILLS_DIR, dry_run=dry_run)
    verb = "would sync" if dry_run else "synced"
    click.secho(
        f"{verb} {outcome.total} learned skill(s) from {source}",
        bold=True,
    )
    for slug in outcome.created:
        click.secho(f"  + {slug}", fg="green")
    for slug in outcome.updated:
        click.secho(f"  ~ {slug}", fg="yellow")
    if outcome.unchanged:
        click.echo(f"  ({len(outcome.unchanged)} unchanged)")
