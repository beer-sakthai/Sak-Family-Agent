---
name: SakThai-hf-datasets-data-validation-quality
description: "Comprehensive guide to data validation, quality assurance, and cleaning pipelines using the Hugging Face Datasets library — schema validation, filtering, deduplication, distribution checks, outlier detection, null handling, and dataset integrity veri"
---

# HF Datasets Data Validation & Quality Assurance

Trigger when: loading a new dataset and needing to verify its quality before use, building a data preprocessing pipeline with automated quality checks, cleaning tool-calling datasets (common in Beer's ecosystem), checking for null/missing values, deduplicating training examples, filtering by quality criteria, validating schema types and column compatibility, or building a reusable QA function for dataset CI/CD.

## Overview

The Hugging Face `datasets` library provides a full toolkit for data validation and quality assurance built on Apache Arrow. This skill covers the complete pipeline from schema validation through cleaning to final integrity verification.

**Key insight**: Arrow's columnar format means most operations are zero-copy or memory-mapped, making validation on datasets with millions of rows fast and memory-efficient — no need to load everything into Python objects.

## 1. Schema Validation

### 1.1 Inspecting Features

Always start by inspecting the dataset's schema before any processing:

```python
from datasets import load_dataset

dataset = load_dataset("my-dataset", split="train")

# Full schema
dataset.features

# Per-column inspection
for col_name, feature in dataset.features.items():
    print(f"{col_name}: {feature}")

# Column names
dataset.column_names

# Shape
len(dataset)
```

### 1.2 Type Checking with Features

Features define the expected types. Use `Features` to validate data on creation:

```python
from datasets import Features, Value, ClassLabel, Sequence, Dataset

# Define expected schema
expected_schema = Features({
    "text": Value("string"),
    "label": ClassLabel(names=["pos", "neg"]),
    "tokens": Sequence(Value("string")),
    "score": Value("float32"),
})

# Validate when creating — raises on mismatch
dataset = Dataset.from_dict(raw_data, features=expected_schema)
```

### 1.3 Casting Features

When a dataset has wrong types, cast them:

```python
from datasets import Value, ClassLabel

# Single column
dataset = dataset.cast_column("label", ClassLabel(names=["neg", "pos"]))

# Multiple columns at once
new_features = dataset.features.copy()
new_features["label"] = ClassLabel(names=["negative", "positive"])
new_features["idx"] = Value("int64")
dataset = dataset.cast(new_features)
```

**Compatibility rules:**
- `Value("int32")` ↔ `Value("int64")`: safe, Arrow widens
- `Value("int32")` → `Value("bool")`: only if column contains only 0/1
- `Value("string")` ↔ `ClassLabel(...)`: requires `class_encode_column()` or `map()` with explicit conversion
- `Value("float32")` → `Value("float64")`: safe

### 1.4 ClassLabel Encoding

Convert string/integer label columns into `ClassLabel` for proper categorical handling:

```python
# Auto-detect classes from column values
dataset = dataset.class_encode_column("label")

# With null handling
dataset = dataset.class_encode_column("label", include_nulls=True)

# Verify
print(dataset.features["label"])  # ClassLabel(num_classes=N, names=[...])
print(dataset.features["label"].names)  # list of class names
```

## 2. Null/Missing Value Detection

### 2.1 Finding Nulls

```python
import numpy as np

def find_nulls(dataset, columns=None):
    """Return null counts per column in the dataset."""
    cols = columns or dataset.column_names
    null_counts = {}
    for col in cols:
        # Dataset.unique() returns None-masked values
        col_data = dataset[col]
        # Count None/NaN
        null_mask = [v is None for v in col_data]
        if isinstance(col_data[0], (int, float)) if col_data else False:
            null_mask = null_mask | [np.isnan(v) if v is not None else True for v in col_data]
        null_counts[col] = sum(null_mask)
    return null_counts

nulls = find_nulls(dataset)
print(f"Columns with nulls: {{k: v for k, v in nulls.items() if v > 0}}")
```

### 2.2 Removing Null Rows

```python
# Remove rows where any critical column is null
critical_columns = ["text", "label"]
for col in critical_columns:
    dataset = dataset.filter(lambda x: x[col] is not None)
```

### 2.3 Filling Null Values

```python
def fill_nulls(batch):
    """Replace None with defaults."""
    for col in batch:
        batch[col] = [
            "" if v is None and col == "text" else
            0 if v is None and col == "label" else
            v
            for v in batch[col]
        ]
    return batch

dataset = dataset.map(fill_nulls, batched=True)
```

## 3. Filtering by Quality Criteria

### 3.1 Basic Filtering

`Dataset.filter()` keeps rows matching a condition:

```python
# Single condition
dataset = dataset.filter(lambda x: len(x["text"]) > 10)

# Multiple conditions
def quality_filter(example):
    return (
        len(example["text"]) > 10 and
        example["text"].strip() != "" and
        example["text"] != example.get("text_duplicate", "")
    )

dataset = dataset.filter(quality_filter)
```

### 3.2 Filtering with Index

```python
# Keep every 2nd row
dataset = dataset.filter(lambda example, idx: idx % 2 == 0, with_indices=True)
```

### 3.3 Batched Filtering (Efficient)

For speed, process in batches:

```python
def filter_short_texts(batch):
    """Return boolean mask for rows to keep."""
    mask = [len(t) >= 10 for t in batch["text"]]
    return mask  # list of bools, same length as batch

dataset = dataset.filter(filter_short_texts, batched=True)
```

### 3.4 Text Quality Heuristics

Common quality heuristics for text datasets:

```python
def text_quality_filter(example):
    text = example.get("text", "") or ""
    return (
        len(text) >= 20 and           # Minimum length
        len(text) <= 100000 and        # Maximum length
        text.count(" ") >= 3 and       # Has word structure
        text.strip() == text and       # No leading/trailing whitespace (optional)
        not text.isupper() and         # Not all uppercase
        sum(c.isalpha() for c in text) / max(len(text), 1) > 0.5  # ≥50% letters
    )

dataset = dataset.filter(text_quality_filter)
```

## 4. Deduplication

### 4.1 Exact Deduplication

```python
# Simple — remove exact duplicate rows across ALL columns
dataset = dataset.unique("text")  # Returns unique values only — loses other columns!

# Better — filter keeping first occurrence
def deduplicate_text(dataset, column="text"):
    seen = set()
    def dedup_filter(example):
        val = example[column]
        if val in seen:
            return False
        seen.add(val)
        return True
    return dataset.filter(dedup_filter)

dataset = deduplicate_text(dataset, "text")
print(f"After dedup: {len(dataset)} rows")
```

### 4.2 Multi-Column Deduplication

```python
def deduplicate_multi(dataset, columns):
    seen = set()
    def dedup_filter(example):
        key = tuple(str(example[col]) for col in columns)
        if key in seen:
            return False
        seen.add(key)
        return True
    return dataset.filter(dedup_filter)

dataset = deduplicate_multi(dataset, ["text", "label"])
```

### 4.3 Fuzzy Deduplication (Near-Duplicate Detection)

For near-duplicate detection, use MinHash/LSH. The datasets library doesn't ship this, but it integrates well with external libraries:

```python
# Approach: embed + cluster + deduplicate
# 1. Generate embeddings using sentence-transformers
# 2. Cluster similar embeddings
# 3. Keep 1 representative per cluster

# Example with sentence-transformers:
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_embeddings(batch):
    batch["embedding"] = model.encode(batch["text"]).tolist()
    return batch

dataset = dataset.map(compute_embeddings, batched=True, batch_size=32)
# Then use sklearn DBSCAN or faiss for clustering
```

## 5. Distribution Analysis

### 5.1 Label Distribution

```python
from collections import Counter

def label_distribution(dataset, column="label"):
    values = dataset[column]
    # ClassLabel stores ints internally — convert to names
    if hasattr(dataset.features[column], "names"):
        names = dataset.features[column].names
        values = [names[v] for v in values]
    return Counter(values)

dist = label_distribution(dataset)
for label, count in dist.most_common():
    print(f"  {label}: {count} ({count/len(dataset)*100:.1f}%)")
```

### 5.2 Text Length Distribution

```python
import numpy as np

def text_length_stats(dataset, column="text"):
    lengths = [len(t) for t in dataset[column]]
    return {
        "min": min(lengths),
        "max": max(lengths),
        "mean": np.mean(lengths),
        "median": np.median(lengths),
        "std": np.std(lengths),
        "p5": np.percentile(lengths, 5),
        "p95": np.percentile(lengths, 95),
    }

stats = text_length_stats(dataset)
for k, v in stats.items():
    print(f"  {k}: {v:.1f}")
```

### 5.3 Detecting Distribution Imbalance

```python
def is_imbalanced(distribution, threshold=0.1):
    """Check if any class has < threshold proportion."""
    total = sum(distribution.values())
    for label, count in distribution.items():
        if count / total < threshold:
            return True, label, count / total
    return False, None, None
```

## 6. Outlier Detection

### 6.1 Value Range Validation

```python
def validate_ranges(dataset, constraints):
    """
    constraints: dict of {column: (min, max)} or {column: allowed_set}
    Returns list of invalid row indices.
    """
    invalid_indices = []
    for i, example in enumerate(dataset):
        for col, constraint in constraints.items():
            val = example[col]
            if isinstance(constraint, tuple):
                lo, hi = constraint
                if val is not None and not (lo <= val <= hi):
                    invalid_indices.append(i)
                    break
            elif isinstance(constraint, set):
                if val not in constraint:
                    invalid_indices.append(i)
                    break
    return invalid_indices

# Example: scores must be 0-5, labels must be in expected set
invalid = validate_ranges(dataset, {
    "score": (0.0, 5.0),
    "label": {"pos", "neg", "neutral"},
})
print(f"Out-of-range rows: {len(invalid)}")

# Remove them
dataset = dataset.select([i for i in range(len(dataset)) if i not in set(invalid)])
```

### 6.2 Statistical Outlier Detection (IQR method)

```python
import numpy as np

def remove_statistical_outliers(dataset, column, factor=1.5):
    """Remove outliers using Interquartile Range method."""
    values = np.array([v for v in dataset[column] if v is not None])
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr

    def outlier_filter(example):
        v = example[column]
        return v is not None and lower <= v <= upper

    before = len(dataset)
    dataset = dataset.filter(outlier_filter)
    removed = before - len(dataset)
    print(f"Removed {removed} outliers from '{column}' (bounds: [{lower:.2f}, {upper:.2f}])")
    return dataset
```

## 7. Data Integrity Verification

### 7.1 Checksum / Fingerprint Verification

Every processed dataset has a fingerprint. Use it to verify processing chains:

```python
print(f"Dataset fingerprint: {dataset._fingerprint}")

# Fingerprint changes after any transformation
# You can version datasets by fingerprint
```

### 7.2 Schema Preservation Check

After applying `map()`, verify the schema hasn't silently changed:

```python
def verify_schema(before_features, after_dataset):
    """Check that no columns were unexpectedly dropped or changed."""
    before_cols = set(before_features.keys())
    after_cols = set(after_dataset.features.keys())

    dropped = before_cols - after_cols
    added = after_cols - before_cols

    issues = []
    if dropped:
        issues.append(f"Columns dropped: {dropped}")
    if added:
        issues.append(f"Columns added: {added}")

    return issues

original_features = dataset.features.copy()
# ... do processing ...
issues = verify_schema(original_features, dataset)
if issues:
    print("Schema changed!")
    for i in issues:
        print(f"  ⚠ {i}")
```

### 7.3 Row Count Consistency

```python
def check_row_count(dataset, expected=None, label="dataset"):
    count = len(dataset)
    if expected is not None and count != expected:
        print(f"⚠ {label}: expected {expected} rows, got {count}")
    else:
        print(f"✓ {label}: {count} rows")
    return count
```

### 7.4 JSONL Serialization Format Validation

A common data integrity bug: files with `.jsonl` extension stored as a JSON array (single `[{...}]` object) instead of one JSON object per line. Libraries expecting line-delimited JSON silently produce zero rows.

**Detection — check the first byte:**

```python
import json

def check_jsonl_format(filepath):
    """Verify a .jsonl file is actually line-delimited JSON (not a JSON array)."""
    with open(filepath) as f:
        first_char = f.read(1).strip()
        f.seek(0)
        content = f.read()

    if first_char == "[":
        # JSON array — wrong format for .jsonl
        try:
            data = json.loads(content)
            print(f"JSON ARRAY ({len(data)} items, {len(content)} bytes) — should be JSONL")
            return False
        except json.JSONDecodeError:
            print("INVALID JSON")
            return False

    elif first_char == "{":
        # Proper JSONL — verify each line independently parseable
        lines = content.strip().split("\n")
        valid = 0
        invalid_indices = []
        for i, line in enumerate(lines):
            try:
                json.loads(line)
                valid += 1
            except json.JSONDecodeError:
                invalid_indices.append(i)

        if invalid_indices:
            print(f"JSONL: {valid}/{len(lines)} valid, {len(invalid_indices)} broken at lines {invalid_indices[:5]}")
            return False
        else:
            print(f"JSONL: {valid} lines, all parseable")
            return True
    else:
        print(f"Unknown format: starts with {repr(first_char)}")
        return False
```

**Batch scan all dataset repos:**

```python
from huggingface_hub import HfApi

api = HfApi()
author = "Nanthasit"

for ds in api.list_datasets(author=author):
    siblings = api.get_repo_info(ds.id, repo_type="dataset").siblings
    for sib in siblings:
        if not sib.rfilename.endswith(".jsonl"):
            continue
        local = api.hf_hub_download(ds.id, sib.rfilename, repo_type="dataset")
        ok = check_jsonl_format(local)
        if not ok:
            print(f"  ⚠ {ds.id.split('/')[1]}/{sib.rfilename}")
```

**Fix: Convert JSON array to proper JSONL:**

```python
import json

with open("broken.jsonl") as f:
    data = json.load(f)  # Parse the JSON array

with open("fixed.jsonl", "w") as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
```

**Verification after fix:**

```python
with open("fixed.jsonl") as f:
    for i, line in enumerate(f):
        obj = json.loads(line.strip())
        # Assert expected keys per your schema
        assert "messages" in obj, f"Line {i}: missing 'messages'"
        assert "tools" in obj, f"Line {i}: missing 'tools'"
```

**Real-world example (2026-07-29):** `Nanthasit/sakthai-irrelevance-supplement` had `data/train.jsonl` stored as a JSON array (10 items in `[{...}]`). Fixed by converting to proper JSONL format.

## 8. Complete QA Pipeline

A reusable pipeline combining the above checks:

```python
from datasets import Dataset, Features, Value, ClassLabel
from collections import Counter
import numpy as np

class DatasetQA:
    """Quality Assurance pipeline for Hugging Face Datasets."""

    def __init__(self, dataset, name="dataset"):
        self.dataset = dataset
        self.name = name
        self.report = {"name": name, "checks": []}

    def check_schema(self, expected_schema=None):
        """Verify features match expected schema."""
        if expected_schema:
            actual = self.dataset.features
            mismatches = []
            for col, expected_feat in expected_schema.items():
                if col not in actual:
                    mismatches.append(f"Missing column: {col}")
                elif str(actual[col]) != str(expected_feat):
                    mismatches.append(
                        f"Column '{col}': expected {expected_feat}, got {actual[col]}"
                    )
            result = len(mismatches) == 0
            self.report["checks"].append({
                "check": "schema",
                "passed": result,
                "details": mismatches if mismatches else "Schema matches expected"
            })
            return result
        return True

    def check_nulls(self, columns=None):
        """Report null counts per column."""
        cols = columns or self.dataset.column_names
        nulls = {}
        for col in cols:
            col_data = self.dataset[col]
            null_count = sum(1 for v in col_data if v is None)
            if null_count > 0:
                nulls[col] = null_count

        self.report["checks"].append({
            "check": "nulls",
            "passed": len(nulls) == 0,
            "details": nulls if nulls else "No null values found"
        })
        return len(nulls) == 0

    def check_label_balance(self, column="label", threshold=0.05):
        """Check label distribution for severe imbalance."""
        if column not in self.dataset.features:
            return True
        values = self.dataset[column]
        if hasattr(self.dataset.features[column], "names"):
            names = self.dataset.features[column].names
            values = [names[v] for v in values]
        dist = Counter(values)
        total = sum(dist.values())
        imbalanced_labels = {
            k: v/total for k, v in dist.items() if v/total < threshold
        }
        self.report["checks"].append({
            "check": "label_balance",
            "passed": len(imbalanced_labels) == 0,
            "details": imbalanced_labels if imbalanced_labels else "Labels balanced"
        })
        return len(imbalanced_labels) == 0

    def check_text_lengths(self, column="text", min_len=1, max_len=100000):
        """Verify text lengths are within acceptable range."""
        if column not in self.dataset.column_names:
            return True
        lengths = [len(t) for t in self.dataset[column]]
        out_of_range = sum(1 for l in lengths if l < min_len or l > max_len)
        self.report["checks"].append({
            "check": "text_lengths",
            "passed": out_of_range == 0,
            "details": {
                "min": min(lengths),
                "max": max(lengths),
                "mean": np.mean(lengths),
                "out_of_range": out_of_range,
            }
        })
        return out_of_range == 0

    def check_duplicates(self, column="text"):
        """Check for duplicate values in a column."""
        if column not in self.dataset.column_names:
            return True
        values = self.dataset[column]
        unique = set(values)
        duplicates = len(values) - len(unique)
        self.report["checks"].append({
            "check": "duplicates",
            "passed": duplicates == 0,
            "details": {"duplicate_count": duplicates, "duplicate_pct": duplicates/len(values)*100}
        })
        return duplicates == 0

    def run_all(self, expected_schema=None):
        """Run all checks and return pass/fail."""
        checks = [
            ("Schema", self.check_schema(expected_schema)),
            ("Nulls", self.check_nulls()),
            ("Label Balance", self.check_label_balance()),
            ("Text Lengths", self.check_text_lengths()),
            ("Duplicates", self.check_duplicates()),
        ]
        all_pass = all(c[1] for c in checks)
        self.report["all_passed"] = all_pass
        return all_pass

    def print_report(self):
        """Print formatted report."""
        print(f"\n{'='*50}")
        print(f"QA Report: {self.name}")
        print(f"{'='*50}")
        print(f"Rows: {len(self.dataset)}")
        print(f"Columns: {self.dataset.column_names}")
        print()
        for check in self.report["checks"]:
            status = "✓" if check["passed"] else "✗"
            print(f"  [{status}] {check['check']}")
            if not check["passed"]:
                print(f"         {check['details']}")
        print()
        print(f"Overall: {'PASSED' if self.report.get('all_passed') else 'FAILED'}")
        print(f"{'='*50}")
        return self.report["all_passed"]
```

### Usage

```python
qa = DatasetQA(dataset, name="tool-calling-train")
qa.run_all(expected_schema=my_features)
qa.print_report()
```

## 9. Cleaning Tool-Calling Datasets (Beer's Ecosystem)

For tool-calling datasets specifically (like Beer's `sakthai-combined-v6`):

```python
def validate_tool_call(example):
    """Validate a tool-calling example has required fields."""
    required = ["messages", "tools"]  # adjust per your schema
    for field in required:
        if field not in example or example[field] is None:
            return False
    # Check messages contain valid roles
    valid_roles = {"system", "user", "assistant", "tool"}
    for msg in example.get("messages", []):
        if msg.get("role") not in valid_roles:
            return False
        # Check content is not empty for user/assistant
        if msg["role"] in ("user", "assistant") and not msg.get("content", "").strip():
            return False
    return True

# Apply
dataset = dataset.filter(validate_tool_call)
print(f"Valid tool-calling examples: {len(dataset)}")
```

## 10. Dataset Splitting Validation

When creating train/test splits, validate no leakage:

```python
def validate_no_leakage(train_set, test_set, column="text"):
    """Ensure no test example appears in training set."""
    train_texts = set(train_set[column])
    test_texts = set(test_set[column])
    overlap = train_texts & test_texts
    if overlap:
        print(f"⚠ LEAKAGE DETECTED: {len(overlap)} examples in both train and test!")
        return False
    print(f"✓ No leakage: {len(train_set)} train / {len(test_set)} test")
    return True

splits = dataset.train_test_split(test_size=0.1, seed=42)
validate_no_leakage(splits["train"], splits["test"])
```

## 11. Performance Considerations

| Operation | Speed | Memory | Note |
|-----------|-------|--------|------|
| `dataset.filter()` | Fast | Low | O(n), indices mapping only |
| `dataset.filter(batched=True)` | Fastest | Low | Vectorized masks |
| `dataset.map()` | Slow | Medium | Actually runs function on each row |
| `dataset.select()` | Instant | Very low | Just stores index list |
| `dataset.sort()` | Medium | Medium | Creates sorted indices |
| `dataset.shuffle()` | Fast | Low | Creates shuffled index mappings |
| `dataset.unique()` | Fast | Depends | Returns only the column values |
| `dataset.flatten_indices()` | Slow | High | Rewrites entire dataset on disk |

**Watch out for indices mapping slowdown**: After `shuffle()`, `select()`, `sort()`, or `filter()` with non-contiguous indices, random access becomes ~10x slower. Call `flatten_indices()` to materialize the shuffled order and restore speed.

For large datasets (>1M rows), prefer:
- `filter(batched=True)` over `filter()` with a lambda
- `IterableDataset` with `.filter()` for streaming validation without materializing
- `.select()` with precomputed indices for complex multi-step filtering

## 12. IterableDataset Validation (Streaming)

For datasets too large to fit in memory:

```python
# Convert to iterable for streaming validation
iterable_ds = dataset.to_iterable_dataset(num_shards=128)

# Filter while streaming
valid_ds = iterable_ds.filter(quality_filter)

# For statistical checks, sample first
sample = list(iterable_ds.take(1000))
# Compute stats on sample, apply filter based on those stats
```

## Pitfalls

- **`dataset.unique()` returns only the column values** — not a filtered dataset. Use `filter()` with a `seen` set for deduplication preserving other columns.
- **Indices mapping slowdown** is silent — your dataset appears the same size, but random access becomes 10x slower after non-contiguous selection. Use `flatten_indices()` to materialize.
- **`ClassLabel` stores integers internally** — when comparing values, use `.str2int()` or check against `dataset.features["label"].names`.
- **`map()` removes columns not returned** — if your mapped function returns a dict with fewer keys than the input, remaining columns are dropped. Use `remove_columns` explicitly or return all columns.
- **`filter()` with `batched=True` must return a list of bools** — same length as the batch. Returning a single bool silently produces wrong results.
- **Casting is silent on failure** — `cast_column()` raises no error if the data can't be converted. Always verify with `dataset.features` after casting.
- **Null values in Arrow are stored differently** — `None` in Python becomes Arrow null. Use `is None` checks, not `== None`.
- **`Dataset.from_dict()` with numpy arrays** infers types that may not match expected schema. Always pass `features=` explicitly.
