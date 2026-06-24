"""Import skills that SakKing has *learned* into this repo's ``skills/`` tree.

SakKing (the agent runtime at ``~/.sakking``) ships a set of *bundled* skills and
also accumulates *learned* (agent-created) ones over time. This module mirrors
the learned skills into the SakThai repo as first-class ``sakthai-`` skills:

* "learned" = a ``SKILL.md`` whose slug is **not** in SakKing'
  ``skills/.bundled_manifest`` (and is not a SakKing-internal ``sakking-*`` skill).
* Each learned skill is rewritten with the repo's canonical YAML frontmatter and
  a ``sakthai-`` name prefix, so it round-trips through :mod:`sakthai.skills`.
* The sync is **idempotent**: re-running rewrites only the skills whose rendered
  content changed, and reports created / updated / unchanged.

SakKing's learned skills are not guaranteed to carry frontmatter, so parsing here
is deliberately tolerant: a missing or invalid frontmatter block falls back to
deriving a title and description from the Markdown body.
"""

from __future__ import annotations

import contextlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import SKILLS_DIR, sakking_skills_dir

#: Slugs starting with these prefixes are SakKing-internal plumbing, not portable
#: capabilities — excluded from the sync by default.
DEFAULT_EXCLUDE_PREFIXES: tuple[str, ...] = ("sakking-",)

_BUNDLED_MANIFEST = ".bundled_manifest"
_PREFIX = "sakthai-"
_DEFAULT_VERSION = "1.0.0"
_DEFAULT_PLATFORMS: tuple[str, ...] = ("linux", "macos")
_MAX_DESC = 200


def bundled_slugs(skills_root: Path) -> set[str]:
    """Return the set of bundled skill slugs from ``skills/.bundled_manifest``.

    The manifest is ``slug:hash`` per line. A missing manifest yields an empty
    set (every discovered skill is then treated as learned).
    """
    manifest = skills_root / _BUNDLED_MANIFEST
    if not manifest.is_file():
        return set()
    slugs: set[str] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        slug = line.split(":", 1)[0].strip()
        if slug:
            slugs.add(slug)
    return slugs


def _lenient_front(raw: str) -> dict[str, Any]:
    """Recover top-level scalars from frontmatter that is not strict YAML.

    SakKing skills sometimes ship unquoted ``description:`` values that contain a
    colon-space (``coverage: login``), which ``yaml.safe_load`` rejects. This
    line scan salvages the keys we care about so a malformed block still yields a
    usable name/description/version.
    """
    out: dict[str, Any] = {}
    for line in raw.splitlines():
        if not line or line[0] in " \t" or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip("'\"")
        if key in {"name", "description", "version"} and val:
            out[key] = val
    return out


def _split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split a SKILL.md into (frontmatter dict | None, body).

    A leading ``---`` fence is always stripped from the body, even when its YAML
    is malformed, so the raw frontmatter never leaks into the imported body.
    """
    if text.lstrip().startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            body = parts[2].strip()
            front: Any = None
            with contextlib.suppress(yaml.YAMLError):
                front = yaml.safe_load(parts[1])
            if isinstance(front, dict):
                return front, body
            return (_lenient_front(parts[1]) or None), body
    return None, text.strip()


def _first_sentence(paragraph: str) -> str:
    collapsed = " ".join(paragraph.split())
    head = collapsed.split(". ", 1)[0].rstrip(".")
    if len(head) > _MAX_DESC:
        head = head[: _MAX_DESC - 1].rstrip() + "…"
    return head


def _derive_title(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _derive_description(body: str) -> str | None:
    """Pull a one-line description from a body lacking explicit frontmatter."""
    lines = body.splitlines()
    # Prefer the first paragraph under a "## Purpose" (or similar) heading.
    for idx, line in enumerate(lines):
        if line.strip().lower().lstrip("# ").startswith("purpose"):
            para = _collect_paragraph(lines[idx + 1 :])
            if para:
                return _first_sentence(para)
    # Otherwise the first non-heading, non-empty paragraph.
    skip_heading = True
    para_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if skip_heading and stripped.startswith("#"):
            skip_heading = False
            continue
        if not stripped:
            if para_lines:
                break
            continue
        if stripped.startswith("#"):
            break
        para_lines.append(stripped)
    if para_lines:
        return _first_sentence(" ".join(para_lines))
    return None


def _collect_paragraph(lines: Sequence[str]) -> str:
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if collected:
                break
            continue
        if stripped.startswith("#"):
            if collected:
                break
            continue
        collected.append(stripped)
    return " ".join(collected)


def _as_str_list(value: Any) -> list[str]:
    return [str(v) for v in value] if isinstance(value, list) else []


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


@dataclass
class LearnedSkill:
    """A SakKing-learned skill resolved into repo (``sakthai-``) form."""

    source_slug: str
    source_path: Path
    target_slug: str
    category: str
    description: str
    body: str
    version: str = _DEFAULT_VERSION
    platforms: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    related_skills: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Render canonical repo-format SKILL.md content (frontmatter + body)."""
        front: dict[str, Any] = {
            "name": self.target_slug,
            "category": self.category,
            "description": self.description,
            "version": self.version,
            "platforms": list(self.platforms),
            "metadata": {
                "sakthai": {
                    "tags": list(self.tags),
                    "related_skills": list(self.related_skills),
                    "source": f"sakking:{self.source_slug}",
                }
            },
        }
        block = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{block}\n---\n\n{self.body.strip()}\n"


def _target_slug(source_slug: str) -> str:
    return source_slug if source_slug.startswith(_PREFIX) else f"{_PREFIX}{source_slug}"


def _category_for(skill_md: Path, skills_root: Path) -> str:
    try:
        rel = skill_md.parent.relative_to(skills_root)
    except ValueError:
        return "sakking"
    return rel.parts[0] if len(rel.parts) >= 2 else "sakking"


def _resolve_skill(skill_md: Path, skills_root: Path) -> LearnedSkill | None:
    source_slug = skill_md.parent.name
    text = skill_md.read_text(encoding="utf-8")
    front, body = _split_frontmatter(text)
    front = front or {}

    description = front.get("description")
    if not isinstance(description, str) or not description.strip():
        description = _derive_description(body) or _derive_title(body) or source_slug
    description = " ".join(str(description).split())

    version = front.get("version")
    version_str = str(version) if version not in (None, "") else _DEFAULT_VERSION

    platforms = _as_str_list(front.get("platforms")) or list(_DEFAULT_PLATFORMS)

    sakthai_meta = (front.get("metadata") or {}).get("sakthai") or {}
    tags = _as_str_list(sakthai_meta.get("tags")) or _as_str_list(front.get("tags"))
    category = _category_for(skill_md, skills_root)
    tags = _dedupe([*tags, "sakking", category])
    related = _as_str_list(sakthai_meta.get("related_skills")) or _as_str_list(
        front.get("related_skills")
    )

    return LearnedSkill(
        source_slug=source_slug,
        source_path=skill_md,
        target_slug=_target_slug(source_slug),
        category=category,
        description=description,
        body=body,
        version=version_str,
        platforms=platforms,
        tags=tags,
        related_skills=related,
    )


def discover_learned_skills(
    skills_root: Path | None = None,
    *,
    exclude_prefixes: Sequence[str] = DEFAULT_EXCLUDE_PREFIXES,
) -> list[LearnedSkill]:
    """Find SakKing-learned skills (non-bundled, non-internal) under ``skills_root``."""
    root = skills_root if skills_root is not None else sakking_skills_dir()
    if not root.is_dir():
        return []
    bundled = bundled_slugs(root)
    excludes = tuple(exclude_prefixes)
    found: list[LearnedSkill] = []
    seen_targets: set[str] = set()
    for skill_md in sorted(root.rglob("SKILL.md")):
        rel = skill_md.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        source_slug = skill_md.parent.name
        if source_slug in bundled or source_slug.startswith(excludes):
            continue
        skill = _resolve_skill(skill_md, root)
        if skill is None or skill.target_slug in seen_targets:
            continue
        seen_targets.add(skill.target_slug)
        found.append(skill)
    return sorted(found, key=lambda s: s.target_slug)


@dataclass
class SyncOutcome:
    """Result of a sync run, grouped by what happened to each target slug."""

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.created) + len(self.updated) + len(self.unchanged)


def sync_sakking_skills(
    skills_root: Path | None = None,
    dest_dir: Path | None = None,
    *,
    dry_run: bool = False,
    exclude_prefixes: Sequence[str] = DEFAULT_EXCLUDE_PREFIXES,
) -> SyncOutcome:
    """Mirror SakKing-learned skills into ``dest_dir`` (the repo ``skills/`` tree).

    Idempotent: a skill whose rendered content already matches the file on disk
    is reported as ``unchanged`` and not rewritten. With ``dry_run`` no files are
    touched but the outcome still reflects what *would* change.
    """
    dest = dest_dir if dest_dir is not None else SKILLS_DIR
    outcome = SyncOutcome()
    for skill in discover_learned_skills(skills_root, exclude_prefixes=exclude_prefixes):
        target = dest / skill.target_slug / "SKILL.md"
        content = skill.render()
        existing = target.read_text(encoding="utf-8") if target.is_file() else None
        if existing == content:
            outcome.unchanged.append(skill.target_slug)
            continue
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (outcome.updated if existing is not None else outcome.created).append(skill.target_slug)
    return outcome
