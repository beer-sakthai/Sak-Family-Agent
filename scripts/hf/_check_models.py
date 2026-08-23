import json, sys, tempfile

# The dump path is caller-supplied; a hardcoded /tmp path is predictable on a
# shared machine and wrong whenever the dump lives elsewhere. TMPDIR is honoured.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "models.json")

d = json.load(open(SRC))
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
