---
name: sakthai-hf-datasets
description: "Hugging Face Datasets: fast, flexible library for loading, processing, and streaming datasets — bridging the gap between data storage and ML frameworks like PyTorch, TensorFlow, JAX, and Pandas."
tags: [huggingface, datasets, streaming, arrow, cache, preprocessing, mlops]
---

# Hugging Face Datasets

**The `datasets` library** provides a unified interface to thousands of datasets on the Hugging Face Hub, plus tools to load, process, cache, and stream data for machine learning pipelines.

## Core Concepts

- **`Dataset`** — in-memory, random-access table (pyarrow-backed).
- **`IterableDataset`** — streaming dataset that yields examples on-the-fly; useful for datasets too large to fit in memory or disk.
- **Arrow backend** — all columnar data lives in Apache Arrow format, enabling zero-copy reads, fast slicing, and efficient memory sharing with PyTorch/TensorFlow/NumPy/JAX.

## Installation

```bash
pip install datasets

# With extras for specific modalities:
pip install datasets[audio]    # audio decoding via torchcodec
pip install datasets[vision]   # image decoding via PIL/Pillow
pip install datasets[parquet]  # Parquet streaming/packing
```

## Loading from the Hub

```python
from datasets import load_dataset

# Simple load
dataset = load_dataset("glue", "mrpc", split="train")

# With config and splits
dataset = load_dataset("PolyAI/minds14", "en-US", split="train")

# Streaming (no full download)
dataset = load_dataset("HuggingFaceFW/fineweb", split="train", streaming=True)
```

`load_dataset()` accepts:
- `path` — Hub repo ID (e.g., `"glue"`, `"user/my-dataset"`) or local module.
- `name` — dataset configuration/builder name (when a repo has multiple subsets).
- `split` — `"train"`, `"test"`, `"validation"`, or `"train[:10%]"` slicing.
- `streaming` — `True` returns an `IterableDataset`.
- `data_files` — explicit file URLs/globs for manual loading.
- `token` — HF token for private datasets.

## Caching

- Download/cache location defaults to `~/.cache/huggingface/datasets`.
- Each dataset is cached by its unique hash of `(path, config, revision, ...)`.
- Cached files are **immutable** Arrow/Parquet files unless you explicitly modify the dataset.
- Use `datasets.builder.BuilderConfig` or `load_dataset(..., download_mode="force_redownload")` to refresh.
- Cache can be relocated with environment variables (`HF_HOME`, `HF_DATASETS_CACHE`).

## IterableDataset (Streaming)

When `streaming=True`, `load_dataset` returns an `IterableDataset`:

```python
from datasets import load_dataset

ds = load_dataset("HuggingFaceFW/fineweb", split="train", streaming=True)
print(next(iter(ds)))
```

Key features:
- **Instant use** — no need to wait for TB-scale downloads; data is fetched as needed.
- **Sharding** — `ds = ds.to_iterable_dataset(num_shards=64)` splits a dataset into parallel-friendly shards.
- **Shuffling** — `ds.shuffle(seed=42, buffer_size=10_000)` uses an in-memory buffer.
- **Epoch handling** — `ds.set_epoch(epoch)` for reshuffling between training epochs.
- **Column/subset selection** — `ds = load_dataset(..., streaming=True, columns=["url", "date"])` reduces bandwidth.
- **Filtering** — `ds = load_dataset(..., streaming=True, filters=[("language_score", ">=", 0.99)])` pushes predicates down where supported (Parquet).

**When to use IterableDataset:**
- Dataset > available disk space.
- Quick exploratory sampling (`next(iter(ds))`).
- Continuous training on evolving streams.
- Training with PyTorch `DataLoader(num_workers=...)` — shards automatically distribute across workers.

**When NOT to use:**
- Jobs requiring random access (no `dataset[5]`).
- Need to call `dataset.train_test_split()` — converts to `Dataset`.
- Small, static datasets where caching is preferable.

## Map and Process in Batches

```python
def preprocess(examples):
    return tokenizer(examples["text"], truncation=True, max_length=128)

dataset = dataset.map(preprocess, batched=True, batch_size=1000)
```

- `map()` applies a function to all (or selected) examples.
- `batched=True` passes lists of examples for vectorized tokenization/feature extraction.
- `remove_columns` drops unwanted columns after processing.
- `with_indices` and `input_columns` provide flexibility.
- For `IterableDataset`, `map()` returns another `IterableDataset`.

## Formatting for ML Frameworks

```python
# PyTorch
dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
loader = torch.utils.data.DataLoader(dataset, batch_size=8)

# TensorFlow
tf_ds = dataset.to_tf_dataset(columns=["input_ids", "labels"], batch_size=8, shuffle=True)

# NumPy / JAX
dataset.set_format(type="numpy", columns=["input_ids", "labels"])
```

## Dataset Features

`datasets.Features` declares the schema:

```python
from datasets import Dataset, Features, Value, ClassLabel

features = Features({
    "text": Value("string"),
    "label": ClassLabel(names=["negative", "positive"]),
})
```

Built-in feature types: `Value`, `ClassLabel`, `Sequence`, `Translation`, `Image`, `Audio`, `Array2D`, `Array3D`, `Array4D`, `Array5D`, `Binary`, `Timestamp`.

## Cache Management

```python
from datasets import load_dataset

# Force re-download
ds = load_dataset("glue", "mrpc", split="train", download_mode="force_redownload")

# Verify cache path
from datasets import get_dataset_config_names, get_dataset_split_names
```

Command-line tool:
```bash
datasets-cli env                         # show cache and env info
datasets-cli test --dataset_config_name glue --dataset_name mrpc
datasets-cli download --dataset_config_name glue --dataset_name mrpc
```

## Create / Share a Dataset

```python
from datasets import Dataset

data = {"text": ["Hello world", "How are you?"], "label": [0, 1]}
ds = Dataset.from_dict(data)
ds.push_to_hub("your-username/your-dataset")

# With a card
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj=b"---\nlicense: mit\n---\n",
    path_in_repo="README.md",
    repo_id="your-username/your-dataset",
    repo_type="dataset",
)
```

## Common Pitfalls

- **IterableDataset limitations** — slicing (`ds[:10]`) and `train_test_split()` are not supported; convert with `.to_iterable_dataset()` or `.from_generator()` if needed.
- **Memory mapping** — `Dataset` uses mmap; avoid modifying tensors in-place during training as it may corrupt the cache.
- **Audio/Video decoding** — requires `datasets[audio]` or `datasets[vision]` extras; otherwise decode manually with `ffmpeg`/`PIL`.
- **Cache invalidation** — change `name`/`revision`/`trust_remote_code` to force a different cache hash; same parameters reuse the cache.
- **Parallel map()** — use `num_proc=4` with `map()` for CPU-bound preprocessing; it does not change `batched=True` semantics.

## References

- Docs: https://huggingface.co/docs/datasets
- GitHub: https://github.com/huggingface/datasets
- Streaming: https://huggingface.co/docs/datasets/main/en/stream
- Cache management: https://huggingface.co/docs/datasets/main/en/cache

## Research & Fallback Notes

- When `web_search` / `web_extract` (Firecrawl) returns a billing error, fall back to `curl -sL <url>` via the terminal tool. For Hugging Face docs, raw markdown sources are available at `https://raw.githubusercontent.com/huggingface/<repo>/main/docs/source/<page>.md[x]`.
- Example fetch pattern used when researching HF topics:
  ```bash
  curl -sL --max-time 30 "https://raw.githubusercontent.com/huggingface/datasets/main/docs/source/loading.mdx" | sed -n '1,200p'
  ```
- This bypasses SaaS scrapers while still pulling the canonical source text.