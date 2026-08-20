---
name: SakJules-SakThai-hf-hub-pipeline-tags-model-card-enrichment
description: Hugging Face pipeline tags taxonomy (53 canonical tags, verified from pipelines.ts),
  model card YAML metadata enrichment, subtask classification system, and batch-update
  workflows via REST API PATCH and ModelCard.push_to_hub
...
---

# HF Hub Pipeline Tags & Model Card Enrichment

**Skill:** Enriching Hugging Face model cards with proper pipeline tags, metadata (license, library_name, tags, datasets, language), and batch-updating across multiple model repos using the `huggingface_hub` Python API.

## Overview

Every model on the Hugging Face Hub can have structured YAML frontmatter in its `README.md` (the model card). The most impactful field is `pipeline_tag`, which:

1. Determines which **inference widget** appears on the model page
2. Enables **search filtering** by task on the Hub
3. Controls **automatic pipeline selection** in `pipeline()` and Inference Client
4. Affects **Inference Endpoints** routing

## Pipeline Tag Taxonomy (53 canonical tags)

Source: `huggingface.js/packages/tasks/src/pipelines.ts` — the canonical source of truth.

### NLP (15 tags)
| Pipeline Tag | Display Name | Notes |
|---|---|---|
| `text-classification` | Text Classification | 17 subtasks (sentiment, NLI, hate-speech, etc.) |
| `token-classification` | Token Classification | 6 subtasks (NER, POS, parsing, etc.) |
| `table-question-answering` | Table Question Answering | |
| `question-answering` | Question Answering | 3 subtasks (extractive, open-domain, closed-domain) |
| `zero-shot-classification` | Zero-Shot Classification | |
| `feature-extraction` | Feature Extraction | |
| `text-generation` | Text Generation | 12 subtasks including `conversational` |
| `fill-mask` | Fill-Mask | |
| `sentence-similarity` | Sentence Similarity | |
| `translation` | Translation | |
| `summarization` | Summarization | 2 subtasks (news-articles, headline-generation) |
| `table-to-text` | Table to Text | Not shown in /models filter |
| `multiple-choice` | Multiple Choice | Not shown in /models filter |
| `text-ranking` | Text Ranking | |
| `text-retrieval` | Text Retrieval | Not shown in /models filter |

> **Note:** `conversational` is NOT a pipeline tag — it's a `WidgetType` alias for backward compatibility and a subtask of `text-generation`. See `references/hf-learnings.md` for the complete subtask taxonomy.

### Audio (6 tags)
| Pipeline Tag | Display Name | Notes |
|---|---|---|
| `text-to-speech` | Text-to-Speech | |
| `text-to-audio` | Text-to-Audio | |
| `automatic-speech-recognition` | Automatic Speech Recognition | 1 subtask |
| `audio-to-audio` | Audio-to-Audio | 1 subtask (audio-source-separation) |
| `audio-classification` | Audio Classification | 3 subtasks |
| `voice-activity-detection` | Voice Activity Detection | |

### Computer Vision (19 tags)
| Pipeline Tag | Display Name | Notes |
|---|---|---|
| `depth-estimation` | Depth Estimation | |
| `image-classification` | Image Classification | 3 subtasks |
| `object-detection` | Object Detection | 2 subtasks (face-detection, object-detection) |
| `image-segmentation` | Image Segmentation | 3 subtasks (instance, panoptic, semantic) |
| `text-to-image` | Text-to-Image | |
| `image-to-text` | Image-to-Text | 3 subtasks (captioning, text-recognition, document-export) |
| `image-to-image` | Image-to-Image | |
| `image-to-video` | Image-to-Video | |
| `unconditional-image-generation` | Unconditional Image Generation | |
| `video-classification` | Video Classification | |
| `text-to-video` | Text-to-Video | |
| `zero-shot-image-classification` | Zero-Shot Image Classification | |
| `mask-generation` | Mask Generation | |
| `zero-shot-object-detection` | Zero-Shot Object Detection | |
| `text-to-3d` | Text-to-3D | |
| `image-to-3d` | Image-to-3D | |
| `image-feature-extraction` | Image Feature Extraction | |
| `keypoint-detection` | Keypoint Detection | 1 subtask (pose-estimation) |
| `video-to-video` | Video-to-Video | |

### Multimodal (9 tags)
| Pipeline Tag | Display Name | Notes |
|---|---|---|
| `audio-text-to-text` | Audio-Text-to-Text | |
| `image-text-to-text` | Image-Text-to-Text | |
| `image-text-to-image` | Image-Text-to-Image | |
| `image-text-to-video` | Image-Text-to-Video | |
| `visual-question-answering` | Visual Question Answering | 1 subtask |
| `document-question-answering` | Document Question Answering | 1 subtask |
| `video-text-to-text` | Video-Text-to-Text | |
| `visual-document-retrieval` | Visual Document Retrieval | |
| `any-to-any` | Any-to-Any | 1 subtask |

### Tabular (4 tags)
| Pipeline Tag | Display Name | Notes |
|---|---|---|
| `tabular-classification` | Tabular Classification | 2 subtasks |
| `tabular-regression` | Tabular Regression | 1 subtask |
| `tabular-to-text` | Tabular to Text | 3 subtasks |
| `time-series-forecasting` | Time Series Forecasting | 2 subtasks |

### Reinforcement Learning (1 tag)
| Pipeline Tag | Display Name | Notes |
|---|---|---|
| `reinforcement-learning` | Reinforcement Learning | 1 subtask |

### Graph & Other (1 tag)
| Pipeline Tag | Display Name | Notes |
|---|---|---|
| `graph-ml` | Graph Machine Learning | |

## ModelCardData Fields Reference

Available via `huggingface_hub.repocard_data.ModelCardData`:

| Field | Type | Description | Example |
|---|---|---|---|
| `pipeline_tag` | `str \| None` | One of 53 canonical pipeline tags | `"text-generation"` |
| `library_name` | `str \| None` | Framework/library used | `"transformers"`, `"sentence-transformers"` |
| `license` | `str \| None` | SPDX license identifier | `"apache-2.0"`, `"mit"`, `"cc-by-4.0"` |
| `license_name` | `str \| None` | Custom license name (when license="other") | `"My Custom License"` |
| `license_link` | `str \| None` | URL for custom license | `"https://example.com/license"` |
| `tags` | `list[str]` | Arbitrary tags for search/discovery | `["sakthai", "tool-use", "function-calling"]` |
| `language` | `list[str]` | ISO 639 codes | `["en"]`, `["th", "en"]` |
| `datasets` | `list[str]` | Dataset repos used for training | `["Nanthasit/sakthai-combined-v6"]` |
| `metrics` | `list[str]` | Evaluation metrics | `["accuracy", "f1"]` |
| `base_model` | `str \| list[str]` | Base model(s) this was fine-tuned from | `"Qwen/Qwen2.5-1.5B"` |
| `model_name` | `str \| None` | Display name | `"SakThai Context 1.5B"` |
| `eval_results` | `list[EvalResult]` | Structured evaluation results | See `EvalResult` dataclass |

## Batch Update Workflow

Update model card metadata across multiple repos without touching the markdown body.

> **Note:** `HfApi.metadata_update()` does NOT exist in `huggingface_hub` (v1.24.0). Use the Hub REST API `PATCH` endpoint for metadata-only updates, or upload a full `README.md` for structural changes.

### Pattern A: REST API PATCH (Metadata-Only, Fastest)

```python
import requests
from huggingface_hub import HfApi

api = HfApi()
token = api.token
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {token}"})

# Update just the pipeline tag
session.patch(
    "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-tools",
    json={"pipeline_tag": "text-generation"},
)

# Update multiple fields at once
session.patch(
    "https://huggingface.co/api/models/Nanthasit/sakthai-context-1.5b-tools",
    json={
        "pipeline_tag": "text-generation",
        "library_name": "transformers",
        "license": "apache-2.0",
        "tags": ["sakthai", "tool-use", "function-calling", "deepseek"],
        "language": ["en"],
        "datasets": ["Nanthasit/sakthai-combined-v6"],
    },
)
```

### Pattern B: Full Card Upload (for structural changes + metadata)

```python
from huggingface_hub import HfApi, ModelCard, ModelCardData

api = HfApi()

# Using ModelCardData for structured metadata
card_data = ModelCardData(
    language="en",
    license="apache-2.0",
    library_name="transformers",
    pipeline_tag="text-generation",
    tags=["sakthai", "tool-use", "function-calling"],
    datasets=["Nanthasit/sakthai-combined-v6"],
    base_model="Qwen/Qwen2.5-1.5B",
)

card = ModelCard.from_template(
    card_data,
    template_path=None,  # Use default template
)
card.push_to_hub("Nanthasit/sakthai-context-1.5b-tools")
```

### Full Card Rewrite (for structural changes)

When you need to change both metadata AND the markdown body:

```python
from huggingface_hub import HfApi

api = HfApi()
card_content = """---
pipeline_tag: text-generation
license: apache-2.0
library_name: transformers
tags:
  - sakthai
  - tool-use
language:
  - en
datasets:
  - Nanthasit/sakthai-combined-v6
base_model: Qwen/Qwen2.5-1.5B
---

# My Model

Description here.
"""

api.upload_file(
    path_or_fileobj=card_content.encode(),
    path_in_repo="README.md",
    repo_id="Nanthasit/sakthai-context-1.5b-tools",
    repo_type="model",
    commit_message="docs: enrich model card with metadata",
)
```

## Reference
- `references/hf-learnings.md` — Deep-dive notes
- Source: `huggingface_hub/repocard_data.py`, `huggingface_hub/hf_api.py`
- Pipeline tags source: https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/pipelines.ts
- HF docs: https://huggingface.co/docs/hub/en/model-cards
