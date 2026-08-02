#!/usr/bin/env python3
"""
Reusable scan: check which sibling cards mention a target model name.

Usage:
  python3 scripts/scan-model-references.py <target-model-short-name> [<author>]

Examples:
  python3 scripts/scan-model-references.py 0.5b-tools
  python3 scripts/scan-model-references.py sakthai-embedding Nanthasit

Output for each card: name, downloads, mention count, and whether target is present.
Also checks datasets and Spaces, plus collection membership.
"""

import sys
import os
from huggingface_hub import HfApi

TARGET = sys.argv[1] if len(sys.argv) > 1 else "0.5b-tools"
AUTHOR = sys.argv[2] if len(sys.argv) > 2 else "Nanthasit"

api = HfApi(token=os.environ.get('HF_TOKEN') or None)

def scan_repos(repo_list, repo_type, label):
    """Scan a list of repos for mentions of TARGET. repo_list is list of ModelInfo/DatasetInfo/SpaceInfo."""
    print(f"\n=== {label} ({len(repo_list)} total) ===")
    for r in repo_list:
        rid = r.id.split("/")[1] if "/" in r.id else r.id
        if rid == AUTHOR:
            continue  # skip profile repo
        try:
            readme = api.hf_hub_download(r.id, "README.md", repo_type=repo_type)
            with open(readme) as f:
                content = f.read()
            count = content.count(TARGET)
            dl = getattr(r, 'downloads', None) or 0
            private = getattr(r, 'private', False)
            tag = getattr(r, 'pipeline_tag', '') or ''
            status = "PRIVATE" if private else f"dl={dl:>5d}"
            print(f"  {rid:42s} {status:12s}  mentions={count}  {tag[:20]}")
        except Exception as e:
            print(f"  {rid:42s} ERROR: {type(e).__name__}")

# Models
models = [m for m in api.list_models(author=AUTHOR)]
models.sort(key=lambda m: m.downloads or 0, reverse=True)
scan_repos(models, "model", "Model Cards")

# Datasets
datasets = list(api.list_datasets(author=AUTHOR))
datasets.sort(key=lambda d: d.downloads or 0, reverse=True)
scan_repos(datasets, "dataset", "Datasets")

# Spaces
spaces = list(api.list_spaces(author=AUTHOR))
scan_repos(spaces, "space", "Spaces")

# Collection membership
print(f"\n=== Collection ===")
try:
    col = api.get_collection(f"{AUTHOR}/sakthai-model-family-6a64745450b12d421c1f9f02")
    found = [item for item in col.items if TARGET in item.item_id]
    print(f"  {TARGET} in collection: {len(found) > 0}")
except Exception as e:
    print(f"  Could not check collection: {type(e).__name__}")

print(f"\nScan complete. Target: '{TARGET}', Author: {AUTHOR}")
