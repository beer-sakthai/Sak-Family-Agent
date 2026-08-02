# Collection Note Download Count Refresh

Documented 2026-07-30 — pattern for refreshing stale download counts in HF collection item notes.

## Problem

Collection item notes (the brief descriptions visible in a collection grid) often embed download counts like "1,197 downloads". Unlike shields.io dynamic badges, these notes are **static text** — they never auto-update. Over 2-4 weeks, drift of +10-15% is typical.

In the SakThai ecosystem (14 tracked items), actual drift after ~2 weeks:
- Total noted sum: 3,948 → API reality: 4,460 (+512, +13%)
- Largest single drift: 104→188 (Embedding-Multilingual, +81%)
- Most items drifted by 20-80%

## Detection

Compare the download count in each item's note against the current API value:

```python
from huggingface_hub import get_collection, HfApi

col = get_collection("user/collection-slug")
api = HfApi()
dl_map = {}
for m in api.list_models(author="user"):
    dl_map[m.id] = m.downloads or 0
for d in api.list_datasets(author="user"):
    dl_map[d.id] = d.downloads or 0

stale = []
for item in col.items:
    n = item.note
    if isinstance(n, dict):
        n = n.get("text", "")
    if not n:
        continue
    current_dl = dl_map.get(item.item_id)
    if current_dl is None:
        continue
    dl_str = f"{current_dl:,}"
    if dl_str not in n:
        stale.append((item, current_dl, n))
```

## Fix (via curl — cron-safe)

```bash
# Update a single item note
curl -s -X PATCH \
  "https://huggingface.co/api/collections/{namespace}/{slug}/items/{item_object_id}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note": "New note text with 1,269 downloads"}'
```

Key details:
- URL: `PATCH /api/collections/{slug}/items/{item_object_id}` — slug accepts both short and hash-suffixed forms for PATCH (unlike `delete_collection_item` which requires hash suffix)
- Body: `{"note": "new text"}` — the API internally converts to `{"text": "...", "html": "..."}` format
- Note length limit: 500 characters (silently truncated beyond that)
- Response: returns the updated Collection object (all items, not just the changed one)
- No batch endpoint — update one item at a time (calls are fast, <1s each)

## Verify

```bash
curl -s "https://huggingface.co/api/collections/{slug}" | \
python3 -c "
import json,sys
d = json.load(sys.stdin)
items = d.get('items', [])
ok = sum(1 for i in items if '1,269' in (i.get('note',{}) if isinstance(i.get('note'), dict) else str(i.get('note'))))
print(f'{ok}/{len(items)} items verified fresh')
"
```

## Cadence

- **Every 2-4 weeks** is appropriate for a growing ecosystem
- **Trigger:** drift > 10% on any item, or 2+ weeks since last refresh
- If notes omit download counts entirely, refresh is never needed — prefer qualitative descriptors like "most popular" or "lightest model"

## Relevant Skills

- `hf-hub-collections` — comprehensive collection API reference (Python lib, curl patterns, pitfalls)
- `hf-ecosystem-maintenance` → `references/stale-count-detection.md` — stale N-count detection on model/dataset/space cards (related but different problem)
