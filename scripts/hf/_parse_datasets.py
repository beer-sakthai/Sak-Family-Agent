"""Tabulate a Hugging Face datasets JSON dump and total its downloads.

Reads the JSON dump produced by the corresponding Hub API call. The path is
taken from argv rather than a hardcoded ``/tmp`` name: ``/tmp`` is
world-writable, so a fixed filename there can be pre-created or symlinked by
another user on the same host.

Usage: _parse_datasets.py <datasets.json>
"""

import json
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: _parse_datasets.py <datasets.json>")

with open(sys.argv[1]) as f:
    data = json.load(f)

print(f"Total datasets: {len(data)}")
total_dl = 0
for m in data:
    did = m.get("downloads", 0)
    total_dl += did
    updated = m.get("lastModified", "N/A")[:10]
    pid = m.get("datasetId", "?")
    private = m.get("private", False)
    print(f"  {pid:55s} | dl:{did:>8} | updated:{updated} | priv:{private}")
print(f"\nTotal dataset downloads: {total_dl}")
