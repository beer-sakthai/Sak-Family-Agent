---
name: SakThai-hf-datasets-uploading
version: 1.0.0
description: Complete end-to-end reference for uploading datasets to the Hugging Face
  Hub. Covers web UI, Git CLI, huggingface_hub Python SDK, hf CLI, dataset cards,
  metadata configuration, Data Studio preview, large-scale dataset uploads, Xet-accelerated
  uploads, and best practices for zero-cost dataset publishing.
category: mlops
tags:
- cli
- dataset-card
- datasets
- git
- hf
- hub
- huggingface
- python-sdk
- uploading
- xet
author: SakThai
---

# HF Hub — Uploading Datasets (End-to-End Workflow)

> **Support files:** `references/dataset-card-improvement-cron.md` — the recurring
> one-card-per-run cron workflow (tracker path, live-list resolution, standard
> upgrade set, documentation-only repo handling). Load it when improving Beer's
> dataset cards.

## Overview

Uploading datasets to the Hugging Face Hub makes them discoverable, versioned, and
usable with the `datasets` library and dozens of ML tools. The Hub supports four
primary upload methods, each suited to a different scenario:

| Method | Best For | Git/Versioning | Skill Level |
|--------|----------|---------------|-------------|
| **Web UI** | Small datasets, quick uploads, non-developers | ✓ (automatic) | Beginner |
| **`huggingface_hub` Python SDK** | Programmatic, large-scale, CI/CD pipelines | ✓ | Developer |
| **`hf upload` CLI** | Terminal workflows, folder syncing | ✓ | Developer |
| **Git CLI** | Advanced Git workflows, branches, PRs | ✓ | Expert |

## Prerequisites

1. **HF Account** — [Create one](https://huggingface.co/join) (free)
2. **Authentication** — Log in with `huggingface-cli login` or set `HF_TOKEN`
3. **Dataset format** — Recommended: Parquet for tabular/structured data, raw files
   for image/audio/video, WebDataset for large-scale streaming

## Method 1: Web UI Upload (No-Code)

### Step 1: Create a Dataset Repository

1. Go to [New Dataset](https://huggingface.co/new-dataset)
2. Enter a name (lowercase, hyphens preferred)
3. Choose **Public** (visible to everyone) or **Private** (org members only)
4. Click **Create dataset**

### Step 2: Upload Files

1. Navigate to the **Files and versions** tab
2. Click **Add file** → **Upload files**
3. Drag and drop files (`.csv`, `.parquet`, `.jsonl`, `.txt`, images, audio, video)
4. Write a commit message
5. Click **Commit changes**

### Step 3: Create a Dataset Card

1. Click **Create Dataset Card** — this creates a `README.md`
2. Fill in the **Metadata UI** (license, language, task categories, size, etc.)
3. Write documentation in the card body (description, use cases, limitations, ethical
   considerations, data source)
4. Click **Save**

The dataset card is essential for discoverability. Without proper metadata, the dataset
won't appear in relevant searches or filters.

## Method 2: `huggingface_hub` Python SDK (Programmatic)

### Authentication

```python
from huggingface_hub import HfApi, login

# Option A: Login via CLI (preferred for scripts)
login(token="hf_...")

# Option B: Pass token directly
api = HfApi(token="hf_...")
```

### Create a Dataset Repository

```python
api.create_repo(
    repo_id="username/my-dataset",
    repo_type="dataset",
    private=False,         # or True for private
    exist_ok=True,         # don't error if exists
)
```

### Upload a Single File

```python
api.upload_file(
    path_or_fileobj="/path/to/data.csv",       # local file path
    path_in_repo="data/train.csv",             # remote path
    repo_id="username/my-dataset",
    repo_type="dataset",
)
```

### Upload an Entire Folder

```python
api.upload_folder(
    folder_path="/path/to/local/dataset/",
    repo_id="username/my-dataset",
    repo_type="dataset",
    path_in_repo=".",                          # root of repo
    ignore_patterns=["**/*.tmp", "**/logs/*"], # optional
    allow_patterns=["*.jsonl", "*.parquet"],    # optional
)
```

### Upload with Deletion (Clean Before Push)

```python
api.upload_folder(
    folder_path="./new-data",
    repo_id="username/my-dataset",
    repo_type="dataset",
    path_in_repo="data/",
    delete_patterns=["*.txt"],                  # delete remote .txt before uploading
)
```

### Non-Blocking Upload (Background)

```python
future = api.upload_folder(
    folder_path="./checkpoints",
    repo_id="username/my-dataset",
    repo_type="dataset",
    run_as_future=True,                         # non-blocking
)
# Do other work...
future.result()                                 # wait for completion
```

### Upload via `push_to_hub()` (datasets library)

If the dataset is already loaded with the 🤗 Datasets library:

```python
from datasets import Dataset

dataset = Dataset.from_csv("data.csv")
dataset.push_to_hub(
    "username/my-dataset",
    split="train",          # optional split name
    private=False,
)
```

## Method 3: `hf upload` CLI

### Single File

```bash
hf upload username/my-dataset ./data.csv data/train.csv
```

### Entire Folder

```bash
hf upload username/my-dataset ./dataset-folder .
```

### Using `hf://` URI Syntax

```bash
hf upload hf://datasets/username/my-dataset@main/data/ ./local-data/
```

### Large Upload with Performance Mode

```bash
# Set performance mode for max throughput
export HF_XET_HIGH_PERFORMANCE=1
hf upload username/my-dataset ./large-dataset .
```

## Method 4: Git CLI

Since dataset repos are Git repositories:

```bash
# Clone (empty repo)
git clone https://huggingface.co/datasets/username/my-dataset
cd my-dataset

# Add files
cp /path/to/data.csv .
git add .
git commit -m "Add dataset files"

# Push (uses Git LFS for large files automatically)
git push
```

For large files (>5MB), the Hub's Xet backend handles chunking and deduplication
automatically — no manual LFS configuration needed.

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Large-Scale Dataset Uploads, Parquet Sharding & Webhooks](./references/large-scale-dataset-uploads.md).
