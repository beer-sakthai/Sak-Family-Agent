#!/usr/bin/env python3
"""
Deep-Dive Skills Quality, Integrity, and Schema Auditor for the Sak-Family & AGY ecosystem.
Audits every SKILL.md for valid frontmatter, description quality, symlink health, and body completeness.
"""

import os
import re
from collections import defaultdict

import yaml

AUDIT_ROOTS = [
    "/home/beern/.agents/skills",
    "/home/beern/Sak-Family-Agent/.agents/skills",
    "/home/beern/Sak-Family-Agent/personas",
    "/home/beern/Sak-Family-Agent/.claude/skills",
    "/home/beern/.gemini/config/plugins",
]


def audit_skill_file(filepath):
    issues = []
    category = "unknown"

    # Identify Persona / Category
    if "personas/sakking" in filepath or "sak-king" in filepath:
        category = "SakKing"
    elif "personas/sakthai" in filepath or "sak-thai" in filepath:
        category = "SakThai"
    elif "personas/saksee" in filepath or "sak-see" in filepath:
        category = "SakSee"
    elif "personas/sakjules" in filepath or "sak-jules" in filepath:
        category = "SakJules"
    elif "personas/saktan" in filepath or "sak-tan" in filepath:
        category = "SakTan"
    elif "personas/saksit" in filepath or "sak-sit" in filepath:
        category = "SakSit"
    elif "google-agents-cli" in filepath:
        category = "Google-ADK"
    elif "superpowers" in filepath:
        category = "Superpowers"
    elif "oh-my-gemini" in filepath or "gemini-kit" in filepath:
        category = "oh-my-gemini"
    elif "shared" in filepath:
        category = "Shared"
    else:
        category = "General/Tool"

    if not os.path.exists(filepath):
        return {
            "path": filepath,
            "category": category,
            "valid": False,
            "issues": ["Broken symlink / file does not exist"],
            "name": os.path.basename(os.path.dirname(filepath)),
            "desc_len": 0,
            "body_len": 0,
        }

    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {
            "path": filepath,
            "category": category,
            "valid": False,
            "issues": [f"Read error: {str(e)}"],
            "name": os.path.basename(os.path.dirname(filepath)),
            "desc_len": 0,
            "body_len": 0,
        }

    # Check YAML Frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)

    name = ""
    description = ""
    body = content

    if frontmatter_match:
        yaml_text = frontmatter_match.group(1)
        body = frontmatter_match.group(2)
        try:
            parsed_yaml = yaml.safe_load(yaml_text)
            if isinstance(parsed_yaml, dict):
                name = parsed_yaml.get("name", "")
                description = parsed_yaml.get("description", "")
            else:
                issues.append("YAML frontmatter is not a key-value dictionary")
        except Exception as e:
            issues.append(f"YAML frontmatter parse error: {str(e)}")
    else:
        # Check if title heading exists as fallback
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            name = h1_match.group(1).strip()
        issues.append("Missing standard --- YAML frontmatter delimiters")

    if not name:
        name = os.path.basename(os.path.dirname(filepath))
        issues.append("Empty skill name")

    if not description:
        issues.append("Missing or empty skill description (affects progressive disclosure)")
    elif len(str(description).strip()) < 15:
        issues.append("Description too brief (<15 characters)")

    if len(body.strip()) < 30:
        issues.append("Skill body content is empty or incomplete (<30 characters)")

    return {
        "path": filepath,
        "category": category,
        "valid": len(issues) == 0,
        "issues": issues,
        "name": str(name),
        "desc_len": len(str(description)),
        "body_len": len(body),
    }


def main():
    discovered_files = set()

    for root in AUDIT_ROOTS:
        if not os.path.exists(root):
            continue
        for dirpath, _, filenames in os.walk(root, followlinks=True):
            if "node_modules" in dirpath or ".git" in dirpath or ".venv" in dirpath:
                continue
            for f in filenames:
                if f == "SKILL.md":
                    real_path = os.path.realpath(os.path.join(dirpath, f))
                    discovered_files.add(real_path)

    total_files = len(discovered_files)
    print(f"Discovered {total_files} unique SKILL.md files across environment.")

    results = []
    category_stats = defaultdict(lambda: {"total": 0, "valid": 0, "issues": 0})
    issue_counts = defaultdict(int)

    for path in sorted(discovered_files):
        res = audit_skill_file(path)
        results.append(res)
        cat = res["category"]
        category_stats[cat]["total"] += 1
        if res["valid"]:
            category_stats[cat]["valid"] += 1
        else:
            category_stats[cat]["issues"] += 1
            for iss in res["issues"]:
                issue_counts[iss] += 1

    valid_count = sum(1 for r in results if r["valid"])
    defect_count = total_files - valid_count

    print("\n" + "=" * 70)
    print(f"🚀 ENVIRONMENT-WIDE SKILL AUDIT REPORT (Total: {total_files})")
    print("=" * 70)
    print(f"✅ Perfectly Formatted Skills: {valid_count} ({valid_count / total_files * 100:.1f}%)")
    print(
        f"⚠️ Skills with Warnings/Issues: {defect_count} ({defect_count / total_files * 100:.1f}%)"
    )
    print("\n📊 CATEGORY BREAKDOWN:")
    print(f"{'Category':<18} | {'Total':<8} | {'Valid':<8} | {'Warnings':<8} | {'Health Rate'}")
    print("-" * 65)
    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]["total"], reverse=True):
        health = (stats["valid"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(
            f"{cat:<18} | {stats['total']:<8} | {stats['valid']:<8} | {stats['issues']:<8} | {health:.1f}%"
        )

    print("\n🔍 TOP DETECTED ISSUES:")
    for iss, cnt in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f" - [{cnt}x] {iss}")


if __name__ == "__main__":
    main()
