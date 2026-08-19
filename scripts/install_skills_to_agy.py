#!/usr/bin/env python3
"""
Install and register all 930+ Sak-Family, Claude, and Gemini skills to Antigravity (AGY).
Links skills into ~/.agents/skills and Sak-Family-Agent/.agents/skills.
"""

import os
import glob
import re
import shutil

TARGET_GLOBAL = os.path.expanduser("~/.agents/skills")
TARGET_WORKSPACE = "/home/beern/Sak-Family-Agent/.agents/skills"

SOURCES = [
    "/home/beern/Sak-Family-Agent/personas/sakthai/skills/*",
    "/home/beern/Sak-Family-Agent/personas/sakjules/skills/*",
    "/home/beern/Sak-Family-Agent/personas/sakking/skills/*",
    "/home/beern/Sak-Family-Agent/personas/saksee/skills/*",
    "/home/beern/Sak-Family-Agent/personas/saktan/skills/*",
    "/home/beern/Sak-Family-Agent/personas/saksit/skills/*",
    "/home/beern/Sak-Family-Agent/personas/saknoi/skills/*",
    "/home/beern/Sak-Family-Agent/personas/shared/skills/*",
    "/home/beern/Sak-Family-Agent/.claude/skills/*",
    "/home/beern/.gemini/config/plugins/*/skills/*",
    "/home/beern/.gemini/config/skills/*",
]

def sanitize_skill_name(name: str) -> str:
    """Normalize skill name to standard lowercase kebab-case."""
    s = name.strip()
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', s)
    s = s.lower()
    s = re.sub(r'[^a-z0-9_-]', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

def main():
    os.makedirs(TARGET_GLOBAL, exist_ok=True)
    os.makedirs(TARGET_WORKSPACE, exist_ok=True)

    installed_count = 0
    skipped_count = 0
    errors = 0

    seen_names = set()

    for pattern in SOURCES:
        for skill_dir in glob.glob(pattern):
            if not os.path.isdir(skill_dir):
                continue

            skill_md = os.path.join(skill_dir, "SKILL.md")
            if not os.path.exists(skill_md):
                continue

            folder_name = os.path.basename(skill_dir)
            normalized_name = sanitize_skill_name(folder_name)

            if not normalized_name or normalized_name in seen_names:
                # Add disambiguation if needed
                parent_name = os.path.basename(os.path.dirname(os.path.dirname(skill_dir)))
                normalized_name = f"{sanitize_skill_name(parent_name)}-{normalized_name}"

            seen_names.add(normalized_name)

            # Link into Global ~/.agents/skills
            dest_global = os.path.join(TARGET_GLOBAL, normalized_name)
            if os.path.islink(dest_global) or os.path.exists(dest_global):
                try:
                    if os.path.islink(dest_global):
                        os.unlink(dest_global)
                    elif os.path.isdir(dest_global):
                        shutil.rmtree(dest_global)
                except Exception as e:
                    print("Ignored exception")

            try:
                os.symlink(os.path.abspath(skill_dir), dest_global)
            except Exception as e:
                errors += 1
                continue

            # Link into Workspace .agents/skills
            dest_workspace = os.path.join(TARGET_WORKSPACE, normalized_name)
            if os.path.islink(dest_workspace) or os.path.exists(dest_workspace):
                try:
                    if os.path.islink(dest_workspace):
                        os.unlink(dest_workspace)
                    elif os.path.isdir(dest_workspace):
                        shutil.rmtree(dest_workspace)
                except Exception as e:
                    print("Ignored exception")

            try:
                os.symlink(os.path.abspath(skill_dir), dest_workspace)
                installed_count += 1
            except Exception as e:
                errors += 1

    print(f"=== Antigravity (AGY) Skills Installation Summary ===")
    print(f"✅ Successfully installed & symlinked skills: {installed_count}")
    print(f"📁 Global Directory: {TARGET_GLOBAL} ({len(os.listdir(TARGET_GLOBAL))} skills)")
    print(f"📁 Workspace Directory: {TARGET_WORKSPACE} ({len(os.listdir(TARGET_WORKSPACE))} skills)")
    print(f"⚠️ Errors encountered: {errors}")

if __name__ == '__main__':
    main()
