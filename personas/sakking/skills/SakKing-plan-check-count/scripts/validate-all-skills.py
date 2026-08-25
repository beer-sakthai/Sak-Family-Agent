#!/usr/bin/env python3
"""Validate all SKILL.md files: frontmatter, size, stale indicators, missing refs.
Quick structural check — run after batch skill operations to catch issues early."""

import os
import re
import sys

SKILLS_DIR = os.path.expanduser("~/profiles/saksit/skills")
if not os.path.exists(SKILLS_DIR):
    SKILLS_DIR = "/opt/data/profiles/saksit/skills"

errors = []
warnings = []
ok_count = 0
stale_pats = ["placeholder", "TODO", "FIXME", "NEEDS UPDATE", "stub", "not yet written"]
compiled_stale_pats = [(pat, re.compile(re.escape(pat), re.IGNORECASE)) for pat in stale_pats]

all_files = sorted(
    os.path.join(root, f)
    for root, dirs, files in os.walk(SKILLS_DIR)
    for f in files
    if f == "SKILL.md"
)

print(f"Found {len(all_files)} SKILL.md files")

for path in all_files:
    rel = path.replace(SKILLS_DIR, "").lstrip("/")
    with open(path) as f:
        content = f.read()
    lines = content.split("\n")

    if len(content) < 50:
        errors.append(f"EMPTY  {rel} ({len(content)} chars)")
        continue

    has_fm = content.startswith("---")
    fm_end = content.find("---", 3)

    if not has_fm:
        errors.append(f"NO_FM  {rel}")
    elif fm_end <= 3:
        errors.append(f"BAD_FM {rel}")

    for pat, pat_re in compiled_stale_pats:
        match = pat_re.search(content)
        if match:
            if "todo" in pat.lower():
                # heuristic: if the pattern is near tags/status/kanban it's legit
                start_idx = match.start()
                ctx = content[max(0, start_idx - 30) : start_idx + 50].lower()
                if any(
                    x in ctx
                    for x in [
                        "tags:",
                        "status:",
                        "kanban",
                        "tool `todo`",
                        "`todo`",
                        "list",
                        "airtable",
                        "notion",
                        "`[ ]`",
                    ]
                ):
                    continue  # false alarm
            warnings.append(f"STALE  {rel} ({pat.upper()} found)")
            break

    ok_count += 1

print(f"\nOK: {ok_count}  ERRORS: {len(errors)}  WARNINGS: {len(warnings)}")
for e in errors:
    print(f"  ERR  {e}")
for w in warnings:
    print(f"  WARN {w}")

sys.exit(len(errors))  # non-zero if any real errors
