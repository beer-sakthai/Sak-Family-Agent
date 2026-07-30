---
name: SakThai-hf-datasets-5-batch-by-column
author: SakThai
license: MIT
description: >
  Complete guide to datasets 5.0.0's IterableDataset.batch(by_column=...) —
  groups streaming samples by column value into variable-size batches.
  Essential for robotics (batch by episode), multi-turn conversations
  (batch by conversation_id), and any grouped-sequential data. Covers the
  full API, the Arrow-accumulation strategy, memory behaviour, and
  practical recipes.
version: 1.0.0
metadata:
  hermes:
    tags: [huggingface, datasets, iterable-dataset, batch, streaming, arrow, robotics]
    category: mlops
category: mlops
---

# HF Datasets 5: IterableDataset.batch(by_column=...)

## Overview

Added in datasets `4.9.0` and refined through `5.0.0`, `batch(by_column=...)`
groups **successive samples sharing the same column value** into a single
batched row. Unlike fixed-size batching (`batch_size=32`), column-batching
produces variable-length batches — one per unique value transition in the key
column(s).

Primary use cases:

- **Robotics / RL:** group frames by `"episode"` so each batch = one full
  episode trajectory
- **Conversations:** group messages by `"conversation_id"` for chat-style
  training
- **Time-series:** group measurements by `"session_id"` or `"trial_number"`
- **Multi-document:** group chunks by `"document_id"` for retrieval training

## API

```python
def batch(
    self,
    batch_size: Optional[int] = None,
    by_column: Optional[Union[str, list[str]]] = None,
    drop_last_batch: bool = False,
) -> "IterableDataset":
    ...
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `batch_size` | `int` or `None` | `None` | Controls accumulation chunk size when `by_column` is set; number of items per batch for fixed-size batching. |
| `by_column` | `str` or `list[str]` or `None` | `None` | Column(s) to batch by. Successive rows with the same value(s) are grouped together. |
| `drop_last_batch` | `bool` | `False` | Drop the final incomplete batch when switching to a new key. |

**Must provide at least one of** `batch_size` or `by_column`.

## How It Works (Internals)

### Pipeline

1. **Arrow format switch** — `self.with_format("arrow")` ensures raw
   `pyarrow.Table` objects flow through the pipeline
2. **Accumulation via `_batch_accumulate_arrow_table_by_columns`** — a
   batched-map function that receives successive Arrow tables from the
   streaming generator
3. **Key comparison** — for each incoming table chunk, the function checks
   whether the first row's key column value matches the key of the
   accumulated buffer
   - **Same key** → append to accumulator, return an empty table
   - **Different key** → flush accumulator + current table, cut into
     list-column batches per key boundary
4. **List-column output** — every column becomes a `ListArray` where each
   element contains all values for one group

### The Cut Algorithm (table.py: `_batch_accumulate_arrow_table_by_columns`)

```python
# Find where key column value changes between consecutive rows
cut_array = pc.not_equal(table[columns[0]][1:], table[columns[0]][:-1])
for column in columns[1:]:
    cut_array = pc.or_(cut_array, pc.not_equal(table[column][1:], table[column][:-1]))

# Convert to list offsets
offsets = pc.indices_nonzero(cut_array)
offsets = pc.add(1, offsets)
offsets = pa.concat_arrays([pa.array([0], type=pa.int32()), offsets.cast(pa.int32())])

# Build list arrays from offsets
batched_columns = []
for column_name in table.column_names:
    column = table[column_name].combine_chunks()
    batched_columns.append(pa.ListArray.from_arrays(offsets, column))
```

Key detail: **pyarrow `ListArray`** is zero-copy from the offsets, so no
unnecessary data duplication.

### Memory Behaviour

- **Accumulator is list of `pa.Table`** — grows in memory until a key change
  flushes it
- `batch_size` acts as a **chunk size** for incoming data, not the output
  batch size. Smaller `batch_size` = more frequent key checks = lower peak
  memory, but more overhead
- Long runs of the same key (e.g. a 100K-frame episode) still accumulate
  until the key changes — **watch memory for very long sequences**
- The final batch stays in the accumulator if a new key never arrives —
  `drop_last_batch=True` drops it

## Comparison: Fixed-size vs Column Batching

| Aspect | `batch(batch_size=32)` | `batch(by_column="episode")` |
|--------|----------------------|----------------------------|
| Output batch size | Always 32 | Variable (one per key change) |
| Item ordering | Preserved | Preserved within key groups |
| Streaming | Yes (chunked) | Yes (accumulated) |
| Use case | Training loops | Grouped/sequential data |
| Memory bound | O(batch_size) | O(longest key run) |

## Practical Recipes

### Robotics: Group frames by episode

```python
from datasets import load_dataset

ds = load_dataset("some/robotics-dataset", split="train", streaming=True)
ds = ds.batch(by_column="episode")

for batch in ds:
    # batch["episode"] = [0, 0, 0, ...]  # all same value
    # batch["frame"]   = [0, 1, 2, ...]  # all frames of that episode
    # batch["image"]   = [img0, img1, ...]
    process_episode(batch)
```

### Multi-column grouping

```python
ds = ds.batch(by_column=["user_id", "session_id"])
# Groups rows where BOTH user_id AND session_id match consecutively
```

### Combined with batch_size for memory control

```python
ds = ds.batch(by_column="episode", batch_size=1000)
# Process 1000 rows at a time within each episode accumulation
```

### From map-style to streaming + batching

```python
from datasets import Dataset

# Start with a map-style dataset
map_ds = Dataset.from_list([
    {"episode": 0, "frame": 0, "obs": "a"},
    {"episode": 0, "frame": 1, "obs": "b"},
    {"episode": 1, "frame": 0, "obs": "c"},
])

# Convert to streaming (zero-copy from local files) then batch by episode
iter_ds = map_ds.to_iterable_dataset()
batched = iter_ds.batch(by_column="episode")

for batch in batched:
    print(batch["episode"], batch["frame"], batch["obs"])
# [0, 0] [0, 1] ['a', 'b']
# [1] [0] ['c']
```

### Cleaning up the output format

Batched rows use `ListArray` columns. To convert to Python lists in
a specific format:

```python
batched = ds.batch(by_column="episode").with_format("numpy")
# or keep as dict-of-lists:
batched = ds.batch(by_column="episode")
for batch in batched:
    assert isinstance(batch["image"], list)  # list of lists
```

## Key Constraints

1. **Requires consecutive runs** — only groups *adjacent* rows with the same
   key. If episode 0 rows are not contiguous, they produce separate batches.
   Sort by the key column first if needed.
2. **Not for deduplication** — use `filter()` + `unique()` for that;
   `by_column` groups rather than removes duplicates.
3. **Memory for long runs** — a single key spanning millions of rows
   accumulates all of them before flushing. For extremely long sequences,
   consider splitting the key into sub-chunks.
4. **ListArray output** — every column becomes a `ListArray`. Access
   individual elements via standard Python list indexing.
5. **Format chaining** — `with_format()` applies *before* the batch
   transform's internal Arrow conversion. The output format inherits from
   the dataset's original format setting.

## Version History

| Version | Change |
|---------|--------|
| 4.9.0   | Initial `by_column` parameter added to `IterableDataset.batch()` |
| 5.0.0   | Improved multi-shard shuffle buffer for streaming, batch stabilised |
