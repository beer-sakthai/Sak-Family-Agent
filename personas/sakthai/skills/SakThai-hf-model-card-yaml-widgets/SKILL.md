---
name: SakThai-hf-model-card-yaml-widgets
author: SakThai
license: MIT
title: HF Model Card YAML Metadata & Widget Configuration
description: Master Hugging Face model card YAML metadata — schema, pipeline_tag, widget config, programmatic creation via huggingface_hub, ModelCard components (Gallery), and metadata validation patterns.
category: mlops
tags: [huggingface, model-cards, yaml, metadata, widgets, hub, discoverability]
created: 2026-07-23
---
# HF Model Card YAML Metadata & Widget Configuration

## Overview

Model cards are the `README.md` at the root of every HF Hub model repo. They have two parts:

1. **YAML metadata** (between `---` delimiters at the top) — controls discoverability, licensing, widget display
2. **Markdown body** — human-readable model description

This skill covers everything about the YAML metadata layer and the inference widget system built on top of it.

---

## 1. Model Card YAML Metadata Schema

All metadata lives in the YAML frontmatter between `---` fences at the top of `README.md`.

### Standard Fields

```yaml
---
version: 1.0.0
language:                      # ISO 639-1 code(s) — single value or list
  - en
  - fr
tags:                          # Used for Hub filtering / search
  - text-classification
  - transformers
pipeline_tag: text-generation  # Overrides auto-detected pipeline type
library_name: transformers     # Framework used (transformers, diffusers, etc.)
datasets:                      # Datasets used for training
  - sst2
metrics:                       # Evaluation metrics
  - accuracy
base_model: google-bert/bert-base-uncased  # Parent model for fine-tuned models
model-index:                   # Structured evaluation results (for leaderboards)
  - name: my-model
    results:
      - task:
          type: text-classification
        dataset:
          type: glue
          name: GLUE (MRPC)
        metrics:
          - name: accuracy
            type: accuracy
            value: 0.85
widget:                        # Inference widget example inputs
  - text: "I loved this movie!"
    example_title: "Positive"
inference:                     # Inference configuration
  parameters:
    temperature: 0.7
    max_new_tokens: 100
co2_eq_emissions:              # Carbon emissions reporting
  emissions: 0.5
  source: codecarbon
---
```

### Key Metadata Fields Reference

| Field | Type | Purpose |
|-------|------|---------|
| `license` | string | SPDX license ID. Renders badge on model page. |
| `license_link` | string | URL to custom license if not SPDX-listed |
| `language` | string \| list | ISO 639-1 codes. Used for Hub filtering. |
| `tags` | list | Freeform tags for discoverability + pipeline_tag inference |
| `pipeline_tag` | string | **Critical** — determines which widget type renders. Overrides auto-detection. |
| `library_name` | string | Framework (transformers, diffusers, timm, etc.) |
| `datasets` | list | Links to datasets on Hub |
| `metrics` | list | Evaluation metric names |
| `base_model` | string \| list | Parent model(s) for derived/fine-tuned models |
| `model-index` | list | Structured eval results (YAML format) |
| `widget` | list | Example inputs for the inference widget |
| `inference` | object | Widget inference parameters |
| `co2_eq_emissions` | object | Carbon footprint data |
| `safetensors` | object | SafeTensors conversion info |
| `paperswithcode_id` | string | PwC dataset ID for cross-linking |
| `config` | object | Model-specific config overrides |
| `extra_gated_prompt` | string | Custom gate prompt for gated models |
| `extra_gated_fields` | object | Custom gate fields (e.g., organization, reason) |

---

## 2. Inference Widget System

### How Widget Type is Determined (Priority Order)

1. **`pipeline_tag`** in YAML metadata — manual override (highest priority)
2. **Model config** (`config.json`) — for `transformers` library models, the architecture's base class determines pipeline type
3. **Tags** — if a `tag: text-classification` exists in metadata, inferred pipeline = `text-classification`
4. **Conversational widget** — shown on models with `pipeline_tag: text-generation` or `image-text-to-text` AND tagged `conversational`

### Supported pipeline_tag Values

Common values: `text-generation`, `text-classification`, `token-classification`, `image-classification`, `image-to-text`, `text-to-image`, `text-to-speech`, `automatic-speech-recognition`, `object-detection`, `image-segmentation`, `table-question-answering`, `document-question-answering`, `zero-shot-classification`, `conversational`, `image-text-to-text`, `fill-mask`, `sentence-similarity`, etc.

### Widget Example Configuration

```yaml
widget:
  - text: "This new restaurant has amazing food and great service!"
    example_title: "Positive Review"
  - text: "I'm really disappointed with this product. Poor quality and overpriced."
    example_title: "Negative Review"
  - text: "The weather is nice today."
    example_title: "Neutral Statement"
```

For **image generation / multimodal models**:

```yaml
widget:
  - text: "a girl wandering through the forest"
    output:
      url: images/sample1.jpeg
  - text: "a tiny witch child"
    output:
      url: images/sample2.jpeg
```

### Model Card Components (Special HTML Elements)

The `Gallery` component renders output images from widget metadata:

```md
<Gallery />

## Model description
...
```

Other components: `ModelCard` components are custom HTML elements injected into the markdown. The `Gallery` component is the primary one, backed by widget metadata.

---

## 3. Programmatic Model Card Creation via `huggingface_hub`

### Loading Existing Cards

```python
from huggingface_hub import ModelCard

card = ModelCard.load("bert-base-uncased")
card.data          # ModelCardData — YAML metadata
card.data.to_dict() # → dict
card.text          # Markdown body (without YAML header)
card.content       # Full content (YAML + body)
```

### Creating from Text

```python
content = """---
language: en
version: 1.0.0
---

# My Model Card
"""
card = ModelCard(content)
```

### Creating with ModelCardData + Jinja2 Template

```python
from huggingface_hub import ModelCard, ModelCardData

card_data = ModelCardData(
    language='en',
    license='apache-2.0',
    library_name='transformers',
    pipeline_tag='text-generation',
    tags=['llm', 'conversational'],
    datasets=['my-corpus'],
)

# Using Jinja2 template (requires jinja2 installed)
card = ModelCard.from_template(
    card_data,
    template_path='path/to/template.md',
    model_name='MyCoolModel',
    author='beer-sakthai'
)
card.save('my_model_card.md')
card.push_to_hub('beer-sakthai/my-model', repo_type='model')
```

### Updating Metadata via Python

```python
from huggingface_hub import ModelCard

card = ModelCard.load("beer-sakthai/my-model")

# Update metadata
card.data.tags = ['text-classification', 'bert']
card.data.language = 'en'
card.data.pipeline_tag = 'text-classification'

# Add widget examples
card.data.widget = [
    {"text": "This movie was amazing!", "example_title": "Positive"},
    {"text": "Terrible experience.", "example_title": "Negative"},
]

# Push update
card.push_to_hub("beer-sakthai/my-model", repo_type="model")
```

---

## 4. Discoverability Best Practices

### Essential fields for search ranking

```yaml
---
version: 1.0.0
language: en
tags:
  - text-classification
  - sentiment-analysis
  - transformers
library_name: transformers
pipeline_tag: text-classification
datasets:
  - glue
metrics:
  - accuracy
base_model: google-bert/bert-base-uncased
---
```

- **`tags`** are the primary search filter mechanism — add specific task tags
- **`pipeline_tag`** determines which category filter the model appears under
- **`library_name`** helps users find models compatible with their framework
- **`datasets`** links to training data (bidirectional discoverability)
- **`metrics`** enables eval-result-based filtering
- **`base_model`** creates parent-child linkages visible in the Hub UI

### Model Cards for Gated Models

```yaml
---
extra_gated_prompt: "Please describe your intended use case"
extra_gated_fields:
  Organization: text
  I agree to terms: checkbox
---
```

---

## 5. Common Pitfalls

- **YAML indentation** — YAML is whitespace-sensitive. `widget:` entries must be a list under proper indentation.
- **`pipeline_tag` mismatch** — Setting an invalid or unsupported `pipeline_tag` breaks widget rendering. Use standard values only.
- **`model-index` formatting** — Strict YAML nesting. Validate with a YAML linter before pushing.
- **Widget examples break image widgets** — Missing `output.url` for image-generation models results in a broken widget.
- **ModelCardData constructor** — Field names use underscores (e.g., `pipeline_tag`), not hyphens. The `to_yaml()` method handles conversion.
- **Empty `README.md`** — Without YAML frontmatter, models get default metadata which may be incorrect.
- **Large model-index blocks** — Can hit YAML parsing limits. Keep evaluation results concise.

---

## 6. Family-Level Discoverability

When managing a **model family** (multiple related models under one account), add cross-linking and consistent branding to every card.

### Cross-Link Family Table

Append a table linking to sibling models at the bottom of every card:

```markdown
## Model Family

| Model | Size | Type | Downloads |
|-------|:----:|:----:|:---------:|
| [1.5B-merged](https://huggingface.co/user/1.5b) | 934 MB | Tool-calling GGUF | 942 |
| [0.5B-merged](https://huggingface.co/user/0.5b) | 380 MB | Lightweight GGUF | 785 |
```

This lets visitors discover the whole family from any single model page. Generate programmatically from `api.model_info()` for each model.

### Consistent Branding Header

Add a branded header after YAML frontmatter:

```markdown
<div align="center">
  <h1>🏠 Family Name</h1>
  <p><em>Part of <strong>Org</strong> — tagline.</em></p>
  <p>
    <a href="https://huggingface.co/collections/user/slug">
      <img src="https://img.shields.io/badge/📦-View%20Family-8A2BE2" alt="Family"/>
    </a>
  </p>
</div>

---
```

### Conversational Tag for Chat Widget

For text-generation models, add `conversational` tag to enable in-browser chat:

```yaml
tags:
  - conversational
```

Apply via: `content.replace('tags:', 'tags:\\n- conversational', 1)`

### Batch Update Pattern

```python
for model_id in MODELS:
    content = read_readme(f'user/{model_id}')
    if 'conversational' not in content.split('---')[1]:
        content = content.replace('tags:', 'tags:\\n- conversational', 1)
    if 'Model Family' not in content:
        content += FAMILY_TABLE
    api.upload_file(path_or_fileobj=content.encode(), path_in_repo='README.md',
                    repo_id=f'user/{model_id}', repo_type='model')
```

### Pitfalls

- Guard with `if 'X' not in content[:N]` before adding — don't overwrite existing headers
- Target 5-8 tags — too many dilute search signal
- Verify badge URLs before pushing

---

## 7. Honest Assessment & Benchmark Reporting

A model card's most important job is **accuracy** — misleading claims damage trust more than missing features.

### When to Say "Pending" Not "5/5"

If you cannot fully verify a benchmark score due to infrastructure limits (no GPU, wrong inference engine, single-trial methodology), **do not publish a score**. Use one of:

```yaml
# Best — honest about limitations
- name: Tool-Calling
  value: "Pending — requires Ollama/server for proper evaluation"
  
# Acceptable — if you have partial data
- name: Tool-Calling  
  value: "Preliminary: see Honest Assessment section"

# Never — unverified claim that may be wrong
- name: Tool-Calling
  value: "5/5"  # ❌ Only if you can prove it with multi-trial methodology
```

### Multi-Trial Benchmark Requirement

Single-trial benchmarks are misleading. Run **5 trials minimum** and report the pass rate:

```markdown
## Benchmark

| Test | Pass rate | Trials |
|------|:---------:|:------:|
| get_weather | 5/5 | ✅ |
| search_web | 3/5 | ⚠️ |
| irrelevance | 5/5 | ✅ |
```

### Format Matching Is Critical

The model's **training format** must match the **testing format**:
- If trained on OpenAI `tool_calls` JSON, test with that format — not raw XML
- If trained on ChatML + `<tool>` tags, test with that format
- Document the test format in the model card

### Safety Warnings

If the model has known safety gaps (e.g., complies with harmful instructions), document them prominently:

```markdown
## Safety Warning

This model may comply with harmful instructions. **Do not use for 
security-critical applications.** Guardrails required before production use.
```

### Optimal Settings Section

After benchmarks, add a settings table so users can reproduce results:

```markdown
## Recommended Settings

| Parameter | Value | Why |
|-----------|-------|-----|
| System prompt | "You are a function-calling assistant." | Triggers tool output |
| Temperature | 0.01 | Maximum consistency |
| Threads | 2 | Best on 2-core CPU |
```

### Honest Assessment Pattern

When benchmark scores are preliminary or limited, add a standalone note:

```markdown
## Honest Assessment

The benchmark scores above are based on preliminary testing. This model
requires proper infrastructure (Ollama, llama.cpp server, or Transformers
pipeline) to evaluate correctly. Verified results coming soon.
```

### Pitfalls

- **Never publish unverified claims** — test first, publish second
- **Document methodology** — engine, quantization, temperature, thread count
- **Include failure cases** — don't cherry-pick only passing tests
- **Multi-trial** — a single pass doesn't prove reliability
- **Format match** — testing with wrong format produces misleading failures
- **Base model comparison** — test the base model too, to identify inherited limitations vs fine-tuning damage

## 8. Related Skills

- `huggingface-hub` — General HF Hub CLI and Python library usage
- `hf-inference-providers` — Understanding Inference Providers behind widgets
- `hf-hub-storage-management` — Managing repo storage quotas for large model cards
- `hf-trending-crawl` — Crawls model metadata including tags and pipeline tags

## Reference Files

| File | Covers |
|------|--------|
| [`references/batch-model-card-workflow.md`](references/batch-model-card-workflow.md) | End-to-end pipeline for batch model card generation and upload across multiple repos |
| [`references/benchmark-integrity.md`](references/benchmark-integrity.md) | Lessons from real benchmark failures: single-trial traps, wrong-format testing, base-model comparison, safety baselines |

## References

- [Widgets Documentation](https://huggingface.co/docs/hub/en/models-widgets)
- [Model Cards Documentation](https://huggingface.co/docs/hub/en/model-cards)
- [huggingface_hub ModelCard Guide](https://huggingface.co/docs/huggingface_hub/en/guides/model-cards)
- [Model Card Components (Gallery)](https://huggingface.co/docs/hub/en/model-cards-components)
