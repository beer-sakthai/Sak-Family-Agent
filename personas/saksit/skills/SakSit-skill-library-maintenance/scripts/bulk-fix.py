#!/usr/bin/env python3
"""Bulk-fix common skill frontmatter issues at scale.

Fixes applied (each opt-in via CLI flag):
  --fix-desc     : Shorten descriptions to ≤60 chars (requires DESC_MAP dict)
  --fix-tags     : Add missing tags (requires TAGS_MAP dict)
  --fix-name     : Fix frontmatter name to match directory name
  --fix-related  : Remove broken related_skills cross-references

Usage:

    uv run python3 scripts/bulk-fix.py --fix-desc --fix-tags --fix-name --fix-related

Pitfalls:
  • Skills live under category directories: skills/<cat>/<name>/SKILL.md
  • yaml.dump() corrupts complex frontmatter — use targeted text replacement
    instead of rewriting the entire YAML block.
  • Related_skills may appear as inline YAML [item1, item2] — line-level
    removal won't catch these.
  • Always run the structural test after fixing to verify no regressions.
"""

import os
import re
import sys
from pathlib import Path

import yaml


# ----- SHORT DESCRIPTION MAP -----
# (truncated list — populate from session context or a companion file)
DESC_MAP: dict[str, str] = {}


# ----- TAGS MAP -----
TAGS_MAP: dict[str, list[str]] = {}


def parse_frontmatter(content: str):
    m = re.match(r"^---\s*\n(.*?)\n(?:---|\.\.\.)", content, re.DOTALL)
    if not m:
        return None, None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, None
    if not isinstance(fm, dict):
        return None, None
    return fm, m.group(1)


def fix_descriptions(base: Path, dry_run: bool = True) -> int:
    """Shorten descriptions to ≤60 chars using DESC_MAP."""
    count = 0
    for sp in sorted(base.rglob("SKILL.md")):
        name = sp.parent.name
        if name not in DESC_MAP:
            continue
        content = sp.read_text(encoding="utf-8")
        fm, fm_text = parse_frontmatter(content)
        if fm is None:
            continue
        old_desc = fm.get("description", "")
        if not old_desc or len(old_desc) <= 65:
            continue
        new_desc = DESC_MAP[name]
        # Replace the description line in the raw frontmatter text
        new_fm = re.sub(
            r"^description:.*$",
            f'description: "{new_desc}"',
            fm_text,
            count=1,
            flags=re.MULTILINE,
        )
        if new_fm == fm_text:
            continue
        new_content = content.replace(fm_text, new_fm, 1)
        if not dry_run:
            sp.write_text(new_content, encoding="utf-8")
        count += 1
    return count


def fix_tags(base: Path, dry_run: bool = True) -> int:
    """Add missing tags using TAGS_MAP."""
    count = 0
    for sp in sorted(base.rglob("SKILL.md")):
        name = sp.parent.name
        if name not in TAGS_MAP:
            continue
        content = sp.read_text(encoding="utf-8")
        fm, fm_text = parse_frontmatter(content)
        if fm is None:
            continue
        existing_tags = fm.get("tags", [])
        if existing_tags:
            continue
        new_tags = TAGS_MAP[name]
        tag_line = f"tags: [{', '.join(new_tags)}]"
        new_fm = fm_text
        if "description:" in new_fm:
            new_fm = re.sub(
                r"^(description:.*?)$",
                r"\1\n" + tag_line,
                new_fm,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            new_fm = new_fm + "\n" + tag_line
        new_content = content.replace(fm_text, new_fm, 1)
        if not dry_run:
            sp.write_text(new_content, encoding="utf-8")
        count += 1
    return count


def fix_names(base: Path, dry_run: bool = True) -> int:
    """Fix frontmatter name to match directory name."""
    count = 0
    for sp in sorted(base.rglob("SKILL.md")):
        name = sp.parent.name
        content = sp.read_text(encoding="utf-8")
        fm, fm_text = parse_frontmatter(content)
        if fm is None:
            continue
        fm_name = fm.get("name", "")
        if not fm_name or fm_name == name:
            continue
        # Replace the name line
        new_fm = re.sub(
            r"^name:.*$", f"name: {name}", fm_text, count=1, flags=re.MULTILINE
        )
        new_content = content.replace(fm_text, new_fm, 1)
        if not dry_run:
            sp.write_text(new_content, encoding="utf-8")
        count += 1
    return count


def _all_skill_names(base: Path) -> set[str]:
    """Return set of all skill directory names."""
    return {sp.parent.name for sp in base.rglob("SKILL.md")}


def fix_related(base: Path, dry_run: bool = True) -> int:
    """Remove broken related_skills references."""
    known = _all_skill_names(base)
    count = 0
    for sp in sorted(base.rglob("SKILL.md")):
        content = sp.read_text(encoding="utf-8")
        fm, fm_text = parse_frontmatter(content)
        if fm is None:
            continue
        rel = fm.get("related_skills", [])
        if not rel:
            meta = fm.get("metadata", {})
            if isinstance(meta, dict):
                rel = meta.get("hermes", {}).get("related_skills", [])
        if not rel:
            continue
        good = [r for r in rel if r in known or any(r.lower() in k.lower() for k in known)]
        if len(good) == len(rel):
            continue
        # Remove broken items
        # For list format (- item):
        new_fm = fm_text
        for r in rel:
            if r not in good:
                line_pattern = re.compile(
                    r"^\s*-\s*" + re.escape(r) + r"\s*$", re.MULTILINE
                )
                new_fm = line_pattern.sub("", new_fm)
        # For inline [item1, item2] format:
        for r in rel:
            if r not in good:
                inline_pat = re.compile(
                    r"(related_skills:\s*\[)([^\]]*?)\b"
                    + re.escape(r)
                    + r"\b[\s,]*(.*?\])"
                )
                m = inline_pat.search(new_fm)
                if m:
                    prefix = m.group(1)
                    middle = m.group(2).rstrip(", ")
                    suffix = m.group(3).lstrip(", ")
                    replacement = prefix + middle
                    if middle and not suffix.startswith("]"):
                        replacement += ", "
                    replacement += suffix
                    new_fm = new_fm[: m.start()] + replacement + new_fm[m.end() :]
        if new_fm != fm_text:
            new_content = content.replace(fm_text, new_fm, 1)
            if not dry_run:
                sp.write_text(new_content, encoding="utf-8")
            count += 1
    return count


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bulk-fix skill frontmatter")
    parser.add_argument("--fix-desc", action="store_true", help="Shorten descriptions")
    parser.add_argument("--fix-tags", action="store_true", help="Add missing tags")
    parser.add_argument("--fix-name", action="store_true", help="Fix name mismatches")
    parser.add_argument("--fix-related", action="store_true", help="Remove broken refs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change, don't write")
    parser.add_argument("--skills-base", default="/opt/data/profiles/saksit/skills",
                        help="Path to skills directory")
    args = parser.parse_args()

    base = Path(args.skills_base)
    if not base.is_dir():
        print(f"Error: {base} not found", file=sys.stderr)
        sys.exit(1)

    total = 0
    if args.fix_desc:
        n = fix_descriptions(base, dry_run=args.dry_run)
        print(f"Descriptions fixed: {n}")
        total += n
    if args.fix_tags:
        n = fix_tags(base, dry_run=args.dry_run)
        print(f"Tags added: {n}")
        total += n
    if args.fix_name:
        n = fix_names(base, dry_run=args.dry_run)
        print(f"Names fixed: {n}")
        total += n
    if args.fix_related:
        n = fix_related(base, dry_run=args.dry_run)
        print(f"Related refs cleaned: {n}")
        total += n

    print(f"\nTotal: {total} {'changes (dry-run)' if args.dry_run else 'applied'}")
    if not any([args.fix_desc, args.fix_tags, args.fix_name, args.fix_related]):
        parser.print_help()


if __name__ == "__main__":
    main()
