# HF Learnings: Dataset Card Metadata — Complete Reference

## Topic
`hf-hub-dataset-card-metadata-comprehensive-reference`

## Date
2026-07-26

## Sources
- https://huggingface.co/docs/hub/en/datasets-cards — Dataset Cards
- https://github.com/huggingface/hub-docs/blob/main/datasetcard.md — Dataset Card specifications
- https://huggingface.co/docs/hub/en/datasets-manual-configuration — Manual Configuration
- https://huggingface.co/docs/hub/en/repositories-licenses — License identifiers
- https://huggingface.co/api/tasks — Pipeline/task taxonomy
- https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/dataset-libraries.ts — Supported dataset libraries
- https://huggingface.co/docs/hub/en/datasets-gated — Gated datasets
- https://huggingface.co/docs/hub/en/repositories-licenses — License table
- https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md — Dataset card template

---

## Summary

Comprehensive reference on the Hugging Face dataset card YAML metadata system. Dataset cards are `README.md` files in dataset repos with a YAML frontmatter block that controls how the dataset appears on the Hub — including discoverability (tags, licenses, tasks), configuration (splits, subsets, data files), gating (access control), and rich metadata (features, sizes, creators). Proper metadata is essential for making datasets findable, reusable, and correctly documented.

---

## 1. YAML Metadata Frontmatter

Every dataset card starts with a YAML frontmatter block delimited by `---`:

```yaml
---
language:
- en
- fr
license: apache-2.0
pretty_name: "My Dataset"
tags:
- image-classification
- biology
task_categories:
- image-classification
---
```

### Complete Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `language` | Optional | List of ISO 639-1 codes | Languages present in the dataset (e.g., `en`, `fr`, `zh`) |
| `pretty_name` | Recommended | String | Human-readable display name |
| `license` | Recommended | String | License identifier from the HF license table |
| `license_name` | Conditional | String | Custom license name (required if `license: other`) |
| `license_link` | Conditional | String | Path to license file in repo (e.g., `LICENSE`) or URL |
| `license_details` | Legacy | String | Deprecated, use `license_name` + `license_link` instead |
| `tags` | Optional | List of strings | Tags for discoverability — can include modalities, tasks, libraries, arxiv IDs, etc. |
| `task_categories` | Recommended | List of strings | Top-level task categories from the HF pipeline taxonomy |
| `task_ids` | Optional | List of strings | Specific subtask IDs |
| `annotations_creators` | Optional | List of strings | Who created the annotations |
| `language_creators` | Optional | List of strings | Who created the language data |
| `language_details` | Optional | List of BCP-47 codes | Language+region codes (e.g., `fr-FR`, `en-US`) |
| `size_categories` | Recommended | List of strings | Size bucket of the dataset |
| `source_datasets` | Optional | List of strings | Source datasets this was derived from |
| `paperswithcode_id` | Optional | String | Dataset ID on PapersWithCode |
| `extra_gated_fields` | Conditional | List | Custom fields for gated access |
| `extra_gated_prompt` | Conditional | String | Custom access agreement prompt |
| `configs` | Optional | List | Dataset subset/configuration definitions |
| `dataset_info` | Optional | Object | Programmatic metadata (features, splits, sizes) |

---

## 2. License Identifiers

Licenses use string identifiers from the [HF license table](https://huggingface.co/docs/hub/en/repositories-licenses). Using a valid identifier causes the license badge to render on the dataset page.

### Most Common Licenses

| License | Identifier |
|---------|-----------|
| Apache 2.0 | `apache-2.0` |
| MIT | `mit` |
| Creative Commons Zero v1.0 | `cc0-1.0` |
| CC-BY-4.0 | `cc-by-4.0` |
| CC-BY-SA-4.0 | `cc-by-sa-4.0` |
| CC-BY-NC-4.0 | `cc-by-nc-4.0` |
| BSD 3-Clause | `bsd-3-clause` |
| MIT | `mit` |
| Open Data Commons | `odc-by` |
| Open Database License | `odbl` |
| Community Data License Agreement — Permissive v2.0 | `cdla-permissive-2.0` |
| Community Data License Agreement — Sharing v1.0 | `cdla-sharing-1.0` |
| PDDL (Public Domain) | `pddl` |
| GNU GPL v3.0 | `gpl-3.0` |
| GNU LGPL v3.0 | `lgpl-3.0` |
| Llama 3.3 Community | `llama3.3` |
| AI Model License | varies (e.g., `openrail`, `creativeml-openrail-m`) |

### Custom Licenses

If your license isn't in the table, use:
```yaml
license: other
license_name: my-custom-license-1.0
license_link: LICENSE  # or URL to remote license file
```

---

## 3. Task Categories (Pipelines)

Task categories come from the [HF Tasks API](https://huggingface.co/api/tasks). Use these as `task_categories` values.

### All Valid Task Categories

| Category | Use Case |
|----------|----------|
| `text-classification` | Sentiment, spam, etc. |
| `token-classification` | NER, POS tagging |
| `question-answering` | Extractive/abstractive QA |
| `summarization` | Text summarization |
| `translation` | Machine translation |
| `text-generation` | Language modeling, completion |
| `fill-mask` | Masked language modeling |
| `text-to-image` | Image generation from text |
| `image-to-text` | Captioning, OCR |
| `image-classification` | Image classification |
| `image-segmentation` | Semantic/instance segmentation |
| `object-detection` | Object detection |
| `image-to-image` | Image enhancement, style transfer |
| `depth-estimation` | Depth map prediction |
| `video-classification` | Video classification |
| `automatic-speech-recognition` | Speech-to-text |
| `text-to-speech` | TTS |
| `audio-classification` | Audio/sound classification |
| `audio-to-audio` | Audio enhancement, source separation |
| `feature-extraction` | Embeddings |
| `sentence-similarity` | Semantic similarity |
| `text-ranking` | Ranking/search |
| `table-question-answering` | Table QA |
| `tabular-classification` | Tabular classification |
| `tabular-regression` | Tabular regression |
| `visual-question-answering` | VQA |
| `document-question-answering` | Document QA |
| `zero-shot-classification` | Zero-shot |
| `zero-shot-image-classification` | Zero-shot image |
| `text-to-3d` | 3D generation |
| `image-to-3d` | 3D from image |
| `image-text-to-text` | Vision-language |
| `image-text-to-image` | Image editing |
| `image-text-to-video` | Video from text+image |
| `video-text-to-text` | Video QA |
| `any-to-any` | Multimodal any-to-any |
| `mask-generation` | Mask generation |
| `keypoint-detection` | Keypoint detection |
| `reinforcement-learning` | RL |
| `visual-document-retrieval` | Document retrieval |
| `unconditional-image-generation` | Raw image gen |

### Subtask IDs (`task_ids`)

For finer granularity, use subtask names. Examples:
- For `question-answering`: `extractive-qa`, `abstractive-qa`, `open-domain-qa`
- For `image-classification`: `multi-class-image-classification`, `multi-label-image-classification`, `single-label-image-classification`
- For `text-classification`: `sentiment-classification`, `topic-classification`, `language-identification`
- For `token-classification`: `named-entity-recognition`, `part-of-speech-tagging`

---

## 4. Size Categories

Size categories describe the number of elements (rows/examples) in the dataset. Use ranges:

| Identifier | Meaning |
|-----------|---------|
| `n<1K` | Fewer than 1,000 examples |
| `1K<n<10K` | 1,000 to 10,000 |
| `10K<n<100K` | 10,000 to 100,000 |
| `100K<n<1M` | 100,000 to 1 million |
| `1M<n<10M` | 1 million to 10 million |
| `10M<n<100M` | 10 million to 100 million |
| `100M<n<1B` | 100 million to 1 billion |
| `1B<n` | More than 1 billion |

```yaml
size_categories:
- 100K<n<1M
```

---

## 5. Modality Tags

The Hub auto-detects dataset modality from file types, but you can force-set it with tags:

| Tag | Modality |
|-----|----------|
| `3d` | 3D data (point clouds, meshes) |
| `audio` | Audio/speech |
| `geospatial` | GIS, remote sensing |
| `image` | Images |
| `tabular` | Tabular/structured data |
| `text` | Text |
| `timeseries` | Time-series data |
| `video` | Video |

```yaml
tags:
- audio
```

---

## 6. Library Association Tags

Associate libraries that can natively load the dataset. The dataset page shows these as integration badges.

Valid library tags:
- `argilla`
- `dask`
- `datasets` (🤗 Datasets)
- `distilabel`
- `fiftyone`
- `mlcroissant`
- `pandas`
- `webdataset`

```yaml
tags:
- datasets
- pandas
```

To propose a new library, see the [supported libraries source](https://github.com/huggingface/huggingface.js/blob/main/packages/tasks/src/dataset-libraries.ts).

---

## 7. Creators

### Annotations Creators

Who created the annotations/labels:

| Value | Meaning |
|-------|---------|
| `crowdsourced` | Via crowdsourcing (e.g., Mechanical Turk) |
| `expert-generated` | Subject matter experts |
| `found` | Extracted from existing sources |
| `machine-generated` | Automatically generated |
| `no-annotation` | No annotations |

### Language Creators

Who created/collected the language data (same values as annotations creators):

```yaml
annotations_creators:
- crowdsourced
language_creators:
- found
```

---

## 8. Source Datasets

If the dataset is derived from other HF datasets, reference them:

```yaml
source_datasets:
- wikipedia
- laion/laion-2b
- bigcode/the-stack-v2
```

This creates cross-links between dataset pages.

---

## 9. Language Details

For language+region specificity, use BCP-47 codes:

```yaml
language:
- en
- fr
language_details:
- en-US
- fr-FR
```

---

## 10. Configurations (Subsets)

Define named subsets (configs) with custom data files and splits:

```yaml
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.csv
  - split: test
    path: data/test.csv
- config_name: processed
  data_files:
  - split: train
    path: data/processed_train.parquet
```

Each config can define:
- `config_name`: Unique name for the subset
- `data_files`: List of split→path mappings
- Builder-specific parameters

---

## 11. Dataset Info (Programmatic Metadata)

The `dataset_info` block stores machine-readable metadata about features, splits, and sizes. This can be auto-generated using `datasets-cli`:

```yaml
dataset_info:
  features:
    - name: id
      dtype: int32
    - name: text
      dtype: string
    - name: label
      dtype: int32
  config_name: default
  splits:
    - name: train
      num_bytes: 79317110
      num_examples: 87599
    - name: test
      num_bytes: 5842710
      num_examples: 10570
  download_size: 35142551
  dataset_size: 89789763
```

Supporting multiple configs:
```yaml
dataset_info:
  - config_name: config_a
    features: ...
  - config_name: config_b
    features: ...
```

---

## 12. Gated Datasets

Restrict dataset access with gating. Define custom fields users must fill:

```yaml
extra_gated_fields:
- Name: text
- Affiliation: text
- Email: text
- I agree to use this dataset only for non-commercial purposes: checkbox
extra_gated_prompt: "By clicking access, you agree to the dataset terms."
```

See [Gated Datasets](https://huggingface.co/docs/hub/en/datasets-gated) for full docs.

---

## 13. Paper Linking

If the dataset card includes a link to a Paper page (HF paper page or arxiv URL), the Hub auto-extracts the arXiv ID and adds `arxiv:<PAPER_ID>` as a dataset tag:

```markdown
See [the paper](https://arxiv.org/abs/2401.12345) for details.
```

This enables:
- Clicking through to the paper page
- Filtering for other models/datasets citing the same paper

---

## 14. Best Practices

### Completeness checklist
- ✅ `pretty_name` — set a human-readable name
- ✅ `license` — use a valid identifier or `other` + `license_name`/`license_link`
- ✅ `task_categories` — at least one from the HF pipeline taxonomy
- ✅ `size_categories` — accurate size bucket
- ✅ `language` — list all languages
- ✅ `tags` — include modality, library, and discovery tags
- ✅ Source datasets if derived from other HF repos
- ✅ `dataset_info` — auto-generated for programmatic use
- ✅ Paper link if published

### Discoverability
- Use multiple relevant `task_categories` tags
- Add modality tags to match the data type
- Tag libraries that can load your dataset
- Write a good README description alongside metadata
- Use specific `tags` for domain-specific vocab (e.g., `biology`, `medical`, `legal`)

### Common pitfalls
- ❌ Using invalid license string → license won't render as badge
- ❌ Typos in task categories → won't match filter system
- ❌ Missing `---` at start and end → YAML not parsed
- ❌ Duplicate keys in YAML → validation error
- ❌ Too many generic tags → reduces filtering effectiveness

---

## 15. Metadata UI on Hub

When creating or editing a dataset README.md on the Hub web UI, a Metadata UI form helps fill the main metadata fields without writing YAML manually. This is available in the dataset repo editor.

---

## 16. Template

The official dataset card template is available at:
https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md

Use it as a starting point for new dataset cards.
