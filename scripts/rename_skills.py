#!/usr/bin/env python3
"""Apply the skill *naming convention* to a persona skill tree.

The convention (see :mod:`sakthai.skills`): every skill in the shared library
is named ``Sak-<slug>``; every skill authored by a persona is named
``Sak<Name>-<slug>`` (``SakKing-``, ``SakThai-``, ``SakSee-``, ``SakSit-``); a
skill's leaf folder name must equal its ``name`` field; ``name`` ≤ 64 chars.

Most of the existing trees predate the convention (plain slugs, or the legacy
``sakthai-`` prefix). This script is the **deferred mass-rename tool**: it
rewrites both the leaf folder name and the frontmatter ``name:`` field to the
convention-correct value, leaving the rest of the file untouched.

It is **dry-run by default** — it prints the planned moves and exits without
touching disk. Pass ``--apply`` to perform them.

Usage::

    # Preview the shared library rename (Sak- prefix)
    python scripts/rename_skills.py shared

    # Apply a persona overlay rename (SakSit- prefix)
    python scripts/rename_skills.py saksit --apply

After applying, ``sakthai skills validate --naming`` should pass for that layer,
and ``python scripts/compose_persona.py <persona> --out ...`` still composes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))
sys.path.insert(0, str(REPO_ROOT))

from sakthai.skills import (  # noqa: E402  (path bootstrap above)
    PERSONA_SKILL_PREFIXES,
    SHARED_SKILL_PREFIX,
    parse_skill,
    target_skill_name,
)

PERSONAS_DIR = REPO_ROOT / "personas"
#: ``layer name -> (skills root, required prefix)``.
LAYERS: dict[str, tuple[Path, str]] = {
    "shared": (PERSONAS_DIR / "shared" / "skills", SHARED_SKILL_PREFIX),
    **{
        persona: (PERSONAS_DIR / persona / "skills", prefix)
        for persona, prefix in PERSONA_SKILL_PREFIXES.items()
    },
}


def _planned_renames(root: Path, prefix: str) -> list[tuple[Path, str, str]]:
    """Return ``(skill_md, old_name, new_name)`` for every skill needing a rename."""
    plan: list[tuple[Path, str, str]] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        try:
            skill = parse_skill(skill_md)
        except Exception:  # noqa: BLE001 — malformed skills are validate's job
            continue
        new_name = target_skill_name(skill.name, prefix)
        folder = skill_md.parent.name
        if skill.name != new_name or folder != new_name:
            plan.append((skill_md, skill.name, new_name))
    return plan


def _apply(skill_md: Path, old_name: str, new_name: str) -> None:
    """Rewrite the ``name:`` field, then rename the leaf folder to ``new_name``."""
    text = skill_md.read_text(encoding="utf-8")
    # Replace only the first `name:` line in the frontmatter.
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip().startswith("name:"):
            indent = line[: len(line) - len(line.lstrip())]
            lines[i] = f"{indent}name: {new_name}\n"
            break
    skill_md.write_text("".join(lines), encoding="utf-8")
    folder = skill_md.parent
    if folder.name != new_name:
        folder.rename(folder.with_name(new_name))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layer", choices=list(LAYERS), help="which skill layer to rename")
    parser.add_argument(
        "--apply", action="store_true", help="perform the renames (default: dry-run)"
    )
    args = parser.parse_args(argv)

    root, prefix = LAYERS[args.layer]
    if not root.is_dir():
        print(f"no such skills root: {root}", file=sys.stderr)
        return 1

    plan = _planned_renames(root, prefix)
    if not plan:
        print(f"ok: {args.layer} already follows the naming convention")
        return 0

    verb = "renaming" if args.apply else "would rename"
    print(f"{verb} {len(plan)} skill(s) in {args.layer} -> prefix '{prefix}':")
    for skill_md, old_name, new_name in plan:
        print(f"  {old_name}  ->  {new_name}")
        if args.apply:
            _apply(skill_md, old_name, new_name)
    if not args.apply:
        print("\n(dry-run — re-run with --apply to perform these renames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
