"""Tabulate a Hugging Face spaces JSON dump and total its downloads.

Reads the JSON dump produced by the corresponding Hub API call. The path is
taken from argv rather than a hardcoded ``/tmp`` name: ``/tmp`` is
world-writable, so a fixed filename there can be pre-created or symlinked by
another user on the same host.

Usage: _parse_spaces.py <spaces.json>
"""

import json
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: _parse_spaces.py <spaces.json>")

with open(sys.argv[1]) as f:
    data = json.load(f)

print(f"Total spaces: {len(data)}")
total_dl = 0
for m in data:
    did = m.get("downloads", 0)
    total_dl += did
    updated = m.get("lastModified", "N/A")[:10]
    pid = m.get("spaceId", "?")
    sdk = m.get("sdk", "N/A")
    private = m.get("private", False)
    print(f"  {pid:55s} | dl:{did:>8} | {sdk:10s} | updated:{updated} | priv:{private}")
print(f"\nTotal space downloads: {total_dl}")
