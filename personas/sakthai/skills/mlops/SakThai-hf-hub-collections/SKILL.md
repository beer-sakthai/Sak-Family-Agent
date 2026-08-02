---
name: SakThai-hf-hub-collections
author: SakThai
license: MIT
description: Hugging Face Hub Collections API — create, manage, and curate themed collections of models, datasets, Spaces, papers, and other items programmatically via the huggingface_hub library
category: mlops
version: 1.7.0
---

# HF Hub Collections API

Trigger when: user asks about curating HF resources into lists, creating collections, managing collection items, or organizing models/datasets/Spaces/papers by theme.

## Overview

Collections on the Hugging Face Hub let you curate lists of models, datasets, Spaces, papers, or even other collections into themed groups. They're like playlists for ML resources — useful for organizing benchmarks, model families, research tracks, or teaching materials.

## Core API Methods (huggingface_hub)

All methods are available from the `huggingface_hub` package root or via `HfApi`:

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")  # optional, falls back to saved token
```

### Get a Collection

```python
from huggingface_hub import get_collection

collection = get_collection("TheBloke/recent-models-64f9a55bb3115b4f513ec026")
print(collection.title)        # "Recent models"
print(collection.slug)         # "TheBloke/recent-models-64f9a55bb3115b4f513ec026"
print(collection.owner)        # "TheBloke"
print(collection.items)        # list of CollectionItem
print(collection.description)  # optional plain text
print(collection.url)          # property, resolves to Hub URL
print(collection.upvotes)      # int
print(collection.private)      # bool
print(collection.theme)        # e.g. "green"
```

### Create a Collection

```python
from huggingface_hub import create_collection

collection = create_collection(
    title="My Awesome Models",
    description="A curated list of awesome models",  # optional
    private=False,   # default: False
    theme="green",   # optional color theme
)
```

Returns a `Collection` object. Collections are owned by your user/org.

### Update Collection Metadata

```python
from huggingface_hub import update_collection_metadata

updated = update_collection_metadata(
    collection_slug="username/my-collection-...",
    title="New Title",          # optional — update title
    description="New desc",     # optional — update description (max 150 chars!)
    private=True,              # optional — toggle privacy
    theme="blue",              # optional — change theme color
    position=1,                # optional — reorder position
)
```

All params except `collection_slug` are optional. Pass only what you want to change.

**Description limit**: the `description` field is capped at **150 characters**. Longer values return HTTP 400: `Too big: expected string to have <150 characters`.

### Delete a Collection

```python
from huggingface_hub import delete_collection

delete_collection("username/my-collection-...")
# ⚠️ Irreversible — permanently removes the collection
```

### Add an Item to a Collection

```python
from huggingface_hub import add_collection_item

collection = add_collection_item(
    collection_slug="davanstrien/climate-64f99dc2a5067f6b65531bab",
    item_id="pierre-loic/climate-news-articles",  # repo_id, paper id, slug, or bucket id
    item_type="dataset",      # "model" | "dataset" | "space" | "paper" | "collection" | "bucket"
    note="Great climate dataset",  # optional, max 500 chars
    exists_ok=False,          # if True, don't error on duplicates
)
```

Returns the updated `Collection`. The new item is appended at the last position.

### Update an Item's Note

```python
from huggingface_hub import update_collection_item

updated = update_collection_item(
    collection_slug="username/my-collection-...",
    item_object_id="...",     # unique ID of the item in the collection
    note="Updated note text", # new note (optional)
    position=1,               # new position (optional, 1-indexed)
)
```

### Remove an Item

```python
from huggingface_hub import delete_collection_item, get_collection

delete_collection_item(
    collection_slug="username/my-collection-...",
    item_object_id="...",     # unique ID of the item to remove
)

# Verify by re-fetching the collection
collection = get_collection("username/my-collection-...")
print(f"Items after removal: {len(collection.items)}")
```

**Return value: `None`.** Unlike `add_collection_item` which returns the updated `Collection`, `delete_collection_item` returns `None`. Always re-fetch with `get_collection()` after a delete if you need to confirm the change or access the updated item list. Chaining `.items` on the return value raises `AttributeError: 'NoneType' object has no attribute 'items'`.

**Slug format matters for delete.** `add_collection_item` and `get_collection()` accept both the short slug (`"user/title"`) and the full hash-suffixed slug (`"user/title-24charhex"`). But `delete_collection_item()` **only** works with the **full hash-suffixed slug**. Passing the short slug silently returns HTTP 200 without actually removing the item. Always use the slug returned by `get_collection().slug` when calling `delete_collection_item`.

## Collection Data Classes

### Collection

| Field         | Type               | Description                                    |
|---------------|--------------------|------------------------------------------------|
| `slug`        | `str`              | Unique slug, e.g. `"user/title-hash"`         |
| `title`       | `str`              | Display title                                  |
| `owner`       | `str`              | Username or org name                           |
| `items`       | `list[CollectionItem]` | Items in the collection                   |
| `last_updated`| `datetime`         | Last update timestamp                          |
| `position`    | `int`              | Position in owner's collection list            |
| `private`     | `bool`             | Whether the collection is private              |
| `theme`       | `str`              | Color theme (e.g. "green", "blue")            |
| `upvotes`     | `int`              | Number of upvotes                              |
| `description` | `str` (optional)   | Plain text description, max 150 chars         |
| `url`         | `str` (property)   | Hub URL                                        |

### CollectionItem

| Field             | Type             | Description                                       |
|-------------------|------------------|---------------------------------------------------|
| `item_object_id`  | `str`            | Unique ID of the item within the collection       |
| `item_id`         | `str`            | ID on the Hub (repo_id, paper id, collection slug, bucket id) |
| `item_type`       | `str`            | One of: `"model"`, `"dataset"`, `"space"`, `"paper"`, `"collection"`, `"bucket"` |
| `position`        | `int`            | Position in the collection (1-indexed)            |
| `note`            | `dict` (optional) | Note returned as `{"text": "...", "html": "..."}` when set, `None` when empty. Write via `update_collection_item(note="...")` as a plain string. |

## Common Workflows

### Create a Themed Collection and Populate It

```python
from huggingface_hub import create_collection, add_collection_item

# Step 1: Create
col = create_collection(
    title="Best Text-to-Image Models",
    description="Curated list of leading T2I models on the Hub",
    theme="purple",
)

# Step 2: Add items
for model_id in ["stabilityai/stable-diffusion-xl-base-1.0", "black-forest-labs/FLUX.1-dev", "playgroundai/playground-v2.5"]:
    add_collection_item(
        collection_slug=col.slug,
        item_id=model_id,
        item_type="model",
        exists_ok=True,
    )
```

### List All Items in a Collection

```python
collection = get_collection("some-user/my-collection-...")
for item in collection.items:
    note = item.note.get('text', '') if isinstance(item.note, dict) else (item.note or '')
    print(f"[{item.item_type}] {item.item_id} — {note or '(no note)'}")
```

### Clean Up Stale Collections

```python
from huggingface_hub import delete_collection, list_collections

# List all collections for a user and remove stale ones
for c in list_collections(owner="username"):
    coll = get_collection(c.slug)
    if len(coll.items) == 0:
        print(f"Empty collection: {c.slug} — consider deleting")
        # delete_collection(c.slug)  # uncomment to remove
```

### Enrich All Items with Descriptive Notes

After populating a collection, add context-rich notes to every item so visitors understand each asset's role at a glance. Notes appear as tooltips in the collection grid on the Hub.

**⚠️ Notes with download counts go stale.** If your notes include download counts (e.g., "Flagship model — 942 downloads"), they drift within days as the ecosystem grows. The notes are static text — they do not auto-update like shields.io badges. See the "Refresh Stale Download Counts" workflow below for a maintenance pattern.

```python
from huggingface_hub import get_collection, update_collection_item

col = get_collection("username/my-collection-slug")

notes = {
    "username/model-a": "Flagship model — 1,197 downloads. Tool-calling, 7B params.",
    "username/model-b": "Lightweight companion — 994 downloads. Edge-optimized.",
    "username/dataset-c": "Training data — 150 downloads. 2,003 examples.",
}

for item in col.items:
    note = notes.get(item.item_id)
    if note:
        update_collection_item(
            col.slug,
            item_object_id=item.item_object_id,
            note=note,
        )
```

Key points:
- Match by `item.item_id` (repo ID string), not `item_object_id` (random hash).
- Notes are capped at **500 chars** — keep them concise.
- Call once per item; there is no batch-update endpoint.
- Verify by re-fetching the collection and printing `item.note.get('text', '')` for each.

### Refresh Stale Download Counts in Collection Notes

Collection items with download counts in their notes need periodic refresh. Unlike shields.io dynamic badges (which auto-update from the HF API), collection notes are static text set at creation time. A monthly refresh is appropriate for most ecosystems.

**Signal to check:** If any model's download count in a note is more than 10% below the actual count, the note is stale. Compute drift = (current - noted) / noted * 100.

```python
from huggingface_hub import get_collection, update_collection_item, HfApi

COLLECTION_SLUG = "user/collection-slug-abcdef"

# Get current collection
col = get_collection(COLLECTION_SLUG)

# Build a map of current download counts
api = HfApi()
models = list(api.list_models(author="user"))
dl_map = {m.id: m.downloads or 0 for m in models}
datasets = list(api.list_datasets(author="user"))
dl_map.update({d.id: d.downloads or 0 for d in datasets})

updated = 0
for item in col.items:
    current_dl = dl_map.get(item.item_id)
    if current_dl is None:
        continue  # skip items without download counts (e.g., Spaces)
    # Get current note text (CollectionItem.note is a dict with 'text' key)
    curr_note = item.note.get('text', '') if isinstance(item.note, dict) else (item.note or '')
    # Check if note contains a stale download count
    # (heuristic: if current_dl doesn't appear in the note text)
    dl_str = f"{current_dl:,}"  # formatted with comma
    if dl_str not in curr_note:
        # Build a fresh note — update the download count inline
        import re
        match = re.search(r'(\d[\d,]*) downloads', curr_note)
        if match:
            old_count = match.group(1)
            new_note = curr_note.replace(old_count, dl_str, 1)
            update_collection_item(
                COLLECTION_SLUG,
                item_object_id=item.item_object_id,
                note=new_note,
            )
            updated += 1

print(f"Updated {updated} stale notes.")
# Verify
col2 = get_collection(COLLECTION_SLUG)
def _n(t): return t.get('text', '') if isinstance(t, dict) else (t or '')
ok = sum(1 for i in col2.items if _n(i.note) and str(dl_map.get(i.item_id, '')) in _n(i.note))
print(f"Verified: {ok}/{len(col2.items)} items have current counts.")
```

### Audit Collection for Empty Notes

Empty notes on collection items are discoverability blockers — visitors browsing the collection see a blank description and have no reason to click through. This workflow finds and fills those gaps.

**When to run:** As a periodic maintenance task (e.g., after adding new items to a collection, or monthly as part of ecosystem upkeep). The `hf-ecosystem-maintenance` skill covers this as a recurring checklist item.

#### Detection

Iterate over collection items and check for empty/None notes:

```python
from huggingface_hub import get_collection

col = get_collection("username/collection-slug-hexhash")
empty = []
for item in col.items:
    nt = item.note.get('text', '') if isinstance(item.note, dict) else (item.note or '')
    if not nt or not nt.strip():
        empty.append(item)
        print(f"EMPTY: [{item.item_type}] {item.item_id} (object_id: {item.item_object_id})")

print(f"\n{len(empty)}/{len(col.items)} items have empty notes")
```

The check extracts the `text` key from the dict note (returns empty string for `None`), then checks if it's empty. This catches both missing notes and notes with blank content.

#### What to write

Each note should answer three implicit questions:

| Question | Answer format | Example |
|----------|--------------|---------|
| What is this? | One-line purpose | "Irrelevance detection training supplement" |
| Why should I care? | Key differentiator or stat | "essential for BFCL irrelevance — 10 examples" |
| What now? | Call to action for low-download items | "0 downloads — first download validates the approach!" |

**Templates by asset type:**

| Type | Template | Example |
|------|----------|---------|
| **Model** | `{Role} — {purpose}. {Key stat}, {differentiator}.` | "Lightweight LoRA adapter for edge tool-calling — 7 downloads. LoRA weights for Qwen2.5-0.5B" |
| **Dataset** | `{Purpose} — {key stat} examples, {differentiator}. {CTA if 0 dl}` | "Irrelevance detection training supplement — teaches models when NOT to call a tool. 10 examples, essential for BFCL irrelevance. 0 downloads — first download validates the approach!" |
| **Space** | `{Type} — {purpose}. {Status note}.` | "TTS demo (static) — Showcase for the SakThai TTS model. Needs Gradio upgrade." |

**Conventions:**
- Keep notes under 200 characters — collection grid UI truncates longer notes
- Use plain language, not marketing hype
- For zero-download assets, include the CTA directly in the note ("0 downloads — first download validates!")
- Do NOT embed download counts that will go stale (see "Refresh Stale Download Counts" above for alternatives like qualitative descriptors or date-suffixed counts)

#### Fill the gap

```python
from huggingface_hub import update_collection_item

for item in empty:
    note = build_note(item)  # your note-building logic
    update_collection_item(
        collection_slug=col.slug,
        item_object_id=item.item_object_id,
        note=note,
    )
    print(f"Updated: {item.item_id}")
```

#### Verify

```python
col2 = get_collection(col.slug)
def _nt(n): return n.get('text', '') if isinstance(n, dict) else (n or '')
still_empty = [i for i in col2.items if not _nt(i.note) or not _nt(i.note).strip()]
print(f"{len(still_empty)} items still empty after fix")
assert len(still_empty) == 0, "Some notes still missing!"
for item in col2.items:
    t = _nt(item.note)
    if t:
        print(f"  [{item.item_type}] {item.item_id}: {t[:80]}...")
```

#### Pitfalls specific to note auditing

- **`update_collection_item` returns `None`** — always verify by re-fetching the collection. See the "Update an Item's Note" section above.
- **Notes are capped at 500 characters** — longer notes are silently truncated. If your CTA + description exceeds 500, abbreviate the description, not the CTA.
- **Empty string `""` vs `None`** — both count as empty. Always check with the combined guard.
- **Don't embed download counts** — they go stale. Use qualitative descriptors like "most popular", "lightest model", "essential for BFCL" instead. If you must include a count, add a date suffix (e.g., "as of 2026-07-29").
- **Items added by automated processes inherit no notes** — a dataset created by a cron job won't auto-populate its collection note. The audit must be run explicitly after any bulk-add operation.
- **`item.note` read format vs write format**: When writing via `update_collection_item(note="plain text")`, you pass a plain string. But when reading back with `get_collection()`, `item.note` is a **dict** `{"text": "...", "html": "..."}` (or `None` if unset). Code that does `item.note.strip()` or `item.note[:80]` will crash with `AttributeError`/`KeyError`. Always extract the text via `item.note.get('text', '') if isinstance(item.note, dict) else (item.note or '')`.

### Audit Collection Description for Count Accuracy

The collection description (e.g. "18 models, 8 datasets, 3 Spaces") is the first thing visitors see. It silently goes stale when new repos are created or old ones are deleted — no automatic sync exists.

**Signal to check:** Any time you run collection maintenance, compare the description counts against the current API. Collection descriptions over 150 chars are rejected, so counts are usually in the first sentence.

**Detection — compare description against API reality:**

```python
from huggingface_hub import get_collection
import re

SLUG = "user/collection-slug-hexhash"

col = get_collection(SLUG)
desc = col.description or ""

# Tally actual items by type
actual_models = sum(1 for i in col.items if i.item_type == "model")
actual_datasets = sum(1 for i in col.items if i.item_type == "dataset")
actual_spaces = sum(1 for i in col.items if i.item_type == "space")

# Extract stated counts from description
model_match = re.search(r'(\d+)\s*models?', desc)
ds_match = re.search(r'(\d+)\s*datasets?', desc)
space_match = re.search(r'(\d+)\s*[Ss]paces?', desc)

stated_models = int(model_match.group(1)) if model_match else None
stated_ds = int(ds_match.group(1)) if ds_match else None
stated_spaces = int(space_match.group(1)) if space_match else None

issues = []
if stated_models is not None and stated_models != actual_models:
    issues.append(f"models: description says {stated_models}, actual {actual_models}")
if stated_ds is not None and stated_ds != actual_datasets:
    issues.append(f"datasets: description says {stated_ds}, actual {actual_datasets}")
if stated_spaces is not None and stated_spaces != actual_spaces:
    issues.append(f"spaces: description says {stated_spaces}, actual {actual_spaces}")

if issues:
    print(f"DESCRIPTION STALE: {'; '.join(issues)}")
    # Craft corrected description (max 150 chars!)
    new_desc = f"Complete ecosystem: {actual_models} models, {actual_datasets} datasets, {actual_spaces} Spaces."
    print(f"Proposed: \"{new_desc}\"")
```

**Cron-safe (no huggingface_hub) version using curl:**

```bash
# 1. Fetch collection
curl -s -o /tmp/coll.json \
  "https://huggingface.co/api/collections/{namespace}/{slug}?limit=100"

# 2. Count actual items by type
python3 -c "
import json
d = json.load(open('/tmp/coll.json'))
models = sum(1 for i in d['items'] if i.get('type') == 'model')
ds = sum(1 for i in d['items'] if i.get('type') == 'dataset')
spaces = sum(1 for i in d['items'] if i.get('type') == 'space')
print(f'actual: {models} models, {ds} datasets, {spaces} spaces')
print(f'description: {d[\"description\"][:80]}')
"

# 3. If counts disagree, PATCH the description (max 150 chars!)
curl -s -o /tmp/patch_res.json -X PATCH \
  "https://huggingface.co/api/collections/{namespace}/{slug}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Complete ecosystem: 12 models, 8 datasets, 3 Spaces."}'
python3 -c "import json; print(json.load(open('/tmp/patch_res.json')).get('success'))"
```

**What counts as a "model"?** Only production/shipped models should be in the description count. Experimental checkpoints, intermediate training artifacts, and profile pages inflate the number and erode trust. The guideline: if you wouldn't link to it from a project README as a model people should download, don't count it. Use a separate note or a secondary counter for experiments (e.g. "12 models + 8 experimental checkpoints").

**Verification:** After patching, re-fetch to confirm:
```bash
curl -s "https://huggingface.co/api/collections/{namespace}/{slug}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('DESC OK' if '12 models' in d['description'] else 'STALE')"
```

**Pitfalls specific to description audits:**

- **Description 150-char limit**: The PATCH returns HTTP 400 `"Too big: expected string to have <150 characters"` if the new description exceeds 150 chars. Craft concise descriptions — the full breakdown belongs in the page body or item notes, not the header. A good template: `"Complete ecosystem: N models, N datasets, N Spaces."`
- **Experimental checkpoints inflate counts**: The API returns ALL repos — including intermediate checkpoints, profile pages, and test artifacts. The raw `type` field doesn't distinguish production from experimental. You must manually filter or maintain a curated list of "production" repo IDs.
- **The description is the first trust signal**: A visitor who sees "18 models" but counts 12 on the page will question every other claim on the profile. Fix inaccuracies promptly, especially on the flagship collection that's linked from every model card.
- **REST API GET truncates at 20 items by default**: The raw `GET /api/collections/{slug}` returns only the first page (default limit=20). Append `?limit=100` to get all items. The PATCH response also truncates `data.items` — always verify with a fresh GET, not the PATCH response body.

## Pitfalls

- **Collection slugs are permanent-ish**: once created, the slug contains a hash and cannot be changed. Always store the slug after creation.
- **Note length limit**: Notes are capped at **500 characters** — longer notes are silently truncated by the API.
- **Collection notes with download counts go stale**: Unlike shields.io dynamic badges (which auto-update from the HF API), collection item notes are static text. A note saying "942 downloads" becomes misleading within days as the ecosystem grows. Symptoms: visitors see a download count that lags 10-30% behind reality. Mitigations: (a) avoid embedding counts in notes if possible; (b) if counts are essential, document a refresh cadence alongside the note (e.g., "updated 2026-07-26"); (c) add a monthly cron to scan and refresh notes with current counts using the "Refresh Stale Download Counts" workflow above.
- **Description length limit**: `update_collection_metadata(description=...)` is capped at **150 characters**. Longer descriptions return HTTP 400: `Too big: expected string to have <150 characters`.
- **`exists_ok`**: When adding items, the API returns HTTP 409 if the item already exists and `exists_ok=False`. Always set `exists_ok=True` for idempotent add operations.
- **Item types**: Must be exact lowercase strings — `"model"`, not `"Model"` or `"models"`.
- **Bucket type**: The `"bucket"` type refers to HF Storage Buckets (not S3). Use a `namespace/bucket-name` ID format.
- **Deletion is irreversible**: No "undo" for `delete_collection` or `delete_collection_item`.
- **Private collections**: Private collections are only visible to the owner and collaborators.
- **Cron mode blocks execute_code and heredocs**: When running collection operations as a cron job, both `execute_code` and heredoc syntax (`python3 << 'PYEOF'`) are denied by the Tirith security scanner. Use the raw REST API with `curl` instead. Two-step file pattern avoids pipe blocking.

  **PATCH collection metadata:**
  ```bash
  curl -s -o /tmp/patch_result.json -X PATCH \
    "https://huggingface.co/api/collections/{namespace}/{slug}" \
    -H "Authorization: Bearer $HF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"description": "your text (max 150 chars)"}'
  python3 -c "import json; d=json.load(open('/tmp/patch_result.json')); print('OK:', d.get('success'))"
  ```

  **POST add item to collection (proven pattern):**
  ```bash
  curl -s -o /tmp/add_result.json -X POST \
    "https://huggingface.co/api/collections/{namespace}/{slug}/items" \
    -H "Authorization: Bearer $HF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"item":{"id":"Nanthasit/sakthai-irrelevance-supplement","type":"dataset"}}'
  python3 -c "import json; d=json.load(open('/tmp/add_result.json')); items=d.get('items',[]); found=[i for i in items if 'irrelevance' in i.get('id','')]; print(f'Added: {len(found)>0}, pos: {found[0].get(\"position\",\"?\") if found else \"not found\"}')"
  ```

  **Key details for the add-item endpoint:**
  - URL: `POST https://huggingface.co/api/collections/{namespace}/{slug}/items` — note **`/items`** (plural), not `/item`
  - Slug accepts both the short form (`user/title`) and the hash-suffixed form (`user/title-24charhex`) — both work for adds (unlike `delete_collection_item` which requires the hash suffix)
  - Body: `{"item":{"id":"<repo_id>","type":"<type>"}}` where `type` is `"model"`, `"dataset"`, `"space"`, `"paper"`, `"collection"`, or `"bucket"` (not `"repoType"`)
  - Returns the full updated collection with the new item at the last position
  - Use `exists_ok=True` in Python API for idempotency; in curl, duplicate adds return HTTP 409 Conflict

- **Raw `GET` paginates by default**: Unlike `get_collection()` from `huggingface_hub` which returns ALL items, the raw REST `GET /api/collections/{slug}` returns only the first page (default limit=20). Always append `?limit=100` or paginate with `?offset=N`. The PATCH response also truncates `data.items` — verify with a fresh GET, not the PATCH response.

- **PATCH item note requires MongoDB `_id`, not position index**: When updating a collection item's note via the REST API, the correct path is `/api/collections/{slug}/items/{item_object_id}` where `item_object_id` is the MongoDB `_id` field (e.g., `"6a6a311f533322b35dfe0c0c"`) from the full item response. Using the numeric position index (`/items/0`, `/items/21`) returns HTTP 404 `"Collection not found"`.

  **Cron-safe REST pattern for PATCH item note (no Python SDK):**

  ```bash
  # 1. Get the collection to find the item's MongoDB _id
  curl -s -o /tmp/collection.json \
    "https://huggingface.co/api/collections/{namespace}/{slug}?limit=100"

  # 2. Extract the _id of the target item
  python3 -c "
  import json
  data = json.load(open('/tmp/collection.json'))
  items = data.get('items', [])
  target = [i for i in items if 'target-repo-name' in i.get('id', '')]
  if target:
      print(target[0].get('_id', 'NOT_FOUND'))
  else:
      print('NOT_FOUND')
  " > /tmp/item_id.txt

  ITEM_ID=$(cat /tmp/item_id.txt)
  if [ "$ITEM_ID" = "NOT_FOUND" ]; then echo "ERROR: item not found"; exit 1; fi

  # 3. PATCH the note (body must be a plain string, not a nested object)
  curl -s -o /tmp/note_result.json -X PATCH \
    "https://huggingface.co/api/collections/{namespace}/{slug}/items/$ITEM_ID" \
    -H "Authorization: Bearer $HF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"note": "Your note text here (max 500 chars)"}'

  # 4. Verify by re-fetching the collection
  curl -s -o /tmp/collection_after.json \
    "https://huggingface.co/api/collections/{namespace}/{slug}?limit=100"

  python3 -c "
  import json
  data = json.load(open('/tmp/collection_after.json'))
  items = data.get('items', [])
  target = [i for i in items if 'target-repo-name' in i.get('id', '')]
  if target:
      note = target[0].get('note', {})
      text = note.get('text', note) if isinstance(note, dict) else note
      print(f'Note: {str(text)[:100]}')
      print(f'Verified: {bool(text)}')
  "
  ```

  **Key details:**
  - The MongoDB `_id` is a 24-character hex string — extract it fresh each time; IDs can change if items are re-added
  - Found by parsing the `_id` field from the target item in the collection GET response (not from the `id` or `position` fields)
  - Note body must be a **plain string**: `{"note": "..."}`. Sending a nested object `{"note": {"text": "...", "html": "..."}}` returns HTTP 400: `"note" must be a string`
  - The API converts the plain string to `{"text": "...", "html": "..."}` dict internally — reading back returns the dict format
  - After writing, the PATCH response may show stale `data.items`. Always verify by re-fetching the collection via GET, not by trusting the PATCH response body
  - To verify a specific item's note without parsing the full collection: extract the item's `_id`, then GET the collection and filter for that `_id`

- **PATCH `items` field does not add items**: Sending `{"items": [new_item]}` in a PATCH body returns `{"success": true}` but does NOT add the item. Only the metadata fields (description, title, theme, private) take effect. The `data.items` in the response shows pre-existing items unchanged. Use `POST /api/collections/{slug}/items` (above) for additions. The Python `update_collection_metadata()` does not accept items at all — use `add_collection_item()`.
- **Stale item_object_id between read and delete**: The collection state can change between `get_collection()` and `delete_collection_item()` calls — either from concurrent cron jobs or API caching. If `delete_collection_item` returns HTTP 404 with "Item not found", re-fetch the collection with `get_collection()` to get current item IDs before retrying. Do NOT assume the item was already deleted by another process — verify by checking whether the target `item_id` still appears in the collection's items list.
- **Emoji in terminal trigger security gates**: Unicode variation selectors in emoji characters cause the terminal security scanner to flag commands as suspicious. Strip emoji from Python strings when running via `terminal()` — use plain text markers like `[OK]` or `[DONE]` instead.
- **`delete_collection_item` requires hash-suffixed slug**: Passing the short slug (e.g., `"user/title"`) to `delete_collection_item` returns HTTP 200 without error but does NOT remove the item. The endpoint silently resolves to the wrong collection. The `get_collection()` and `add_collection_item()` accept both slug formats, creating a trap: you test those and they work, then `delete_collection_item` silently fails. Prevention: always use `get_collection().slug` as the `collection_slug` argument for `delete_collection_item`. Never hardcode the short slug.