import json, os, sys, tempfile

# The dump path is caller-supplied; a hardcoded /tmp path is predictable on a
# shared machine and wrong whenever the dump lives elsewhere. TMPDIR is honoured.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "spaces.json")

d = json.load(open(SRC))
print(f"Spaces count: {len(d)}")
print(f"Keys in first: {list(d[0].keys())}")
for item in d:
    sid = item.get('_id') or item.get('id') or item.get('spaceId', 'MISSING')
    if 'id' in item and 'spaceId' not in item:
        sid = item['id']
    print(f"  id={sid}  sdk={item.get('sdk','N/A')}  dl={item.get('downloads',0)}")
