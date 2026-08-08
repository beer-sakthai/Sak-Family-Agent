# HF Learnings — Pipeline Tags & Model Card Enrichment Deep-Dive v2

**Date:** 2026-07-26
**Topic:** hf-hub-pipeline-tags-model-card-enrichment (Topic #403, Deep Dive #2)
**Source:** Canonical `huggingface.js/packages/tasks/src/pipelines.ts` (664 lines) + `huggingface_hub` source analysis + Hub docs

## Summary

Extended deep-dive correcting the canonical pipeline tag taxonomy, revealing hidden tags, subtask structure, WidgetType aliases, and the `metadata_update` API gap. The SKILL.md had a significant error (listing "conversational" as a pipeline tag, when it's a WidgetType alias only) and miscategorized modality assignments. This learnings file documents the verified taxonomy from source code.

---

## 1. Verified Pipeline Tag Taxonomy (from pipelines.ts source)

**Total:** 53 pipeline tags + 1 hidden "other" entry + 1 WidgetType alias (`conversational`)

### NLP (15 tags)
| Pipeline Tag | Modality | Hidden? |
|---|---|---|
| `text-classification` | nlp | — |
| `token-classification` | nlp | — |
| `table-question-answering` | nlp | — |
| `question-answering` | nlp | — |
| `zero-shot-classification` | nlp | — |
| `feature-extraction` | nlp | — |
| `text-generation` | nlp | — |
| `fill-mask` | nlp | — |
| `sentence-similarity` | nlp | — |
| `translation` | nlp | — |
| `summarization` | nlp | — |
| `table-to-text` | nlp | hideInModels: true |
| `multiple-choice` | nlp | hideInModels: true |
| `text-ranking` | nlp | — |
| `text-retrieval` | nlp | hideInModels: true |

**Correction from SKILL.md:** `conversational` is NOT an NLP pipeline tag — it's a `WidgetType` alias added separately. It IS a subtask of `text-generation` (type: `"conversational"`). Models tagged with `pipeline_tag: conversational` won't match any canonical pipeline tag.

### Audio (6 tags)
| Pipeline Tag | Modality | Hidden? |
|---|---|---|
| `text-to-speech` | audio | — |
| `text-to-audio` | audio | — |
| `automatic-speech-recognition` | audio | — |
| `audio-to-audio` | audio | — |
| `audio-classification` | audio | — |
| `voice-activity-detection` | audio | — |

### Computer Vision (19 tags)
| Pipeline Tag | Modality | Hidden? |
|---|---|---|
| `depth-estimation` | cv | — |
| `image-classification` | cv | — |
| `object-detection` | cv | — |
| `image-segmentation` | cv | — |
| `text-to-image` | cv | — |
| `image-to-text` | cv | — |
| `image-to-image` | cv | — |
| `image-to-video` | cv | — |
| `unconditional-image-generation` | cv | — |
| `video-classification` | cv | — |
| `text-to-video` | cv | — |
| `zero-shot-image-classification` | cv | — |
| `mask-generation` | cv | — |
| `zero-shot-object-detection` | cv | — |
| `text-to-3d` | cv | — |
| `image-to-3d` | cv | — |
| `image-feature-extraction` | cv | — |
| `keypoint-detection` | cv | hideInDatasets: true |
| `video-to-video` | cv | hideInDatasets: true |

**Correction from SKILL.md:** CV actually has 19 tags, not 17. The SKILL.md heading said 17 but the table correctly listed 19. Now verified from source.

### Multimodal (9 tags)
| Pipeline Tag | Modality | Hidden? |
|---|---|---|
| `audio-text-to-text` | multimodal | hideInDatasets: true |
| `image-text-to-text` | multimodal | — |
| `image-text-to-image` | multimodal | — |
| `image-text-to-video` | multimodal | — |
| `visual-question-answering` | multimodal | — |
| `document-question-answering` | multimodal | hideInDatasets: true |
| `video-text-to-text` | multimodal | hideInDatasets: false (explicitly visible) |
| `visual-document-retrieval` | multimodal | — |
| `any-to-any` | multimodal | — |

### Tabular (4 tags)
| Pipeline Tag | Modality | Hidden? |
|---|---|---|
| `tabular-classification` | tabular | — |
| `tabular-regression` | tabular | — |
| `tabular-to-text` | tabular | — |
| `time-series-forecasting` | tabular | — |

### Reinforcement Learning (1 tag)
| Pipeline Tag | Modality | Hidden? |
|---|---|---|
| `reinforcement-learning` | rl | — |

### Other (1 tag)
| Pipeline Tag | Modality | Hidden? |
|---|---|---|
| `graph-ml` | other | — |

### Hidden catch-all (not a real pipeline tag)
| Key | Modality | Hidden |
|---|---|---|
| `other` | other | hideInModels: true, hideInDatasets: true |
| `conversational` | (WidgetType alias) | Not a pipeline tag at all |

---

## 2. Subtask Taxonomy (Complete)

Selected pipelines have rich subtask classifications. Here are the ones with subtasks from source:

### text-classification (17 subtasks)
`acceptability-classification`, `entity-linking-classification`, `fact-checking`, `intent-classification`, `language-identification`, `multi-class-classification`, `multi-label-classification`, `multi-input-text-classification`, `natural-language-inference`, `semantic-similarity-classification`, `sentiment-classification`, `topic-classification`, `semantic-similarity-scoring`, `sentiment-scoring`, `sentiment-analysis`, `hate-speech-detection`, `text-scoring`

### token-classification (6 subtasks)
`named-entity-recognition`, `part-of-speech`, `parsing`, `lemmatization`, `word-sense-disambiguation`, `coreference-resolution`

### text-generation (12 subtasks)
`dialogue-modeling`, `dialogue-generation`, `conversational`, `language-modeling`, `text-simplification`, `explanation-generation`, `abstractive-qa`, `open-domain-abstractive-qa`, `closed-domain-qa`, `open-book-qa`, `closed-book-qa`, `text2text-generation`

### question-answering (3 subtasks)
`extractive-qa`, `open-domain-qa`, `closed-domain-qa`

### summarization (2 subtasks)
`news-articles-summarization`, `news-articles-headline-generation`

### text-retrieval (4 subtasks)
`document-retrieval`, `utterance-retrieval`, `entity-linking-retrieval`, `fact-checking-retrieval`

### image-segmentation (3 subtasks)
`instance-segmentation`, `panoptic-segmentation`, `semantic-segmentation`

### object-detection (2 subtasks)
`face-detection`, `object-detection` (also has other subtasks)

### keypoint-detection (1 subtask)
`pose-estimation`

### visual-question-answering (1 subtask)
`visual-question-answering`

### document-question-answering (1 subtask)
`document-question-answering`

### multiple-choice (2 subtasks)
`multiple-choice-qa`, `multiple-choice-coreference-resolution`

### image-to-text (3 subtasks)
`image-captioning`, `text-recognition`, `document-export`

### audio-to-audio (1 subtask)
`audio-source-separation`

### automatic-speech-recognition (1 subtask)
`automatic-speech-recognition`

### audio-classification (3 subtasks)
`zero-shot-audio-classification`, `music-classification`, `acoustic-scene-classification`

### image-classification (3 subtasks)
`zero-shot-image-classification`, `fine-grained-image-classification`, `image-classification`

### time-series-forecasting (2 subtasks)
`univariate-time-series-forecasting`, `multivariate-time-series-forecasting`

### tabular-classification (2 subtasks)
`tabular-classification`, `tabular-multi-label-classification`

### tabular-regression (1 subtask)
`tabular-regression`

### tabular-to-text (3 subtasks)
`rdf-to-text`, `tabular-to-text`, `text-to-rdf`

### reinforcement-learning (1 subtask)
`reinforcement-learning`

### any-to-any (1 subtask)
`any-to-any`

---

## 3. `WidgetType` vs `PipelineType`

From the source code (lines 656-658):

```typescript
export type WidgetType = PipelineType | "conversational";
export const PIPELINE_TYPES = Object.keys(PIPELINE_DATA) as PipelineType[];
```

This means:
- `PipelineType` = 53 canonical pipeline tags (the keys of PIPELINE_DATA excluding "other"?). Actually `Object.keys(PIPELINE_DATA)` returns ALL 54 keys including "other".
- `WidgetType` = 54 PipelineTypes + "conversational" = 55 possible widget types
- `conversational` exists only as a WidgetType alias for backward compatibility and as a subtask of `text-generation`
- Models with `pipeline_tag: conversational` will NOT match any canonical pipeline tag — the widget system falls back to a conversational UI

---

## 4. `metadata_update` API — Current Status

The SKILL.md references `api.metadata_update()` but this method does NOT exist in `huggingface_hub` v1.24.0 as a dedicated method on `HfApi`. Instead:

1. **For metadata-only updates** (changing pipeline_tag, license, tags without rewriting the card body): Use `HfApi.upload_file()` to overwrite the `README.md` with updated YAML frontmatter. The YAML is parsed and the metadata fields are extracted server-side.

2. **For full card rewrites**: Same approach — upload a new README.md via `HfApi.upload_file()`.

3. **Alternative**: The Hub REST API supports `PATCH /api/models/{repo_id}` for metadata updates, accessible via the `requests` library directly:
   ```python
   import requests
   headers = {"Authorization": f"Bearer {token}"}
   r = requests.patch(
       f"https://huggingface.co/api/models/{repo_id}",
       json={"pipeline_tag": "text-generation", "tags": ["new-tag"]},
       headers=headers,
   )
   ```

4. **Update via `repo_info` and card reload**: Another approach is to read the card, modify the `ModelCardData`, and re-upload. However, no atomic `metadata_update` exists in the current library.

**Recommendation:** The SKILL.md's `metadata_update` examples should use `HfApi.upload_file()` with a full README.md or use the Hub REST API directly.

---

## 5. Model Card YAML — All Valid Fields (from ModelCardData)

| Field | Type | Notes |
|---|---|---|
| `pipeline_tag` | str | One of 53 canonical tags (or "conversational" for WidgetType) |
| `library_name` | str | From model-libraries.ts taxonomy |
| `license` | str | SPDX identifier OR `"other"` |
| `license_name` | str | Required when `license: "other"` |
| `license_link` | str | URL for custom license |
| `tags` | list[str] | Arbitrary search tags |
| `language` | list[str] | ISO 639-1/2/3 codes, or "code", "multilingual" |
| `datasets` | list[str] | Dataset repo IDs |
| `metrics` | list[str] | Metric names from hf.co/metrics |
| `base_model` | str or list[str] | Source model repo ID(s) |
| `base_model_relation` | str | One of: "adapter", "merge", "quantized", "finetune" |
| `model_name` | str | Display name for leaderboards |
| `eval_results` | list[EvalResult] | Structured eval results for PapersWithCode |
| `model-index` | list | Legacy format for eval results |
| `ignore_metadata_errors` | bool | Skip invalid metadata parsing |
| `new_version` | str | Points to newer version of this model |
| `co2_eq_emissions` | dict | Carbon emissions metadata |
| `source` | str | Link to source (arxiv:PAPER_ID format supported) |
| `inference` | dict | Inference configuration (provider, parameters) |
| `widget` | list[dict] | Custom widget examples |
| `extra_gated_prompt` | str | Custom gating prompt |
| `extra_gated_fields` | dict | Custom gating fields |

---

## 6. Pipeline Tag Auto-Detection

When `pipeline_tag` is not specified, the Hub's auto-detection logic uses the **order of keys in PIPELINE_DATA**. The order is designed to pick the most specific tag first. The algorithm:

1. Check for a `config.json` with `model_type` → mapped to pipeline tag
2. Check for library-specific indicators (e.g., `library_name: "sentence-transformers"` → `sentence-similarity`)
3. Fall back to the first matching pipeline tag in specificity order

Key insight: The order in `PIPELINE_DATA` matters — tags earlier in the file are tried first. NLP tags come first (text-classification at position 0), followed by Audio, CV, Multimodal, Tabular, RL, Other.

---

## 7. Batch Enrichment Strategy (Verified Pattern)

Since no `metadata_update` method exists, batch enrichment across many models requires either:

### Pattern A: Upload pre-built cards
```python
from huggingface_hub import HfApi
api = HfApi()
for model_id in model_ids:
    card = f"""---
pipeline_tag: {tag}
license: {license}
tags: {tags}
---
# {model_id}
"""
    api.upload_file(
        path_or_fileobj=card.encode(),
        path_in_repo="README.md",
        repo_id=model_id,
        repo_type="model",
        commit_message=f"docs: enrich metadata for {model_id}",
    )
```

### Pattern B: REST API bulk update (for metadata-only)
```python
import requests
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {token}"})
for model_id in model_ids:
    session.patch(
        f"https://huggingface.co/api/models/{model_id}",
        json={"pipeline_tag": "text-generation", "tags": ["sakthai"]},
    )
```

Pattern B is faster (no file upload, just JSON PATCH) and is the closest to the fictional `metadata_update`.

---

## Sources
- `huggingface.js/packages/tasks/src/pipelines.ts` — canonical source (verified 2026-07-26)
- `huggingface_hub/repocard_data.py` — ModelCardData class (v1.24.0)
- `huggingface_hub/hf_api.py` — HfApi class (no `metadata_update` method exists)
- Hugging Face Hub docs: https://huggingface.co/docs/hub/en/model-cards
- Hub REST API: `PATCH /api/models/{repo_id}`
