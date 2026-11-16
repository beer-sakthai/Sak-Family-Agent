# Hugging Face SDK (`huggingface_hub`) in Cron Mode

Using the `huggingface_hub` Python SDK directly via `uv run` is the cleanest
approach for complex HF operations in cron mode — no raw REST API calls, no
curl-based workarounds needed.

## Why this works in cron mode

`terminal("uv run python3 -c '...'")` is a simple invocation and **does not
trigger** any tirith security guards:

| Concern | Status | Why |
|---------|--------|-----|
| Pipe-to-interpreter | ✅ Pass | No `\|`, just `terminal()` → `uv run python3` |
| `execute_code` block | ✅ Pass | Uses `terminal()`, not `execute_code()` |
| Write to `/tmp` | ✅ Pass | No file writes needed |
| Token exposure | ✅ Pass | Uses saved HF token from cache |

## Basic pattern

```bash
uv run python3 -c "
from huggingface_hub import HfApi
api = HfApi()
# ... your code ...
print(result)
"
```

## When to use vs. curl

| Approach | When to use |
|----------|-------------|
| **`uv run python3` + SDK** | Complex operations: collection management, repo creation, model card edits, batch queries, multi-step workflows with conditional logic |
| **`curl` to `/tmp/` + `python3` parse** | Simple data fetches (GET a JSON response, parse, print), when SDK is unnecessary overhead |

## Real example — collection curator

```bash
uv run python3 -c "
from huggingface_hub import HfApi
api = HfApi()

slug = 'Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02'

# Add item (note= for description, not description=)
api.add_collection_item(
    slug,
    item_id='Nanthasit/sakthai-combined-v10',
    item_type='dataset',
    note='v10 combined training dataset -- expanded examples.',
    exists_ok=True
)

# Update collection metadata (doesn't take note=)
api.update_collection_metadata(
    slug,
    description='Collection: 20 models, 11 datasets, 4 Spaces.'
)

print('Done')
"
```

## Pitfalls

### 1. Parameter naming — `note=` not `description=`

`HfApi.add_collection_item()` takes `note=` (str, max 500 chars) for the
item's descriptive text, NOT `description=`. Passing `description=` raises
`TypeError: got an unexpected keyword argument 'description'`.

Similarly, `HfApi.update_collection_item()` takes `note=` and `position=`
as optional kwargs — NOT `description=`.

**Collection-level** description is set via `update_collection_metadata()`
with `description=` (str, max **150 chars**).

Quick reference:

| Method | Summary text param | Limit |
|--------|-------------------|-------|
| `add_collection_item()` | `note=` | 500 chars |
| `update_collection_item()` | `note=` | 500 chars |
| `update_collection_metadata()` | `description=` | 150 chars |

### 2. `uv` first-run overhead

The first time `uv run python3 -c "..."` is called for a given module, `uv`
downloads and caches the dependency. This adds ~2-5s on first use. Subsequent
runs use the cached version and are near-instant.

**Mitigation:** If strict timing matters, force a cache warm-up at job setup
time: `uv run python3 -c "from huggingface_hub import HfApi; print('warm')"`.
After that, all successive runs in the same session skip the install phase.

### 3. Token authentication

`HfApi()` reads the token from `~/.cache/huggingface/token` automatically
when no explicit token is passed. This works in cron mode as long as:

- The token file exists (set up via `huggingface-cli login` or manual write)
- The cron job's `HOME` env or HF cache path resolves to the right location

Verify before relying on it:
```bash
uv run python3 -c "
from huggingface_hub import get_token
tok = get_token()
print('Token available:', tok is not None and len(tok) > 10)
"
```

### 4. `update_collection_item()` returns `None`

Unlike `add_collection_item()` which returns the updated collection,
`update_collection_item()` returns `None`. Always verify by re-fetching
with `get_collection()`:
```bash
uv run python3 -c "
from huggingface_hub import HfApi
api = HfApi()
col = api.get_collection('user/collection-slug-hex')
# Find your item and check its note
for i in col.items:
    if 'target-repo' in i.item_id:
        print(f'Note: {i.note}')
"
```

### 5. Cross-type `item_id` collisions

A model AND dataset can share the same repo ID (e.g., `user/sakthai-coder-browser`).
When iterating, represent items as `(item_id, item_type)` tuples, not just
`item_id` strings. The collection API requires `item_type` to disambiguate.

### 6. Don't embed download counts if they'll go stale

If your note includes a download count (e.g., "1,599 downloads"), it will
be stale after a few days. Either:
- Use qualitative descriptors ("most popular," "lightest model")
- Add a date suffix ("as of 2026-07-31")
- Run a periodic refresh script

## Full cross-type collection scan (models + datasets + spaces)

```bash
uv run python3 -c "
from huggingface_hub import HfApi, get_collection
import requests

api = HfApi()
SLUG = 'Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02'

# 1. Get collection items
col = get_collection(SLUG)
coll_items = {(i.item_id, i.item_type) for i in col.items}

# 2. Get all account repos across types
account_items = set()
for item_id in [m['id'] for m in requests.get(
    'https://huggingface.co/api/models?author=Nanthasit&limit=100').json()]:
    account_items.add((item_id, 'model'))
for item_id in [d['id'] for d in requests.get(
    'https://huggingface.co/api/datasets?author=Nanthasit&limit=100').json()]:
    account_items.add((item_id, 'dataset'))
for item_id in [s['id'] for s in requests.get(
    'https://huggingface.co/api/spaces?author=Nanthasit&limit=100').json()]:
    account_items.add((item_id, 'space'))

# 3. Diff
missing = sorted(account_items - coll_items)
if missing:
    print(f'Adding {len(missing)} missing items:')
    for item_id, item_type in missing:
        api.add_collection_item(SLUG, item_id, item_type=item_type,
                                note='Auto-added by collection curator', exists_ok=True)
        print(f'  + {item_type}: {item_id}')
else:
    print('Collection is complete.')
"
```
