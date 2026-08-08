---
name: SakJules-SakThai-hf-hub-notebooks-integration-deep-dive
description: ">-   Complete deep-dive on Jupyter Notebook integration with the Hugging Face Hub —   one-click Colab/Kaggle model launching, custom notebook.ipynb in repos, .ipynb   rendering, the /colab and /kaggle endpoints, Open in Colab buttons, and practical  "
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

## 8. Programmatic Notebook Management

### Listing notebooks in a repo

```python
from huggingface_hub import HfApi
api = HfApi()
files = api.list_repo_files("username/my-model", repo_type="model")
notebooks = [f for f in files if f.endswith(".ipynb")]
print(f"Found {len(notebooks)} notebooks: {notebooks}")
```

### Downloading a notebook

```python
from huggingface_hub import hf_hub_download

nb_path = hf_hub_download(
    repo_id="username/my-model",
    filename="demo.ipynb",
    repo_type="model",
)
```

### Reading notebook metadata programmatically

```python
import json

with open(nb_path) as f:
    nb = json.load(f)

print(f"Kernel: {nb['metadata']['kernelspec']['display_name']}")
print(f"Language: {nb['metadata']['kernelspec']['language']}")
print(f"Cells: {len(nb['cells'])}")
```

### Checking for custom `notebook.ipynb`

```python
from huggingface_hub import HfApi
api = HfApi()
files = api.list_repo_files("NousResearch/Genstruct-7B")
print("Has custom notebook:" if "notebook.ipynb" in files else "No custom notebook")
```

## 9. Papermill + HF Hub Integration

`papermill` executes notebooks parameterically and saves results. Combined with HF Hub:

```python
import papermill as pm
from huggingface_hub import HfApi

# Execute notebook with parameters
pm.execute_notebook(
    "template.ipynb",
    "/tmp/output.ipynb",
    parameters={"model_name": "gpt2", "epochs": 5},
)

# Upload results to Hub
api = HfApi()
api.upload_file(
    path_or_fileobj="/tmp/output.ipynb",
    path_in_repo="results/experiment-1.ipynb",
    repo_id="username/my-experiments",
    commit_message="Run experiment with 5 epochs",
)
```

## 10. External Platform Integration

| Platform | Integration Method | Notes |
|----------|-------------------|-------|
| Google Colab | `/colab` endpoint on model page | Free GPU; custom notebook.ipynb supported |
| Kaggle | `/kaggle` endpoint on model page | Free GPU/TPU; requires Kaggle account |
| Paperspace | Manual via Git URL | Clone HF repo into Paperspace notebook |
| Deepnote | Import `.ipynb` from HF URL | Supports direct URL import |
| Binder | Manual Binder URL | `mybinder.org/v2/gh/huggingface/notebooks/HEAD` |
| Vertex AI | Manual import | Upload `.ipynb` from HF to Vertex AI Workbench |

## 11. Best Practices for Notebook Authors

1. **Pin versions**: Add `!pip install transformers==4.47.1` as the first code cell to ensure reproducibility.
2. **Test end-to-end**: Run the notebook from scratch in Colab/Kaggle before uploading.
3. **Keep under 10MB**: Large notebooks timeout during Hub rendering. Clear cell outputs before committing.
4. **Use 'Restart and run all'**: Verify the notebook runs cleanly from a cold start.
5. **Add Colab badge to README**: Makes the notebook discoverable from the repo's front page.
6. **Include markdown explanations**: Don't just dump code — explain what each section does.
7. **Strip large outputs**: Remove large images or DataFrames from output cells before upload.

## 12. Dataset Notebooks (EDA & Training Walkthroughs)

Notebooks in dataset repos serve different purposes than model repos:

- **EDA notebooks**: Show dataset statistics, distributions, sample visualizations
- **Training walkthroughs**: Fine-tune a model on the dataset from scratch
- **Preprocessing demos**: Demonstrate the data cleaning/augmentation pipeline

Upload to a dataset repo:
```bash
hf upload username/my-dataset ./eda.ipynb notebooks/eda.ipynb
```

Accessed at:
```
https://huggingface.co/datasets/username/my-dataset/blob/main/notebooks/eda.ipynb
```

The Hub renders these the same way as model repo notebooks — with syntax highlighting, output display, and the "Open in Colab" button.

## 13. API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/{type}/{owner}/{repo}/blob/main/{path}.ipynb` | GET | Rendered notebook view |
| `/{type}/{owner}/{repo}/blob/main/{path}.ipynb?raw=true` | GET | Raw JSON of notebook |
| `/{type}/{owner}/{repo}/colab` | GET | Auto-redirect to Colab |
| `/{type}/{owner}/{repo}/kaggle` | GET | Auto-redirect to Kaggle |
| `/api/{type}/{owner}/{repo}/tree/main` | GET | List files including notebooks |
| `/api/{type}/{owner}/{repo}/raw/main/{path}` | GET | Raw file access (for curl downloads) |

## 14. Pitfalls

- **`notebook.ipynb` at root only**: Only a file named exactly `notebook.ipynb` at the repo root triggers the custom notebook override. Notebooks in subdirectories are ignored.
- **No in-browser editing**: The Hub renders notebooks read-only. Users must launch in Colab/Kaggle to edit.
- **Large outputs break rendering**: Notebooks with embedded Base64 images >10MB fail to render.
- **Colab/Kaggle buttons are model-page only**: Dataset and Space pages don't show the dropdown buttons.
- **Kaggle requires account**: The redirect works but users need a Kaggle login to actually open the notebook.
- **Auth needed for non-public repos**: Custom notebooks in gated/private repos won't render for unauthenticated users.

## 15. References

- [Official Docs: Jupyter Notebooks on the Hub](https://huggingface.co/docs/hub/en/notebooks)
- [HF Hub Docs: Repositories](https://huggingface.co/docs/hub/en/repositories-getting-started)

The `huggingface_hub` library provides several auth methods designed for
interactive notebook environments.

### notebook_login() — primary method

```python
from huggingface_hub import notebook_login

# Displays a widget to paste your HF User Access Token
notebook_login()
```

- Auto-detects IPython/Jupyter environment
- Shows an input widget for pasting a token
- Saves to `~/.cache/huggingface/token`
- Configures git credentials automatically
- `skip_if_logged_in=True` (default): skip if already authenticated

### interpreter_login() — terminal fallback

Forces terminal-based prompt when notebook detection fails:

```python
from huggingface_hub import interpreter_login
interpreter_login()
```

### login() — auto-detect

```python
from huggingface_hub import login

# No token = browser-based OAuth flow in notebooks
login()

# Or pass a token explicitly
import os
login(token=os.getenv("HF_TOKEN"))
```

### auth_switch() — multiple token profiles

```python
from huggingface_hub import auth_switch
auth_switch("work-token")
auth_switch("personal-token")
```

### auth_list() — list saved tokens

```python
from huggingface_hub import auth_list
print(auth_list())
```

### logout() — clear cached token

```python
from huggingface_hub import logout
logout()
```

### Best practice for notebooks

```python
try:
    from huggingface_hub import notebook_login, whoami
    notebook_login()
    user = whoami()
    print(f"Authenticated as: {user['name']}")
except ImportError:
    print("Install with: !pip install -q huggingface_hub")
```

### Token scopes

| Scope         | Notebook use case                         |
|---------------|-------------------------------------------|
| Read          | Loading models, datasets, inference       |
| Write         | Uploading results, creating repos         |
| Inference     | Using InferenceClient in notebooks        |
| Manage org    | Team admin workflows                      |

## 7. Hub SDK Notebook Utilities

### HfFileSystem — remote FS from notebooks

```python
from huggingface_hub import HfFileSystem
fs = HfFileSystem()
for path in fs.ls("datasets/merve/emotion"):
    print(path)
```

### create_repo / upload_file from notebooks

```python
from huggingface_hub import create_repo, upload_file

repo_url = create_repo("my-results", private=True)
upload_file(
    path_or_fileobj="metrics.json",
    path_in_repo="results/metrics.json",
    repo_id="my-org/my-results",
    commit_message="Add results from notebook"
)
```

### snapshot_download

```python
from huggingface_hub import snapshot_download

local_path = snapshot_download(
    repo_id="my-org/my-model",
    local_dir="./models/my-model",
    token=True
)
```

## 8. Notebooks in Spaces

### Voilà dashboard Spaces

Convert notebooks to interactive dashboards with Voilà:

```yaml
# Space metadata
sdk: docker
app: voila your_notebook.ipynb
```

### Gradio / Streamlit companion notebooks

Space READMEs often link to companion notebooks via badge:

```markdown
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](
  https://colab.research.google.com/github/.../example.ipynb
)
```

### Linked datasets for notebook exploration

Use Data Studio for GUI exploration; notebooks for custom analysis.

## 9. Best Practices Summary

- **Pin versions**: `!pip install transformers==4.47.1` in first cell
- **Strip outputs** before committing to keep .ipynb small
- **Add Colab badge** to README for discoverability
- **Test end-to-end** in Colab/Kaggle before uploading custom `notebook.ipynb`
- **Use notebook_login()** at the top, never hardcode tokens
- **Keep notebooks under 10MB** for smooth Hub rendering
- **Use markdown cells** as documentation between code cells

## Limitations & Considerations

- **Large notebooks** (>10MB) may render slowly or timeout on the Hub
- **Custom CSS/JS** in notebook cells is not rendered on the Hub (security)
- **Interactive widgets** (ipywidgets, Plotly interact) are rendered as static snapshots
- **Colab-specific features** (e.g., `google.colab` auth) only work in Colab, not in the Hub viewer
- **Kaggle**: requires a Kaggle account; notebook is opened for editing, not auto-run
- **Custom `notebook.ipynb`** must be at the repo root and exactly named `notebook.ipynb`

## API Verification

You can verify notebook rendering or check for notebook files programmatically using the Hugging Face Hub API:

```python
from huggingface_hub import list_repo_files

# Check if a model repo has a custom notebook
files = list_repo_files("google/gemma-3-4b-it")
has_notebook = "notebook.ipynb" in files
print(f"Has custom notebook: {has_notebook}")

# List all .ipynb files in a dataset
notebooks = [f for f in list_repo_files("dataset-org/dataset-name", repo_type="dataset") 
             if f.endswith(".ipynb")]
print(f"Found {len(notebooks)} notebooks")
```

## References

- [Official Docs: Jupyter Notebooks on the Hub](https://huggingface.co/docs/hub/en/notebooks)
- [Original Blog: Notebook Rendering on the Hub](https://huggingface.co/blog/notebooks-hub)
- [Google Colab Partnership Blog](https://huggingface.co/blog/hf-google-colab)
- [Google Cloud Partnership Announcement](https://huggingface.co/blog/2025/google-cloud-partnership)
- [Jupyter Agents Blog: Training LLMs with Notebooks](https://huggingface.co/blog/jupyter-agent-2)
- [HF Cookbook](https://huggingface.co/learn/cookbook)
- [Hugging Face Hub Docs](https://huggingface.co/docs/hub)

## Support Files

| File | Description |
|------|-------------|
| `references/official-docs.md` | Raw HF Hub docs for notebooks — authoritative reference content |
| `scripts/verify-notebook-in-repo.py` | Verify whether a repo has notebook files and custom `notebook.ipynb`; usage: `python scripts/verify-notebook-in-repo.py <repo_id>` |
