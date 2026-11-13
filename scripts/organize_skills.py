#!/usr/bin/env python3
"""Organize, deduplicate, and standardize skills across all 6 Sak Family personas.

Usage:
    uv run python scripts/organize_skills.py --dry-run
    uv run python scripts/organize_skills.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.skills import (  # noqa: E402
    PERSONA_SKILL_PREFIXES,
    SHARED_SKILL_PREFIX,
    strip_known_prefix,
)

PERSONAS_DIR = REPO_ROOT / "personas"
SHARED_SKILLS_DIR = PERSONAS_DIR / "shared" / "skills"
PERSONAS = ("sakthai", "sakking", "saksee", "saksit", "sakjules", "saktan")

UNIVERSAL_SHARED_SLUGS = (
    "cycle-dream",
    "cycle-hope",
    "cycle-care",
    "cycle-joy",
    "cycle-trust",
    "cycle-growth",
    "auto-cycle-loop",
    "plan",
    "spike",
    "opencode",
    "nano-pdf",
    "ocr-and-documents",
    "google-workspace",
    "requesting-code-review",
)

DOMAIN_REALLOCATIONS = {
    # B2B SaaS and content belong to SakSit
    "b2b-saas-sales-enablement-content-2026": "saksit",
    "b2b-saas-ugc-strategy-2026": "saksit",
    "b2b-saas-voc-feedback-loop-2026": "saksit",
    "founder-story-three-act": "saksit",
    # Daily ops and rhythm belong to SakTan
    "daily-briefing": "saktan",
    "close-the-day": "saktan",
    "beer-cycle-signals": "saktan",
    "diary-writer": "saktan",
    "family-auto-cycle": "saktan",
    "family-health-audit": "saktan",
    # DevSecOps and GitHub workflow belong to SakJules
    "ci-fixer-master-debug": "sakjules",
    "github-ci-fix": "sakjules",
    "github-organization-adm": "sakjules",
    "github-organization-administration": "sakjules",
    "github-security-compliance-program": "sakjules",
    "github-content-audit": "sakjules",
    "github-family-stewardship": "sakjules",
    # Web and browser belong to SakSee
    "chrome-devtools": "saksee",
    "ga4-to-sheets-dashboard": "saksee",
}


def repair_frontmatter_version(md_path: Path, apply: bool) -> bool:
    """Ensure frontmatter contains version: 1.0.0."""
    try:
        text = md_path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            return False
        front = yaml.safe_load(parts[1])
        if not isinstance(front, dict) or front.get("version"):
            return False

        lines = parts[1].strip("\n").splitlines()
        new_lines = []
        inserted = False
        for line in lines:
            new_lines.append(line)
            if not inserted and (line.startswith("name:") or line.startswith("description:")):
                new_lines.append("version: 1.0.0")
                inserted = True
        if not inserted:
            new_lines.append("version: 1.0.0")

        new_text = f"---\n{chr(10).join(new_lines)}\n---{parts[2]}"
        if apply:
            md_path.write_text(new_text, encoding="utf-8")
        return True
    except Exception:
        return False


def yaml_replace_name(content: str, new_name: str) -> str:
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    lines = parts[1].strip("\n").splitlines()
    new_lines = []
    replaced = False
    for line in lines:
        if line.startswith("name:"):
            new_lines.append(f"name: {new_name}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.insert(0, f"name: {new_name}")
    return f"---\n{chr(10).join(new_lines)}\n---{parts[2]}"


def run_organization(apply: bool = False) -> None:
    print(f"=== Running Skill Organization (apply={apply}) ===")
    SHARED_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Promote universal skills to shared
    promoted_slugs: set[str] = set()
    for slug in UNIVERSAL_SHARED_SLUGS:
        target_name = f"{SHARED_SKILL_PREFIX}{slug}"
        target_dir = SHARED_SKILLS_DIR / target_name
        target_md = target_dir / "SKILL.md"

        if target_md.exists():
            promoted_slugs.add(slug)
            continue

        found = None
        for p in PERSONAS:
            for prefix in (
                PERSONA_SKILL_PREFIXES.get(p, f"Sak{p[3:].capitalize()}-"),
                f"Sak{p.capitalize()}-",
                f"{p.capitalize()}-",
            ):
                cand = PERSONAS_DIR / p / "skills" / f"{prefix}{slug}"
                if (cand / "SKILL.md").exists():
                    found = cand
                    break
            if found:
                break

        if found:
            promoted_slugs.add(slug)
            print(
                f"[PROMOTE] {found.relative_to(REPO_ROOT)} -> {target_dir.relative_to(REPO_ROOT)}"
            )
            if apply:
                shutil.copytree(found, target_dir, dirs_exist_ok=True)
                content = target_md.read_text(encoding="utf-8")
                content = yaml_replace_name(content, target_name)
                target_md.write_text(content, encoding="utf-8")

    # 2. Canonicalize double prefixes (SakThai-sakthai-*)
    for p in PERSONAS:
        sdir = PERSONAS_DIR / p / "skills"
        if not sdir.is_dir():
            continue
        for entry in list(sdir.iterdir()):
            if not entry.is_dir():
                continue
            name_lower = entry.name.lower()
            if f"-{p}-" in name_lower:
                canonical_slug = entry.name.replace("SakThai-sakthai-", "SakThai-")
                canonical_slug = canonical_slug.replace(f"-{p}-", "-")
                target_entry = sdir / canonical_slug
                print(
                    f"[CANONICALIZE] {entry.relative_to(REPO_ROOT)} -> {target_entry.relative_to(REPO_ROOT)}"
                )
                if apply:
                    if target_entry.exists():
                        shutil.rmtree(entry)
                    else:
                        entry.rename(target_entry)
                        md = target_entry / "SKILL.md"
                        if md.exists():
                            content = yaml_replace_name(
                                md.read_text(encoding="utf-8"), canonical_slug
                            )
                            md.write_text(content, encoding="utf-8")

    # 3. Deduplicate universal shared skills from individual persona folders
    for slug in UNIVERSAL_SHARED_SLUGS:
        shared_md = SHARED_SKILLS_DIR / f"{SHARED_SKILL_PREFIX}{slug}" / "SKILL.md"
        if not shared_md.exists() and slug not in promoted_slugs:
            continue
        for p in PERSONAS:
            sdir = PERSONAS_DIR / p / "skills"
            if not sdir.is_dir():
                continue
            for entry in list(sdir.iterdir()):
                if not entry.is_dir():
                    continue
                clean = strip_known_prefix(entry.name)
                if clean == slug or clean == f"{p}-{slug}":
                    print(
                        f"[DEDUP REMOVE] {entry.relative_to(REPO_ROOT)} "
                        f"(now provided by shared {SHARED_SKILL_PREFIX}{slug})"
                    )
                    if apply:
                        shutil.rmtree(entry)

    # 4. Domain reallocations
    reallocated_targets: set[Path] = set()
    for slug, target_persona in DOMAIN_REALLOCATIONS.items():
        target_prefix = PERSONA_SKILL_PREFIXES.get(
            target_persona, f"Sak{target_persona[3:].capitalize()}-"
        )
        target_name = f"{target_prefix}{slug}"
        target_dir = PERSONAS_DIR / target_persona / "skills" / target_name
        for p in PERSONAS:
            if p == target_persona:
                continue
            sdir = PERSONAS_DIR / p / "skills"
            if not sdir.is_dir():
                continue
            for entry in list(sdir.iterdir()):
                if not entry.is_dir():
                    continue
                clean = strip_known_prefix(entry.name)
                if clean.startswith(f"{p}-"):
                    clean = clean[len(p) + 1 :]
                for other_p in PERSONAS:
                    if clean.startswith(f"{other_p}-"):
                        clean = clean[len(other_p) + 1 :]
                if clean == slug:
                    already_present = target_dir.exists() or target_dir in reallocated_targets
                    if already_present:
                        print(
                            f"[REALLOCATE DEDUP] {entry.relative_to(REPO_ROOT)} "
                            f"(target {target_dir.relative_to(REPO_ROOT)} already exists)"
                        )
                        if apply:
                            shutil.rmtree(entry)
                    else:
                        print(
                            f"[REALLOCATE MOVE] {entry.relative_to(REPO_ROOT)} -> "
                            f"{target_dir.relative_to(REPO_ROOT)}"
                        )
                        reallocated_targets.add(target_dir)
                        if apply:
                            shutil.move(str(entry), str(target_dir))
                            md = target_dir / "SKILL.md"
                            if md.exists():
                                content = yaml_replace_name(
                                    md.read_text(encoding="utf-8"), target_name
                                )
                                md.write_text(content, encoding="utf-8")

    # 5. Repair version metadata across all skills
    all_roots = [SHARED_SKILLS_DIR] + [PERSONAS_DIR / p / "skills" for p in PERSONAS]
    repaired_count = 0
    for root in all_roots:
        if not root.is_dir():
            continue
        for md in sorted(root.rglob("SKILL.md")):
            if repair_frontmatter_version(md, apply):
                repaired_count += 1
    action_label = "Backfilled" if apply else "Found"
    print(f"[METADATA] {action_label} version: 1.0.0 in {repaired_count} skills.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply changes to disk")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()
    run_organization(apply=args.apply and not args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
