# HuggingFace API: Download Stats Collection

Shell recipes for querying aggregate download counts across all Beer's HF repos.

## Quick one-liner — all totals at once

```bash
curl -s "https://huggingface.co/api/models?author=Nanthasit&page_size=100" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
total = sum(m.get('downloads', 0) for m in data)
print(f'Models: {total}')
for m in sorted(data, key=lambda x: x.get('downloads',0), reverse=True):
    d = m.get('downloads', 0)
    if d > 0:
        print(f'  {d:>7}  {m.get(\"modelId\", m.get(\"id\",\"?\"))}')"

curl -s "https://huggingface.co/api/datasets?author=Nanthasit&page_size=100" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
total = sum(d.get('downloads', 0) for d in data)
print(f'Datasets: {total}')
for d in sorted(data, key=lambda x: x.get('downloads',0), reverse=True):
    dl = d.get('downloads', 0)
    if dl > 0:
        print(f'  {dl:>7}  {d.get(\"id\",\"?\")}')"

curl -s "https://huggingface.co/api/spaces?author=Nanthasit&page_size=100" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
total = sum(s.get('downloads', 0) for s in data)
print(f'Spaces: {total}')"
```

## Combined total (all repo types)

```bash
python3 -c "
import json, urllib.request, sys

total = 0
for repo_type, label in [('models', 'Models'), ('datasets', 'Datasets'), ('spaces', 'Spaces')]:
    url = f'https://huggingface.co/api/{repo_type}?author=Nanthasit&page_size=100'
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
        subtotal = sum(item.get('downloads', 0) for item in data)
        total += subtotal
        print(f'{label}: {subtotal}')
print(f'\nGRAND TOTAL: {total}')
"
```

## Top-N breakdown (useful for caption body)

```bash
curl -s "https://huggingface.co/api/models?author=Nanthasit&page_size=100" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
top = sorted(data, key=lambda x: x.get('downloads',0), reverse=True)[:5]
print('Top 5 models by downloads:')
for m in top:
    d = m.get('downloads', 0)
    name = m.get('modelId', m.get('id', '?'))
    print(f'  • {name}  —  {d}')
"
```

## API quirks

| Issue | Detail |
|-------|--------|
| **Pagination** | `page_size=100` covers all Beer's repos (currently <50 across all types). If he uploads 100+ models, add `&page=N` or use HF Hub Python library with pagination. |
| **Downloads field location** | Top-level `downloads` integer. Direct on models, datasets, and spaces endpoints. |
| **Zero-download repos** | API returns some repos with 0 downloads (unpublished/showcase repos). These are filtered out in the display above. |
| **Viewer vs download counts** | On the profile page, some repos show "167 • 70" format — the first is likes/views, the second is downloads. The API `downloads` field is the authoritative number. |
| **Rate limiting** | No rate limit observed for these read-only queries at Beer's traffic level. |
