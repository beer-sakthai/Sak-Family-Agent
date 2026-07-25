# HF Learnings — Hub Collections API Deep Dive

## 2026-07-24: hf-hub-collections-api-deep-dive — Full API Reference & Patterns (Topic #107)

### Summary
Comprehensive deep-dive into the Hugging Face Hub Collections API — covering all 7 collection methods from source (`huggingface_hub` v1.x), the `list_collections` pagination engine with 3 sort modes and 2 filter axes, the `Collection` and `CollectionItem` data classes, 6 item types (model, dataset, space, paper, collection, bucket), and practical patterns for programmatic curation, batch population, and integration with other Hub features.

### Source Analysis
All methods live in `huggingface_hub.hf_api.HfApi` (~800 lines from `list_collections` through `delete_collection_item`). Also available as module-level functions (`get_collection`, `create_collection`, etc.) exported from `huggingface_hub/__init__.py` as wrappers around a default `HfApi()` instance.

### Core Data Types

**`CollectionItemType_T`** = `Literal["model", "dataset", "space", "paper", "collection", "bucket"]`

All 6 types are valid. Case-sensitive lowercase only.

**`CollectionSort_T`** = `Literal["lastModified", "trending", "upvotes"]`

Three sort modes for `list_collections`.

**`CollectionItem`** (dataclass):
| Field | Type | Description |
|-------|------|-------------|
| `item_object_id` | `str` | DB-level unique ID within the collection |
| `item_id` | `str` | Hub ID: repo_id, paper id, collection slug, or bucket id |
| `item_type` | `CollectionItemType_T` | One of the 6 types |
| `position` | `int` | Position in collection (1-indexed) |
| `note` | `str \| None` | Plain text note, max 500 chars |

**Note about constructor**: The API returns `_id` (internal DB id) and `id` (Hub ID). The Python class maps `_id → item_object_id` and `id → item_id`. If a collection item is itself a collection (type="collection"), the `slug` kwarg overrides `item_id`.

**`Collection`** (dataclass):
| Field | Type | Description |
|-------|------|-------------|
| `slug` | `str` | Unique slug: `"user/title-hash"` |
| `title` | `str` | Display title |
| `owner` | `str` | Username or org |
| `items` | `list[CollectionItem]` | Items in the collection |
| `last_updated` | `datetime` | Last update (parsed from `lastUpdated` ISO string) |
| `position` | `int` | Position in owner's list |
| `private` | `bool` | Privacy flag |
| `theme` | `str` | Color theme (e.g. "green", "blue", "pink") |
| `upvotes` | `int` | Upvote count |
| `description` | `str \| None` | Plain text desc, max 150 chars |
| `url` | `str` (property) | Resolved to `{endpoint}/collections/{slug}` |

### Method-by-Method API Reference

#### 1. `list_collections()` — Discover Collections

```python
collections = api.list_collections(
    owner="username",           # Filter by owner (str or list[str])
    item="models/gpt2",         # Filter collections containing a specific item
    sort="trending",            # "lastModified" | "trending" | "upvotes"
    limit=10,                   # Max results (default: no limit, all pages)
)
```

**Key behaviors:**
- Returns `Iterable[Collection]` — uses `paginate()` internally for cursor-based pagination
- **Item list is TRUNCATED to 4 items per collection** when listing. Use `get_collection()` for full item list.
- The `limit` parameter truncates early — stops fetching pages once limit is reached (uses `islice`)
- No `owner` filter = global search across all Hub collections
- `item` format: `"models/teknium/OpenHermes-2.5-Mistral-7B"`, `"datasets/squad"`, `"papers/2311.12983"`

**Combined filter example:**
```python
# Trending collections about a specific model, owned by a user
trending = api.list_collections(
    owner="huggingface",
    item="models/google/gemma-2-2b",
    sort="trending",
    limit=5
)
```

#### 2. `get_collection()` — Full Collection Detail

```python
collection = api.get_collection("TheBloke/recent-models-64f9a55bb3115b4f513ec026")
```

**Returns ALL items** (no truncation). This is the only way to get the complete item list.

**Internal**: Simple GET to `{endpoint}/api/collections/{slug}`. Returns full Collection dataclass.

#### 3. `create_collection()` — New Collection

```python
collection = api.create_collection(
    title="Awesome Agents",
    namespace="beer-sakthai",       # Defaults to your username
    description="My curated agent list",  # Max 150 chars
    private=False,                   # Public by default
    exists_ok=False,                 # Error if slug collision (unless True)
)
```

**Important details:**
- `namespace` defaults to `self.whoami(token)["name"]` — the authenticated user
- The slug is auto-generated from title + hash: `"namespace/title-24charhex"`
- `exists_ok=True` catches HTTP 409 and returns existing collection via `get_collection()`
- No `theme` parameter in `create_collection`! Theme is set via `update_collection_metadata()` after creation.
- Description max 150 chars (truncation edge: source says "The maximum size for a description is 150 characters")

**Slug structure**: `{owner}/{normalized-title}-{24-char-hex}`. The hex hash is based on the collection — changing the title updates the slug prefix but the trailing ID stays the same.

#### 4. `update_collection_metadata()` — Edit Metadata

```python
updated = api.update_collection_metadata(
    collection_slug="username/my-collection-abc123",
    title="New Title",
    description="Updated desc",     # Max 150 chars
    position=1,                     # Reorder: 1 = first in owner's list
    private=True,
    theme="pink",                   # Color theme: "green", "blue", "pink", "purple", etc.
)
```

**All args are optional.** PATCH request sends only non-None values. The response returns the full Collection from `r.json()["data"]`.

**Theme options** (observed on Hub): "green", "blue", "pink", "purple", "yellow", "red", "orange", "teal", "cyan", "indigo", "gray". These affect the visual presentation on profile pages.

#### 5. `delete_collection()` — Permanently Delete

```python
api.delete_collection(
    collection_slug="username/old-collection-abc123",
    missing_ok=True,                # No error if already gone
)
```

**IRREVERSIBLE.** No trash/undo. The `missing_ok` parameter catches HTTP 404.

#### 6. `add_collection_item()` — Add Items

```python
collection = api.add_collection_item(
    collection_slug="username/my-collection-abc123",
    item_id="openai-community/gpt2",     # repo_id, paper id, slug, or bucket id
    item_type="model",                    # One of 6 types
    note="Baseline GPT-2 model",          # Optional, max 500 chars
    exists_ok=True,                       # Skip if already present
)
```

**Returns the full updated Collection** (after the item is appended at last position).

**Error handling:**
- HTTP 403: Read-only access to the repo (wrong token, insufficient org role)
- HTTP 404: Item doesn't exist on the Hub
- HTTP 409: Item already exists in collection (unless `exists_ok=True`)

**Item type → ID format:**
| Type | ID format | Example |
|------|-----------|---------|
| `"model"` | `user/repo-name` | `"openai-community/gpt2"` |
| `"dataset"` | `user/dataset-name` | `"squad"` |
| `"space"` | `user/space-name` | `"hf-docs/doc-builder"` |
| `"paper"` | arXiv ID | `"2307.09288"` |
| `"collection"` | Full slug | `"moonshotai/kimi-k2"` |
| `"bucket"` | `namespace/bucket-name` | `"username/my-bucket"` |

#### 7. `update_collection_item()` — Modify Item

```python
api.update_collection_item(
    collection_slug="username/my-collection-abc123",
    item_object_id=collection.items[0].item_object_id,  # FROM the item, not the repo ID
    note="Updated note text",           # Max 500 chars
    position=0,                         # Move to first position
)
```

**Note**: The `item_object_id` is the DB-internal `_id` field, NOT the Hub repo ID. You must retrieve it from a `CollectionItem` object first. Returns `None`.

#### 8. `delete_collection_item()` — Remove Item

```python
api.delete_collection_item(
    collection_slug="username/my-collection-abc123",
    item_object_id=collection.items[-1].item_object_id,  # Last item
    missing_ok=True,
)
```

**IRREVERSIBLE.** Uses `item_object_id` (DB id), not `item_id` (Hub repo id).

### Advanced Patterns

#### Pattern 1: Batch Population with Error Tolerance

```python
from huggingface_hub import HfApi

api = HfApi()

# Create the collection
col = api.create_collection(
    title="Top Open LLMs 2026",
    description="Curated collection of leading open-weight LLMs on the Hub",
)

# Batch add with error tolerance
models = [
    ("meta-llama/Llama-3.1-8B", "model"),
    ("beer-sakthai/my-dataset", "dataset"),  # Will silently skip if 404 + exists_ok
]

for item_id, item_type in models:
    try:
        api.add_collection_item(
            col.slug, item_id, item_type,
            exists_ok=True,
        )
    except Exception as e:
        print(f"Skipped {item_id}: {e}")
```

#### Pattern 2: List Collections by Topic

```python
# Find all trending collections about Hugging Face's smolagents
collections = api.list_collections(
    item="models/huggingface/smolagents",
    sort="upvotes",
    limit=20,
)

for col in collections:
    print(f"[{col.upvotes}⬆] {col.title} by {col.owner} — {col.description or '(no desc)'}")
    # items are truncated to 4 here — use get_collection() for full list
```

#### Pattern 3: Mirror Collection Locally

```python
from huggingface_hub import HfApi

api = HfApi()

# Get source collection with all items
source = api.get_collection("some-user/cool-models-abc123")

# Create a private copy in your namespace
dest = api.create_collection(
    title=f"Mirror: {source.title}",
    description=f"Mirror of @{source.owner}/{source.slug}",
    private=True,
)

# Copy all items
for item in source.items:
    api.add_collection_item(
        dest.slug, item.item_id, item.item_type,
        note=item.note,
        exists_ok=True,
    )
```

#### Pattern 4: Paper + Model + Dataset Collections for Research

```python
# Create a collection for a research project
col = api.create_collection(
    title="My Research: Efficient LLM Inference",
    description="Papers, models, and datasets for my LLM inference optimization project",
)

# Add a paper
api.add_collection_item(col.slug, "2305.14314", "paper",
    note="QLoRA: Efficient Finetuning of Quantized LLMs")

# Add companion model
api.add_collection_item(col.slug, "TimDettmers/guanaco-33b-merged", "model",
    note="QLoRA finetuned Guanaco 33B")

# Add dataset
api.add_collection_item(col.slug, "timdettmers/openassistant-guanaco", "dataset",
    note="Dataset used for QLoRA training")
```

#### Pattern 5: Organize Using Notes for Annotations

```python
# Add items with rating/status in notes
items = [
    ("meta-llama/Llama-3.1-8B", "model", "⭐ Production-ready, great for chat"),
    ("mistralai/Mistral-7B-v0.1", "model", "⚠ Good baseline but dated"),
    ("google/gemma-2-2b", "model", "🔄 Testing on edge devices"),
]

for item_id, item_type, note in items:
    api.add_collection_item(
        col.slug, item_id, item_type,
        note=note,
        exists_ok=True,
    )
```

#### Pattern 6: Programmatic Curation from Search Results

```python
from huggingface_hub import HfApi

api = HfApi()

# Create collection
col = api.create_collection(
    title="Trending Text Generation Models",
    description="Auto-curated from Hub trending models",
)

# Search for trending text-generation models
from huggingface_hub import HfApi
models = api.list_models(
    task="text-generation",
    sort="downloads",
    direction=-1,
    limit=10,
)

# Add to collection
for model in models:
    api.add_collection_item(
        col.slug, model.id, "model",
        note=f"⬇ {model.downloads:,} downloads",
        exists_ok=True,
    )
```

### Hub Web UI Features (not available via API)

The API does **NOT** support:
- **Item images** — adding images to collection items is UI-only (drag-and-drop)
- **History tracking** — who edited what, available in web UI
- **Drag-and-drop reordering** — use `update_collection_item(position=)` via API instead
- **Gating Group Collections** — Team/Enterprise feature, no API endpoint exposed
- **Resource Group assignment** — Team/Enterprise, UI-only

### Behavioral Quirks & Pitfalls

1. **`list_collections` truncates items to 4** — Always use `get_collection()` when you need the full item list. This is documented in the warning on `list_collections`.

2. **`item_object_id` vs `item_id` confusion** — Operations that modify/delete individual items require the internal `item_object_id` (from `CollectionItem.item_object_id`), NOT the Hub repo ID. Getting this wrong returns HTTP 404.

3. **No `theme` on `create_collection`** — Theme can only be set via `update_collection_metadata()` after creation. If you want a themed collection, you must do two calls.

4. **Slug changes on title update** — When you update the title, the slug prefix changes (e.g., `"my-collection-abc"` → `"my-updated-collection-abc"`) but the trailing hash stays the same. The old slug URL no longer works.

5. **Description is 150 chars max** — Silently truncated by API. No error raised.

6. **Notes are 500 chars max** — Silently truncated. Plain text only, but URLs auto-link in web UI.

7. **`exists_ok` on `create_collection` only catches 409** — If a collection with the *same slug* already exists, it returns that collection. But slugs are hash-based, so collision is unlikely unless the exact same title was used before.

8. **No rate limit documentation** — Collections API is subject to the same Hub API rate limits (~100 req/min for unauthenticated, higher with token). Batch operations may need pacing.

### Zero-Cost Strategies

Collections are **completely free** — no storage costs, no GPU compute, no usage limits beyond standard Hub API rate limits. They're ideal for:

1. **Building public portfolios** — Showcase your work on your HF profile at zero cost
2. **Curating learning resources** — Organize models/datasets/papers by topic for study
3. **Auto-curation via cron** — Run a daily cron job to update a "Trending Today" collection
4. **Research paper companion pages** — Link paper + models + datasets in one URL
5. **Team onboarding** — Create collections of recommended resources for new team members
6. **Buckets integration** — Use collections to link buckets of data to their associated models

### Comparison: Collections vs Other Curating Tools

| Feature | Collections | Model Card Links | README Lists | Bookmarks |
|---------|------------|-----------------|--------------|-----------|
| Dedicated page | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Multiple types | ✅ All 6 | ❌ Models only | ✅ Any | ❌ N/A |
| Sortable/resizable | ✅ Yes | ❌ No | ✅ Manual | ❌ No |
| Notes per item | ✅ 500 chars | ❌ No | ✅ Unlimited | ❌ No |
| Images per item | ✅ UI only | ❌ No | ✅ Unlimited | ❌ No |
| API access | ✅ Full CRUD | ❌ No | ❌ Git commit | ❌ No |
| Team/Enterprise gating | ✅ Group gating | ❌ No | ❌ No | ❌ No |
| Profile visibility | ✅ Top of profile | ❌ No | ✅ In README | ❌ No |

### Resources
- Source: `huggingface_hub/hf_api.py` lines 9908–10400 (collections methods)
- Source: `huggingface_hub/hf_api.py` lines 1427–1526 (CollectionItem + Collection dataclasses)
- Hub docs: https://huggingface.co/docs/hub/en/collections
- Raw docs (Markdown): https://huggingface.co/docs/hub/en/collections.md
- Community discussion: https://huggingface.co/spaces/huggingface/HuggingDiscussions/discussions/12
- Collections page: https://huggingface.co/collections
- Gating Group Collections: https://huggingface.co/docs/hub/en/enterprise-gating-group-collections
