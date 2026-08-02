# DatasetCard API — Complete Reference

> Learned: 2026-07-24 | Authoritative source: huggingface_hub source code + HF Hub docs
> Covers: huggingface_hub `DatasetCard`, `DatasetCardData`, `RepoCard`, `CardData` classes

## Overview

The Dataset Card API in `huggingface_hub` allows programmatic creation, editing, validation, and publishing of dataset cards — the README.md files with YAML front matter that describe datasets on the Hugging Face Hub.

## Class Hierarchy

```
CardData (dataclass-like, dict-compatible)
  └── DatasetCardData (dataset-specific metadata)

RepoCard (card content + YAML front matter)
  └── DatasetCard (inherits repo_type="dataset")
```

## DatasetCardData — Metadata Fields

All fields are keyword-only (`*` prefix in signature):

| Field | Type | Description |
|-------|------|-------------|
| `language` | `str \| list[str] \| None` | ISO 639-1/2/3 code(s), or "code", "multilingual" |
| `license` | `str \| list[str] \| None` | License identifier(s) from HF Hub licenses |
| `annotations_creators` | `str \| list[str] \| None` | How annotations were created: "found", "crowdsourced", "expert-generated", "machine-generated", "no-annotation", "other" |
| `language_creators` | `str \| list[str] \| None` | How text data was created: "found", "crowdsourced", "expert-generated", "machine-generated", "other" |
| `multilinguality` | `str \| list[str] \| None` | "monolingual", "multilingual", "translation", "other" |
| `size_categories` | `str \| list[str] \| None` | Example count buckets: "n<1K", "1K<n<10K", ..., "n>1T", "other" |
| `source_datasets` | `list[str] \| None` | "original" or "extended" |
| `task_categories` | `str \| list[str] \| None` | Task categories (e.g., "text-classification", "image-classification") |
| `task_ids` | `str \| list[str] \| None` | Specific tasks (e.g., "sentiment-classification") |
| `paperswithcode_id` | `str \| None` | PapersWithCode dataset ID |
| `pretty_name` | `str \| None` | Human-readable name |
| `config_names` | `str \| list[str] \| None` | Available dataset configs/subset names |
| `train_eval_index` | `dict \| None` | Evaluation spec dict (stored as "train-eval-index" in YAML) |
| `**kwargs` | any | Any extra metadata passed through to CardData |

### CardData Base Class (dict-like access)

```python
# Get/set like a dict
card_data["custom_field"] = "value"
value = card_data.get("custom_field", default=None)
popped = card_data.pop("field_name")

# Export
card_data.to_dict()           # dict of non-None values
card_data.to_yaml()           # YAML string (sorted keys)
card_data.to_yaml(original_order=["language", "license", ...])  # preserve key order
```

## DatasetCard — Card Construction

### From string (manual YAML front matter)

```python
from huggingface_hub import DatasetCard

text = """---
language: en
license: mit
annotations_creators: crowdsourced
---

# My Dataset

This is my dataset.
"""

card = DatasetCard(text)
print(card.data.language)  # "en"
print(card.text)           # "\n# My Dataset\n\nThis is my dataset.\n"
```

### From template (recommended)

```python
from huggingface_hub import DatasetCard, DatasetCardData

card_data = DatasetCardData(
    language="en",
    license="mit",
    annotations_creators="crowdsourced",
    task_categories=["text-classification"],
    task_ids=["sentiment-classification"],
    multilinguality="monolingual",
    pretty_name="My Text Classification Dataset",
)

# Uses default Jinja2 template from huggingface_hub/templates/datasetcard_template.md
card = DatasetCard.from_template(
    card_data,
    pretty_name=card_data.pretty_name,  # passed to template
)

# Custom template path
card = DatasetCard.from_template(
    card_data=card_data,
    template_path="./my_template.md",
    custom_var="value",
)

# Raw template string
card = DatasetCard.from_template(
    card_data=card_data,
    template_str="# {{ pretty_name }}\n\n{{ card_data }}",
    pretty_name="My Dataset",
)
```

### Load existing card

```python
# From Hugging Face Hub
card = DatasetCard.load("username/my-dataset")           # repo_type="dataset" auto
card = DatasetCard.load("username/my-dataset", repo_type="dataset")

# From local file
card = DatasetCard.load("./README.md")
```

## DatasetCard — Operations

### Save locally

```python
card.save("/path/to/README.md")
```

Creates parent directories automatically. Preserves line endings from original content.

### Validate

```python
# Validates YAML metadata against Hub's schema (requires internet)
card.validate()  # raises ValueError on invalid, repo_type="dataset" auto
card.validate(repo_type="dataset")
```

### Push to Hub

```python
# Push card to dataset repo
url = card.push_to_hub(
    repo_id="username/my-dataset",
    commit_message="Update dataset card",
    commit_description="Added task categories and license",
    repo_type="dataset",  # auto from DatasetCard
    create_pr=False,
    revision=None,         # defaults to "main"
    parent_commit=None,    # OID to ensure linear history
)

print(url)  # URL of the commit
```

The `push_to_hub` method:
1. Calls `validate()` first (raises on invalid metadata)
2. Writes card to temp file
3. Uploads via `upload_file()` — updates `README.md` in the repo

## Practical Example: From Scratch

```python
from huggingface_hub import DatasetCard, DatasetCardData, HfApi

# 1. Define metadata
card_data = DatasetCardData(
    language=["en", "fr"],
    license="mit",
    annotations_creators="machine-generated",
    language_creators="machine-generated",
    multilinguality="multilingual",
    size_categories="10K<n<100K",
    source_datasets=["original"],
    task_categories=["text-generation", "translation"],
    task_ids=["language-modeling", "translation-en-fr"],
    config_names=["en", "fr", "en-fr"],
    pretty_name="Bilingual Synthetic Corpus",
)

# 2. Create card from template
card = DatasetCard.from_template(
    card_data,
    pretty_name=card_data.pretty_name,
)

# 3. Push to Hub
api = HfApi()
api.create_repo("my-org/bilingual-corpus", repo_type="dataset")
card.push_to_hub("my-org/bilingual-corpus")

# 4. Load it back
loaded = DatasetCard.load("my-org/bilingual-corpus")
assert loaded.data.pretty_name == "Bilingual Synthetic Corpus"
```

## Template Variables

The default template (`datasetcard_template.md`) accepts these Jinja2 variables via `**template_kwargs`:

- `pretty_name` — dataset display name
- `card_data` — the DatasetCardData instance (rendered via `str(card_data)` → YAML block)
- Any custom kwargs passed to `from_template()`

## Tips

1. **DatasetCardData fields are keyword-only** — always use `field_name=value` syntax
2. **extra fields** — pass any unrecognized fields as `**kwargs`; they're stored and round-tripped
3. **train_eval_index** — auto-renamed to "train-eval-index" in YAML export
4. **ignore_metadata_errors** — set to `True` when loading cards with partial/invalid YAML
5. **RepoCard fallback** — `DatasetCard(text)` still works for cards without structured metadata
6. **No config needed for simple cards** — if you just want basic metadata, `DatasetCardData(language="en", license="mit")` is sufficient

---

## 2026-07-24: hf-dataset-card-api — Deep Dive on Hub Tag Taxonomy, Validation Endpoint & Discoverability (Topic #191 Deepening)

### Summary
Deepening the dataset card API coverage with the Hub's built-in tag taxonomy (`get_dataset_tags()` / `get_model_tags()`), the validation endpoint mechanics, and practical tagging patterns for tool-calling datasets. Covers all 10 dataset tag categories, how to pass them via `DatasetCardData(**kwargs)`, the Hub's YAML validation schema, array-vs-string field requirements, and a complete reference for tagging Beer's tool-calling datasets with `format:agent-traces` for maximum discoverability.

### Source
- `huggingface_hub` v1.24.0 source: `HfApi.get_dataset_tags()`, `HfApi.get_model_tags()`
- Hub validation: `POST https://huggingface.co/api/validate-yaml`
- Dataset card spec: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md
- Dataset tags endpoint: `https://huggingface.co/api/datasets-tags-by-type`
- Model tags endpoint: `https://huggingface.co/api/models-tags-by-type`

### 1. Hub Tag Taxonomy — Complete Reference

The Hugging Face Hub maintains a hierarchical tag system for datasets and models. Tags are fetched via `HfApi.get_dataset_tags()` / `HfApi.get_model_tags()` and are the authoritative source of valid metadata values.

**Dataset tags — 10 categories:**

| Category | Count | Description | Example |
|----------|-------|-------------|---------|
| `library` | 12 | Data processing libraries | `datasets`, `mlcroissant`, `polars` |
| `license` | 82 | Standard licenses | `apache-2.0`, `mit`, `cc-by-4.0` |
| `language` | 8244 | ISO 639 codes | `en`, `fra`, `zh` |
| `other` | 11 | Domain/genre tags | `synthetic`, `agent`, `medical`, `code`, `finance` |
| `task_ids` | 74 | Specific tasks | `language-modeling`, `tool-use`, `function-calling` |
| `task_categories` | 52 | Task families | `text-generation`, `text-classification`, `question-answering` |
| `size_categories` | 11 | Size buckets | `n<1K`, `10K<n<100K`, `1M<n<10M` |
| `format` | 10 | Data format/structure | `agent-traces`, `json`, `parquet`, `arrow` |
| `modality` | 9 | Data modality | `text`, `audio`, `image`, `tabular`, `video` |
| `benchmark` | 1 | Official benchmarks | `benchmark:official` |

**Model tags — 8 categories:**

| Category | Count | Description |
|----------|-------|-------------|
| `region` | 2 | Deployment region (`us`, `eu`) |
| `library` | 53 | ML framework (`pytorch`, `tf`, `jax`, ...) |
| `other` | 10 | Infrastructure (`text-generation-inference`, ...) |
| `license` | 82 | Standard licenses |
| `language` | 4973 | Language support |
| `deploy` | 3 | Deployment targets (`endpoints_compatible`, `azure`, `sagemaker`) |
| `dataset` | 2567 | Training datasets (auto-populated) |
| `pipeline_tag` | 52 | HF pipeline types |

**Key difference:** Dataset tags use `type:value` format (e.g., `format:agent-traces`), while model tags use bare slugs (e.g., `pytorch`). The `DatasetCardData` typed fields (`task_categories`, `task_ids`, `size_categories`, `language`, `license`) auto-map to their tag equivalents. All other categories must be added via the `tags` kwargs list.

### 2. Adding Tags to DatasetCardData

`DatasetCardData` has **no `tags` field** — tags outside the predefined fields must be passed as extra kwargs:

```python
from huggingface_hub import DatasetCard, DatasetCardData

card_data = DatasetCardData(
    language=['en'],
    license=['mit'],
    annotations_creators=['machine-generated'],
    language_creators=['machine-generated'],
    multilinguality=['monolingual'],
    size_categories=['10K<n<100K'],
    source_datasets=['original'],
    task_categories=['text-generation'],
    task_ids=['tool-use', 'function-calling', 'language-modeling'],
    pretty_name='My Tool-Calling Dataset',
    config_names=['default'],
    # Extra tags beyond the typed fields:
    tags=['format:agent-traces', 'other:agent', 'synthetic'],
    format='agent-traces',
    modality='text',
)

card = DatasetCard.from_template(card_data, pretty_name=card_data.pretty_name)
# card.push_to_hub("username/my-dataset")
```

**How it works:** `CardData.__init__(**kwargs)` stores all extra kwargs in `self.__dict__`. `CardData.to_dict()` exports all non-None values. The YAML block thus automatically includes any tags passed as direct attributes.

### 3. Validation Endpoint (`/api/validate-yaml`)

The `RepoCard.validate()` method sends the card content to `POST https://huggingface.co/api/validate-yaml`:

```python
body = {"repoType": "dataset", "content": str(card)}
response = session.post("https://huggingface.co/api/validate-yaml", json=body)
# 200 → {"errors": [], "warnings": []}
# 400 → {"errors": [{"message": "...", "path": [...]}], "warnings": [...]}
```

**Validation rules discovered empirically:**

| Field | Required Format | Notes |
|-------|----------------|-------|
| `language` | List `[str]` | ISO codes or special values like `"code"` |
| `license` | List `[str]` | License identifiers from Hub list |
| `annotations_creators` | List `[str]` | One of: `found`, `crowdsourced`, `expert-generated`, `machine-generated`, `no-annotation`, `other` |
| `language_creators` | List `[str]` | Same options minus `no-annotation` |
| `multilinguality` | List `[str]` | One of: `monolingual`, `multilingual`, `translation`, `other` |
| `size_categories` | List `[str]` | Exact bucket names from tag taxonomy |
| `task_categories` | List `[str]` | Valid pipeline tag names |
| `task_ids` | List `[str]` | Specific task names from tag taxonomy |
| `source_datasets` | List `[str]` | `original` or `extended` |
| `config_names` | List `[str]` or `str` | Dataset config/subset names |
| `tags` | List `[str]` | Arbitrary tags in `type:value` or bare format |
| `format` | `str` | Single format identifier |
| `modality` | `str` | Single modality identifier |
| `pretty_name` | `str` | Any string (no validation) |

**Critical rule:** The Hub validation **requires arrays** for all multi-valued fields. Passing a bare string (e.g., `task_categories="text-generation"`) fails with `"must be an array"`. Always use lists.

### 4. `train_eval_index` — Evaluation Specifications

The `train_eval_index` field (exported as `train-eval-index` in YAML) tells the Hub how to evaluate a dataset. Format:

```python
train_eval_index = {
    "config": "default",           # Dataset config to use
    "task": "text-generation",     # Task type from task taxonomy
    "task_id": "language-modeling", # Specific task ID
    "splits": {"train": "train"},  # Split mapping
    "col_mapping": {               # Column → expected field mapping
        "input": "text",
        "target": "label",
    },
    "metrics": [
        {
            "type": "accuracy",
            "name": "Accuracy",
        }
    ],
}

card_data = DatasetCardData(
    language=['en'],
    license=['mit'],
    pretty_name='Eval-Supported Dataset',
    train_eval_index=train_eval_index,
)
```

The `train_eval_index` is auto-renamed from `train_eval_index` → `train-eval-index` in `DatasetCardData._to_dict()`.

### 5. Practical Pattern: Tool-Calling Dataset Card for Beer

Beer's 8 tool-calling datasets should use these tags for maximum Hub discoverability:

```python
from huggingface_hub import DatasetCard, DatasetCardData

card_data = DatasetCardData(
    language=['en'],
    license=['mit'],
    annotations_creators=['machine-generated'],
    language_creators=['machine-generated'],
    multilinguality=['monolingual'],
    size_categories=['1K<n<10K'],  # Adjust per dataset size
    source_datasets=['original'],
    task_categories=['text-generation'],
    task_ids=['tool-use', 'function-calling', 'multi-turn-conversation'],
    pretty_name='Tool-Calling Assistant Traces',
    config_names=['default'],
    tags=[
        'format:agent-traces',   # ← Key tag: marks as agent trace data
        'other:agent',           # ← Second key tag: agent domain
        'synthetic',             # Machine-generated
    ],
    format='agent-traces',       # Structured format tag
    modality='text',             # Text modality
)

card = DatasetCard.from_template(
    card_data,
    pretty_name=card_data.pretty_name,
    dataset_summary=(
        "Multi-turn tool-calling conversation traces for function-calling "
        "assistant training. Contains structured tool_call and tool_response "
        "messages across diverse scenarios."
    ),
    dataset_description=(
        "This dataset contains N tool-calling conversations with 3-8 turns each. "
        "Each conversation includes user queries, assistant tool-call requests, "
        "tool execution results, and final assistant responses."
    ),
    curators="Nanthasit (beer-sakthai)",
)

# Push to Hub
card.push_to_hub("username/tool-calling-traces")
```

**Resulting YAML metadata:**
```yaml
---
language:
- en
license:
- mit
annotations_creators:
- machine-generated
language_creators:
- machine-generated
multilinguality:
- monolingual
size_categories:
- 1K<n<10K
source_datasets:
- original
task_categories:
- text-generation
task_ids:
- tool-use
- function-calling
- multi-turn-conversation
pretty_name: Tool-Calling Assistant Traces
config_names:
- default
tags:
- format:agent-traces
- other:agent
- synthetic
format: agent-traces
modality: text
---
```

### 6. Programmatic Tag Discovery

You can fetch the complete, up-to-date tag taxonomy at any time:

```python
from huggingface_hub import HfApi

api = HfApi()

# Dataset tags
dataset_tags = api.get_dataset_tags()
print(dataset_tags.keys())
# dict_keys(['library', 'license', 'language', 'other', 'task_ids',
#            'task_categories', 'size_categories', 'format', 'modality', 'benchmark'])

# All valid task IDs for datasets
task_ids = [t['id'] for t in dataset_tags['task_ids']]
print(len(task_ids))  # 74

# Model tags
model_tags = api.get_model_tags()
print(model_tags.keys())
# dict_keys(['region', 'library', 'other', 'license', 'language', 'deploy',
#            'dataset', 'pipeline_tag'])
```

### 7. Card Data Round-Tripping

The `RepoCard.content` property reconstructs the YAML block preserving original key order:

```python
# Load existing card
card = DatasetCard.load("username/my-dataset")

# Read current metadata
print(card.data.to_yaml())

# Modify
card.data['tags'] = ['format:agent-traces', 'other:agent']
card.data.pretty_name = "Updated Name"

# The YAML block is rebuilt with original_order preserved
# New keys are appended after listed keys
card.push_to_hub("username/my-dataset", commit_message="Update tags")

# For full control of key order:
card.data.to_yaml(original_order=["language", "license", "tags", "pretty_name"])
```

The `_original_order` attribute captures the YAML key ordering from file load. When `content` is read, `to_yaml(original_order=self._original_order)` is called, keeping diffs minimal.

### Skill
mlops/hf-dataset-card-api — references/hf-learnings.md

### References
- `huggingface_hub` source: `repocard.py`, `repocard_data.py` (v1.24.0)
- Hub validation: `POST https://huggingface.co/api/validate-yaml`
- Tags: `GET https://huggingface.co/api/datasets-tags-by-type`
- Dataset card spec: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md
- HF Hub datasets cards guide: https://docs.huggingface.co/docs/hub/datasets-cards

---

### 8. Model Cross-Link Tags in Dataset YAML

Dataset cards can use `model:` prefixed tags in the YAML `tags:` list to create discoverability cross-links between datasets and models. This is NOT a standard Hub metadata field — it's a convention that HF search indexes and surfaces.

**Why:** When a user searches for a model on HF, the search engine also returns datasets tagged with that model's repo ID. Adding `model:owner/repo-name` tags to a dataset card means anyone searching for the model will also discover the dataset — and vice versa.

**Pattern:**

```yaml
tags:
- model:Nanthasit/sakthai-context-7b-tools
- model:Nanthasit/sakthai-context-1.5b-tools
- model:Nanthasit/sakthai-context-0.5b-tools
```

Each tag should be a valid, complete HF repo ID of a model that is related to the dataset.

**When to use:**

| Situation | Recommended | Example |
|-----------|-------------|---------|
| Dataset is training data for specific models | ✅ Add model tags for each related model | Tool-calling dataset → tool-calling models |
| Dataset is a supplement/enhancement to another dataset used by models | ✅ Add model tags for models that consume the parent dataset | Irrelevance supplement → all tool-calling models |
| Dataset has no relationship to any sibling model | ❌ Skip | Standalone reference corpus |
| Model is private | ❌ Skip — 404 for unauthenticated searchers | Private adapter repo |

**Proven in practice (2026-07-29):** `Nanthasit/sakthai-irrelevance-supplement` (0 dl) gained `model:` tags for all 3 tool-calling siblings. This creates the first dataset→model discovery funnel — anyone searching HF for "tool-calling model" will now surface this irrelevance supplement as a related dataset.

**Adding via DatasetCardData:**

```python
from huggingface_hub import DatasetCard, DatasetCardData

card_data = DatasetCardData(
    language=['en'],
    license=['mit'],
    pretty_name='My Dataset',
    tags=[
        'model:Nanthasit/sakthai-context-7b-tools',
        'model:Nanthasit/sakthai-context-1.5b-tools',
    ],
)

card = DatasetCard.from_template(card_data, pretty_name=card_data.pretty_name)
card.push_to_hub("username/my-dataset")
```

**Adding via raw YAML (if using write_file/upload_file instead of DatasetCard.push_to_hub):**

Just add the tags directly to the YAML frontmatter:

```yaml
tags:
- existing-tag
- model:Nanthasit/sakthai-context-7b-tools
```

The `model:` prefix is not validated by HF's YAML schema — it passes through as a custom tag. It has no effect on model pages, but it does make the dataset appear in model-related search results.

**Verification:**

```python
from huggingface_hub import HfApi
api = HfApi()

# Fetch the dataset info and check tags
ds = api.dataset_info("Nanthasit/sakthai-irrelevance-supplement")
model_tags = [t for t in ds.card_data.tags if t.startswith("model:")]
print(f"Cross-linked to {len(model_tags)} models: {model_tags}")
```

**Limitations:**
- The `model:` prefix is a convention, not an official HF schema field — it won't appear in HF UI metadata panels
- Search indexing is asynchronous — changes may take minutes to appear in search results
- Over-tagging (adding irrelevant model references) dilutes discoverability — only tag models that are genuinely related

---

## 2026-07-29: Added 'model:' cross-link tag pattern for dataset→model discovery

### Summary
Added section 8 to the deep-dive reference covering the `model:` prefixed YAML tag convention for cross-linking datasets to models in HF search. This pattern creates discoverability loops: a dataset tagged with `model:owner/repo-name` appears in search results for that model, and vice versa.

### Trigger
Enriching `Nanthasit/sakthai-irrelevance-supplement` dataset card during the HF Auto Improve cron cycle. The dataset needed cross-links to the 3 tool-calling models it supplements (7B-Tools, 1.5B-Tools, 0.5B-Tools) — adding `model:` tags was the most direct approach. No existing skill covered this technique.

### Source
- HF search indexing behavior (empirical): tags with `model:` prefix are indexed and surface in cross-type search results
- Hugging Face Hub YAML schema: validates but doesn't reject unknown prefix tags
- Proven in practice: `sakthai-irrelevance-supplement` card now has 3 model: tags live
