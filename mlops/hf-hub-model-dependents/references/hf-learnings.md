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
