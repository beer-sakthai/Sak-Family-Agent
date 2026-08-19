---
name: SakThai-hf-model-release-checklist
description: "Complete reference on the Hugging Face Hub Model Release Checklist \u2014 a structured\
  \ workflow for releasing ML models to the Hub with proper metadata, model cards,\
  \ library integration, discoverability optimization, access control, and post-release\
  \ maintenance. Covers YAML metadata, pipeline tags, base_model relations, gated\
  \ access, collections, Spaces demos, quantized variants, and carbon emissions reporting."
---

# Hugging Face Hub — Model Release Checklist

## Overview

The **Model Release Checklist** is the official Hugging Face recommended workflow for sharing ML models on the Hub. A well-executed release dramatically increases your model's visibility, usability, and community impact. This skill documents every step — from preparation to post-release — with concrete YAML, Markdown, and API examples.

**Why it matters:**
- Models with proper metadata appear in search filters and gain inference widgets
- Models with library integration get automatic code snippets and download tracking
- Models with well-written cards get more stars, downloads, and community contributions
- Models with gated access give authors control over usage while enabling responsible sharing

## The Complete Release Workflow

### Phase 1: Preparation

#### 1.1 Model Weights

| Practice | Why |
|----------|-----|
| **Use individual repos** per variant/quantization | Each model gets its own URL, search ranking, download stats |
| **Prefer `safetensors`** over pickle | Safer (no arbitrary code execution), faster |
| **Convert `.bin` files** to safetensors | Use the [weight conversion tool](https://huggingface.co/docs/safetensors/en/convert-weights) |
| **Use separate repos** for different sizes/variants | Group them in a [collection](https://huggingface.co/docs/hub/collections) |

#### 1.2 Repository Setup

Choose the right owner:
- **Personal account**: `username/model-name`
- **Organization**: `org-name/model-name` (better for teams, gets org-level visibility)

Create via:
- [Web UI](https://huggingface.co/new)
- `huggingface_hub` Python: `create_repo("org/model-name")`
- `hf` CLI: `hf co create org/model-name`

### Phase 2: Model Card (README.md)

The model card is the **most important file** in your repo. It's the README.md and contains both YAML metadata and Markdown body.

#### 2.1 Required YAML Metadata

```yaml
---
pipeline_tag: text-generation           # Required: determines widget + API
library_name: transformers              # Required for code snippets + download stats
language:
  - en                                  # ISO 639-1 codes
license: apache-2.0                     # Required: must be a valid SPDX identifier
tags:
  - fine-tune
  - instruct
datasets:
  - org/dataset-name                    # Training datasets (appear on model page)
base_model: org/base-model              # If fine-tune/quantized/merge of another model
---
```

**Pipeline tag taxonomy** (common values):
| Tag | Task |
|-----|------|
| `text-generation` | LLMs, chatbots |
| `text-to-image` | Image generation |
| `image-text-to-text` | Vision-Language Models |
| `text-to-speech` | TTS |
| `automatic-speech-recognition` | ASR |
| `image-classification` | Image classification |
| `token-classification` | NER, POS tagging |
| `text-classification` | Sentiment, toxicity |
| `fill-mask` | Masked language models |
| `sentence-similarity` | Embedding models |

#### 2.2 Advanced YAML Metadata

```yaml
---
# Version relationships
base_model: org/base-model
base_model_relation: quantized          # Optional: quantized, finetune, merged, distilled

# New version banner (on old model card)
new_version: org/updated-model

# Carbon emissions
co2_eq_emissions:
  emissions: 123.45
  source: "CodeCarbon"
  training_type: "pre-training"
  geographical_location: "US-East"
  hardware_used: "8xA100 GPUs"

# Extra gated fields (for gated models)
extra_gated_fields:
  Organization: text
  Intended use: text
  I agree to terms: checkbox
---
```

#### 2.3 Model Card Body Structure

A strong model card includes these sections in order:

```markdown
---
# (metadata above)
---

# Model Name

## Model Description
What the model does, architecture, target use cases.

## Intended Uses & Limitations
- **Intended use cases:** ...
- **Out-of-scope:** ...
- **Limitations & biases:** ...

## How to Get Started with the Model

Use the code below to get started with the model.

```python
from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained("org/model-name")
tokenizer = AutoTokenizer.from_pretrained("org/model-name")
```

Or load as a pipeline:
```python
from transformers import pipeline
pipe = pipeline("text-generation", model="org/model-name")
```

## Training Details
- **Training data:** [dataset](https://huggingface.co/datasets/org/data)
- **Hardware:** 8x A100 80GB
- **Optimizer:** AdamW
- **Learning rate:** 2e-5
- **Epochs:** 3

## Evaluation Results

| Benchmark | Score |
|-----------|-------|
| MMLU 5-shot | 72.3 |
| GSM8K 8-shot | 68.1 |
| HumanEval 0-shot | 45.2 |

(Use the [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard) format where possible.)

## Environmental Impact

- **Carbon emissions:** 123.45 kg CO₂ eq. (CodeCarbon)
- **Training location:** US-East

## Citation

```
@misc{org-model-2026,
  author = {Author, A.},
  title = {Model Name},
  year = {2026},
  publisher = {Hugging Face},
  journal = {Hugging Face Hub},
  howpublished = {\url{https://huggingface.co/org/model-name}}
}
```

## Model Card Authors
Name, Name

## Model Card Contact
email@example.com
```

### Phase 3: Discoverability Optimization

#### 3.1 Library Integration

Set `library_name` in YAML to unlock:
- Auto-generated code snippets on the model page
- Download tracking (only registered libraries count)
- "Use in [library]" buttons

```yaml
library_name: transformers   # or: diffusers, timm, sentence-transformers, etc.
```

To register a custom library: see [Adding Libraries](https://huggingface.co/docs/hub/en/models-adding-libraries)

#### 3.2 Custom Notebook

Add `notebook.ipynb` at repo root to get:
- Custom Colab/Kaggle content instead of auto-generated
- One-click launch from model page

See [HF Hub Notebooks Integration](https://huggingface.co/docs/hub/en/notebooks).

#### 3.3 Collections

Group related models into a [collection](https://huggingface.co/docs/hub/collections):
- Different size variants (0.5B, 1.5B, 7B)
- Base + fine-tuned versions
- Original + quantized variants

#### 3.4 Interactive Demo (Space)

Create a Gradio/Streamlit/Static Space and link from the model card:

```yaml
# In Space YAML:
sdk: gradio
app_file: app.py
models:
  - org/model-name
```

The model will appear in the Space's "Models" section and the Space will appear on the model page.

#### 3.5 Visual Examples (For image/video models)

Use the `<Gallery>` component:

```markdown
<Gallery>
![Example 1](./images/example1.png)
![Example 2](./images/example2.png)
</Gallery>
```

### Phase 4: Access Control

#### 4.1 Visibility

- **Private** during development (only you and org members can see)
- **Public** when ready to share

Set via repo Settings → Make public.

#### 4.2 Gated Access

Enable when:
- Model has dual-use concerns
- You want to collect user information
- You need to control who can download

**Gating modes:**
| Mode | Behaviour |
|------|-----------|
| Automatic | Users share info, get immediate access |
| Manual | You review and approve each request |

**Via API (programmatic access management):**

```python
from huggingface_hub import HfApi
api = HfApi()

# List pending requests
pending = api.list_pending_access_requests("org/model-name")

# Accept a user
api.accept_access_request("org/model-name", "username")

# Reject with reason
api.reject_access_request("org/model-name", "username",
                          rejection_reason="Commercial use requires separate license")

# Grant access without request
api.grant_access("org/model-name", "username")
```

**Custom gated fields:**
```yaml
extra_gated_fields:
  Organization: text
  Country: text
  I will not use for military purposes: checkbox
  Expected use date: date_picker
```

**Download access report:**
From repo Settings → Download user access report → JSON with user, status, email, timestamps.

### Phase 5: Post-Release

#### 5.1 Versioning

When releasing a newer version:
1. Add `new_version` metadata to the OLD model's card:

```yaml
# In old model card
new_version: org/updated-model
```

This displays a banner: "A newer version of this model is available."

2. Create the new model repo with `base_model` pointing to the old one.

#### 5.2 Quantized Variants

Release GGUF/AWQ/GPTQ versions in separate repos:

```yaml
# In quantized model card
base_model: org/original-model
base_model_relation: quantized
```

This builds the **model tree** visualization on the Hub.

#### 5.3 Monitor & Respond

- Check download stats (visible on model page)
- Respond to community questions in Discussions
- Update the model card as new benchmarks or findings emerge

## API Reference

### huggingface_hub Methods for Model Management

```python
from huggingface_hub import HfApi
api = HfApi()

# Create repo
api.create_repo("org/model-name", private=True)

# Upload files
api.upload_file(
    path_or_fileobj="model.safetensors",
    path_in_repo="model.safetensors",
    repo_id="org/model-name",
)

# Update model card metadata
api.update_model_card(
    repo_id="org/model-name",
    card_data={
        "pipeline_tag": "text-generation",
        "library_name": "transformers",
        "language": ["en"],
        "license": "apache-2.0",
        "datasets": ["org/dataset"],
        "base_model": "org/base-model",
    }
)

# Set gating
api.update_repo_settings("org/model-name", gated="manual")

# Access request management
pending = api.list_pending_access_requests("org/model-name")
api.accept_access_request("org/model-name", "username")
api.reject_access_request("org/model-name", "username",
                          rejection_reason="Commercial use requires license")
api.grant_access("org/model-name", "username")

# Upload notebook
api.upload_file(
    path_or_fileobj="notebook.ipynb",
    path_in_repo="notebook.ipynb",
    repo_id="org/model-name",
)
```

### CLI Commands (hf CLI)

```bash
# Create repo
hf co create org/model-name

# Clone
git clone https://huggingface.co/org/model-name

# Push files (via git)
cd model-name
git add .
git commit -m "Initial release"
git push

# Set gating (web UI)
# Visit: https://huggingface.co/org/model-name/settings
```

## Best Practices Summary

| Step | Action | Impact |
|------|--------|--------|
| ✅ | safetensors format | Security + fast loading |
| ✅ | pipeline_tag set | Search filtering + inference widget |
| ✅ | library_name set | Code snippets + download stats |
| ✅ | license set | Legal clarity + search filter |
| ✅ | datasets listed | Training provenance visible |
| ✅ | base_model specified | Model tree built automatically |
| ✅ | Usage code in card | Users can run immediately |
| ✅ | Custom notebook.ipynb | One-click Colab/Kaggle |
| ✅ | Space demo linked | Try in browser without code |
| ✅ | Collection created | Group related variants |
| ✅ | Gating if needed | Usage control + user info |
| ✅ | Carbon emissions | Environmental transparency |

## Example: End-to-End Release Script

```python
"""Complete model release workflow."""
from huggingface_hub import HfApi, create_repo, upload_file, update_model_card

api = HfApi()
REPO_ID = "org/my-model"

# 1. Create repo
create_repo(REPO_ID, private=True)

# 2. Upload weights and config
for file in ["model.safetensors", "config.json", "tokenizer.json"]:
    upload_file(
        path_or_fileobj=f"./output/{file}",
        path_in_repo=file,
        repo_id=REPO_ID,
    )

# 3. Update model card metadata
update_model_card(
    repo_id=REPO_ID,
    card_data={
        "pipeline_tag": "text-generation",
        "library_name": "transformers",
        "language": ["en"],
        "license": "apache-2.0",
        "datasets": ["org/training-data"],
        "base_model": "org/base-model",
        "tags": ["fine-tune", "instruct"],
        "co2_eq_emissions": {
            "emissions": 45.2,
            "source": "CodeCarbon",
            "training_type": "fine-tuning",
            "hardware_used": "1x A100",
        },
    },
    repo_type="model",
)

# 4. Upload usage notebook
upload_file(
    path_or_fileobj="./notebook.ipynb",
    path_in_repo="notebook.ipynb",
    repo_id=REPO_ID,
)

# 5. Set public (after verification)
api.update_repo_settings(REPO_ID, private=False)

print(f"✅ Model released: https://huggingface.co/{REPO_ID}")
```

## Limitations

- **library_name** must be a [registered library](https://huggingface.co/docs/hub/en/models-libraries) for download tracking
- **Gated access** is per-repo; for multi-repo gating use [Gating Group Collections](https://huggingface.co/docs/hub/en/enterprise-gating-group-collections) (Team/Enterprise)
- **model tree** only builds automatically for `base_model` relationships, not arbitrary links
- **Collections** can contain at most 100 repos (may be increased over time)
- **Carbon emissions** display is not automatic — must be added to YAML metadata
- **Evaluation results** widget uses the [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard) format for best rendering

## Support Files

| File | Covers |
|------|--------|
| `references/model-card-enrichment-patterns.md` | Badge patterns, multi-language code examples, benchmark comparison tables, YAML tag strategies, upload patterns, verification checklist |
| `references/official-docs.md` | Official Hugging Face docs reference links |

## References

- [Official Docs: Model Release Checklist](https://huggingface.co/docs/hub/en/model-release-checklist)
- [Official Docs: Model Cards](https://huggingface.co/docs/hub/en/model-cards)
- [Official Docs: Uploading Models](https://huggingface.co/docs/hub/en/models-uploading)
- [Official Docs: Gated Models](https://huggingface.co/docs/hub/en/models-gated)
- [Official Docs: Model Card Metadata](https://huggingface.co/docs/hub/en/model-cards#model-card-metadata)
- [Official Docs: Pipeline Tags](https://huggingface.co/docs/hub/en/model-cards#specifying-a-task--pipeline-tag-)
- [Model Card Template](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/modelcard_template.md)
- [Annotated Model Card](https://huggingface.co/docs/hub/en/model-card-annotated)
- [Collections](https://huggingface.co/docs/hub/en/collections)
- [huggingface_hub: Model Card API](https://huggingface.co/docs/huggingface_hub/guides/model-cards)
