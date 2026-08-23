import json, os, sys, tempfile

# The dump path is caller-supplied; a hardcoded /tmp path is predictable on a
# shared machine and wrong whenever the dump lives elsewhere. TMPDIR is honoured.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "datasets.json")

with open(SRC) as f:
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
