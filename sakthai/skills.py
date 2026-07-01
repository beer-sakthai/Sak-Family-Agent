"""Discover and inspect skills (``SKILL.md`` files with YAML frontmatter)."""

from __future__ import annotations

import contextlib
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .config import (LIBRARY_DIR, SKILLS_DIR, gemini_extensions_dir,
                     sakthai_home)

_UNCATEGORIZED = "general"

#: Longest a skill ``name`` may be (matches the authoring guide's MAX_NAME_LENGTH).
SKILL_NAME_MAX = 64

#: Prefix every skill in the *shared* library carries: ``Sak-<slug>``.
SHARED_SKILL_PREFIX = "Sak-"

#: Prefix a skill authored by a specific persona carries: ``Sak<Name>-<slug>``.
PERSONA_SKILL_PREFIXES: dict[str, str] = {
    "sakking": "SakKing-",
    "sakthai": "SakThai-",
    "saksee": "SakSee-",
    "saksit": "SakSit-",
    "saktan": "SakTan-",
}

#: Legacy prefix that predates the convention; stripped when retargeting a name.
_LEGACY_SKILL_PREFIX = "sakthai-"


class SkillParseError(ValueError):
    """Raised when a SKILL.md has missing or invalid frontmatter."""


@dataclass(frozen=True)
class SkillInfo:
    name: str
    path: Path
    category: str | None = None
    description: str | None = None
    version: str | None = None
    platforms: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    related_skills: list[str] = field(default_factory=list)
    body: str = ""


def _as_str_list(value: Any) -> list[str]:
    return [str(v) for v in value] if isinstance(value, list) else []


@lru_cache(maxsize=1024)
def _load_skill_file(path: Path) -> tuple[dict[str, Any], str]:
    """Read and parse a SKILL.md file, caching the results."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SkillParseError(f"{path}: no YAML frontmatter found")
    try:
        front = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise SkillParseError(f"{path}: invalid YAML — {exc}") from exc
    if not isinstance(front, dict):
        raise SkillParseError(f"{path}: empty or non-mapping frontmatter")
    return front, parts[2].strip()


def parse_skill(path: Path) -> SkillInfo:
    """Parse one SKILL.md into a :class:`SkillInfo`. Raises on bad frontmatter."""
    front, body = _load_skill_file(path)
    name = front.get("name")
    if not name or not isinstance(name, str):
        raise SkillParseError(f"{path}: missing required field: name")

    sakthai_meta = (front.get("metadata") or {}).get("sakthai") or {}
    return SkillInfo(
        name=name,
        path=path,
        category=front.get("category"),
        description=front.get("description"),
        version=front.get("version"),
        platforms=_as_str_list(front.get("platforms")),
        tags=_as_str_list(sakthai_meta.get("tags")),
        related_skills=_as_str_list(sakthai_meta.get("related_skills")),
        body=body,
    )


def list_skills(skills_dir: Path) -> list[SkillInfo]:
    """Parse skills directly under ``skills_dir`` (flat layout), skipping bad ones."""
    found_list: list[SkillInfo] = []
    for entry in sorted(skills_dir.iterdir()):
        skill_md = entry / "SKILL.md"
        if entry.is_dir() and skill_md.exists():
            with contextlib.suppress(SkillParseError):
                found_list.append(parse_skill(skill_md))
    return sorted(found_list, key=lambda s: s.name)


def validate_skills(skills_dir: Path) -> list[tuple[Path, str]]:
    """Return (path, reason) for each flat-layout skill that is missing or broken."""
    errors: list[tuple[Path, str]] = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            errors.append((entry, "missing SKILL.md"))
            continue
        try:
            parse_skill(skill_md)
        except SkillParseError as exc:
            errors.append((skill_md, str(exc).split(": ", 1)[-1]))
    return errors


def _category_for(skill: SkillInfo, skill_md: Path, root: Path) -> str:
    """Resolve a display category: explicit field → nesting dir → name prefix → general."""
    if skill.category:
        return skill.category
    try:
        rel = skill_md.parent.relative_to(root)
    except ValueError:
        rel = Path(skill.name)
    if len(rel.parts) >= 2:
        return rel.parts[0]
    if skill.name.startswith("sakthai-"):
        suffix = skill.name.removeprefix("sakthai-")
        if "-" in suffix:
            return suffix.split("-", 1)[0]
    return _UNCATEGORIZED


@lru_cache(maxsize=32)
def collect_skills(*roots: Path) -> list[SkillInfo]:
    """Recursively find every SKILL.md under each root, with categories filled in."""
    found_list: list[SkillInfo] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for skill_md in sorted(root.rglob("SKILL.md")):
            if skill_md in seen:
                continue
            seen.add(skill_md)
            with contextlib.suppress(SkillParseError):
                skill = parse_skill(skill_md)
                category = _category_for(skill, skill_md, root)
                found_list.append(replace(skill, category=category))
    return sorted(found_list, key=lambda s: (s.name.lower(), str(s.path)))


def _source_for(skill_md: Path, roots: tuple[Path, ...]) -> str:
    for root in roots:
        try:
            skill_md.relative_to(root)
        except ValueError:
            continue
        return root.name
    return ""


def build_catalog(*roots: Path) -> list[dict[str, Any]]:
    """Group :func:`collect_skills` by category into a display/export structure."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for skill in collect_skills(*roots):
        category = skill.category or _UNCATEGORIZED
        grouped.setdefault(category, []).append(
            {
                "name": skill.name,
                "version": skill.version,
                "description": skill.description,
                "tags": skill.tags,
                "platforms": skill.platforms,
                "related_skills": skill.related_skills,
                "source": _source_for(skill.path, roots),
            }
        )
    return [
        {
            "category": category,
            "count": len(skills),
            "skills": sorted(skills, key=lambda s: str(s["name"]).lower()),
        }
        for category, skills in sorted(grouped.items(), key=lambda kv: kv[0].lower())
    ]


def find_skill(name: str, *roots: Path) -> SkillInfo | None:
    """Find a parsed skill by exact name across the given roots."""
    for skill in collect_skills(*roots):
        if skill.name == name:
            return skill
    return None


def default_skill_roots() -> tuple[Path, ...]:
    """Roots searched for injectable skills: bundled + library + installed extensions."""
    gemini_ext = gemini_extensions_dir()
    roots = [SKILLS_DIR, LIBRARY_DIR, sakthai_home() / "extensions"]
    if gemini_ext.is_dir():
        roots.append(gemini_ext)
    return tuple(roots)


def render_skills_prompt_block(
    names: Sequence[str], roots: Sequence[Path] | None = None
) -> str:
    """Render the bodies of the named skills as a system-prompt block.

    Skills are matched by exact name across ``roots`` (defaulting to
    :func:`default_skill_roots`). Unknown names are skipped; returns ``""`` when
    nothing matches.
    """
    if not names:
        return ""
    search = tuple(roots) if roots is not None else default_skill_roots()
    by_name = {skill.name: skill for skill in collect_skills(*search)}
    sections: list[str] = []
    for name in names:
        skill = by_name.get(name)
        if skill is None:
            continue
        heading = f"### {skill.name}"
        if skill.description:
            heading += f" — {skill.description}"
        body = skill.body.strip()
        sections.append(f"{heading}\n\n{body}" if body else heading)
    if not sections:
        return ""
    return "## Active skills\n\n" + "\n\n".join(sections)


def validate_tree(*roots: Path) -> list[tuple[Path, str]]:
    """Validate every SKILL.md under each root, flagging empty skill folders too."""
    errors: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(p for p in root.iterdir() if p.is_dir()):
            if child.name.startswith("."):
                continue
            if not any(child.rglob("SKILL.md")):
                errors.append((child, "missing SKILL.md"))
        for skill_md in sorted(root.rglob("SKILL.md")):
            if skill_md in seen:
                continue
            seen.add(skill_md)
            try:
                parse_skill(skill_md)
            except SkillParseError as exc:
                errors.append((skill_md, str(exc).split(": ", 1)[-1]))
    return errors


def _all_known_prefixes() -> tuple[str, ...]:
    """Every convention prefix (shared + per-persona) plus the legacy one."""
    return (SHARED_SKILL_PREFIX, *PERSONA_SKILL_PREFIXES.values(), _LEGACY_SKILL_PREFIX)


def strip_known_prefix(slug: str) -> str:
    """Drop a single leading convention/legacy prefix from ``slug`` if present."""
    for prefix in _all_known_prefixes():
        if slug.startswith(prefix):
            return slug[len(prefix) :]
    return slug


def target_skill_name(current: str, prefix: str) -> str:
    """The convention-correct name for ``current`` under ``prefix`` (idempotent)."""
    return f"{prefix}{strip_known_prefix(current)}"


def naming_violations(root: Path, *, prefix: str) -> list[tuple[Path, str]]:
    """Report skills under ``root`` that break the naming convention.

    Each parseable ``SKILL.md`` is checked for: a ``name`` ≤ ``SKILL_NAME_MAX``
    chars, a ``name`` that matches its leaf folder, and the required ``prefix``
    for this layer (``Sak-`` shared, ``Sak<Name>-`` for a persona). Parse errors
    are left to :func:`validate_tree`; this only judges *naming*.
    """
    violations: list[tuple[Path, str]] = []
    if not root.is_dir():
        return violations
    for skill_md in sorted(root.rglob("SKILL.md")):
        try:
            skill = parse_skill(skill_md)
        except SkillParseError:
            continue
        folder = skill_md.parent.name
        issues: list[str] = []
        if len(skill.name) > SKILL_NAME_MAX:
            issues.append(f"name exceeds {SKILL_NAME_MAX} chars")
        if not skill.name.startswith(prefix):
            issues.append(f"missing required prefix '{prefix}'")
        if skill.name != folder:
            issues.append(f"name '{skill.name}' != folder '{folder}'")
        if issues:
            violations.append((skill_md, "; ".join(issues)))
    return violations
