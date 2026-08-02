#!/usr/bin/env python3
"""verify-model-card.py — Reusable model card verification script.

Usage:
    python3 scripts/verify-model-card.py Nanthasit/sakthai-context-1.5b-tools [--repo-type model]
    python3 scripts/verify-model-card.py Nanthasit/sakthai-combined-v6 --repo-type dataset

Checks a live HF README.md for common issues:
  • YAML frontmatter presence and basic validity
  • Tags properly split (not one-liner concatenations like "tag1 [tag2, tag3]")
  • No stale hardcoded download counts (bare numbers next to "download" text)
  • Has required YAML fields (pipeline_tag, license, language)
  • Has family cross-links table (SakThai Model Family)
  • No empty sections (headers followed immediately by next header)
  • Broken cross-reference links (detects doubled letters like "1.5bb" or "7bb")

Returns exit code 0 = all checks pass, 1 = one or more failed.
"""

import sys
import re
import json
from huggingface_hub import hf_hub_download, HfApi

repo_id = sys.argv[1] if len(sys.argv) > 1 else None
repo_type = "model"
for i, arg in enumerate(sys.argv):
    if arg == "--repo-type" and i + 1 < len(sys.argv):
        repo_type = sys.argv[i + 1]

if not repo_id:
    print("Usage: python3 verify-model-card.py <repo_id> [--repo-type model|dataset|space]")
    sys.exit(1)

# ── Download live README ──────────────────────────────────────────
try:
    path = hf_hub_download(repo_id, "README.md", repo_type=repo_type)
    with open(path) as f:
        content = f.read()
except Exception as e:
    print(f"❌ FAILED to download README: {e}")
    sys.exit(1)

lines = content.splitlines()
checks = []
failed = 0

# ── 1. YAML frontmatter ──────────────────────────────────────────
has_yaml = content.startswith("---")
yaml_end = content.find("---", 3)
has_closing = yaml_end > 3 and yaml_end < 2000
checks.append(("YAML frontmatter present", has_yaml and has_closing))

# ── 2. Tags properly split (no one-liner brackets) ──────────────
yaml_section = content[3:yaml_end] if has_yaml and yaml_end > 3 else content[:2000]
bad_tags = re.findall(r"^-\s+\w+\s*\[.*?\]", yaml_section, re.MULTILINE)
checks.append(("Tags properly split (no one-liner brackets)", len(bad_tags) == 0))

# ── 3. Stale download counts ─────────────────────────────────────
# Looks for bare numbers next to "download" text, like "56 downloads"
stale_dl = re.findall(r"\b(\d+)\s+downloads?\b", content)
# Filter: if it finds any, flag it — they go stale
checks.append(("No hardcoded download counts (go stale)", len(stale_dl) == 0))

# ── 4. Required YAML fields ──────────────────────────────────────
required_fields = ["pipeline_tag", "license", "language"]
if repo_type == "model":
    required_fields.append("tags")
missing_fields = []
for field in required_fields:
    if f"{field}:" not in yaml_section:
        missing_fields.append(field)
checks.append((f"Required YAML fields present ({', '.join(required_fields)})", len(missing_fields) == 0))

# ── 5. Family cross-links table (model repos only) ──────────────
if repo_type == "model":
    has_family = "SakThai Model Family" in content
    checks.append(("SakThai Model Family cross-links table", has_family))

# ── 6. Empty sections ────────────────────────────────────────────
# Headers followed by blank/newline/next-header = empty section
empty_sections = []
for i, line in enumerate(lines):
    if line.startswith("##"):
        # Look ahead for content (non-blank, non-header)
        has_content = False
        for j in range(i + 1, min(i + 15, len(lines))):
            if lines[j].startswith("##"):
                break
            if lines[j].strip() and not lines[j].startswith("|") and not lines[j].startswith("---"):
                has_content = True
                break
        if not has_content:
            section_name = line.strip("# ")
            empty_sections.append(section_name)
checks.append(("No empty sections", len(empty_sections) == 0))

# ── 7. Broken cross-reference links (doubled letters) ────────────
# Common pattern: "1.5bb-merged" or "7bb-merged" instead of "1.5b-merged"
bad_links = re.findall(r"\b[\w.-]*?([a-z])\1{1}[\w.-]*?(?:-merged|-tools)", content)
checks.append(("No doubled-letter link typos", len(bad_links) == 0))

# ── 8. Dynamic download badge (if family table exists) ──────────
if "SakThai Model Family" in content or "downloads" in content[:500]:
    has_badge = "img.shields.io/badge/dynamic" in content or "img.shields.io/github/downloads" in content
    checks.append(("Dynamic download badge (not hardcoded)", has_badge))

# ── Report ──────────────────────────────────────────────────────
print(f"Verification for {repo_id} ({repo_type})")
print(f"  README: {len(content)} chars, {len(lines)} lines")
print()

all_pass = True
for label, result in checks:
    icon = "✅" if result else "❌"
    if not result:
        all_pass = False
        failed += 1
    print(f"  {icon} {label}")

print()
if all_pass:
    print(f"✅ All {len(checks)} checks passed")
else:
    print(f"❌ {failed}/{len(checks)} checks FAILED")
    if empty_sections:
        print(f"\n  Empty sections detected: {', '.join(empty_sections)}")
    if bad_links:
        print(f"\n  Potential link typos: {bad_links}")
    if stale_dl:
        print(f"\n  Hardcoded download count(s): {', '.join(stale_dl)}")

sys.exit(0 if all_pass else 1)
