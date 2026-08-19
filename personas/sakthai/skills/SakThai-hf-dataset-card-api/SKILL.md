---
name: SakThai-hf-dataset-card-api
description: "Complete reference for Hugging Face DatasetCard API \u2014 creating, editing, validating,\
  \ and publishing dataset cards via huggingface_hub"
---

# HF Dataset Card API

Trigger when: user asks about creating dataset cards, DatasetCard/DatasetCardData, dataset README metadata, dataset card templates, pushing dataset metadata to the Hub.

## Key Areas

- **DatasetCardData**: Metadata fields — language, license, task_categories, task_ids, size_categories, annotations_creators, language_creators, multilinguality, source_datasets, config_names, pretty_name
- **DatasetCard**: Card class inherits from RepoCard — init from string, from_template, load from hub/file, save locally, push_to_hub, validate
- **CardData base class**: dict-like access (get/pop/__getitem__/__setitem__), to_dict(), to_yaml()
- **Default template**: Jinja2 template at `huggingface_hub/templates/datasetcard_template.md`

See `references/hf-learnings.md` for the complete deep-dive reference.
