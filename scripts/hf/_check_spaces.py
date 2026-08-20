"""Summarise a Hugging Face spaces JSON dump: ids, SDKs and download counts.

Reads the JSON dump produced by the corresponding Hub API call. The path is
taken from argv rather than a hardcoded ``/tmp`` name: ``/tmp`` is
world-writable, so a fixed filename there can be pre-created or symlinked by
another user on the same host.

Usage: _check_spaces.py <spaces.json>
"""

import json
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: _check_spaces.py <spaces.json>")

with open(sys.argv[1]) as f:
    data = json.load(f)

print(f"Spaces count: {len(data)}")
print(f"Keys in first: {list(data[0].keys())}")
for item in data:
    sid = item.get("_id") or item.get("id") or item.get("spaceId", "MISSING")
    if "id" in item and "spaceId" not in item:
        sid = item["id"]
    print(f"  id={sid}  sdk={item.get('sdk', 'N/A')}  dl={item.get('downloads', 0)}")
