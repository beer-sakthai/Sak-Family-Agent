#!/usr/bin/env python3
"""Validate all SKILL.md files: frontmatter, size, stale indicators, missing refs.

Quick structural check — run after batch skill operations to catch issues early.

Heuristic Note for 'todo' / 'TODO':
The word 'todo' commonly appears in valid documentation context (e.g., tags, status,
kanban, tool references, task lists, integrations like airtable or notion).
To avoid false positive STALE warnings on legitimate skill documentation, matches
for 'todo' are checked against line-level false-alarm indicators on a per-match basis.
If ALL 'todo' occurrences in a file match legitimate context, the 'todo' pattern is
treated as a false alarm. If AT LEAST ONE occurrence is a true stale task marker
(e.g., 'TODO: fix this'), a STALE warning is raised.
"""

import os
import re
import sys

STALE_PATTERNS = ["placeholder", "TODO", "FIXME", "NEEDS UPDATE", "stub", "not yet written"]
TODO_FALSE_ALARM_KEYWORDS = [
    "tags:",
    "status:",
    "kanban",
    "tool `todo`",
    "`todo`",
    "todo list",
    "airtable",
    "notion",
    "[ ]",
    "- [ ]",
    "* [ ]",
]


def is_todo_false_alarm(match_start: int, match_end: int, content: str) -> bool:
    """Determine if a specific 'todo' match in content is a legitimate documentation/metadata reference.

    Evaluates the line containing the match for known false alarm keywords
    (e.g. tags:, status:, tool references, kanban, or checkbox lists).
    """
    line_start = content.rfind("\n", 0, match_start)
    line_start = 0 if line_start == -1 else line_start + 1

    line_end = content.find("\n", match_end)
    line_end = len(content) if line_end == -1 else line_end

    line = content[line_start:line_end].lower()
    return any(kw in line for kw in TODO_FALSE_ALARM_KEYWORDS)


def check_stale_indicators(content: str) -> list[str]:
    """Check content for stale indicators, evaluating 'todo' false alarms per match instance.

    Returns a list of matched stale pattern strings that indicate actual stale content.
    """
    found_stale: list[str] = []

    for pat in STALE_PATTERNS:
        # Build regex for pattern matching with word boundaries for single words
        if pat.isalnum():
            regex = re.compile(rf"\b{re.escape(pat)}\b", re.IGNORECASE)
        else:
            regex = re.compile(re.escape(pat), re.IGNORECASE)

        matches = list(regex.finditer(content))
        if not matches:
            continue

        if "todo" in pat.lower():
            # Evaluate all 'todo' matches in the content.
            # If all matches are false alarms, ignore this pattern.
            # If any match is NOT a false alarm (e.g. 'TODO: fix this'), flag as stale.
            has_real_todo = False
            for m in matches:
                if not is_todo_false_alarm(m.start(), m.end(), content):
                    has_real_todo = True
                    break
            if has_real_todo:
                found_stale.append(pat.upper())
        else:
            found_stale.append(pat.upper())

    return found_stale


def validate_skill_content(content: str, rel_path: str) -> tuple[list[str], list[str]]:
    """Validate the content of a single SKILL.md file.

    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if len(content) < 50:
        errors.append(f"EMPTY  {rel_path} ({len(content)} chars)")
        return errors, warnings

    has_fm = content.startswith("---")
    fm_end = content.find("---", 3)

    if not has_fm:
        errors.append(f"NO_FM  {rel_path}")
    elif fm_end <= 3:
        errors.append(f"BAD_FM {rel_path}")

    stale_matches = check_stale_indicators(content)
    for pat in stale_matches:
        warnings.append(f"STALE  {rel_path} ({pat} found)")

    return errors, warnings


def resolve_skills_dir(target_dir: str | None = None) -> str:
    """Resolve SKILLS_DIR location from argument, environment variable, or fallback paths."""
    if target_dir and os.path.exists(target_dir):
        return target_dir

    env_dir = os.getenv("SKILLS_DIR")
    if env_dir and os.path.exists(env_dir):
        return env_dir

    user_skills = os.path.expanduser("~/profiles/saksit/skills")
    if os.path.exists(user_skills):
        return user_skills

    opt_skills = "/opt/data/profiles/saksit/skills"
    if os.path.exists(opt_skills):
        return opt_skills

    # Fallback to repo root personas if available
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_personas = os.path.abspath(os.path.join(script_dir, "../../../.."))
    if os.path.exists(repo_personas):
        return repo_personas

    return opt_skills


def validate_skills_dir(skills_dir: str) -> tuple[int, list[str], list[str]]:
    """Scan and validate all SKILL.md files under skills_dir."""
    errors: list[str] = []
    warnings: list[str] = []
    ok_count = 0

    if not os.path.exists(skills_dir):
        errors.append(f"Directory not found: {skills_dir}")
        return ok_count, errors, warnings

    all_files = sorted(
        os.path.join(root, f)
        for root, dirs, files in os.walk(skills_dir)
        for f in files
        if f == "SKILL.md"
    )

    for path in all_files:
        rel = path.replace(skills_dir, "").lstrip("/")
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            errors.append(f"READ_ERR {rel} ({e})")
            continue

        file_errors, file_warnings = validate_skill_content(content, rel)
        errors.extend(file_errors)
        warnings.extend(file_warnings)
        if not file_errors:
            ok_count += 1

    return ok_count, errors, warnings


def main(argv: list[str] | None = None) -> int:
    """Main execution point for validate-all-skills script."""
    if argv is None:
        argv = sys.argv[1:]

    target = argv[0] if argv else None
    skills_dir = resolve_skills_dir(target)

    print(f"Validating SKILL.md files in: {skills_dir}")
    ok_count, errors, warnings = validate_skills_dir(skills_dir)

    print(f"\nOK: {ok_count}  ERRORS: {len(errors)}  WARNINGS: {len(warnings)}")
    for e in errors:
        print(f"  ERR  {e}")
    for w in warnings:
        print(f"  WARN {w}")

    return len(errors)


if __name__ == "__main__":
    sys.exit(main())
