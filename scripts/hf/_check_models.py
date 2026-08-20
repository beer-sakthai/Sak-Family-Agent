"""Summarise a Hugging Face models JSON dump: combined/profile repos and pipeline tags.

Reads the JSON dump produced by the corresponding Hub API call. The path is
taken from argv rather than a hardcoded ``/tmp`` name: ``/tmp`` is
world-writable, so a fixed filename there can be pre-created or symlinked by
another user on the same host.

Usage: _check_models.py <models.json>
"""

import json
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: _check_models.py <models.json>")

with open(sys.argv[1]) as f:
    data = json.load(f)

print(f"Total from API: {len(data)}")
# Check combined-v6 and profile
for m in data:
    pid = m["modelId"]
    if "combined" in pid or "Nanthasit/Nanthasit" in pid:
        print(
            f"  {pid}: private={m.get('private')} "
            f"pipeline={m.get('pipeline_tag', 'N/A')} dl={m.get('downloads', 0)}"
        )
# Count by pipeline_tag
from collections import Counter

tags = Counter(m.get("pipeline_tag", "N/A") for m in data)
print(f"By pipeline: {dict(tags)}")
