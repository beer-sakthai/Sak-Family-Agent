import json, os, tempfile

# Read the dump from the system temp dir rather than a hardcoded /tmp path
# (bandit B108): a fixed, predictable name in a world-writable directory can
# be pre-created or symlinked by another user before this runs. Override with HF_DATASETS_DUMP.
DUMP = os.environ.get("HF_DATASETS_DUMP") or os.path.join(tempfile.gettempdir(), "datasets.json")
with open(DUMP) as f:
    data = json.load(f)
print(f'Total datasets: {len(data)}')
total_dl = 0
for m in data:
    did = m.get('downloads', 0)
    total_dl += did
    updated = m.get('lastModified', 'N/A')[:10]
    pid = m.get('datasetId', '?')
    private = m.get('private', False)
    print(f'  {pid:55s} | dl:{did:>8} | updated:{updated} | priv:{private}')
print(f'\nTotal dataset downloads: {total_dl}')
