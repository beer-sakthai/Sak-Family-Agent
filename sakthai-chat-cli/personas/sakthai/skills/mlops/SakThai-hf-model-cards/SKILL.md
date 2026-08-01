---
name: SakThai-hf-model-cards
description: "Hugging Face Model Cards: repository metadata, YAML frontmatter, tags, pipeline types, license, and how to write a great README.md."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, hf, model-cards, metadata, yaml, readme, hub, documentation]
platforms: [linux, macos, windows]
---

# Hugging Face Model Cards: Metadata & YAML Frontmatter

Every model (and dataset) repository on the Hugging Face Hub has a **model card** — a `README.md` file whose YAML frontmatter controls how the Hub displays, filters, and indexes the repo.

## Why It Matters

- The Hub parses the frontmatter to set the model’s **pipeline tag** (text-generation, image-classification, etc.).
- **Tags** determine search results and which UI widgets appear on the repo page.
- **License** must be one of the Hub’s accepted identifiers for compliance.
- Bad or missing metadata means the model may not appear where users expect it.

## Minimal Valid Model Card

Create a `README.md` at the root of your repo with this header:

```yaml
---
license: apache-2.0
tags:
  - text-generation
  - llama
library_name: transformers
pipeline_tag: text-generation
---
```

Everything after the closing `---` is free-form Markdown for the actual model card.

## Core YAML Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `license` | SPDX license ID | `mit`, `apache-2.0`, `cc-by-4.0` |
| `tags` | Labels for search and filtering | `text-generation`, `llama`, `chat` |
| `pipeline_tag` | The primary task UI widget | `text-generation`, `image-classification`, `automatic-speech-recognition` |
| `library_name` | Primary framework repo targets | `transformers`, `diffusers`, `peft`, `text-generation-inference` |
| `base_model` | For fine-tuned models | `meta-llama/Llama-2-7b-hf` |
| `datasets` | Training data provenance | `tatsu-lab/stanford_alpaca` |
| `language` | ISO 639-1 codes preferred | `en`, `fr`, `multilingual` |
| `inference` | Whether hosted inference is supported | `true` / `false` |
| `model-index` | Links to benchmark results | See below |

## pipeline_tag Reference

Common values include:

- `text-generation`
- `text-classification`
- `token-classification`
- `question-answering`
- `fill-mask`
- `summarization`
- `translation`
- `automatic-speech-recognition`
- `text-to-speech`
- `image-classification`
- `object-detection`
- `image-segmentation`
- `text-to-image`
- `image-to-image`
- `inpainting`
- `depth-estimation`

A full list is maintained at https://huggingface.co/docs/hub/main#how-to-use

## Writing the Actual Model Card

After the YAML header, the Markdown body should cover:

1. **Model description** — architecture, size, training data, license.
2. **Intended use** — what it’s designed for and known limitations.
3. **Bias, risks, and limitations** — required for HF-hosted models with Inference API access.
4. **How to use** — short code snippet loading the model.
5. **Training details** — hyperparameters, hardware, framework versions.
6. **Evaluation** — benchmark results with tables or leaderboard links.
7. **Citation** — BibTeX entry.

### Example Header for a Fine-Tune

```yaml
---
license: apache-2.0
base_model: meta-llama/Llama-2-7b-hf
tags:
  - text-generation
  - llama
  - instruct
library_name: transformers
pipeline_tag: text-generation
language:
  - en
datasets:
  - tatsu-lab/stanford_alpaca
---
```

## Model Card Viewer (HTML)

When rendered on the Hub, the markdown becomes an HTML model card with:

- **Model Summary** metadata block (auto-generated from YAML).
- **Model Browser** — dropdowns to switch between tasks if multiple `pipeline_tag`s exist.
- **Files and versions** pane tracking upload history.

## Validating & Updating Metadata

- Edit the `README.md` directly on `huggingface.co` or push via `git` / `huggingface-cli upload`.
- Changing YAML does **not** create a new Git revision unless the commit is accepted.
- Use `huggingface-cli repo-info <repo-id> --repo-type model` to see parsed metadata.
- For programmatic updates, use `HfApi.upload_file` with `path_in_repo="README.md"`.

## Special k: model-index for Leaderboards

If you have benchmark results, add a structured block:

```yaml
---
model-index:
  - name: MyModel-7B
    results:
      - task:
          type: text-generation
        dataset:
          type: crowdsource
        metrics:
          - name: MT-Bench
            type: mt_bench
            value: 7.2
---
```

This feeds the Hub’s **Papers with Code** integration and auto-populates comparison tables.

## Key Facts

- The YAML frontmatter is the single source of truth for Hub metadata; tags and `pipeline_tag` drive search, UI widgets, and filtering.
- Model card safety disclosures (bias, risks) are required for certain hosted-inference accounts.
- `model-index` blocks link your repo’s benchmark numbers to Papers with Code leaderboards automatically.
- Hub metadata updates via `huggingface-cli` or `git` require a new commit to take effect.
- Accepted licenses must match the Hub’s SPDX curated list; unsupported values show warnings and can block repo visibility.
