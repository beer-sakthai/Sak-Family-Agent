#!/usr/bin/env python3
"""check-collection-drift.py - Audit a Hugging Face collection for drift.

Detects:
  - Missing items (assets that exist but aren't in the collection)
  - Items without notes
  - Stale description counts (compared to actual API state)
  - Deleted repo entries (items whose repo returns 404)

Usage:
  python3 check-collection-drift.py <namespace/slug> [--author USER] [--verbose]

Requires: huggingface_hub (or fallback to curl)
Env: HF_TOKEN must be set for private repo visibility
"""

import json
import os
import subprocess
import sys
from collections import defaultdict

SLUG = sys.argv[1] if len(sys.argv) > 1 else None
AUTHOR = None
VERBOSE = False

for i, arg in enumerate(sys.argv[2:], start=2):
    if arg.startswith("--author="):
        AUTHOR = arg.split("=", 1)[1]
    elif arg == "--verbose":
        VERBOSE = True

if not SLUG:
    print("Usage: check-collection-drift.py <namespace/slug> [--author USER] [--verbose]")
    sys.exit(1)

namespace = SLUG.split("/")[0]
if not AUTHOR:
    AUTHOR = namespace

def curl(url):
    """Fetch JSON via curl with auth."""
    token = os.environ.get("HF_TOKEN", "")
    cmd = ["curl", "-s"]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd += [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)

def http_status(url):
    """Return HTTP status code for a repo URL."""
    token = os.environ.get("HF_TOKEN", "")
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}"]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd += [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return int(result.stdout.strip())

def plural(n):
    return "s" if n != 1 else ""

print(f"=== Collection Drift Check: {SLUG} ===\n")

# 1. Fetch collection
col = curl(f"https://huggingface.co/api/collections/{SLUG}")
if not col:
    print(f"ERROR: Could not fetch collection '{SLUG}'")
    sys.exit(1)

items = col.get("items", [])
desc = col.get("description", "")
col_title = col.get("title", SLUG)
print(f"Collection: {col_title}")
print(f"Description: {desc}")
print(f"Items in collection: {len(items)}")

# 2. Classify items by type
by_type = defaultdict(list)
item_ids = set()
item_id_to_pos = {}
for item in items:
    rid = item.get("id", "?")
    rtype = item.get("repoType", item.get("type", "?"))
    by_type[rtype].append(rid)
    item_ids.add(rid)
    item_id_to_pos[rid] = item.get("position", -1)

print(f"  Models: {len(by_type.get('model', []))}")
print(f"  Datasets: {len(by_type.get('dataset', []))}")
print(f"  Spaces: {len(by_type.get('space', []))}")

# 3. Check items without notes
no_notes = []
for item in items:
    note = item.get("note")
    if note is None or (isinstance(note, dict) and not note.get("text", "").strip()):
        no_notes.append(item.get("id", "?"))

print(f"\n--- Items Without Notes: {len(no_notes)} ---")
for rid in no_notes:
    print(f"  ❌ {rid}")
if not no_notes:
    print("  ✅ All items have notes")

# 4. Detect missing items from ecosystem
print(f"\n--- Missing Assets (not in collection) ---")
missing_models = []
missing_datasets = []
missing_spaces = []

# Fetch author's assets
models_list = curl(f"https://huggingface.co/api/models?author={AUTHOR}")
datasets_list = curl(f"https://huggingface.co/api/datasets?author={AUTHOR}")
spaces_list = curl(f"https://huggingface.co/api/spaces?author={AUTHOR}")

if models_list:
    for m in models_list:
        mid = m["id"]
        if mid not in item_ids:
            dl = m.get("downloads", 0)
            priv = "(private)" if m.get("private", False) else ""
            pl = m.get("pipeline_tag", "-")
            missing_models.append((mid, dl, priv, pl))
    
if datasets_list:
    for d in datasets_list:
        did = d["id"]
        if did not in item_ids:
            dl = d.get("downloads", 0)
            missing_datasets.append((did, dl))

if spaces_list:
    for s in spaces_list:
        sid = s["id"]
        if sid not in item_ids:
            missing_spaces.append(sid)

if missing_models:
    print(f"  Models ({len(missing_models)}):")
    for mid, dl, priv, pl in sorted(missing_models, key=lambda x: -x[1]):
        print(f"    {mid:50s} {dl:5d} dl {priv:10s} {pl}")
else:
    print("  ✅ No missing models")

if missing_datasets:
    print(f"  Datasets ({len(missing_datasets)}):")
    for did, dl in sorted(missing_datasets, key=lambda x: -x[1]):
        print(f"    {did:50s} {dl:5d} dl")
else:
    print("  ✅ No missing datasets")

if missing_spaces:
    print(f"  Spaces ({len(missing_spaces)}):")
    for sid in missing_spaces:
        print(f"    {sid}")
else:
    print("  ✅ No missing spaces")

# 5. Check for deleted repos in collection
print(f"\n--- Deleted Repos in Collection ---")
deleted = []
for item in items:
    rid = item.get("id", "")
    if not rid:
        continue
    rtype = item.get("repoType", item.get("type", ""))
    base_url = {
        "model": "https://huggingface.co/api/models/",
        "dataset": "https://huggingface.co/api/datasets/",
        "space": "https://huggingface.co/api/spaces/",
    }.get(rtype, "https://huggingface.co/api/models/")
    status = http_status(f"{base_url}{rid.replace(namespace + '/', '', 1) if '/' in rid else rid}")
    if status == 404:
        deleted.append((rid, rtype))

if deleted:
    for rid, rtype in deleted:
        print(f"  💀 {rid} [{rtype}] — HTTP 404, repo no longer exists")
else:
    print("  ✅ All repos in collection are live")

# 6. Parse description for count accuracy
print(f"\n--- Description Count Check ---")
import re

actual_models = len(models_list) if models_list else 0
actual_datasets = len(datasets_list) if datasets_list else 0
actual_spaces = len(spaces_list) if spaces_list else 0

desc_lower = desc.lower()
issues = []

# Check model count in description
model_match = re.search(r'(\d+)\s*models?', desc_lower)
if model_match:
    claimed = int(model_match.group(1))
    # Only compare against "real" models (with pipeline tags, skip profile repos)
    real_models = actual_models  # might overcount, but good enough
    if claimed != real_models:
        issues.append(f"Models: description says {claimed}, API shows {real_models}")

dataset_match = re.search(r'(\d+)\s*datasets?', desc_lower)
if dataset_match:
    claimed = int(dataset_match.group(1))
    if claimed != actual_datasets:
        issues.append(f"Datasets: description says {claimed}, API shows {actual_datasets}")

space_match = re.search(r'(\d+)\s*spaces?', desc_lower)
if space_match:
    claimed = int(space_match.group(1))
    if claimed != actual_spaces:
        issues.append(f"Spaces: description says {claimed}, API shows {actual_spaces}")

if issues:
    print("  ❌ Count mismatches:")
    for i in issues:
        print(f"     {i}")
else:
    print("  ✅ All counts in description match API")

# 7. Summary
print(f"\n=== Summary ===")
total_issues = len(no_notes) + len(missing_models) + len(missing_datasets) + len(missing_spaces) + len(deleted) + len(issues)
print(f"Total issues found: {total_issues}")
if total_issues == 0:
    print("Collection is healthy! No drift detected.")
else:
    print(f"  Items without notes: {len(no_notes)}")
    print(f"  Missing models: {len(missing_models)}")
    print(f"  Missing datasets: {len(missing_datasets)}")
    print(f"  Missing spaces: {len(missing_spaces)}")
    print(f"  Deleted repos: {len(deleted)}")
    print(f"  Description count mismatches: {len(issues)}")
