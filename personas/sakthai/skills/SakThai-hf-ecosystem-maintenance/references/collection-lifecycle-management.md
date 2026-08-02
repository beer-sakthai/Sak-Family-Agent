# Collection Lifecycle Management

Documented 2026-07-29 — full lifecycle for Hugging Face collections: create, add items, update items (notes, description), remove items, detect drift, and handle edge cases (private repos, deleted repos).

## Overview

A HF collection is a curated list of models, datasets, Spaces, and papers. Unlike a user's "Liked" list, collections are manually curated — items don't auto-populate. **Drift is inevitable:** items created after the collection won't appear, descriptions go stale, and deleted items leave gaps.

## Core Operations

### 1. Get Collection State

```bash
curl -s "https://huggingface.co/api/collections/{namespace}/{slug}" \
  -H "Authorization: Bearer $HF_TOKEN"
```

The response includes:
- `title`, `description` — collection metadata
- `slug` — full slug including MongoDB hash suffix (e.g., `namespace/slug-647abc...`)
- `items[]` — array of items, each with `id`, `repoType`, `position`, `note`, `_id` (MongoDB document ID)
- `position` field — 0-indexed order of items

### 2. Update Collection Description

```bash
curl -s -X PATCH \
  "https://huggingface.co/api/collections/{namespace}/{slug}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "New description with current counts"}'
```

**URL forms:** Both short slug (`namespace/slug`) and hash-suffixed slug (`namespace/slug-hash`) work for PATCH. Using the short form simplifies scripting.

### 3. Add an Item

```bash
curl -s -X POST \
  "https://huggingface.co/api/collections/{namespace}/{slug}/items" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"item": {"id": "author/repo-name", "type": "model"}}'
```

**`type` values:** `"model"`, `"dataset"`, `"space"`, `"paper"`

**Private repos:** Private repos CAN be added to collections. The API accepts them and they appear in the collection response with `"private": true`. Other users won't see them, but the collection owner can.

**Error handling:**
- `"Cannot add item to collection: model 'X' not found"` — the repo doesn't exist (404). Check the exact repo ID. Common causes: typo, repo was deleted, repo is under a different namespace.
- Items are appended at the end. There's no "insert at position" parameter — you'd need to re-add all items in order to reorder.
- No batch add — add items one at a time.

### 4. Update an Item Note

Notes are the brief descriptions visible on the collection grid page.

```bash
curl -s -X PATCH \
  "https://huggingface.co/api/collections/{namespace}/{slug}/items/{item_object_id}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note": "New note text here"}'
```

**Key details:**
- **`item_object_id`** is the MongoDB `_id` field, not the repo name. Get it from the collection API response.
- **`note` must be a plain string.** Passing `{"note": {"text": "...", "html": "..."}}` returns `"note" must be a string`.
- The API internally converts the string to `{"text": "...", "html": "..."}` format.
- **Character limit:** 500 characters (silently truncated beyond that).
- **Empty notes:** Items added via POST have no `note` field in the API response (not even `null`). You must add a note explicitly via PATCH.

**URL forms:** Only the hash-suffixed slug works for item-level PATCH. Tested: short slug returns `"Collection not found"`.

### 5. Find Items Without Notes

```python
import json
with open('collection.json') as f:
    c = json.load(f)
for item in c.get('items', []):
    note = item.get('note')
    if note is None or (isinstance(note, dict) and not note.get('text', '').strip()):
        print(f"NO NOTE: {item['id']}  _id={item['_id']}  pos={item['position']}")
```

Items without notes show no snippet on the collection grid page — they appear as blank tiles with just a name, reducing click-through.

### 6. Delete an Item

```bash
curl -s -X DELETE \
  "https://huggingface.co/api/collections/{namespace}/{slug}/items/{item_object_id}" \
  -H "Authorization: Bearer $HF_TOKEN"
```

Requires the hash-suffixed slug. The short-form slug returns 404 for DELETE on items.

### 7. Detect Collection Drift

Collection drift has three forms:

**A. Missing items** — repos exist in the ecosystem but are absent from the collection.

Detection: fetch all models/datasets/spaces by author, then diff against collection item IDs.

```python
from huggingface_hub import HfApi
api = HfApi()
all_models = {m.id for m in api.list_models(author="YourAuthor")}
all_datasets = {d.id for d in api.list_datasets(author="YourAuthor")}
all_spaces = {s.id for s in api.list_spaces(author="YourAuthor")}
all_assets = all_models | all_datasets | all_spaces

collected = {item.item_id for item in get_collection("slug").items}
missing = all_assets - collected
```

**B. Stale description** — collection description mentions counts that no longer match.

Example: description says "12 models, 5 datasets" but API shows 21 models, 8 datasets. PATCH the description with current counts.

**C. Stale download counts in notes** — item notes embed numbers like "1,269 downloads" that drift over time. See `references/collection-note-refresh.md` for detection and bulk update patterns.

## Real Example: SakThai Collection (2026-07-29)

**Before:**
- Description: `"13 models · 6 datasets · 3 Spaces"`
- Items: 20
- Missing: sakthai-embedding (private, 34 dl), bench-v1 (0 dl), bench-v2 (0 dl)

**After:**
- Description: `"18 models · 8 datasets · 3 Spaces"` — via PATCH
- Items: 23 — added 3 missing items via POST
- All items have notes — added notes for 3 new items via PATCH items

**API calls used:**

```bash
# Update description
curl -s -X PATCH -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  "https://huggingface.co/api/collections/Nanthasit/sakthai-model-family" \
  -d '{"description":"Complete SakThai ecosystem: 18 models (text, vision, code, TTS, embeddings), 8 datasets, 3 Spaces. Six agents, one mind."}'

# Add items
curl -s -X POST -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  "https://huggingface.co/api/collections/Nanthasit/sakthai-model-family/items" \
  -d '{"item":{"id":"Nanthasit/sakthai-embedding","type":"model"}}'

# Add note to item (using hash-suffixed slug + MongoDB _id)
curl -s -X PATCH -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  "https://huggingface.co/api/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02/items/6a6a5d03533322b35d011a30" \
  -d '{"note":"English-only embeddings - 34 downloads. Lightweight 22M params."}'
```

## Repo Lifecycle Tracking

Repos can be deleted or renamed at any time. A collection item whose repo is deleted still appears in the collection API response but the `id` won't resolve via the repo API.

**Detection:** For each collection item, check HTTP status:
```bash
curl -o /dev/null -s -w "%{http_code}" \
  "https://huggingface.co/api/models/{author}/{repo}"
# 404 = deleted/renamed
```

**Response:** Either remove the item from the collection (DELETE endpoint) or note it in the collection description as deprecated.

## Cadence

| Operation | Frequency | Trigger |
|-----------|-----------|---------|
| Description refresh | Every 2 weeks or after creating 2+ new assets | Cron cycle |
| Missing item audit | Every 3rd cron cycle | Collection item count < ecosystem asset count |
| Note download count refresh | Every 2–4 weeks | Drift > 10% on any item |
| Deleted repo check | Monthly | 404 on item repo check |

## Related Skills

- `hf-ecosystem-maintenance` → `references/collection-note-refresh.md` — stale download count detection in notes (narrower scope)
- `hf-hub-collections` — comprehensive collection API reference (Python lib, curl patterns, pitfalls)
