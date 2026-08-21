import json, os, tempfile

# The dump path is caller-supplied; a hardcoded /tmp path is predictable on a
# shared machine and wrong whenever the dump lives elsewhere. TMPDIR is honoured.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "models.json")

with open(SRC) as f:
    data = json.load(f)
print(f'Total models: {len(data)}')
total_dl = 0
for m in data:
    did = m.get('downloads', 0)
    total_dl += did
    likes = m.get('likes', 0)
    pipeline = m.get('pipeline_tag', 'N/A')
    updated = m.get('lastModified', 'N/A')[:10]
    pid = m.get('modelId', '?')
    private = m.get('private', False)
    gated = m.get('gated', False)
    print(f'  {pid:55s} | dl:{did:>8} | likes:{likes:>4} | {pipeline:20s} | updated:{updated} | priv:{private} | gate:{gated}')
print(f'\nTotal model downloads: {total_dl}')
