# HF Learnings — Dataset Card Metadata Complete Reference

## 2026-07-25: hf-hub-dataset-card-metadata-comprehensive-reference — Dataset Card YAML Metadata System (Topic #375 Deepening)

### Summary
Deep-dive into the Hugging Face dataset card YAML metadata system — the structured front matter that goes at the top of dataset `README.md` files. Covers every field in `DatasetCardData`, the validated values for each field (annotations_creators, language_creators, multilinguality, size_categories, source_datasets, task_categories, task_ids), license identifiers (standard + custom), config_names, train_eval_index, the `extra_gated` gating configuration, and the `huggingface_hub` Python API for creating and pushing dataset cards programmatically.

### Key Findings

| Area | Finding |
|------|---------|
| **Location** | Dataset card YAML goes between `---` delimiters at the **top** of `README.md`. Validated at push time by the Hub. |
| **Programmatic API** | `DatasetCardData()` class in `huggingface_hub.repocard_data` — instantiate with keyword args and pass to `DatasetCard.from_template(card_data, ...)`. |
| **Push to Hub** | `card.push_to_hub(repo_id, repo_type="dataset")` — creates or updates README.md with validated YAML. |
| **License system** | Standard identifiers from HF's license catalog + `other` with `license_name` + `license_link` for custom licenses. |
| **Gating** | `extra_gated` section in YAML controls dataset access gating — agreement form, fields, and requirements. |
| **Task taxonomy** | `task_categories` and `task_ids` pull from HF's task taxonomy at `huggingface.js/packages/tasks/src/tasks.ts`. |
| **Size categories** | Controlled vocabulary: `n<1K`, `1K<n<10K`, `10K<n<100K`, `100K<n<1M`, `1M<n<10M`, `10M<n<100M`, `100M<n<1B`, `1B<n<10B`, `10B<n<100B`, `100B<n<1T`, `n>1T`, `other`. |
| **Config names** | `config_names` field lists available dataset configurations (e.g., subsets like `fr`, `en` for multilingual datasets). |

### Dataset Card YAML Fields — Complete Reference

#### Required / Common Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `license` | str or list[str] | License(s) for the dataset | `mit`, `apache-2.0`, `[mit, cc-by-4.0]` |
| `language` | list[str] | ISO 639-1/2/3 codes or special values | `[en, fr, code, multilingual]` |
| `pretty_name` | str | Human-readable name | `"Common Voice Corpus 17.0"` |
| `task_categories` | str or list[str] | High-level task category | `text-classification` |
| `task_ids` | str or list[str] | Specific task | `sentiment-classification` |

#### Descriptive Fields

| Field | Type | Description | Allowed Values |
|-------|------|-------------|----------------|
| `annotations_creators` | str or list[str] | How annotations were created | `found`, `crowdsourced`, `expert-generated`, `machine-generated`, `no-annotation`, `other` |
| `language_creators` | str or list[str] | How text data was created | `found`, `crowdsourced`, `expert-generated`, `machine-generated`, `other` |
| `multilinguality` | str or list[str] | Language coverage | `monolingual`, `multilingual`, `translation`, `other` |
| `size_categories` | str or list[str] | Number of examples | See table above |
| `source_datasets` | list[str] | Original or extended | `original`, `extended` (plus optional dataset IDs) |
| `config_names` | str or list[str] | Available configs/subset names | `[fr, en, de]` for a multilingual dataset |
| `paperswithcode_id` | str | PapersWithCode dataset ID | `common-voice` |

#### Evaluation Fields

| Field | Type | Description |
|-------|------|-------------|
| `train-eval-index` | dict | Evaluation spec for automated benchmarking on the Hub. Contains `config`, `task`, `task_id`, `splits`, `col_mapping`, `metadata` sections. |

#### Gating Fields

| Field | Type | Description |
|-------|------|-------------|
| `extra_gated` | dict | Configuration for dataset access gating (user must agree to terms before viewing/downloading) |
| `extra_gated.prompt` | str | Message shown to users before granting access |
| `extra_gated.fields` | list[dict] | Form fields: `name`, `type` (text, checkbox, etc.), `required` |
| `extra_gated.groups` | list[str] | HF org groups that are auto-approved |

### License Identifiers — Complete Reference

Hugging Face maintains a license registry at `https://huggingface.co/docs/hub/repositories-licenses`. The most common:

| Identifier | License | SPDX |
|------------|---------|------|
| `apache-2.0` | Apache License 2.0 | Apache-2.0 |
| `mit` | MIT License | MIT |
| `bsd-2-clause` | BSD 2-Clause | BSD-2-Clause |
| `bsd-3-clause` | BSD 3-Clause | BSD-3-Clause |
| `cc-by-4.0` | Creative Commons Attribution 4.0 | CC-BY-4.0 |
| `cc-by-sa-4.0` | CC Attribution-ShareAlike 4.0 | CC-BY-SA-4.0 |
| `cc0-1.0` | CC Zero v1.0 Universal | CC0-1.0 |
| `gpl-2.0` | GNU General Public License v2.0 | GPL-2.0-only |
| `gpl-3.0` | GNU General Public License v3.0 | GPL-3.0-only |
| `lgpl-2.1` | GNU Lesser General Public License v2.1 | LGPL-2.1-only |
| `lgpl-3.0` | GNU Lesser General Public License v3.0 | LGPL-3.0-only |
| `agpl-3.0` | GNU Affero General Public License v3.0 | AGPL-3.0-only |
| `mpl-2.0` | Mozilla Public License 2.0 | MPL-2.0 |
| `unlicense` | The Unlicense | Unlicense |
| `deepseek` | DeepSeek License | Custom |
| `llama2` | Llama 2 Community License | Custom |
| `falcon-180B` | TII Falcon 180B License | Custom |
| `other` | Custom license | — |

When `license: other`, you MUST also provide:
- `license_name: str` — a short identifier for your license
- `license_link: str` — either a relative path (`LICENSE`) or absolute URL to the license text

### Task Categories & Task IDs

Task categories and IDs are defined in `huggingface.js/packages/tasks/src/tasks.ts`. Key categories:

| Category | Example Task IDs |
|----------|-----------------|
| `text-classification` | `sentiment-classification`, `topic-classification`, `natural-language-inference` |
| `token-classification` | `named-entity-recognition`, `part-of-speech` |
| `text-generation` | `language-modeling`, `dialogue-generation` |
| `fill-mask` | `fill-mask` |
| `summarization` | `summarization` |
| `translation` | `translation` |
| `question-answering` | `extractive-qa`, `open-domain-qa`, `multiple-choice-qa` |
| `text2text-generation` | `text2text-generation` |
| `image-classification` | `image-classification` |
| `object-detection` | `object-detection`, `face-detection` |
| `image-segmentation` | `instance-segmentation`, `semantic-segmentation`, `panoptic-segmentation` |
| `text-to-image` | `text-to-image` |
| `image-to-text` | `image-to-text`, `image-captioning`, `optical-character-recognition` |
| `automatic-speech-recognition` | `automatic-speech-recognition` |
| `text-to-speech` | `text-to-speech` |
| `audio-classification` | `audio-classification` |
| `tabular-classification` | `tabular-classification` |
| `tabular-regression` | `tabular-regression` |
| `reinforcement-learning` | `reinforcement-learning` |
| `robotics` | `robotics` |
| `other` | `other` |

### Complete YAML Example

```yaml
---
pretty_name: "My Fine-Tuning Dataset"
language:
- en
- fr
license: mit
task_categories:
- text-classification
task_ids:
- sentiment-classification
annotations_creators:
- crowdsourced
language_creators:
- crowdsourced
multilinguality:
- multilingual
size_categories:
- 100K<n<1M
source_datasets:
- original
config_names:
- en
- fr
train-eval-index:
- config: en
  task: text-classification
  task_id: sentiment-classification
  splits:
    train: train
    validation: validation
    test: test
  col_mapping:
    text: text
    label: target
  metadata:
    - name: Accuracy
      type: accuracy
---
```

### Gating (Dataset Access Control) Example

```yaml
---
extra_gated:
  prompt: "By clicking 'Agree', you confirm that you will use this dataset only for non-commercial research purposes."
  fields:
    - name: name
      type: text
      required: true
    - name: affiliation
      type: text
      required: true
    - name: commercial_use
      type: checkbox
      label: "I will not use this dataset for commercial purposes"
      required: true
  groups:
    - academic-researchers
---
```

### Best Practices

1. **Always include `pretty_name`** — makes the dataset searchable and identifiable
2. **List ALL task categories** — not just the primary one; improves discoverability
3. **Use standard license identifiers** — avoid `other` unless absolutely necessary
4. **Include `config_names`** — especially important for multilingual/multi-config datasets
5. **Use `source_datasets: original`** for new datasets, or list source dataset IDs for derived datasets
6. **`size_categories`** — use the controlled vocabulary; the Hub may reject invalid values
7. **`train-eval-index`** — include only if you want automated benchmarking. Complex to set up correctly

### Sources
- `huggingface_hub` source: `src/huggingface_hub/repocard_data.py` — `DatasetCardData` dataclass definition
- `huggingface_hub` source: `src/huggingface_hub/repocard.py` — `DatasetCard.from_template()` and `push_to_hub()`
- Hub docs: https://huggingface.co/docs/hub/en/datasets-overview
- Hub docs: https://huggingface.co/docs/hub/en/repositories-licenses
- Hub docs: https://huggingface.co/docs/hub/en/repositories-gated
- Model card spec: https://github.com/huggingface/hub-docs/blob/main/modelcard.md
- Task taxonomy: `huggingface.js/packages/tasks/src/tasks.ts`
- Verified via `huggingface_hub` source code inspection, 2026-07-25

### Skill Deepened
`hf-hub-dataset-card-metadata-comprehensive-reference/` — `references/hf-learnings.md` created (this file). SKILL.md already has `author: SakThai` and `license: MIT`.
