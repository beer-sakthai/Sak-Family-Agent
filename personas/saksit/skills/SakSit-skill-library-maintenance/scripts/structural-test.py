#!/usr/bin/env python3
"""Structural test for every SKILL.md in the skill library.

Checks:
  • YAML frontmatter parses cleanly
  • description ≤ 65 chars (60-char hard limit + 5-char grace for edge cases)
  • tags present
  • frontmatter name matches directory name
  • All linked files (references/, templates/, scripts/, assets/) resolve on disk
  • related_skills cross-references resolve to an existing skill name
  • required_commands binaries exist on $PATH
  • required_environment_variables are set

Usage::

    uv pip install pyyaml -q
    uv run python3 scripts/structural-test.py

Pitfalls:
  • Runs with `uv run python3` — system python3 does not have pyyaml.
  • Regex prose-filter avoids false-positives like "enforces the
    references/templates/scripts/assets subdir" but may still catch edge cases.
  • required_commands check is best-effort — some commands may be in hermetic
    containers or behind shell aliases.
"""

import os
import re
import shutil
import sys
from pathlib import Path

import yaml


def walk_skills(base: Path) -> list[Path]:
    """Return all SKILL.md files under *base*, deepest first."""
    return sorted(base.rglob("SKILL.md"), key=lambda p: len(p.parents), reverse=True)


def parse_frontmatter(content: str):
    """Extract YAML frontmatter from a SKILL.md string.

    Returns (dict|None, str|None) — (parsed_frontmatter, error_message).
    """
    m = re.match(r"^---\s*\n(.*?)\n(?:---|\.\.\.)", content, re.DOTALL)
    if not m:
        return None, "No frontmatter delimiters found"
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    if not isinstance(fm, dict):
        return None, "Frontmatter is not a dict"
    return fm, None


def get_tags(fm: dict) -> list:
    """Return tags from frontmatter, checking both flat and metadata.hermes keys."""
    tags = fm.get("tags", [])
    if not tags:
        meta = fm.get("metadata", {})
        if isinstance(meta, dict):
            tags = meta.get("hermes", {}).get("tags", [])
    return tags or []


def get_related(fm: dict) -> list:
    """Return related_skills, checking both flat and metadata.hermes keys."""
    rel = fm.get("related_skills", [])
    if not rel:
        meta = fm.get("metadata", {})
        if isinstance(meta, dict):
            rel = meta.get("hermes", {}).get("related_skills", [])
    return rel or []


def prose_context_before(text: str, pos: int, window: int = 40) -> str:
    """Return lowercased text *window* chars before *pos*."""
    start = max(0, pos - window)
    return text[start:pos].lower()


def is_prose_reference(text_before: str) -> bool:
    """Heuristic: if preceded by prose-signalling words, glob patterns, or path context, skip."""
    # Prose-signalling words
    if re.search(
            r"\b(the|and|or|in|of|for|to|by|subdir|allowlist|enforce|our|like|location|directory|path|here|see|under)\b",
            text_before,
        ):
        return True
    # Code-block indicator (backtick prefix)
    if text_before.rstrip().endswith('`'):
        return True
    return False


def find_skill_by_name(name: str, all_skills: list[Path]) -> bool:
    """Check if any skill directory or filename contains *name*."""
    for sp in all_skills:
        if name.lower() in sp.parent.name.lower():
            return True
        if name.lower() in sp.stem.lower():
            return True
    return False


def test_skill(sp: Path) -> list[dict]:
    """Run all checks against one SKILL.md. Returns list of issue dicts."""
    issues: list[dict] = []
    name = sp.parent.name

    content = sp.read_text(encoding="utf-8")
    fm, err = parse_frontmatter(content)
    if err:
        return [{"skill": name, "check": "frontmatter", "detail": err}]
    if fm is None:
        return [{"skill": name, "check": "frontmatter", "detail": "Returned None"}]

    # 1. Name matches directory
    fm_name = fm.get("name", "")
    if fm_name and fm_name != name:
        issues.append(
            {"skill": name, "check": "name-mismatch",
             "detail": f"fm name='{fm_name}' ≠ dir '{name}'"}
        )

    # 2. Description
    desc = fm.get("description", "")
    if not desc:
        issues.append({"skill": name, "check": "no-description", "detail": ""})
    elif len(desc) > 65:
        issues.append(
            {"skill": name, "check": "desc-over-65",
             "detail": f"{len(desc)} chars"}
        )

    # 3. Tags
    if not get_tags(fm):
        issues.append({"skill": name, "check": "no-tags", "detail": ""})

    # 4. Linked files — body (after frontmatter)
    body_match = re.match(
        r"^---\s*\n.*?\n(?:---|\.\.\.)", content, re.DOTALL
    )
    body = content[body_match.end():] if body_match else content

    ref_dir = sp.parent
    for m in re.finditer(r"(references|templates|scripts|assets)/[\w./-]+", body):
        raw = m.group(0).strip(")`.,\"'")
        if prose_context_before(body, m.start()):
            if is_prose_reference(prose_context_before(body, m.start())):
                continue
        resolved = ref_dir / raw
        if not resolved.exists():
            issues.append(
                {"skill": name, "check": "missing-ref",
                 "detail": f"{raw}"}
            )

    # 5. Related skills
    for rs in get_related(fm):
        if not find_skill_by_name(rs, all_skills):
            issues.append(
                {"skill": name, "check": "broken-related",
                 "detail": f"related '{rs}' not found"}
            )

    # 6. Required commands
    for cmd in (fm.get("required_commands") or []):
        if not shutil.which(cmd):
            issues.append(
                {"skill": name, "check": "missing-cmd",
                 "detail": f"command '{cmd}' not on $PATH"}
            )

    # 7. Required environment variables
    for env_var in (fm.get("required_environment_variables") or []):
        if not os.environ.get(env_var):
            issues.append(
                {"skill": name, "check": "missing-env",
                 "detail": f"env '{env_var}' not set"}
            )

    return issues


def format_report(all_skills: list[Path], issues: list[dict]):
    """Print a structured report to stdout."""
    by_check: dict[str, list[dict]] = {}
    for iss in issues:
        by_check.setdefault(iss["check"], []).append(iss)

    print(f"Skill Library Structural Test")
    print(f"{'=' * 55}")
    print(f"  Skills scanned : {len(all_skills)}")
    skill_ok = len(all_skills) - len({i["skill"] for i in issues})
    print(f"  Clean          : {skill_ok}")
    print(f"  Total issues   : {len(issues)}")
    print()

    # Sort by severity: critical checks first
    severity = {
        "frontmatter": 0, "name-mismatch": 0, "missing-ref": 1,
        "broken-related": 1, "desc-over-65": 2, "no-tags": 2,
        "no-description": 0, "missing-cmd": 1, "missing-env": 1,
    }
    for check in sorted(by_check, key=lambda c: severity.get(c, 9)):
        items = by_check[check]
        label = check.replace("-", " ").title()
        print(f"\n{'=' * 55}")
        print(f"  {'⚠️' if severity.get(check, 2) < 2 else '🟡'}  "
              f"{label}: {len(items)}")
        print(f"{'-' * 55}")
        for item in items[:20]:
            detail = f" — {item['detail']}" if item["detail"] else ""
            print(f"    • {item['skill']}{detail}")
        if len(items) > 20:
            print(f"    … and {len(items) - 20} more")

    # Summary bar
    print(f"\n{'=' * 55}")
    print("Summary by Check")
    print(f"{'=' * 55}")
    for check in sorted(by_check, key=lambda c: -len(by_check[c])):
        count = len(by_check[check])
        bar = "█" * min(count // 2 + 1, 30)
        print(f"  {check:<25} {count:>4}  {bar}")


if __name__ == "__main__":
    base = Path(os.environ.get("SKILLS_BASE", "/opt/data/profiles/saksit/skills"))
    if not base.is_dir():
        print(f"SKILLS_BASE '{base}' not found. Set SKILLS_BASE env var.", file=sys.stderr)
        sys.exit(1)

    all_skills = walk_skills(base)
    # Make available as module-level for find_skill_by_name
    globals()["all_skills"] = all_skills

    all_issues: list[dict] = []
    for sp in all_skills:
        all_issues.extend(test_skill(sp))

    format_report(all_skills, all_issues)

    # Exit with non-zero if any critical issues found
    critical = {"frontmatter", "no-description", "name-mismatch", "missing-ref"}
    if any(i["check"] in critical for i in all_issues):
        sys.exit(2)
