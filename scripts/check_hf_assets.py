#!/usr/bin/env python3
"""Check all Nanthasit HF assets - models, datasets, spaces."""
import json, os, subprocess

HF_TOKEN = open(os.path.expanduser("~/.cache/huggingface/token")).read().strip()

def api(url):
    r = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: Bearer {HF_TOKEN}", url],
        capture_output=True, text=True, timeout=15
    )
    return json.loads(r.stdout)

# Models
models = api("https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1&limit=50")
print("=== MODELS ===")
print(f"Count: {len(models)}")
for m in models:
    card = m.get('cardData') or {}
    tags = card.get('tags', [])
    print(f"  {m['id'].split('/')[1]:32s} | {m['downloads']:>6d} dl | {m.get('pipeline_tag','N/A'):20s} | likes:{m.get('likes',0)} | tags:{len(tags)}")

# Datasets
datasets = api("https://huggingface.co/api/datasets?author=Nanthasit&sort=downloads&direction=-1&limit=30")
print("\n=== DATASETS ===")
print(f"Count: {len(datasets)}")
for d in datasets:
    print(f"  {d['id'].split('/')[1]:32s} | {d['downloads']:>6d} dl")

# Spaces
spaces = api("https://huggingface.co/api/spaces?author=Nanthasit&sort=downloads&direction=-1&limit=30")
print("\n=== SPACES ===")
print(f"Count: {len(spaces)}")
for s in spaces:
    print(f"  {s['id'].split('/')[1]:32s} | likes:{s.get('likes',0)} | sdk:{s.get('sdk','N/A')}")
