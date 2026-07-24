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
