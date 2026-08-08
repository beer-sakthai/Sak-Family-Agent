---
name: SakThai-hf-datasets-streaming-deep-dive
description: "Complete deep-dive into Hugging Face Datasets streaming — load, process, and train with IterableDataset for large-scale data without downloading the full dataset. Covers streaming from Hub, local files, Parquet column projection/filter pushdown, Iter"
---

# Hugging Face Datasets Streaming — Deep Dive

## Why streaming matters

Dataset streaming lets you work with a dataset **without downloading it**. Data is fetched on-the-fly as you iterate. Essential when:

- Dataset size exceeds available disk space (e.g., FineWeb = 45 TB)
- You don't want to wait for a full download before exploring
- You need to quickly sample a few examples
- Running on a resource-constrained environment (Beer's case: no income, limited disk)
- You want zero-cost operation — streaming uses HTTP range requests, no GPU/storage billing

**Three key wins for Beer:**
1. **No disk space needed** — stream 45 TB datasets on a laptop
2. **Instant start** — first sample in milliseconds, not hours
3. **Free forever** — no download bandwidth costs, no local storage costs

## Two dataset types

| Feature | `Dataset` | `IterableDataset` (streaming) |
|---------|-----------|-------------------------------|
| Loading | Full download + Arrow cache | On-the-fly from source |
| Memory | Entire dataset in memory/disk | One sample (or batch) at a time |
| Random access | ✅ O(1) by index | ❌ Must iterate sequentially |
| Map/Filter | Applied eagerly, cached | Applied lazily, on-the-fly |
| Best for | Small/medium datasets, random access | Large datasets, training loops |

## Loading in streaming mode

### From the Hub
```python
from datasets import load_dataset

# Standard loading (downloads everything)
dataset = load_dataset("HuggingFaceFW/fineweb", split="train")

# Streaming mode (instant, no download)
dataset = load_dataset("HuggingFaceFW/fineweb", split="train", streaming=True)

# First sample in milliseconds
print(next(iter(dataset)))
```

### From local files (no Arrow conversion)
```python
data_files = {"train": "path/to/oscar/*.jsonl.gz"}
dataset = load_dataset("json", data_files=data_files, split="train", streaming=True)
```

No conversion to Arrow — data streams directly from the original files.

### Parquet: column projection + filter pushdown

Parquet's columnar format enables efficient partial reads:

```python
# Only load two columns
dataset = load_dataset(
    "HuggingFaceFW/fineweb", split="train", streaming=True,
    columns=["url", "date"]
)

# Push down a filter (language_score >= 0.99)
dataset = load_dataset(
    "HuggingFaceFW/fineweb", split="train", streaming=True,
    filters=[("language_score", ">=", 0.99)]
)
```

This is **zero-cost data filtering** — only matching rows are deserialized.

### Convert existing Dataset to IterableDataset

```python
# Faster: convert from already-cached Dataset
iterable = dataset.to_iterable_dataset()

# Slower: re-stream from source
iterable = load_dataset("ethz/food101", streaming=True)
```

`to_iterable_dataset()` supports **sharding** for parallel loading:

```python
iterable = dataset.to_iterable_dataset(num_shards=64)
iterable = iterable.shuffle(buffer_size=10_000)
dataloader = DataLoader(iterable, num_workers=4)  # 64/4 = 16 shards per worker
```

## Core IterableDataset API

### Column operations
```python
# Rename
dataset = dataset.rename_column("text", "content")

# Remove columns
dataset = dataset.remove_columns("timestamp")

# Cast feature types
new_features = dataset.features.copy()
new_features["label"] = ClassLabel(names=["negative", "positive"])
dataset = dataset.cast(new_features)

# Cast single column
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))
```

### Shuffle
```python
shuffled = dataset.shuffle(seed=42, buffer_size=10_000)

# Reshuffle per epoch (seed changes: seed + epoch)
for epoch in range(epochs):
    shuffled.set_epoch(epoch)
    for example in shuffled:
        ...
```

**buffer_size** controls the shuffle window. Larger = better randomness, more memory.

### Take and Skip (dataset splitting)
```python
head = dataset.take(5)           # First 5 examples
train = shuffled.skip(1000)      # Skip first 1000
```

⚠️ `take`/`skip` lock shard order — shuffle **before** splitting.

### Shard and Reshard
```python
# Divide into N shards, pick one
shard_0 = dataset.shard(num_shards=2, index=0)

# Increase shard count (useful for parallelism)
dataset = dataset.reshard()  # e.g., 4 → 3600 shards via Parquet row groups
```

### Map (on-the-fly processing)
```python
def add_prefix(example):
    example["text"] = "Prefix: " + example["text"]
    return example

dataset = dataset.map(add_prefix)

# With column removal
dataset = dataset.map(add_prefix, remove_columns=["timestamp", "url"])

# Batch processing (default batch_size=1000)
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def encode(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length")

dataset = dataset.map(encode, batched=True, remove_columns=["text"])
```

### Filter
```python
# By value
filtered = dataset.filter(lambda x: x["text"].startswith("San Francisco"))

# By index
even = dataset.filter(lambda x, idx: idx % 2 == 0, with_indices=True)
```

### Batch (create fixed-size batches)
```python
# Yield batches of 32
batched = dataset.batch(batch_size=32, drop_last_batch=True)
for batch in batched:
    # batch is a dict of lists/lists-of-tensors
```

### Concatenate
```python
from datasets import concatenate_datasets

stories = load_dataset("ajibawa-2023/General-Stories-Collection", split="train", streaming=True)
stories = stories.select_columns(["text"])
wiki = load_dataset("wikimedia/wikipedia", "20231101.en", split="train", streaming=True)
wiki = wiki.select_columns(["text"])

combined = concatenate_datasets([stories, wiki])
# Horizontal concatenation
combined = concatenate_datasets([stories, stories_ids], axis=1)
```

### Interleave
```python
from datasets import interleave_datasets

es = load_dataset("allenai/c4", "es", split="train", streaming=True)
fr = load_dataset("allenai/c4", "fr", split="train", streaming=True)

# Alternating
multi = interleave_datasets([es, fr])

# With sampling probabilities
multi = interleave_datasets([es, fr], probabilities=[0.8, 0.2], seed=42)
```

`stopping_strategy` options:
- `first_exhausted` (default): stops when any dataset runs out
- `all_exhausted`: oversamples — loops exhausted datasets until all are seen
- `all_exhausted_without_replacement`: every sample exactly once

## Training loop integration

### PyTorch
```python
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForMaskedLM, DataCollatorForLanguageModeling

dataset = load_dataset("allenai/c4", "en", split="train", streaming=True)
dataset = dataset.shuffle(seed=42, buffer_size=10_000)
dataset = dataset.with_format("torch")

dataloader = DataLoader(dataset, collate_fn=DataCollatorForLanguageModeling(tokenizer), num_workers=4)

model = AutoModelForMaskedLM.from_pretrained("distilbert-base-uncased")
model.train()

for batch in dataloader:
    outputs = model(**batch)
    loss = outputs.loss
    loss.backward()
    optimizer.step()
```

### Using HfFileSystem (raw HTTP streaming)
```python
from huggingface_hub import hffs

# Stream a single file
with hffs.open("datasets/allenai/c4/en/c4-train.00000-of-01024.json.gz", "r") as f:
    print(f.readline())

# With Pandas batch reader
import pandas as pd
with hffs.open("datasets/YOUR_REPO/data.csv") as f:
    for df in pd.read_csv(f, iterator=True, chunksize=5):
        print(len(df))  # 5 rows at a time
```

### cURL for quick inspection
```bash
# Stream first 5 lines
curl -L https://huggingface.co/datasets/fka/awesome-chatgpt-prompts/resolve/main/prompts.csv | head -n 5

# Range request (bytes 40-88)
curl -r 40-88 -L https://huggingface.co/datasets/fka/awesome-chatgpt-prompts/resolve/main/prompts.csv

# Private repos
export HF_TOKEN=hf_xxx
curl -H "Authorization: Bearer $HF_TOKEN" -L https://huggingface.co/...
```

## Parquet streaming (advanced)

Parquet is the recommended format for streaming on HF. **Row groups** (~100 MB each) are the unit of streaming iteration. **Pages** (~1 MB) are the smallest compressed unit.

### PyArrow row-group streaming
```python
import pyarrow.parquet as pq

with pq.ParquetFile("hf://datasets/HuggingFaceFW/finewiki/data/enwiki/000_00000.parquet") as pf:
    for i in range(pf.num_row_groups):
        table = pf.read_row_group(i)
        df = table.to_pandas()
```

PyArrow supports `hf://` paths natively via HfFileSystem.

### Efficient random access (Rust with page index)
```rust
use parquet::arrow::ParquetRecordBatchStreamBuilder;
// Page-level access for sub-row-group precision
// Requires write_page_index=True during Parquet creation
```

Page indexes enable the Dataset Viewer to show data without row-group size limits.

## Best practices for Beer (zero-cost operation)

1. **Always prefer `streaming=True`** when exploring new datasets
2. **Use Parquet with column projection** — only fetch columns you need
3. **Use filter pushdown** on Parquet to skip rows at the source
4. **Batch operations** with `batched=True` in `map()` for tokenization
5. **Use `to_iterable_dataset(num_shards=N)`** for faster local streaming
6. **Set `buffer_size` to 10,000–100,000** for good shuffle quality
7. **Use `set_epoch()`** for proper per-epoch reshuffling in training
8. **Avoid `take()`/`skip()`** before `shuffle()` — they lock shard order
9. **Use `interleave_datasets()`** for multilingual training without disk space
10. **Stream directly from HF with cURL** for quick data inspection — no Python needed

## Gotchas

| Issue | Symptom | Fix |
|-------|---------|-----|
| `take()` after `shuffle()` loses randomness | Deterministic samples | Restructure: shuffle → take → use |
| `num_workers > 1` with IterableDataset | Deadlocks | Use `to_iterable_dataset(num_shards=N)` first |
| Reshuffling each epoch not happening | Same order every epoch | Call `set_epoch(epoch)` between epochs |
| Column not found after map | KeyError | Check `remove_columns` vs returning correct keys |
| Large `buffer_size` OOM | MemoryError | Reduce buffer_size (start at 1,000 for testing) |
| `load_dataset()` with `streaming=True` re-downloads | Wait every session | Use `to_iterable_dataset()` from cached `Dataset` |

## Reference

- [Streaming docs (datasets library)](https://huggingface.co/docs/datasets/en/stream)
- [Streaming on Hub](https://huggingface.co/docs/hub/en/datasets-streaming)
- [IterableDataset API reference](https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.IterableDataset)
- [HfFileSystem docs](https://huggingface.co/docs/huggingface_hub/en/guides/hf_filesystem)
- [Parquet format on HF](https://huggingface.co/docs/hub/en/datasets-parquet)
