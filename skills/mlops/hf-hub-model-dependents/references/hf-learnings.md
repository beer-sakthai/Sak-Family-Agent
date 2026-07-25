# HF Learnings — HF Hub Model Dependents API

## 2026-07-25: hf-hub-model-dependents — Model Dependents & Children Discovery API (Topic #253)

### Summary
Complete reference for the Hugging Face Hub Model Dependents system — how models declare parent relationships, how the Hub tracks children by type (finetune, quantized, adapter, merge), and the full API surface for discovering dependents via REST API and Python library. There is NO dedicated `/dependents` endpoint; instead, dependents discovery is a composition of `expand` parameters on the model info endpoint and `filter` on the list models endpoint.

### How Model Dependencies Work

Models declare their parent relationship through the **`base_model` field** in the model card YAML frontmatter:

```yaml
---
language: en
license: mit
base_model: microsoft/Phi-3.5-mini-instruct
---
```

When a model is uploaded with a `base_model` declaration, the Hub automatically:
1. Registers the model as a **child** of the base model
2. Classifies the **relationship type** based on the model's uploaded files and configuration
3. Updates both the parent's `childrenModelCount` and the child's `baseModels`

### Relationship Types

The Hub auto-classifies children into four types, visible in `childrenModelCount`:

| Type | Meaning | Criteria |
|------|---------|----------|
| `finetune` | Fine-tuned version | Model weights, different training data/task |
| `quantized` | Quantized version | GGUF, bitsandbytes, AWQ, GPTQ, HQQ, ONNX, etc. |
| `adapter` | Adapter (LoRA/DoRA/PEFT) | Small weight files, adapter_config.json present |
| `merge` | Merged model | Multiple base models combined, `merge` tag present |

### REST API Reference

#### 1. Children Count (on base model info)

```
GET /api/models/{model_id}?expand[]=childrenModelCount
```

**Response addition:**
```json
{
  "childrenModelCount": {
    "adapter": 716,
    "merge": 19,
    "quantized": 190,
    "finetune": 328
  }
}
```

**Python:**
```python
from huggingface_hub import HfApi
api = HfApi()
info = api.model_info("microsoft/Phi-3.5-mini-instruct", expand=["childrenModelCount"])
print(info.children_model_count)  # {'adapter': 716, 'merge': 19, 'quantized': 190, 'finetune': 328}
```

#### 2. Base Model Declaration (on child model info)

```
GET /api/models/{model_id}?expand[]=baseModels
```

**Response addition:**
```json
{
  "baseModels": {
    "relation": "finetune",
    "models": [
      {
        "_id": "66bfbb1a43a701a837a745ac",
        "id": "microsoft/Phi-3.5-mini-instruct"
      }
    ]
  }
}
```

**Python:**
```python
info = api.model_info("unsloth/Phi-3.5-mini-instruct", expand=["baseModels"])
print(info.base_models)
# {'relation': 'finetune', 'models': [{'_id': '...', 'id': 'microsoft/Phi-3.5-mini-instruct'}]}
```

#### 3. Children List (filter by base_model)

```
GET /api/models?filter=base_model:{org/model}&sort=downloads&direction=-1&limit=10
```

**Response:** Paginated list of `ModelInfo` objects whose `base_model` matches the specified parent.

**Python:**
```python
from huggingface_hub import HfApi
api = HfApi()
children = list(api.list_models(
    filter="base_model:microsoft/Phi-3.5-mini-instruct",
    sort="downloads",
    direction=-1,
    limit=20
))
for c in children:
    print(c.id, c.downloads)
```

Note: There is **no `list_children()` method** in `HfApi`. Use `list_models()` with the `base_model:` filter.

#### 4. Spaces Using Model

```
GET /api/models/{model_id}?expand[]=spaces
```

**Response addition:** List of Space repo IDs:
```json
{
  "spaces": ["pliny-the-prompter/obliteratus", "baconnier/prompt-plus-plus", ...]
}
```

**Python:**
```python
info = api.model_info("microsoft/Phi-3.5-mini-instruct", expand=["spaces"])
print(len(info.spaces))  # Can be 100+ (API default limit)
print(info.spaces[:5])
```

#### 5. Combined (all expansions)

```
GET /api/models/{model_id}?expand[]=childrenModelCount&expand[]=spaces&expand[]=cardData
```

Returns all three expansions simultaneously for a complete profile of a model's ecosystem.

### Python Library Details

| ModelInfo Field | Type | Source | Description |
|---|---|---|---|
| `children_model_count` | `dict` or `None` | `expand=["childrenModelCount"]` | `{adapter: N, merge: N, quantized: N, finetune: N}` |
| `base_models` | `dict` or `None` | `expand=["baseModels"]` | `{relation: str, models: [{_id: str, id: str}]}` |
| `spaces` | `list[str]` or `None` | `expand=["spaces"]` | List of Spaces using the model |
| `card_data` | `ModelCardData` or `None` | `expand=["cardData"]` | Full model card metadata |

The `ModelInfo` object stores these fields even without `expand`, but they will be `None` if the expand parameter is not passed.

### Important Notes

- **No dedicated dependents endpoint** — The Hub has no `/api/models/{id}/children` or `/api/models/{id}/dependents` REST endpoint (returns 404)
- **Auth required** — The `expand` and `filter` features may require authentication for some queries
- **Datasets don't have dependents** — Only models have the `base_model` relationship system
- **Paginated children** — Use `list_models()` with pagination for large dependency trees
- **Automatic relationship inference** — The Hub infers `finetune` vs `quantized` vs `adapter` vs `merge` based on uploaded file types and config
- **Recursive** — A child can itself have children (e.g., `unsloth/Phi-3.5-mini-instruct` has 244 adapters, 94 finetunes, 66 quantized of its own)

### Skill Created
`mlops/hf-hub-model-dependents/` — Complete reference for HF Hub Model Dependents API with REST and Python patterns.

### Sources
- Direct API testing against `huggingface.co/api/models` endpoints (2026-07-25)
- Source code: `huggingface_hub/hf_api.py` — `ModelInfo` class (lines 900-1100), `list_models()` method (lines 2398-2560)
- Hub docs: https://huggingface.co/docs/hub/en/model-cards (base_model YAML field)
- Hub API: https://huggingface.co/docs/hub/en/api (model endpoints)

---

## 2026-07-25: hf-hub-model-dependents — Deep-Dive v2: Tag System, Merge Models, Real-World Chains & Advanced Discovery (Topic #253)

### V2: What's New
This v2 builds on the v1 foundation with practical findings from live API testing against real models (`bert-base-uncased`, `google/gemma-2-2b-it`, `bartowski/gemma-2-2b-it-GGUF`, `John6666/one-obsession-17-red-sdxl`). Covers the tag-based dependency system, multi-parent merge models, dependency chains, practical discovery patterns, edge cases, and the Hub's auto-classification heuristics.

### 1. The Three Dependency Registration Mechanisms

Models declare parentage through **three overlapping mechanisms** that work at different levels:

| Mechanism | Where | Queryable via | Auto or Manual? |
|-----------|-------|---------------|-----------------|
| **Card YAML `base_model` field** | `card_data.base_model` | `expand=['cardData']` | Manual (declared by uploader) |
| **Hub-auto tags** | `tags` list on ModelInfo | `filter='base_model:X'` and `filter='base_model:{relation}:X'` | Auto (Hub infers from files) |
| **`baseModels` expand** | `info.base_models` with `relation` | `expand=['baseModels']` | Auto (Hub aggregates) |

All three are kept in sync: when a model is uploaded with `base_model: org/model` in YAML, the Hub auto-generates the corresponding tags and updates the `baseModels` relationship.

### 2. The Tag-Based Dependency System (Most Practical Discovery Tool)

When you upload a model declaring `base_model: google/gemma-2-2b-it`, the Hub injects **two tags**:

```
base_model:google/gemma-2-2b-it          # generic parent tag (any relation)
base_model:quantized:google/gemma-2-2b-it  # type-specific tag
```

This dual-tag system enables precise filtering:

```python
# ALL children of any type
children = api.list_models(filter='base_model:google/gemma-2-2b-it')

# Children of a SPECIFIC relation type
gguf_children = api.list_models(filter='base_model:quantized:google/gemma-2-2b-it')
finetune_children = api.list_models(filter='base_model:finetune:google/gemma-2-2b-it')
```

**Verified with live API:**

```
filter='base_model:google/gemma-2-2b-it' → returns ALL children (any relation)
  bartowski/gemma-2-2b-it-GGUF (quantized, 178K downloads)
  MaziyarPanahi/gemma-2-2b-it-GGUF (quantized, 58K downloads)
  mlc-ai/gemma-2-2b-it-q4f16_1-MLC (quantized, 9K downloads)
  google/gemma-2-2b-jpn-it (finetune, 6.5K downloads)
  lmstudio-community/gemma-2-2b-it-GGUF (quantized, 6.5K downloads)
```

**Tag format for merge models** (multi-parent):

```
base_model:merge:Laxhar/noobai-XL-1.0         # parent 1 (type: merge)
base_model:merge:OnomaAIResearch/Illustrious-XL-v2.0  # parent 2
```

Merge models use `base_model:merge:{parent}` for EACH declared parent, following the pattern `base_model:{relation}:{parent_id}`.

### 3. Real Dependency Chain Patterns

Models form **dependency chains** of arbitrary depth. Real verified chain:

```
google/gemma-2-2b (base model)
  └── google/gemma-2-2b-it (finetune: instruct-tuned)
        └── bartowski/gemma-2-2b-it-GGUF (quantized: GGUF)
        └── MaziyarPanahi/gemma-2-2b-it-GGUF (quantized)
        └── mlc-ai/gemma-2-2b-it-q4f16_1-MLC (quantized)
        └── google/gemma-2-2b-jpn-it (finetune: Japanese)
        └── anakin87/gemma-2-2b-neogenesis-ita (finetune: Italian)
        └── ... (476 adapters + 188 quantized + 19 merges + 997 finetunes)
```

Each model's `info.base_models` shows ONLY the **immediate parent** with its relation type. The Hub does NOT return the full ancestry chain — you must traverse manually.

**Verified base_models output:**
- `bartowski/gemma-2-2b-it-GGUF` → `base_models: {'relation': 'quantized', 'models': [{'id': 'google/gemma-2-2b-it'}]}`
- `google/gemma-2-2b-it` → `base_models: {'relation': 'finetune', 'models': [{'id': 'google/gemma-2-2b'}]}`

### 4. Multi-Parent Merge Models

Merge models (from mergekit or manual merging) declare **multiple base models**:

```yaml
# Model card YAML for a merge
base_model:
  - OnomaAIResearch/Illustrious-XL-v2.0
  - Laxhar/noobai-XL-1.0
```

This creates:
- `info.base_models` with `relation: 'merge'` and BOTH parents in the models list
- Tags: `base_model:merge:OnomaAIResearch/Illustrious-XL-v2.0` + `base_model:merge:Laxhar/noobai-XL-1.0`
- The Hub merges the children counts from BOTH parents increment

**Verified with John6666/one-obsession-17-red-sdxl:**
```
base_models: {
  'relation': 'merge',
  'models': [
    {'_id': '67272ad2aa6c5abcad2944c5', 'id': 'Laxhar/noobai-XL-1.0'},
    {'_id': '6801de3f6ccb6c0858f0f21c', 'id': 'OnomaAIResearch/Illustrious-XL-v2.0'}
  ]
}
card_data.base_model: ['OnomaAIResearch/Illustrious-XL-v2.0', 'Laxhar/noobai-XL-1.0']
tags: ['merge', 'base_model:merge:Laxhar/noobai-XL-1.0', 'base_model:merge:OnomaAIResearch/Illustrious-XL-v2.0']
```

### 5. The `base_model` YAML Field — Supported Formats

The `base_model` field in model card YAML supports three formats:

| Format | Example | Use Case |
|--------|---------|----------|
| **Single string** | `base_model: google/gemma-2-2b-it` | Single parent (finetune, quantized, adapter) |
| **List (YAML list)** | `base_model: [model1, model2]` | Multiple parents (merges, composite models) |
| **Dict (YAML mapping)** | `base_model: {model1: filter1}` | *(Used by some HF experiments, not standard)* |

The most common format for merges is the **YAML list**:

```yaml
base_model:
  - Laxhar/noobai-XL-1.0
  - OnomaAIResearch/Illustrious-XL-v2.0
```

### 6. How the Hub Auto-Classifies Relation Types

The Hub's backend classifies uploaded models into the four relation types based on **heuristic file analysis**:

| Detected Pattern | Classification | What Triggers It |
|-----------------|----------------|------------------|
| `adapter_config.json` (+ small `.safetensors`) | `adapter` | PEFT/LoRA/DoRA adapter weights |
| `.gguf` / `.awq` / `.gptq.q4` / `hqq` in files | `quantized` | Quantized format detected in file list |
| `merge` tag + mergekit config + multiple `base_model` entries | `merge` | Multiple parents declared; merge tag present |
| Standard model files (`.safetensors`, `.bin`) | `finetune` | Full weight files, no quantization/adapter markers |
| No `base_model` declared | — (no relation) | Standalone model, no dependency tracking |

**Verified:** The Hub correctly classified `bartowski/gemma-2-2b-it-GGUF` as `quantized` (was picked up by `filter='base_model:quantized:...'`) and `John6666/one-obsession-17-red-sdxl` as `merge` (multiple base_model entries + merge tag).

### 7. Advanced Discovery Patterns

#### 7.1 Building a Full Dependency Chain

To traverse a model's complete ancestry:

```python
from huggingface_hub import HfApi
api = HfApi()

def get_ancestry(model_id: str, max_depth: int = 5) -> list[dict]:
    """Get full ancestry chain from child to root base model."""
    chain = []
    current = model_id
    for _ in range(max_depth):
        info = api.model_info(current, expand=['baseModels'])
        if not info.base_models:
            break
        relation = info.base_models['relation']
        parents = info.base_models['models']
        if not parents:
            break
        # Take the first parent (primary)
        parent_id = parents[0]['id']
        chain.append({'child': current, 'parent': parent_id, 'relation': relation})
        current = parent_id
    return chain

# Example
chain = get_ancestry('bartowski/gemma-2-2b-it-GGUF')
for link in chain:
    print(f"  {link['child']} ({link['relation']}) → {link['parent']}")
# bartowski/gemma-2-2b-it-GGUF (quantized) → google/gemma-2-2b-it
# google/gemma-2-2b-it (finetune) → google/gemma-2-2b
```

#### 7.2 Finding Children by Type

Use the type-specific tag prefix to filter by relation:

```python
# Find ALL quantized versions of a model
quantized_versions = list(api.list_models(
    filter='base_model:quantized:google/gemma-2-2b-it',
    sort='downloads',
    limit=20
))
print(f"Quantized variants: {len(quantized_versions)}")
for m in quantized_versions:
    print(f"  {m.modelId} — {m.downloads} downloads")

# Find adapter (LoRA) variants
adapters = list(api.list_models(
    filter='base_model:adapter:google/gemma-2-2b-it',
    sort='downloads',
    limit=20
))
print(f"Adapter variants: {len(adapters)}")
```

**Important caveat:** The generic `filter='base_model:X'` returns children of ALL relation types. To get children of a specific type, ALWAYS use the type-specific tag prefix `base_model:{relation}:X`.

#### 7.3 Ecosystem Discovery — Complete Model Profile

Get a comprehensive view of a model's position in the Hub ecosystem:

```python
def model_ecosystem(model_id: str) -> dict:
    """Get a complete ecosystem profile for a model."""
    api = HfApi()
    info = api.model_info(model_id, expand=['childrenModelCount', 'spaces', 'cardData'])
    
    profile = {
        'id': model_id,
        'children': info.children_model_count,
        'num_spaces': len(info.spaces) if info.spaces else 0,
        'pipeline_tag': info.pipeline_tag,
        'downloads': info.downloads,
        'likes': info.likes,
    }
    
    # Get top most-downloaded children
    if info.children_model_count:
        total_children = sum(info.children_model_count.values())
        if total_children > 0:
            top_children = list(api.list_models(
                filter=f'base_model:{model_id}',
                sort='downloads',
                limit=5
            ))
            profile['top_children'] = [
                {'id': m.modelId, 'downloads': m.downloads} for m in top_children
            ]
    
    return profile

# Usage
ecosystem = model_ecosystem('google/gemma-2-2b-it')
print(ecosystem)
# {'id': 'google/gemma-2-2b-it', 'children': {'adapter': 476, 'merge': 19, ...}, ...}
```

### 8. Edge Cases & Limitations

1. **children_model_count vs actual list_models()** — The count from `expand=['childrenModelCount']` is the authoritative total. `list_models(filter='base_model:X')` may return fewer results due to pagination, timing, or filter granularity. Always use the count for overview, list_models for detailed iteration.

2. **Cross-org dependencies** — Children can be in any org. `bartowski/gemma-2-2b-it-GGUF` is a child of `google/gemma-2-2b-it` across different accounts. The dependency system is cross-org.

3. **Recursive children** — A child can itself be a parent. `google/gemma-2-2b-it` has children; those children can have children. The Hub counts only immediate children in `children_model_count`.

4. **Dataset repo types** — Only **models** have the `base_model` dependency system. Datasets and Spaces do NOT participate in this relationship tracking.

5. **Max spaces limit** — The `spaces` expansion returns at most 100 entries (API default pagination limit). For models used by 100+ Spaces, use the `/api/models/{id}` endpoint with pagination.

6. **Missing card_data.base_model** — Some models have tags and `base_models` populated even when `card_data` is empty. The Hub can infer relationships from file structure alone (e.g., a repo with only `.gguf` files pointing to a specific base is classified as quantized).

### 9. Quick Reference — API Patterns

| Goal | Code |
|------|------|
| Get children count | `api.model_info(id, expand=['childrenModelCount']).children_model_count` |
| Get parent info | `api.model_info(id, expand=['baseModels']).base_models` |
| List all children | `api.list_models(filter='base_model:X')` |
| List quantized children | `api.list_models(filter='base_model:quantized:X')` |
| List finetune children | `api.list_models(filter='base_model:finetune:X')` |
| List adapter children | `api.list_models(filter='base_model:adapter:X')` |
| List merge children | `api.list_models(filter='base_model:merge:X')` |
| Find Spaces using model | `api.model_info(id, expand=['spaces']).spaces` |
| Check card data base_model | `api.model_info(id, expand=['cardData']).card_data.base_model` |
| Get combined profile | `api.model_info(id, expand=['childrenModelCount','spaces','baseModels','cardData'])` |

### Sources (v2 updates)
- Live API testing against `huggingface.co/api/models` (2026-07-25): `google/gemma-2-2b`, `google/gemma-2-2b-it`, `bartowski/gemma-2-2b-it-GGUF`, `MaziyarPanahi/gemma-2-2b-it-GGUF`, `mlx-community/Llama-3.2-3B-Instruct-4bit`, `John6666/one-obsession-17-red-sdxl`, `bert-base-uncased`
- huggingface_hub v1.24.0+ source code — `HfApi.model_info()`, `HfApi.list_models()`, `ModelInfo` dataclass
- HF Hub API docs: https://huggingface.co/docs/hub/en/api
- hf.co/ model pages for inspected models
