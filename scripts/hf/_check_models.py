import json, os, tempfile

# Read the dump from the system temp dir rather than a hardcoded /tmp path
# (bandit B108): a fixed, predictable name in a world-writable directory can
# be pre-created or symlinked by another user before this runs. Override with HF_MODELS_DUMP.
DUMP = os.environ.get("HF_MODELS_DUMP") or os.path.join(tempfile.gettempdir(), "models.json")
with open(DUMP) as f:
    d = json.load(f)
print(f"Total from API: {len(d)}")
# Check combined-v6 and profile
for m in d:
    pid = m['modelId']
    if 'combined' in pid or 'Nanthasit/Nanthasit' in pid:
        print(f"  {pid}: private={m.get('private')} pipeline={m.get('pipeline_tag','N/A')} dl={m.get('downloads',0)}")
# Count by pipeline_tag
from collections import Counter
tags = Counter(m.get('pipeline_tag', 'N/A') for m in d)
print(f"By pipeline: {dict(tags)}")
