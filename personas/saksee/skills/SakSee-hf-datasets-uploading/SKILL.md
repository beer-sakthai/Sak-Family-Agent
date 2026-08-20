---
name: SakSee-SakThai-hf-datasets-uploading
description: '>-   Complete end-to-end reference for uploading datasets to the Hugging Face Hub.   Covers
  web UI, Git CLI, huggingface_hub Python SDK, hf CLI, dataset cards,   metadata configuration,
  Data Studio preview, large-scale dataset uploads,   Xet-accelera'
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

## Large-Scale Dataset Uploads

### Uploading by Chunks

For massive datasets (hundreds of GBs to TBs):

```python
# The Hub's Xet backend handles chunking automatically.
# Just call upload_folder and it will:
# 1. Stream files in parallel
# 2. Split into multiple commits if needed
# 3. Resume on interruption (no data lost)
api.upload_folder(
    repo_id="username/large-dataset",
    repo_type="dataset",
    folder_path="/path/to/1tb-dataset",
)
```

### Xet Performance Tips

| Setting | Effect | When to Use |
|---------|--------|-------------|
| `HF_XET_HIGH_PERFORMANCE=1` | Max bandwidth + CPU | Large uploads on fast network |
| `HF_XET_CACHE=/local/ssd/cache` | Avoid NFS slowdown | Uploading from cluster/distributed FS |

### Resuming Interrupted Uploads

Xet uploads are **resumable by design** — just re-run the same command:

```python
# If interrupted, re-run:
api.upload_folder(
    repo_id="username/my-dataset",
    repo_type="dataset",
    folder_path="/path/to/dataset",
)
# Already-committed files are detected and skipped.
# Already-uploaded chunks are deduplicated (near-zero data transfer).
```

### What Happens Under the Hood

```
Found 5,000 files to upload
  Preparing   ████████████████████  5,000 / 5,000 ✓
  Uploading   ██████████████░░░░░░  423 / 603 files  3.8GB · 19.7MB/s
  Committing  ██████████████████░░  4,580 / 5,000  6 commits
```

The `upload_folder` method:
1. **Prepares**: scans files, checks against Hub, computes hashes
2. **Uploads**: streams to Xet CAS (content-addressable storage) with chunk dedup
3. **Commits**: creates Git commits in adaptive batches (avoids server limits)

## Dataset Card & Metadata

### Essential Metadata Fields

```yaml
# In README.md frontmatter
license: apache-2.0
language:
  - en
task_categories:
  - text-classification
  - token-classification
size_categories:
  - 10K<n<100K
```

### Programmatic Dataset Card Creation

```python
from huggingface_hub import DatasetCard

card = DatasetCard.from_template(
    repo_id="username/my-dataset",
    pretty_name="My Dataset",
    description="A dataset for...",
    license="mit",
    language=["en"],
    task_categories=["text-classification"],
)

card.push_to_hub("username/my-dataset", repo_type="dataset")
```

## Data Studio Preview

After uploading, the Data Studio automatically parses and displays the data if:
- The dataset contains recognized file formats (CSV, Parquet, JSONL, Arrow)
- It's public, or the user has PRO/Team access for private datasets

To configure the preview (which columns/splits to show):

```bash
# Upload a dataset with a dataset_infos.json or dataset_dict.jsonl
# for configuring splits, features, and preview settings
```

See the [Data files Configuration](https://huggingface.co/docs/hub/en/datasets-data-files-configuration) docs for configuring how the viewer displays your data.

## Supported File Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| Parquet | `.parquet` | ⭐ Recommended — compressed, typed, columnar |
| CSV/TSV | `.csv, .tsv` | Simple tabular data |
| JSON Lines | `.jsonl` | Nested/structured data per row |
| JSON | `.json` | Single JSON document |
| Arrow | `.arrow` | In-memory dataframe exchange |
| Text | `.txt` | Raw text corpora |
| Images | `.png, .jpg, .webp, .svg` | Vision datasets |
| Audio | `.wav, .mp3, .flac, .ogg` | Speech/audio datasets |
| Video | `.mp4, .mov, .avi` | Video datasets |
| PDF | `.pdf` | Document datasets |
| WebDataset | `.tar` | Large-scale streaming (images + metadata) |
| Lance | `.lance` | High-performance columnar storage |

Compressed: `.zip`, `.gz`, `.zst`, `.bz2`, `.lz4`, `.xz`

### Recommendation
- **Tabular/structured data**: Parquet (efficient, typed, fast to query)
- **Nested data**: JSON Lines
- **Images/Audio/Video**: Raw files for individual access; WebDataset/Parquet for scale
- **Small datasets (<1GB)**: CSV or JSON Lines are fine

## Versioning & Branches

All dataset uploads are Git commits. You can:

```bash
# Create a branch
git branch data-v2

# Upload to a specific branch
api.upload_file(
    path_or_fileobj="data.csv",
    path_in_repo="data.csv",
    repo_id="username/my-dataset",
    repo_type="dataset",
    revision="data-v2",
)
```

Use branches for:
- **Iterating** on dataset versions without breaking existing users
- **Pull requests** for collaborative review before merging
- **Staging** data before public release

## CI/CD Integration

### GitHub Actions

```yaml
name: Upload Dataset

on:
  push:
    branches: [main]

jobs:
  upload:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install huggingface-hub datasets
      - run: |
          python -c "
          from huggingface_hub import HfApi
          api = HfApi(token='${{ secrets.HF_TOKEN }}')
          api.upload_folder(
              repo_id='org/my-automated-dataset',
              repo_type='dataset',
              folder_path='./data',
          )
          print('Dataset uploaded successfully!')
          "
```

### Scheduled Uploads (HF Jobs)

```bash
hf jobs run \
  --image python:3.11 \
  "pip install huggingface_hub datasets && python scripts/upload-dataset.py"
```

## Pitfalls

| Pitfall | Symptom | Mitigation |
|---------|---------|------------|
| Forgot `repo_type="dataset"` | File appears in wrong repo type | Always specify `repo_type="dataset"` |
| Uploading non-standard formats | Data Studio can't preview | Convert to Parquet/CSV/JSONL first |
| Hitting storage quota | Upload fails with 4xx | Check [storage limits](https://huggingface.co/docs/hub/en/storage-limits) |
| Git LFS confusion | Large files rejected | Xet handles this automatically in recent versions |
| Interrupted large upload | Partial data | Xet uploads are resumable — just re-run |
| Missing dataset card | Poor discoverability | Always add `README.md` with metadata |
| `path_in_repo` typo | Files in wrong folder | Double-check paths before uploading |
| Uploading duplicate files | Wasted time | Use `upload_folder` which detects already-committed files |
| No authentication | `401 Unauthorized` | Run `huggingface-cli login` first |
| **`upload_file` result is a `CommitInfo` dataclass, not a dict** | `result.get("commit_url")` raises `AttributeError: 'CommitInfo' object has no attribute 'get'` | Use attribute access: `result.commit_url` (a URL string; `.split("/")[-1]` gives the SHA). The upload itself succeeded — the error is only in reading the result. |
| **Verifying a commit SHA: `/api/datasets/{id}/commit/{sha}` returns 404** | "HTTP Error 404: Not Found" when checking a just-made commit | That endpoint does not exist. Fetch `GET /api/datasets/{id}/commits/main` and match the `id` field against your SHA; confirm via the commit `title`/`date`. |
| **Raw README fetch needs auth** | `curl https://huggingface.co/datasets/{id}/raw/main/README.md` → `Invalid username or password` (or `Repository not found` for a wrong/renamed id) | Always send `-H "Authorization: Bearer $HF_TOKEN"`. Fetch the dataset list first (`/api/datasets?author={user}`) to get the exact live repo IDs — don't trust a stale asset list. |
| **`resolve/main/<file>` data URLs redirect** | `curl .../resolve/main/data/train.jsonl` (no `-L`) saves a 281-byte "Temporary Redirect" body → JSONDecodeError when parsing | Use `curl -sL` on all `resolve/main/` URLs (they 302 to `/api/resolve-cache/...`); `raw/main/README.md` does not redirect but `-L` is harmless. For file inventory use `GET /api/datasets/{id}/tree/main?recursive=true` (no redirect, returns path/size/type). |
| **Documentation-only dataset repos** | `load_dataset()` / datasets-server `/splits` → `No (supported) data files found`; only README.md + LICENSE in tree | The repo is metadata-only (seed data migrated elsewhere). Improve the card anyway: document the schema + XML format, add a stats table, and give a **fallback loading example** pointing at the successor dataset. State explicitly that no data files are hosted. |
| **Row-count verification needs `/size`, not `/splits`** | datasets-server `/splits` returns no `num_rows`; `/first-rows` 404s when the config isn't named `default` (e.g. combined-v6, food-penguin, kaggle) | Use `https://datasets-server.huggingface.co/size?dataset={id}` → `size.dataset.num_rows` + `num_bytes_parquet_files` (verified: v7=2424, bench-v2=500, irrelevance-supplement=60). Fall back to counting the raw JSONL/parquet if `/size` 500s. |
| **Cards overstate schema diversity & uniformity** | Card claims "5 distinct tool schemas" / "all responses use X" but raw data disagrees | Hash each row's `tools` array (`md5(json.dumps(tools, sort_keys=True))`) and count distinct hashes; count response-style variants (e.g. `<tool_reject>` 32/60 vs direct 28/60). Verify every numeric claim against the raw data before keeping it — including download counts in ALL tables (model + ecosystem), which drift fast; refresh them live and annotate "verified live YYYY-MM-DD". |
| **Multi-agent concurrent write (silent overwrite)** | **Content reverts to a different state; eval files show wrong model data** | **Always record commit SHA before writes; verify content after every write; never use a shared generic filename (e.g. `health-check.yaml`) — use a unique per-model/per-task name (e.g. `health-check-{model-name}.yaml`). Assume sibling agents can write to the same repo simultaneously. For enrichment: use append-only, never load-edit-save; reject any write where the row count drops.** |

## Verification Checklist

- [ ] Dataset repo created with correct name
- [ ] Files uploaded in supported format (Parquet preferred)
- [ ] Dataset card (`README.md`) with metadata (license, language, task)
- [ ] Data Studio preview works correctly
- [ ] Dataset is publicly accessible (if intended)
- [ ] Split structure is correct (train/val/test)
- [ ] Files are not duplicates (check using `list_repo_files`)
- [ ] Search works: dataset appears in relevant HF searches

## References

- [Official Docs: Uploading Datasets](https://huggingface.co/docs/hub/en/datasets-adding)
- [huggingface_hub Upload Guide](https://huggingface.co/docs/huggingface_hub/guides/upload)
- [Dataset Cards Documentation](https://huggingface.co/docs/hub/en/datasets-cards)
- [Dataset Card YAML Spec](https://github.com/huggingface/hub-docs/blob/main/datasetcard.md)
- [Python API: upload_file](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api#huggingface_hub.HfApi.upload_file)
- [Python API: upload_folder](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api#huggingface_hub.HfApi.upload_folder)
- [CLI: hf upload](https://huggingface.co/docs/huggingface_hub/guides/cli#hf-upload)
- [Storage Limits & Recommendations](https://huggingface.co/docs/hub/en/storage-limits)
- [Data files Configuration](https://huggingface.co/docs/hub/en/datasets-data-files-configuration)
- [Ingesting Datasets](https://huggingface.co/docs/hub/en/datasets-ingesting)
- [Xet Storage Overview](https://huggingface.co/docs/hub/en/xet/index)
