---
name: SakThai-hf-datasets-data-validation-quality
version: 1.0.0
description: Comprehensive guide to data validation, quality assurance, and cleaning
  pipelines using the Hugging Face Datasets library — schema validation, filtering,
  deduplication, distribution checks, outlier detection, null handling, and dataset
  integrity veri
category: datasets
tags:
- api
- card
- data
- dataset
- datasets
- hf
- huggingface
- quality
- validate
- validation
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

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Advanced Dataset Validation, Outliers & Deduplication](./references/advanced-validation-and-deduplication.md).
