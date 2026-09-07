import json, os, tempfile

# Read the dump from the system temp dir rather than a hardcoded /tmp path
# (bandit B108): a fixed, predictable name in a world-writable directory can
# be pre-created or symlinked by another user before this runs. Override with HF_SPACES_DUMP.
DUMP = os.environ.get("HF_SPACES_DUMP") or os.path.join(tempfile.gettempdir(), "spaces.json")
with open(DUMP) as f:
    d = json.load(f)
print(f"Spaces count: {len(d)}")
print(f"Keys in first: {list(d[0].keys())}")
for item in d:
    sid = item.get('_id') or item.get('id') or item.get('spaceId', 'MISSING')
    if 'id' in item and 'spaceId' not in item:
        sid = item['id']
    print(f"  id={sid}  sdk={item.get('sdk','N/A')}  dl={item.get('downloads',0)}")
