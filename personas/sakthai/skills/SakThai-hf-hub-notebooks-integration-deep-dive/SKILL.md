---
name: SakThai-hf-hub-notebooks-integration-deep-dive
version: 1.2.0
description: Complete deep-dive on Jupyter Notebook integration with the Hugging Face
  Hub — one-click Colab/Kaggle model launching, custom notebook.ipynb in repos, .ipynb
  rendering, the /colab and /kaggle endpoints, Open in Colab buttons, and practical
  workflows for sharing reproducible ML research through notebooks on the Hub.
category: hf-hub
tags:
- authentication
- colab
- deep
- dive
- hf
- hub
- huggingface
- integration
- jupyter
- kaggle
- model-cards
- notebooks
- rendering
- spaces
author: SakThai
---

# Hugging Face Hub — Jupyter Notebooks Integration Deep Dive

## Overview

Jupyter notebooks are the standard format for sharing ML code, analysis, and research. The Hugging Face Hub provides deep integration with the Jupyter ecosystem, making notebooks a first-class citizen across models, datasets, and Spaces repositories.

**Key integration points:**
- The Hub **renders `.ipynb` files** directly in the browser (human-readable output)
- Every `.ipynb` file gets an automatic **"Open in Colab"** button
- Model pages have **"Use this model → Google Colab / Kaggle"** dropdown buttons
- Model authors can provide a **custom `notebook.ipynb`** in their repo
- **`/colab` and `/kaggle` URL endpoints** generate one-click notebooks for any model
- Integration with **Colab's free GPU** and **Kaggle's free GPU/TPU** environments

## How It Works

### 1. Model → Colab/Kaggle Integration

When visiting any model page on the Hub:

1. Click the **"Use this model"** dropdown button on the model card
2. Select **"Google Colab"** or **"Kaggle"**
3. A ready-to-run notebook opens in Colab/Kaggle with code to:
   - Load the model via `transformers` or `pipeline`
   - Run inference with example inputs
   - Optionally fine-tune or evaluate

This works without any setup from the model author — the auto-generated notebook uses the model's metadata (pipeline tag, library, config) to produce sensible starter code.

### 2. Direct URL Endpoints

Append to any model page URL:

| Endpoint | Example | Behaviour |
|----------|---------|-----------|
| `/colab` | `hf.co/google/gemma-3-4b-it/colab` | Opens in Google Colab |
| `/kaggle` | `hf.co/google/gemma-3-4b-it/kaggle` | Opens in Kaggle |

This is useful for:
- Linking from documentation, blog posts, or READMEs
- Sharing via social media or chat
- Embedding in course materials

### 3. Custom `notebook.ipynb` in Model Repos

If a model repository contains a file named **`notebook.ipynb`** at the repo root, the Hub uses it **instead of the auto-generated notebook** when users click Colab/Kaggle.

**Benefits of a custom notebook:**
- Showcase **exact usage patterns** for your model
- Include **domain-specific preprocessing** steps
- Demonstrate **advanced features** (quantization, PEFT, custom pipelines)
- Provide **end-to-end workflows** (training → evaluation → deployment)
- Include **visualizations** and **interactive widgets**

**Best practices for custom notebooks:**
- Keep dependencies minimal (list them clearly)
- Use `!pip install` cells at the top for easy setup
- Include a "Restart runtime" reminder after installation
- Test the notebook end-to-end in Colab/Kaggle before uploading
- Set the cell execution order correctly
- Use markdown cells for explanations between code cells

**Example repos with custom notebooks:**
- [NousResearch/Genstruct-7B](https://huggingface.co/NousResearch/Genstruct-7B)
- Many fine-tuned model variants on the Hub

### 4. Notebook Rendering on the Hub

All `.ipynb` files hosted in any repository type (models, datasets, Spaces) are automatically rendered in a human-readable format:

- **Code cells** are syntax-highlighted
- **Output cells** (text, images, plots, DataFrames) are displayed inline
- **Markdown cells** are rendered as formatted text
- **Rich output** (HTML, SVG, LaTeX) is preserved

This means anyone browsing your repo can read the notebook without downloading it or leaving the Hub.

### 5. "Open in Colab" Button

Every `.ipynb` file on the Hub automatically displays an **"Open in Colab"** button at the top of the rendered view. Clicking it opens the notebook directly in Google Colab for execution.

**URL pattern:**
```
https://colab.research.google.com/github/huggingface/notebooks/blob/main/example.ipynb
```

The Hub handles the URL conversion automatically — no special configuration needed.

## Practical Workflows

### Workflow 1: Share a Fine-Tuning Tutorial

1. Create a model repo for your fine-tuned model
2. Add `notebook.ipynb` with the full fine-tuning code
3. Users see custom notebook content when clicking Colab/Kaggle
4. Your notebook serves as both documentation and executable tutorial

### Workflow 2: Build an ML Portfolio

1. Create a dataset repo with your analysis notebooks
2. Include multiple `.ipynb` files for different analyses
3. Each notebook gets rendered + has "Open in Colab" button
4. Employers/browsers see your work directly on the Hub

### Workflow 3: Reproduce Research

1. Upload the exact notebooks used in your research to a model/dataset repo
2. Add a `notebook.ipynb` for the main reproduction script
3. Link to `/colab` from your paper or blog
4. Anyone can reproduce results with one click

## Integration with Related HF Features

| Feature | Relationship |
|---------|-------------|
| **HF Cookbook** | Collection of example notebooks demonstrating HF libraries — many use Colab links |
| **Spaces** | Notebooks can be deployed as Gradio/Streamlit Spaces (separate from .ipynb rendering) |
| **Datasets** | Notebooks analyzing datasets benefit from Hub rendering + Colab launch |
| **Model Cards** | Notebooks complement model documentation with executable examples |
| **Discussions** | Share notebook links in discussions for reproducible bug reports |
| **Collections** | Curate notebook-containing repos into themed collections |

---

## 6bis. Direct URL Suffix Access for Colab & Kaggle

Every model page supports two URL suffixes for one-click launch:

| Endpoint | Example URL | Behaviour |
|----------|-------------|-----------|
| `/colab` | `huggingface.co/{owner}/{repo}/colab` | Redirects to Google Colab with auto-generated notebook |
| `/kaggle` | `huggingface.co/{owner}/{repo}/kaggle` | Redirects to Kaggle with auto-generated notebook |

**If `notebook.ipynb` exists at the repo root**, the custom notebook is used instead of the auto-generated one. The Hub checks for this file on every `/colab` or `/kaggle` request.

Usage in markdown:
```markdown
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://huggingface.co/{owner}/{repo}/colab)
```

## 7. Uploading Notebooks to the Hub

### Via `hf` CLI

```bash
# Upload single notebook
hf upload username/my-model ./getting-started.ipynb notebooks/getting-started.ipynb \
  --commit-message "Add getting started notebook"

# Upload all notebooks from directory
hf upload username/my-model ./notebooks/ notebooks/ \
  --commit-message "Add notebook collection"
```

### Via Git

```bash
git clone https://huggingface.co/username/my-model
cd my-model
cp /path/to/notebook.ipynb .
git add notebook.ipynb
git commit -m "Add demo notebook"
git push
```

### Via Python SDK

```python
from huggingface_hub import HfApi
api = HfApi()

# Single notebook
api.upload_file(
    path_or_fileobj="./demo.ipynb",
    path_in_repo="notebooks/demo.ipynb",
    repo_id="username/my-model",
)

# Folder of notebooks
api.upload_folder(
    folder_path="./notebooks/",
    path_in_repo="notebooks/",
    repo_id="username/my-model",
    allow_patterns="*.ipynb",
)
```

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Programmatic Notebook Management & Automated Papermill Hub Runs](./references/notebooks-programmatic-management.md).
