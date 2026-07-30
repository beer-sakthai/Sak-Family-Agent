# Family Collection Pattern

Create a themed collection bundling all models + datasets from the same project family.

## When to use

After publishing multiple related models (e.g. a base model + adapters + GGUF variants + embedding models). A family collection makes them discoverable as a unified project.

## Steps

### 1. Create collection

```python
col = create_collection(
    title='SakThai Model Family',
    description='All SakThai models, datasets, and Spaces — tool-calling LLMs, embeddings, code, vision, TTS, training data, and agent performance tracking.'
)
```

**Save the slug.** Collections are identified by `owner/title` (without hash suffix in modern HF API). The slug is deterministic from the title — if you recreate a collection with the same title, you get a new one with a different hash.

### 2. Add models, datasets, and Spaces

Use `exists_ok=True` for idempotent adds:

```python
items = [
    ('Nanthasit/sakthai-context-1.5b-merged', 'model'),
    ('Nanthasit/sakthai-context-0.5b-merged', 'model'),
    ('Nanthasit/sakthai-context-7b-merged', 'model'),
    ('Nanthasit/sakthai-context-7b-128k', 'model'),
    ('Nanthasit/sakthai-context-1.5b-tools', 'model'),
    ('Nanthasit/sakthai-context-7b-tools', 'model'),
    ('Nanthasit/sakthai-coder-1.5b', 'model'),
    ('Nanthasit/sakthai-vision-7b', 'model'),
    ('Nanthasit/sakthai-tts-model', 'model'),
    ('Nanthasit/sakthai-embedding-multilingual', 'model'),
    ('Nanthasit/sakthai-combined-v6', 'dataset'),
    ('Nanthasit/sakthai-kaggle-notebooks', 'dataset'),
    ('Nanthasit/SimpleToolCalling', 'dataset'),
    ('Nanthasit/food-penguin-v1', 'dataset'),
    ('Nanthasit/sakthai-tts', 'space'),
    ('Nanthasit/sakthai-leaderboard', 'space'),
]
for item_id, item_type in items:
    add_collection_item(col.slug, item_id, item_type=item_type, exists_ok=True)
```

### 3. Add descriptive notes to specific items

Use `update_collection_item` to set notes (not `add_collection_item` — that only adds new items):

```python
col = get_collection(col.slug)
for item in col.items:
    if '1.5b-merged' in item.item_id and not item.note:
        update_collection_item(
            col.slug,
            item_object_id=item.item_object_id,
            note='Flagship model — 1,197 downloads. Tool-calling GGUF, 1.5B params.'
        )
```

The `item_object_id` is the unique `_id` of the item within the collection — find it via `item.item_object_id` on the `CollectionItem` object. Notes are capped at 500 characters.

### 4. Cross-link from every model card

Add to each model's README.md:

```markdown
## SakThai Model Family

| Model | Size | Type | Downloads |
|-------|:----:|:----:|:---------:|
| [1.5B-merged](...) | 934 MB | Tool-calling | 942 |

[Full collection →](https://huggingface.co/collections/...)
```

### 5. Periodically refresh download counts in notes

Collection notes with download counts go stale. Refresh them monthly (or whenever the ecosystem gains significant downloads):

```python
from huggingface_hub import get_collection, update_collection_item

SLUG = "Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"

# Current download counts per item ID
UPDATED_NOTES = {
    "Nanthasit/sakthai-context-1.5b-merged":
        "Flagship model - 1,197 downloads. Tool-calling GGUF, 1.5B params.",
    "Nanthasit/sakthai-context-0.5b-merged":
        "Lightweight companion - 994 downloads. 0.5B tool-calling GGUF.",
    "Nanthasit/sakthai-context-7b-merged":
        "Full-power model - 562 downloads. 7B tool-calling GGUF.",
    "Nanthasit/sakthai-context-7b-128k":
        "Long context specialist - 351 downloads. 7B GGUF, 128K context.",
    "Nanthasit/sakthai-vision-7b":
        "Vision-language model - 45 downloads. LLaVA-1.5-7B GGUF.",
    "Nanthasit/sakthai-tts-model":
        "Voice of the family - 33 downloads. Kokoro-82M TTS, 15 languages.",
    "Nanthasit/sakthai-embedding-multilingual":
        "Cross-lingual embeddings - 104 downloads. 50+ languages.",
    "Nanthasit/sakthai-combined-v6":
        "Training data - 150 downloads. 2,003 tool-calling examples.",
}

col = get_collection(SLUG)
for item in col.items:
    note = UPDATED_NOTES.get(item.item_id)
    if note and item.note != note:
        update_collection_item(SLUG, item_object_id=item.item_object_id, note=note)
```

**Check drift before updating:** Only run the refresh if the ecosystem has grown. If download counts haven't changed since the last refresh, the notes are still accurate and the refresh is unnecessary (each `update_collection_item` call counts toward API rate limits).

## Example result

Collection: `Nanthasit/sakthai-model-family`

Items: 10 models + 4 datasets + 2 Spaces. Each model card links back to the family table.

## Critical: Verify collection completeness

Collections silently drift when new models/datasets/Spaces are created after the collection was populated. Always verify programmatically:

```python
from huggingface_hub import HfApi, get_collection

api = HfApi()

# ⚠️ Slug format note: The modern slug is just owner/title (no hash suffix).
# Older collections may have a hash suffix appended (e.g., "user/title-xyz...").
# Find the correct slug from the collection's URL on HF.
COLLECTION_SLUG = "Nanthasit/sakthai-model-family"

# Expected items (from your family inventory)
expected = {
    ("Nanthasit/sakthai-context-1.5b-merged", "model"),
    ("Nanthasit/sakthai-context-0.5b-merged", "model"),
    ("Nanthasit/sakthai-context-7b-merged", "model"),
    ("Nanthasit/sakthai-context-7b-128k", "model"),
    ("Nanthasit/sakthai-context-1.5b-tools", "model"),
    ("Nanthasit/sakthai-context-7b-tools", "model"),
    ("Nanthasit/sakthai-coder-1.5b", "model"),
    ("Nanthasit/sakthai-vision-7b", "model"),
    ("Nanthasit/sakthai-tts-model", "model"),
    ("Nanthasit/sakthai-embedding-multilingual", "model"),
    ("Nanthasit/sakthai-combined-v6", "dataset"),
    ("Nanthasit/sakthai-kaggle-notebooks", "dataset"),
    ("Nanthasit/SimpleToolCalling", "dataset"),
    ("Nanthasit/food-penguin-v1", "dataset"),
    ("Nanthasit/sakthai-tts", "space"),
    ("Nanthasit/sakthai-leaderboard", "space"),
}

# Get actual items
col = get_collection(COLLECTION_SLUG)
actual = {(item.item_id, item.item_type) for item in col.items}

# Or via raw REST API (when huggingface_hub isn't available):
# import json, urllib.request
# resp = urllib.request.urlopen(
#     "https://huggingface.co/api/collections/" + COLLECTION_SLUG
# )
# data = json.load(resp)
# Note: Raw REST API returns items with flattened fields — item data
# is at the top level (id, type, pipeline_tag, etc.), NOT nested
# under an "item" key. The Python SDK maps these to CollectionItem
# objects with item_id, item_type, item_object_id, etc.

missing = expected - actual
extra = actual - expected

if missing:
    print(f"⚠ MISSING {len(missing)} items from collection:")
    for item_id, item_type in sorted(missing):
        print(f"  {item_type}: {item_id}")
    for item_id, item_type in missing:
        from huggingface_hub import add_collection_item
        add_collection_item(COLLECTION_SLUG, item_id, item_type=item_type, exists_ok=True)

if extra:
    print(f"⚠ EXTRA items in collection ({len(extra)}):")
    for item_id, item_type in sorted(extra):
        print(f"  {item_type}: {item_id}")
```

Add this check to any cron that maintains the collection. The `add_collection_item(exists_ok=True)` call is idempotent, so missing items can be added back without duplicating existing ones.

## Pitfalls

- **Collection slug format**: Modern HF collections use `owner/title` slugs (no hash suffix). Older collections (and ones created via the web UI in 2025) may have a hash suffix like `owner/title-abcdef123`. Use the slug from the collection's URL or API response — `get_collection` works with both formats.
- **`exists_ok=True` is critical**: Without it, adding an already-present item returns HTTP 409.
- **Item types are lowercase**: `"model"`, not `"Model"` or `"models"`.
- **Notes have 500-char limit**: Longer notes are silently truncated. Use `update_collection_item` to add/modify notes on existing items; `add_collection_item` adds new items only.
- **Slug after rename**: If you rename a collection's title, the slug stays the same (the hash doesn't change). The title updates but the URL/API path remains.
- **REST API item structure**: The raw API returns items as flat JSON objects (`id` at top level, not nested). The Python SDK normalises this: `id` → `item_id`, `type` → `item_type`, `_id` → `item_object_id`.
