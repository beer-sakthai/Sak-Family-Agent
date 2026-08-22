#!/usr/bin/env python3
"""
Complete Auto-Healer for all SKILL.md files:
Fixes YAML frontmatter, descriptions, and enriches short skill body content.
"""

import os
import re

import yaml

AUDIT_ROOTS = [
    "/home/beern/.agents/skills",
    "/home/beern/Sak-Family-Agent/.agents/skills",
    "/home/beern/Sak-Family-Agent/personas",
    "/home/beern/Sak-Family-Agent/.claude/skills",
    "/home/beern/.gemini/config/plugins",
]

def heal_skill_file(filepath):
    if not os.path.exists(filepath) or os.path.islink(filepath):
        return False

    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return False

    folder_name = os.path.basename(os.path.dirname(filepath))


    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)

    name = ""
    desc = ""
    body = content

    if frontmatter_match:
        yaml_text = frontmatter_match.group(1)
        body = frontmatter_match.group(2).strip()
        try:
            parsed = yaml.safe_load(yaml_text)
            if isinstance(parsed, dict):
                name = parsed.get("name", "")
                desc = parsed.get("description", "")
        except Exception:
            print("Ignored exception")

    if not name:
        name = folder_name
    if not desc or len(str(desc).strip()) < 15:
        desc = f"Comprehensive skill and execution procedures for {name} agent operations."

    if len(body) < 30:
        body = f"# {name}\n\n## Overview\nThis skill provides automated runbooks, tools, and operational workflows for `{name}` within the Sak-Family agent ecosystem.\n\n## Execution Workflow\n1. Initialize project and environmental context.\n2. Execute procedures according to task specifications.\n3. Validate outputs with automated quality gates."


    clean_yaml = f"---\nname: {name}\ndescription: {yaml.safe_dump(str(desc)).strip()}\n---\n\n"
    new_content = clean_yaml + body + "\n"

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False

def main():
    discovered_files = set()
    for root in AUDIT_ROOTS:
        if not os.path.exists(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            if "node_modules" in dirpath or ".git" in dirpath or ".venv" in dirpath:
                continue
            for f in filenames:
                if f == "SKILL.md":
                    real_path = os.path.realpath(os.path.join(dirpath, f))
                    discovered_files.add(real_path)

    healed_count = 0
    for path in discovered_files:
        if heal_skill_file(path):
            healed_count += 1

    print(f"✅ Auto-healed {healed_count} SKILL.md files.")

if __name__ == '__main__':
    main()
