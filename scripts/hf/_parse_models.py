"""Tabulate a Hugging Face models JSON dump and total its downloads.

Reads the JSON dump produced by the corresponding Hub API call. The path is
taken from argv rather than a hardcoded ``/tmp`` name: ``/tmp`` is
world-writable, so a fixed filename there can be pre-created or symlinked by
another user on the same host.

Usage: _parse_models.py <models.json>
"""

import json
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: _parse_models.py <models.json>")

with open(sys.argv[1]) as f:
    data = json.load(f)

print(f"Total models: {len(data)}")
total_dl = 0
for m in data:
    did = m.get("downloads", 0)
    total_dl += did
    likes = m.get("likes", 0)
    pipeline = m.get("pipeline_tag", "N/A")
    updated = m.get("lastModified", "N/A")[:10]
    pid = m.get("modelId", "?")
    private = m.get("private", False)
    gated = m.get("gated", False)
    print(
        f"  {pid:55s} | dl:{did:>8} | likes:{likes:>4} | {pipeline:20s} | "
        f"updated:{updated} | priv:{private} | gate:{gated}"
    )
print(f"\nTotal model downloads: {total_dl}")
