#!/usr/bin/env python3
"""Verify collection API note field is handled as dict, not string."""
import json, sys, urllib.request

token_path = "/opt/data/.cache/huggingface/token"
collection_url = "https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"

try:
    token = open(token_path).read().strip()
    req = urllib.request.Request(collection_url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
except Exception as e:
    print(f"FAIL: could not fetch collection: {e}")
    sys.exit(1)

items = d.get("items", [])
errors = []
for i, item in enumerate(items):
    note = item.get("note")
    if note is None:
        errors.append(f"Item {i} ({item.get('id','?')}): note is None")
        continue
    if not isinstance(note, dict):
        errors.append(f"Item {i} ({item.get('id','?')}): note is {type(note).__name__}, not dict")
        continue
    if "text" not in note and "html" not in note:
        errors.append(f"Item {i} ({item.get('id','?')}): note dict has neither 'text' nor 'html' keys")

if errors:
    for e in errors:
        print(f"FAIL: {e}")
    sys.exit(1)
else:
    print(f"PASS: All {len(items)} items have note as dict with text/html keys")
