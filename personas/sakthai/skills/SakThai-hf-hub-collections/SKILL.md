---
name: SakThai-hf-hub-collections
author: SakThai
license: MIT
description: Hugging Face Hub Collections API — create, manage, and curate themed collections of models, datasets, Spaces, papers, and other items programmatically via the huggingface_hub library
category: mlops
version: 1.0.0
---# HF Hub Collections API

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
    description="New desc",     # optional — update description
    private=True,              # optional — toggle privacy
    theme="blue",              # optional — change theme color
    position=1,                # optional — reorder position
)
```

All params except `collection_slug` are optional. Pass only what you want to change.

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
from huggingface_hub import delete_collection_item

delete_collection_item(
    collection_slug="username/my-collection-...",
    item_object_id="...",     # unique ID of the item to remove
)
```

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
| `description` | `str` (optional)   | Plain text description                         |
| `url`         | `str` (property)   | Hub URL                                        |

### CollectionItem

| Field             | Type             | Description                                       |
|-------------------|------------------|---------------------------------------------------|
| `item_object_id`  | `str`            | Unique ID of the item within the collection       |
| `item_id`         | `str`            | ID on the Hub (repo_id, paper id, collection slug, bucket id) |
| `item_type`       | `str`            | One of: `"model"`, `"dataset"`, `"space"`, `"paper"`, `"collection"`, `"bucket"` |
| `position`        | `int`            | Position in the collection (1-indexed)            |
| `note`            | `str` (optional) | Plain text note, max 500 characters               |

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
    print(f"[{item.item_type}] {item.item_id} — {item.note or '(no note)'}")
```

## Pitfalls

- **Collection slugs are permanent-ish**: once created, the slug contains a hash and cannot be changed. Always store the slug after creation.
- **Note length limit**: Notes are capped at **500 characters** — longer notes are silently truncated by the API.
- **`exists_ok`**: When adding items, the API returns HTTP 409 if the item already exists and `exists_ok=False`. Always set `exists_ok=True` for idempotent add operations.
- **Item types**: Must be exact lowercase strings — `"model"`, not `"Model"` or `"models"`.
- **Bucket type**: The `"bucket"` type refers to HF Storage Buckets (not S3). Use a `namespace/bucket-name` ID format.
- **Deletion is irreversible**: No "undo" for `delete_collection` or `delete_collection_item`.
- **Private collections**: Private collections are only visible to the owner and collaborators.
