#!/usr/bin/env python3
"""Refactor, normalize frontmatter metadata, and purge legacy Hermes fields across all skills.

Usage:
    uv run python scripts/refactor_skills_metadata.py --dry-run
    uv run python scripts/refactor_skills_metadata.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))
from sakthai.config import PERSONA_NAMES  # noqa: E402

ALL_PERSONA_ROOTS = [REPO_ROOT / "personas" / p / "skills" for p in PERSONA_NAMES]
SHARED_SKILLS_ROOT = REPO_ROOT / "personas" / "shared" / "skills"

DEFAULT_CATEGORIES = {
    "sakthai": "mlops",
    "saksee": "web-browser",
    "sakjules": "devops",
    "sakking": "coding",
    "saksit": "content-marketing",
    "saktan": "operations",
    "shared": "utilities",
}


def infer_category(persona: str, slug: str, current_cat: str | None) -> str:
    if current_cat and current_cat.strip() and current_cat.strip() != "general":
        return current_cat.strip()

    slug_lower = slug.lower()

    if persona == "sakthai":
        if any(k in slug_lower for k in ("eval", "benchmark", "lighteval", "mmlu")):
            return "evaluation"
        if any(k in slug_lower for k in ("dataset", "parquet", "tokeniz")):
            return "datasets"
        if any(k in slug_lower for k in ("train", "qlora", "lora", "mergekit", "fine-tun")):
            return "training"
        return "mlops"

    if persona == "saksee":
        if any(k in slug_lower for k in ("playwright", "chrome-devtools", "browser", "dom", "ui-")):
            return "web-browser"
        if any(k in slug_lower for k in ("scrap", "extract", "crawl", "spider")):
            return "scraping"
        return "web-browser"

    if persona == "sakjules":
        if any(k in slug_lower for k in ("ci", "workflow", "action", "pull-request", "pr-", "issue")):
            return "devops"
        if any(k in slug_lower for k in ("security", "audit", "cve", "secret", "guardrail")):
            return "security"
        if any(k in slug_lower for k in ("cron", "fleet", "pipeline")):
            return "automation"
        return "devops"

    if persona == "sakking":
        if any(k in slug_lower for k in ("tdd", "debug", "test", "code", "refactor")):
            return "coding"
        if any(k in slug_lower for k in ("subagent", "runner", "execut", "plan")):
            return "agent-runner"
        return "productivity"

    if persona == "saksit":
        if any(k in slug_lower for k in ("seo", "meta-tag", "keywords")):
            return "seo"
        if any(k in slug_lower for k in ("social", "instagram", "youtube", "x-", "xurl")):
            return "social-media"
        if any(k in slug_lower for k in ("b2b", "saas", "sales", "brand", "story")):
            return "content-marketing"
        return "content-marketing"

    if persona == "saktan":
        if any(k in slug_lower for k in ("cycle", "rhythm", "signal", "loop")):
            return "cycle"
        return "operations"

    if persona == "shared":
        if "cycle" in slug_lower:
            return "cycle"
        return "utilities"

    return DEFAULT_CATEGORIES.get(persona, "general")


def infer_tags(persona: str, slug: str, existing_tags: list[str]) -> list[str]:
    tags: set[str] = set()
    for t in existing_tags:
        if isinstance(t, str) and t.strip():
            tags.add(t.strip().lower())

    # Generate from slug parts
    # e.g. SakThai-hf-hub-rate-limits -> tokens: [hf, hub, rate, limits]
    clean_slug = re.sub(r"^(Sak[A-Za-z]+-|Sak-)", "", slug)
    parts = [p.lower() for p in clean_slug.split("-") if len(p) >= 2]
    for p in parts:
        if p not in ("and", "the", "for", "with"):
            tags.add(p)

    # Add persona or domain anchor tag
    if persona == "sakthai":
        tags.add("huggingface")
    elif persona == "saksee":
        tags.add("browser")
    elif persona == "sakjules":
        tags.add("automation")
    elif persona == "sakking":
        tags.add("cli")
    elif persona == "saksit":
        tags.add("content")
    elif persona == "saktan":
        tags.add("daily-ops")
    elif persona == "shared":
        tags.add("shared")

    return sorted(tags)


def refactor_skill_md(md_path: Path, persona: str, apply: bool = False) -> tuple[bool, str]:
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False, "Not 3 parts"

    try:
        front = yaml.safe_load(parts[1])
    except Exception as exc:
        return False, f"YAML parse error: {exc}"

    if not isinstance(front, dict):
        return False, "Frontmatter is not a dict"

    changed = False
    dir_name = md_path.parent.name

    # 1. Name check
    if front.get("name") != dir_name:
        front["name"] = dir_name
        changed = True

    # 2. Version check
    if not front.get("version"):
        front["version"] = "1.0.0"
        changed = True

    # 3. Purge metadata.hermes and collect its fields
    metadata = front.get("metadata")
    hermes_tags: list[str] = []
    hermes_category: str | None = None
    if isinstance(metadata, dict) and "hermes" in metadata:
        hermes_block = metadata.pop("hermes")
        if isinstance(hermes_block, dict):
            if "tags" in hermes_block and isinstance(hermes_block["tags"], list):
                hermes_tags.extend([str(t) for t in hermes_block["tags"]])
            if "category" in hermes_block and isinstance(hermes_block["category"], str):
                hermes_category = hermes_block["category"]
        if not metadata:
            del front["metadata"]
        changed = True

    # 4. Category check & population
    current_category = front.get("category") or hermes_category
    resolved_category = infer_category(persona, dir_name, current_category)
    if front.get("category") != resolved_category:
        front["category"] = resolved_category
        changed = True

    # 5. Tags check & population
    existing_tags: list[str] = []
    if isinstance(front.get("tags"), list):
        existing_tags.extend([str(t) for t in front["tags"]])
    elif isinstance(front.get("tags"), str):
        existing_tags.extend([t.strip() for t in front["tags"].split(",") if t.strip()])

    # Check metadata.sakthai.tags as well
    if isinstance(metadata, dict) and isinstance(metadata.get("sakthai"), dict):
        st_tags = metadata["sakthai"].get("tags")
        if isinstance(st_tags, list):
            existing_tags.extend([str(t) for t in st_tags])

    existing_tags.extend(hermes_tags)
    resolved_tags = infer_tags(persona, dir_name, existing_tags)

    if front.get("tags") != resolved_tags:
        front["tags"] = resolved_tags
        changed = True

    if not changed:
        return False, "No change"

    # Re-order key fields nicely
    ordered_front: dict[str, Any] = {}
    for key in ("name", "version", "description", "category", "tags"):
        if key in front:
            ordered_front[key] = front[key]
    for key, val in front.items():
        if key not in ordered_front:
            ordered_front[key] = val

    serialized_header = yaml.safe_dump(ordered_front, sort_keys=False, allow_unicode=True).rstrip()
    new_text = f"---\n{serialized_header}\n---{parts[2]}"

    if apply:
        md_path.write_text(new_text, encoding="utf-8")

    return True, "Updated"


def run_refactor(apply: bool = False) -> None:
    print(f"=== Running Skills Metadata Refactor (apply={apply}) ===")
    total_scanned = 0
    total_modified = 0

    roots = [(p_root, p_root.parent.name) for p_root in ALL_PERSONA_ROOTS]
    roots.append((SHARED_SKILLS_ROOT, "shared"))

    for root, persona in roots:
        if not root.is_dir():
            continue
        p_scanned = 0
        p_modified = 0
        for skill_dir in sorted(root.iterdir()):
            if not skill_dir.is_dir():
                continue
            md_path = skill_dir / "SKILL.md"
            if not md_path.is_file():
                continue
            p_scanned += 1
            mod, _ = refactor_skill_md(md_path, persona, apply=apply)
            if mod:
                p_modified += 1

        print(f"[{persona}] Scanned: {p_scanned}, Modified: {p_modified}")
        total_scanned += p_scanned
        total_modified += p_modified

    action = "Applied changes to" if apply else "Would modify"
    print(f"=== Complete: {action} {total_modified} / {total_scanned} skills ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate changes without writing")
    parser.add_argument("--apply", action="store_true", help="Write changes to disk")
    args = parser.parse_args()

    apply_mode = args.apply or (not args.dry_run and not sys.argv[1:])
    run_refactor(apply=apply_mode)
