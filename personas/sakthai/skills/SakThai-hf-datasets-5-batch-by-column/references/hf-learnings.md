# HF Learnings: IterableDataset.batch(by_column=...) (Topic #277)

## Summary
Datasets 5.0.0's `IterableDataset.batch(by_column=...)` groups successive
streaming samples by column value into variable-size batches using Arrow
`ListArray`. Essential for robotics (batch by episode), multi-turn
conversations (by conversation_id), and any grouped-sequential data.

## Source
- `src/datasets/iterable_dataset.py` lines 4420–4485 — `IterableDataset.batch()`
- `src/datasets/table.py` lines 71–116 — `_batch_accumulate_arrow_table_by_columns()`
- PyArrow docs: `pa.ListArray.from_arrays()`, `pc.not_equal()`

## Key Architecture
1. **Pipeline**: `with_format("arrow")` → `_map(batched=True, ...)` →
   `_batch_accumulate_arrow_table_by_columns()` which accumulates tables
   while the key column stays the same, then cuts into ListArray batches
   when the key changes.
2. **Cut algorithm**: Uses `pc.not_equal()` to find key‑value transitions,
   `pc.indices_nonzero()` to locate boundaries, then
   `pa.ListArray.from_arrays(offsets, column)` to build variable-size batches
   — all zero-copy within pyarrow.
3. **Accumulator**: A list of `pa.Table` grows in memory until a key change
   flushes it. `batch_size` controls incoming chunk size (not output batch
   size). Watch memory for very long single-key runs.

## Critical Details
- `by_column` accepts `str` or `list[str]` — multi‑column grouping requires
  all columns to match consecutively.
- `drop_last_batch=True` drops the final incomplete batch if the stream ends
  mid‑group.
- Only groups **adjacent** rows with the same key — non‑contiguous same-key
  rows produce separate batches.
- Available since datasets 4.9.0; stabilised in 5.0.0.
- Every output column becomes `ListArray` — access via `batch["col"][i]`.
- Format chaining: `with_format()` applies before the internal Arrow
  conversion; output format inherits from original dataset format.

## Practical Patterns
```python
# Basic — batch by episode
ds = load_dataset("robotics/episodes", split="train", streaming=True)
ds = ds.batch(by_column="episode")

# Multi‑column
ds = ds.batch(by_column=["user_id", "session_id"])

# Memory control via batch_size
ds = ds.batch(by_column="episode", batch_size=500)

# From map → streaming → batched
ds = Dataset.from_list([...]).to_iterable_dataset().batch(by_column="episode")
```

## Related PR
- https://github.com/huggingface/datasets/pull/8172 — batch(by_column=...)
- https://github.com/huggingface/datasets/pull/8194 — multi-shard shuffle
  buffer (used in tandem with batch for better streaming shuffle)
