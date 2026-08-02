---
name: SakThai-hf-hub-repocard-system
version: 1.0.0
author: SakThai
license: MIT
description: Programmatic creation, loading, validation, and management of repository cards on the Hugging Face Hub
category: mlops
tags: [huggingface, model-cards, metadata, hub]
---

# HF Hub RepoCard System (huggingface_hub)

**Skill:** Programmatic creation, loading, validation, and management of model/dataset/space cards on the Hugging Face Hub using the `huggingface_hub` library.

## Overview

The RepoCard system in `huggingface_hub` (v1.24.0) provides a full Python API for working with repository cards (README.md files with YAML frontmatter). It supports all three repo types: **models** (`ModelCard`), **datasets** (`DatasetCard`), and **Spaces** (`SpaceCard`).

### Core Classes
- `RepoCard` — Base class for all repo cards. Handles YAML parsing, content management, template rendering, and push-to-hub.
- `ModelCard(RepoCard)` — For model repos. Uses `ModelCardData` metadata.
- `DatasetCard(RepoCard)` — For dataset repos. Uses `DatasetCardData` metadata.
- `SpaceCard(RepoCard)` — For Space repos. Uses `SpaceCardData` metadata.

### Card Data Classes
- `CardData` — Base dict-like metadata container. Supports `to_dict()`, `to_yaml()`, `get()`, `pop()`, dict-style access.
- `ModelCardData(CardData)` — Model-specific fields: `base_model`, `datasets`, `language`, `library_name`, `license`, `pipeline_tag`, `tags`, `metrics`, `eval_results`, `model_name`.
- `DatasetCardData(CardData)` — Dataset-specific fields: `annotations_creators`, `language_creators`, `multilinguality`, `size_categories`, `task_categories`, `task_ids`, `pretty_name`, `config_names`.
- `SpaceCardData(CardData)` — Space-specific fields: `title`, `sdk`, `sdk_version`, `python_version`, `app_file`, `app_port`, `duplicated_from`.

### Key Operations
- `RepoCard(content)` — Parse a card from markdown string
- `RepoCard.load(repo_id_or_path)` — Load from Hub or local file
- `RepoCard.from_template(card_data, **kwargs)` — Create from Jinja template
- `card.push_to_hub(repo_id)` — Validate + upload to Hub
- `card.save(filepath)` — Save locally
- `card.validate()` — Validate against Hub's `/api/validate-yaml` endpoint
- `metadata_update(repo_id, metadata, repo_type)` — Quick metadata update without full card

### Evaluation Results
- `EvalResult` dataclass — Structured evaluation result (task_type, dataset_type, metric_type, metric_value, source_name, etc.)
- `metadata_eval_result()` — Helper to create eval result dict
- Model-index auto-generation from `EvalResult` list via `eval_results_to_model_index()`

### Template System
- Default templates: `modelcard_template.md`, `datasetcard_template.md` (Jinja2)
- Templates receive `card_data.to_yaml()` and any keyword arguments
- Custom templates supported via `template_path` or `template_str`

## Pitfalls

- **Regex find-and-replace on remote cards creates duplicates** — downloading, partial-replacing, and re-uploading multiple times creates duplicate sections and stale headers. Instead: download once with `hf_hub_download`, edit fully in Python, validate locally (check section count), then upload ONE clean version. Never upload partial fixes.
- Avoid pushing partial edits — each push creates a git commit. Multiple partial pushes leave messy history.

## Reference
- Source: `huggingface_hub/repocard.py`, `huggingface_hub/repocard_data.py`
- Model card spec: https://github.com/huggingface/hub-docs/blob/main/modelcard.md
- Docs: https://huggingface.co/docs/hub/en/model-cards
