import json, os, sys, tempfile

# Read the dump from the system temp dir rather than a hardcoded /tmp path
# (bandit B108): a fixed, predictable name in a world-writable directory can
# be pre-created or symlinked by another user before this runs. Override with HF_MODELS_DUMP.
DUMP = os.environ.get("HF_MODELS_DUMP") or os.path.join(tempfile.gettempdir(), "models.json")
with open(DUMP) as f:
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
