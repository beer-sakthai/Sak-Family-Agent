# Collection Double-Type Detection

## Background

The `sakthai-model-family` collection (slug: `Nanthasit/sakthai-model-family`) had the same repo `Nanthasit/sakthai-combined-v6` listed twice — once with `item_type=dataset` (correct) and once with `item_type=model` (incorrect). This inflated the item count from the true 16 items to a reported 17.

## How to Detect

When auditing a collection's items, group by `item_id` and check for duplicates:

```python
from huggingface_hub import get_collection

col = get_collection("owner/slug")
seen = {}
for item in col.items:
    if item.item_id in seen:
        print(f"DUPLICATE: {item.item_id} appears as {seen[item.item_id]} AND {item.item_type}")
    else:
        seen[item.item_id] = item.item_type
```

## Why It Happens

The HF Hub can list the same repo ID under multiple `item_type` values if:
- The repo was originally created as one type (e.g., dataset) but the Hub's ambiguous metadata also tags it as another type (e.g., model) — this is what happened with `sakthai-combined-v6`.
- A collection item was added manually (drag-and-drop in the UI) with one type, then later the same repo was programmatically added with a different type via the API.
- The Hub's own type inference changed after the item was added to the collection.

## How to Fix

1. Identify which type is correct for the repo.
2. Get the `item_object_id` of the WRONG-type item from the collection.
3. Delete it:

```python
from huggingface_hub import delete_collection_item

delete_collection_item(
    collection_slug="owner/slug",
    item_object_id="wrong-type-item-object-id",
)
```

4. Verify by re-fetching the collection and confirming the repo appears only once.

## Detection Within a Health Check Report

When running `hf-ecosystem-health-check`, add this to the Collections Audit section:

```python
# Collapse items by unique ID
unique_ids = set()
duplicates = []
for item in col.items:
    if item.item_id in unique_ids:
        duplicates.append(f"{item.item_id} ({item.item_type})")
    unique_ids.add(item.item_id)

if duplicates:
    print(f"⚠️ Collection has duplicate items: {duplicates}")
    print(f"  Reported count: {len(col.items)}, Unique count: {len(unique_ids)}")
```

This should be run for every collection in the health check, not just the family collection.
