# New Model Onboarding — Card, Collection, Note, Description

Documented 2026-07-29 — the four-step atomic publish flow for bringing a new model from bare skeleton to fully promoted ecosystem member. Designed for cron-driven maintenance where a new model is discovered (via `new-asset-discovery.md`) and needs its first card and collection entry.

## The Four-Step Flow

```
DISCOVER → CARD → COLLECTION → NOTE → DESCRIPTION → VERIFY
```

Each step depends on the previous one. Do not skip steps or reorder.

## Prerequisites

- The model repo exists on HF (even if just `.gitattributes`)
- HF token with write access (`~/.cache/huggingface/token`)
- Collection slug for the family collection
- A reference card to use as template (sibling model with good README)

## Step 1: Create the README Card

Write a comprehensive README.md with:

**YAML frontmatter (required):**
```yaml
---
license: apache-2.0
language:
- en
library_name: peft        # or transformers
pipeline_tag: text-generation  # triggers HF auto-registration!
tags:
- sakthai
- house-of-sak
- tool-calling
# ... model-specific tags
base_model: Qwen/Qwen2.5-1.5B-Instruct  # if adapter
datasets:
- Nanthasit/sakthai-combined-v7
---
```

**Critical:** Setting `pipeline_tag` in YAML frontmatter on first upload causes HF to auto-detect and register the pipeline tag. Without it, the model shows `pipeline_tag: null` in API responses and is invisible in filtered searches.

**Body sections (in order):**
1. Title + badges (downloads, license, collection link)
2. What's new (version comparison if v2)
3. What it is — one-paragraph description
4. Quick Start — Python code that actually works
5. Training details (base model, method, data)
6. Full Model Family table with download counts + roles
7. Growing the Ecosystem section (promote low-download siblings)
8. Links bar (House of Sak, GitHub, All models, Collection)
9. License

**Upload methods:**

Python SDK (`upload_file` works even when `whoami` returns "Invalid"):
```python
api = HfApi()
api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/sakthai-context-1.5b-tools-v2',
    repo_type='model'
)
```

CLI (requires `hf` CLI):
```bash
hf upload Nanthasit/<repo> /path/to/README.md README.md \
  --commit-message "Add comprehensive model card"
```

Git (works when APIs are blocked):
```bash
git clone --depth 1 "https://user:$HF_TOKEN@huggingface.co/user/repo" /tmp/repo
# ... write README.md ...
git add README.md && git commit -m "Add model card" && git push
```

## Step 2: Add to Collection

After the card is live, add the model to the family collection:

```python
from huggingface_hub import add_collection_item
add_collection_item(
    collection_slug="user/family-collection-hexhash",
    item_id="user/new-model",
    item_type="model",
    exists_ok=True,
)
```

REST (cron-safe):
```bash
curl -s -X POST \
  "https://huggingface.co/api/collections/{namespace}/{slug}/items" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"item":{"id":"Nanthasit/new-model","type":"model"}}'
```

**Key detail:** The REST endpoint is `/items` (plural), and the slug accepts both short and hash-suffixed forms for POST (unlike `delete_collection_item` which requires the hash suffix).

## Step 3: Set the Collection Note

New items added to a collection inherit **no note** (`note: null`). Set it in a second step:

```python
from huggingface_hub import get_collection, update_collection_item

col = get_collection("user/family-collection-hexhash")
for item in col.items:
    if "new-model" in item.item_id:
        update_collection_item(
            col.slug,
            item_object_id=item.item_object_id,
            note="Role description — 0 downloads. Key differentiator, call to action."
        )
```

REST (cron-safe — requires MongoDB `_id`, not position index):
```bash
# 1. Get the _id
curl -s "https://huggingface.co/api/collections/{namespace}/{slug}?limit=100" \
  -o /tmp/col.json
python3 -c "import json; d=json.load(open('/tmp/col.json')); \
  t=[i for i in d['items'] if 'new-model' in i['id']]; \
  print(t[0]['_id'])" > /tmp/item_id.txt

# 2. PATCH note
ITEM_ID=$(cat /tmp/item_id.txt)
curl -s -X PATCH \
  "https://huggingface.co/api/collections/{namespace}/{slug}/items/$ITEM_ID" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note": "Role description — 0 downloads. Key differentiator, call to action."}'
```

**Note format rules:**
- Pass as plain string (`"note": "text"`), not nested object
- Max 500 characters (silently truncated)
- API stores as `{"text": "...", "html": "..."}` dict internally
- Readers get back the dict — always extract via `.get('text', '')`

**What to write (see `hf-hub-collections` SKILL.md "Audit Collection for Empty Notes" for templates):**
- What is this? (one-line role)
- Why should I care? (key stat or differentiator)
- What now? (CTA for zero-download assets)

## Step 4: Update Collection Description

After adding the model, the collection's description (which includes model counts like "13 models") may be stale. Update it:

```python
from huggingface_hub import update_collection_metadata
update_collection_metadata(
    collection_slug="user/family-collection-hexhash",
    description="Updated ecosystem: N models (text, vision, code, TTS, embeddings), M datasets, P Spaces. Tagline."
)
```

REST:
```bash
curl -s -X PATCH \
  "https://huggingface.co/api/collections/{namespace}/{slug}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Updated description (max 150 chars)"}'
```

**150-char limit.** Exceed it and the API returns HTTP 400.

## Verification Checklist

After all four steps, verify:

- [ ] README on HF: HTTP 200 on raw URL
- [ ] Pipeline tag: check API shows correct `pipeline_tag`
- [ ] Collection item: present at expected position
- [ ] Collection note: non-null, readable text
- [ ] Collection description: correct model count (e.g., "N models")

```python
from huggingface_hub import HfApi, get_collection
import requests

# 1. README
r = requests.get(f"https://huggingface.co/{repo_id}/raw/main/README.md")
print(f"README: HTTP {r.status_code} | {len(r.text)} bytes")

# 2. Pipeline tag
info = HfApi().model_info(repo_id)
print(f"Pipeline: {info.pipeline_tag}")

# 3. Collection item + note
col = get_collection(collection_slug)
for item in col.items:
    if repo_id.split('/')[-1] in item.item_id:
        note = item.note.get('text', '') if isinstance(item.note, dict) else (item.note or '')
        print(f"Collection: {item.item_type} | pos={item.position} | note={'✅' if note else '❌'}")
        break

# 4. Description
print(f"Description: {col.description}")
```

## Relation to Other References

| Reference | Role in this flow |
|-----------|-------------------|
| `new-asset-discovery.md` | Step 0 — identifies models needing onboarding |
| `card-enrichment-patterns.md` | Step 1 — patterns for writing good cards |
| `sibling-driven-enrichment.md` | Step 1 — family table templates |
| `cron-execution-patterns.md` | All steps — safe cron workflows |
| `hf-hub-collections/references/family-collection-pattern.md` | Steps 2-4 — collection population |
| `stale-count-detection.md` | Post-onboarding — keeps collection notes fresh |
