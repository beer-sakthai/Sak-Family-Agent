# HF Datasets Text Processing and Deduplication Pipeline

**Date:** 2026-07-25
**Author:** SakThai
**License:** MIT

## Overview

A zero-cost, local-only pipeline for loading, cleaning, processing, and
deduplicating text datasets using the `datasets` library (≥4.8, confirmed
working on 5.0.0). Everything runs on CPU — no GPU or API credits needed.

---

## 1. Text Data Loading

```python
from datasets import load_dataset

# Load text files line-by-line (default)
ds = load_dataset("text", data_files="corpus.txt", split="train")

# Advanced TextConfig options
ds = load_dataset(
    "text",
    data_files="corpus.txt",
    split="train",
    encoding="utf-8",
    chunksize=10 << 20,        # 10MB chunks (default)
    keep_linebreaks=False,      # strip newlines from lines
    sample_by="line",           # "line" | "paragraph" | "document"
)
```

When `sample_by="paragraph"`, blank lines separate paragraphs. When
`sample_by="document"`, `\n\n` sequences separate documents.

### Loading multiple files

```python
# Single split from multiple files
ds = load_dataset("text", data_files=["file1.txt", "file2.txt"], split="train")

# Multiple named splits
ds = load_dataset("text", data_files={"train": "train.txt", "test": "test.txt"})
```

---

## 2. Text Cleaning and Filtering

### Filter by text length (handle None-safe)

```python
def filter_length(example):
    t = example["text"]
    if t is None:
        return False
    # Remove empty / too-short / too-long
    return 5 <= len(t) <= 10000

ds_clean = ds.filter(filter_length, desc="Filtering by length")
```

### Batch filter for speed (10-100x faster on large datasets)

```python
def batch_filter(batch):
    texts = batch["text"]
    mask = []
    for t in texts:
        if t is None or len(t) < 5:
            mask.append(False)
        else:
            mask.append(True)
    return mask

ds_clean = ds.filter(batch_filter, batched=True, batch_size=1000,
                     desc="Batch length filter")
```

### Regex-based content filtering

```python
import re

BAD_PATTERNS = [
    r'https?://\S+',      # URLs
    r'<script[^>]*>',     # HTML tags
    r'[^\x20-\x7E]+',     # non-ASCII (for English-only)
]

def filter_bad_content(example):
    t = example["text"]
    if t is None:
        return False
    for pat in BAD_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return False
    return True

ds_filtered = ds.filter(filter_bad_content, desc="Removing bad content")
```

### Removing empty rows

```python
# Remove rows where text is None or empty string or whitespace-only
def non_empty(example):
    t = example.get("text")
    return t is not None and t.strip() != ""

ds = ds.filter(non_empty)
```

---

## 3. Text Processing with map()

### Tokenize text (adding new columns)

```python
def tokenize_fn(example):
    words = example["text"].split()
    return {
        "tokens": words,
        "num_tokens": len(words),
    }

ds = ds.map(tokenize_fn, desc="Tokenizing")
```

### Add computed columns (char count, word count)

```python
def add_stats(example):
    t = example["text"]
    return {
        "char_count": len(t),
        "word_count": len(t.split()),
        "avg_word_len": sum(len(w) for w in t.split()) / max(len(t.split()), 1),
    }

ds = ds.map(add_stats, desc="Adding text statistics")
```

### Batched processing (for tokenizers)

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

def tokenize_batch(batch):
    return tokenizer(
        batch["text"],
        padding="max_length",
        truncation=True,
        max_length=512,
    )

ds = ds.map(tokenize_batch, batched=True, batch_size=1000,
            desc="Tokenizing batches")
```

### Remove columns after processing

```python
# Process first, then drop raw text to save memory
ds = ds.map(tokenize_fn, remove_columns=["text"],
            desc="Tokenize and drop raw")
```

---

## 4. Exact Deduplication

### Method A: filter() with Python set (memory-efficient)

**Best for datasets < ~10M rows** (set fits in memory).

```python
seen_texts = set()

def dedup_exact(example):
    t = example["text"]
    if t in seen_texts:
        return False
    seen_texts.add(t)
    return True

ds_dedup = ds.filter(dedup_exact, desc="Exact deduplication")
```

### Method B: Multi-column dedup

```python
seen_pairs = set()

def dedup_multi(example):
    key = (example["text"], example["source"])
    if key in seen_pairs:
        return False
    seen_pairs.add(key)
    return True

ds_dedup = ds.filter(dedup_multi, desc="Multi-column dedup")
```

### Method C: Pandas drop_duplicates (convenient, PyArrow-backed)

```python
df = ds.to_pandas()
df_dedup = df.drop_duplicates(subset=["text"], keep="first")
ds_dedup = Dataset.from_pandas(df_dedup)
```

⚠ **Caveat**: `to_pandas()` materializes the entire dataset in memory. Use
only for datasets that fit in RAM. For huge datasets, use Method A with
streaming (see §7).

### Method D: Keep first vs. keep last

```python
# Keep first occurrence (default)
df.drop_duplicates(subset=["text"], keep="first")

# Keep last occurrence
df.drop_duplicates(subset=["text"], keep="last")

# Drop all duplicates entirely
df.drop_duplicates(subset=["text"], keep=False)
```

---

## 5. Fuzzy Deduplication (MinHash LSH)

When texts are near-duplicates (e.g., with minor typos or reformatting), exact
dedup isn't enough. Install `datasketch` for MinHash LSH:

```bash
pip install datasketch
```

### MinHash with Jaccard similarity

```python
from datasketch import MinHash, MinHashLSH
import re

def shingle(text, k=5):
    """Generate k-shingles from text."""
    text = re.sub(r'\s+', ' ', text.lower())
    return {text[i:i+k] for i in range(len(text) - k + 1)}

# Build LSH index
lsh = MinHashLSH(threshold=0.8, num_perm=128)
seen = {}

def dedup_fuzzy(example, idx):
    t = example["text"]
    if not t or len(t) < 20:
        return True  # keep short texts as-is
    
    m = MinHash(num_perm=128)
    for sh in shingle(t, k=5):
        m.update(sh.encode('utf-8'))
    
    # Check if similar to anything already seen
    result = lsh.query(m)
    if result:
        return False  # near-duplicate
    
    lsh.insert(f"doc{idx}", m)
    return True

# Note: filter doesn't pass idx by default, use with_indices=True
ds_dedup = ds.filter(dedup_fuzzy, with_indices=True,
                     desc="Fuzzy dedup (MinHash LSH)")
```

### Memory-efficient fuzzy dedup for large datasets

For datasets >100K rows, process in chunks and serialize the LSH:

```python
import pickle
from datasketch import MinHash, MinHashLSH

CHUNK_SIZE = 50000
SEEN = set()

def process_chunk(ds_chunk, chunk_id):
    lsh = MinHashLSH(threshold=0.85, num_perm=128)
    
    def dedup_chunk(example, idx):
        t = example.get("text", "")
        if not t or len(t) < 20:
            return True
        if t in SEEN:
            return False
        m = MinHash(num_perm=128)
        for sh in shingle(t, k=5):
            m.update(sh.encode('utf-8'))
        if lsh.query(m):
            return False
        lsh.insert(f"{chunk_id}_{idx}", m)
        SEEN.add(t)
        return True
    
    return ds_chunk.filter(dedup_chunk, with_indices=True)
```

---

## 6. Full End-to-End Pipeline

```python
from datasets import Dataset, concatenate_datasets, load_dataset

def clean_text_pipeline(
    data_files,
    min_len=10,
    max_len=100000,
    dedup_exact=True,
    dedup_fuzzy=False,
    output_path="dataset_clean",
):
    """Full text cleaning pipeline returning a clean Dataset."""
    
    # 1. Load
    ds = load_dataset("text", data_files=data_files, split="train",
                      sample_by="line", keep_linebreaks=False)
    
    print(f"Loaded: {len(ds)} rows")
    
    # 2. Remove empty/None
    def non_empty(example):
        return example.get("text") is not None and example["text"].strip() != ""
    
    ds = ds.filter(non_empty, desc="Remove empty")
    print(f"After empty removal: {len(ds)} rows")
    
    # 3. Filter by length
    def by_length(example):
        t = example["text"]
        return min_len <= len(t) <= max_len
    
    ds = ds.filter(by_length, desc="Filter by length")
    print(f"After length filter: {len(ds)} rows")
    
    # 4. Add metadata columns
    def add_metadata(example):
        t = example["text"]
        return {
            "char_count": len(t),
            "word_count": len(t.split()),
        }
    
    ds = ds.map(add_metadata, desc="Add metadata")
    
    # 5. Exact dedup
    if dedup_exact:
        seen = set()
        def dedup(example):
            t = example["text"]
            if t in seen:
                return False
            seen.add(t)
            return True
        ds = ds.filter(dedup, desc="Exact dedup")
        print(f"After exact dedup: {len(ds)} rows")
    
    # 6. Save to disk
    ds.save_to_disk(output_path)
    print(f"Saved to {output_path}")
    
    return ds

# Usage
dataset = clean_text_pipeline(
    data_files="my_corpus.txt",
    min_len=50,
    max_len=5000,
    dedup_exact=True,
)
```

---

## 7. Streaming for Large Datasets

When datasets don't fit in memory, use streaming:

```python
ds_stream = load_dataset("text", data_files="huge_corpus.txt",
                         split="train", streaming=True)

# Dedup with bounded memory (set-based, but reset periodically)
class StreamDeduper:
    def __init__(self, max_seen=1_000_000):
        self.seen = set()
        self.max_seen = max_seen
    
    def is_duplicate(self, text):
        if text in self.seen:
            return True
        self.seen.add(text)
        if len(self.seen) > self.max_seen:
            self.seen.clear()  # trade-off: may miss cross-period dupes
        return False

deduper = StreamDeduper()
ds_clean = ds_stream.filter(lambda x: not deduper.is_duplicate(x["text"]))

# Write deduped stream to parquet
ds_clean.save_to_disk("deduped_stream", num_shards=10)
```

---

## 8. Saving and Exporting

```python
# Save to disk (Arrow format)
ds.save_to_disk("my_dataset/")

# Save as Parquet
ds.to_parquet("my_dataset.parquet")

# Save as CSV
ds.to_csv("my_dataset.csv")

# Save as JSON Lines
ds.to_json("my_dataset.jsonl")

# Load back
from datasets import load_from_disk
ds_loaded = load_from_disk("my_dataset/")
```

### Sharding large outputs

```python
# Split into multiple shards for parallel loading
ds.save_to_disk("sharded_dataset/", num_shards=10)
# Or
ds.to_parquet("sharded/", num_shards=10)
```

---

## 9. Concatenating and Merging

```python
from datasets import concatenate_datasets

ds_a = load_dataset("text", data_files="part1.txt", split="train")
ds_b = load_dataset("text", data_files="part2.txt", split="train")

# Concatenate (column-wise union required)
ds_merged = concatenate_datasets([ds_a, ds_b])

# Interleave (alternating rows from each dataset)
ds_interleaved = concatenate_datasets([ds_a, ds_b], axis=0)
```

---

## Performance Tips

| Technique | Speed | Memory | Best for |
|-----------|-------|--------|----------|
| `.filter()` with set | Fast | ~16 bytes/unique text | <10M unique rows |
| `pandas.drop_duplicates()` | Fast | Full dataset in RAM | <5M rows total |
| `datasketch` MinHash LSH | Slow | Permutation table | <500K rows |
| Streaming filter | Medium | Bounded | >10M rows |
| Batched `.map()` | 10-100x faster | Per-batch | Any size |

---

## Key Takeaways

1. **Exact dedup is free** — use `filter()` with a Python `set` for most cases.
2. **Always handle None** — `None` values crash `len()` and regex.
3. **Batch everything** — `batched=True` with `batch_size=1000` massively
   speeds up `.filter()` and `.map()`.
4. **`remove_columns` early** — drop raw text columns you no longer need to
   reduce memory.
5. **Stream when it's big** — `streaming=True` processes without loading all
   data into RAM.
6. **Save to Parquet or disk** — Arrow format is 10x faster than CSV for
   reloading.
7. **Zero-cost by design** — all techniques above run on local CPU with no
   API calls.
