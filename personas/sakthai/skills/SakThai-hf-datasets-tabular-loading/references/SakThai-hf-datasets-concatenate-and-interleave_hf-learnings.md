# Datasets Concatenation & Interleaving — HF Learning (Deep Dive)

> Research date: 2026-07-24
> Source: Hugging Face datasets v5.0.0, combine.py + arrow_dataset.py + iterable_dataset.py source code
> Topic: hf-datasets-concatenate-and-interleave-deep-dive

## Overview

The `datasets` library provides two merging functions in `datasets.combine`:

1. **`concatenate_datasets(dsets, axis=0)`** — stack datasets vertically (append rows) or horizontally (add columns)
2. **`interleave_datasets(datasets, probabilities, seed, stopping_strategy)`** — alternate between datasets, cycling or sampling

Both support `Dataset` (map-style) and `IterableDataset` (streaming) — but the input list must be **homogeneous** (all Dataset or all IterableDataset). Mixing types raises `ValueError`.

---

## 1. `concatenate_datasets` — Internals

### Signature

```python
def concatenate_datasets(
    dsets: list[DatasetType],       # Dataset or IterableDataset
    info: Optional[DatasetInfo] = None,
    split: Optional[NamedSplit] = None,
    axis: int = 0,                  # 0 = rows, 1 = columns
) -> DatasetType
```

### Vertical (axis=0)

**Map-style path** (`_concatenate_map_style_datasets`):

1. Filters out empty datasets (num_rows == 0)
2. Calls `_check_if_features_can_be_aligned(features_list)` — verifies columns can be unioned
3. Calls `_align_features(features_list)` — determines a superset schema; missing columns get `None`/null
4. If any dataset has `_indices` (from `.select()` or `.shuffle()`), applies offsets to align indices:
   - Each dataset's indices get offset by cumulative length of preceding datasets' `_data` tables
   - `apply_offset_to_indices_table(table, offset)` uses `pyarrow.add()` to shift indices
   - If a dataset lacks `_indices`, creates identity mapping via `_select_with_indices_mapping`
5. Uses `pyarrow.concat_tables()` (from `datasets.table`) to concatenate `_data` Arrow tables
6. Merges `DatasetInfo` via `DatasetInfo.from_merge()` — combines descriptions, citations, etc.

**Iterable path** (`_concatenate_iterable_datasets`):

1. Resolves features on all datasets
2. Wraps ex_iterables in `VerticallyConcatenatedMultiSourcesExamplesIterable`
3. This class yields examples from each source iterable sequentially, chaining them

### Horizontal (axis=1)

**Map-style:**
- All datasets must have the **same number of rows** (`ValueError` if not)
- Checks column names are unique across datasets (`_check_column_names`)
- Uses `pyarrow.concat_tables(axis=1)` — column-wise concat
- No index offsetting needed; flattens indices if present

**Iterable:**
- Wraps ex_iterables in `HorizontallyConcatenatedMultiSourcesExamplesIterable`
- Rebaches Arrow ex_iterables to ensure consistent batch sizes
- The Arrow batch size is determined by `get_arrow_writer_batch_size_from_features()` or `config.DEFAULT_MAX_BATCH_SIZE` (typically 1000)

### Key Edge Cases

| Case | Behaviour |
|------|-----------|
| Empty datasets | Filtered out (if at least one has rows). All-empty → returns first ds |
| Mismatched columns on axis=0 | Filled with `None` after `_align_features` |
| Mismatched row counts on axis=1 | `ValueError: Number of rows must match` |
| Mixed format configs | Format reset to `{}` (no format) with info log |
| Mixed Dataset+IterableDataset | `ValueError` at combine level |
| DatasetDict passed instead of Dataset | `ValueError` with hint to pick a split via `dataset['train']` |

---

## 2. `interleave_datasets` — Internals

### Signature

```python
def interleave_datasets(
    datasets: list[DatasetType],
    probabilities: Optional[list[float]] = None,
    seed: Optional[int] = None,
    info: Optional[DatasetInfo] = None,
    split: Optional[NamedSplit] = None,
    stopping_strategy: Literal[
        "first_exhausted",
        "all_exhausted",
        "all_exhausted_without_replacement"
    ] = "first_exhausted",
) -> DatasetType
```

### Three Stopping Strategies

| Strategy | Behaviour | Result size |
|----------|-----------|-------------|
| `first_exhausted` (default) | Stop when **any one** dataset is exhausted | `min(len(d)) * n_datasets` (cycling, no probs) |
| `all_exhausted` | Stop when **every** dataset has been exhausted at least once. Reuses exhausted datasets by cycling back | `max(len(d)) * n_datasets` or more with probabilities |
| `all_exhausted_without_replacement` | Stop when every sample in every dataset has been yielded exactly once | `sum(len(d))` |

### Map-style Implementation

The map-style interleave works by **computing an index array** and calling `.select()` on a pre-concatenated dataset.

**Step 1:** Concatenate all datasets vertically via `_concatenate_map_style_datasets`.

**Step 2:** Compute offsets — the index in the concatenated table where each dataset starts:

```python
lengths = [len(d) for d in datasets]
offsets = np.cumsum([0] + lengths[:-1])  # e.g. [0, 3, 7] for lengths [3, 4, 3]
```

**Step 3:** Build indices based on the mode:

#### Mode A: `probabilities=None` (cyclic), `first_exhausted`

All datasets contribute `min(lengths)` examples, cycling through:

```
indices = (offsets.reshape(1, -1) + np.arange(min_length).reshape(-1, 1)).flatten()
```

Example: lengths [3, 4, 5], offsets [0, 3, 7], min_length=3
```
offsets        → [[0, 3, 7]]
arange(0..3)   → [[0], [1], [2]]
              → [[0, 3, 7], [1, 4, 8], [2, 5, 9]] → [0, 3, 7, 1, 4, 8, 2, 5, 9]
```

#### Mode B: `probabilities=None`, `all_exhausted` (oversampling)

Cycle through datasets, wrapping exhausted ones. Each dataset's indices repeat modulo its length:

```python
indices = np.mod(np.arange(max_length).reshape(-1, 1), np.array(lengths).reshape(1, -1))
indices = (indices + offsets).flatten()
```

Example: lengths [3, 4, 3], offsets [0, 3, 7], max_length=4
```
arange(0..4) → [[0],[1],[2],[3]]
mod lengths  → [[0,0,0],[1,1,1],[2,2,2],[0,3,0]]
+ offsets    → [[0,3,7],[1,4,8],[2,5,9],[0,6,0]] → flat: [0,3,7,1,4,8,2,5,9,0,6,0]
```

Note: When datasets wrap around, samples can repeat (index 0 appears twice for the first dataset).

#### Mode C: `probabilities=None`, `all_exhausted_without_replacement`

The most complex algorithm — processes chunks by sorted unique lengths:

```python
chunks_boundaries = [0] + sorted(set(lengths))     # [3, 4] for lengths [3,4,3]
chunks = zip(chunks_boundaries[:-1], chunks_boundaries[1:])  # [(0,3), (3,4)]

for start, end in chunks:
    # Take (end-start) elements from each remaining dataset
    indices = (offsets + np.arange(start, end).reshape(-1, 1)).flatten()
    # Remove exhausted datasets (those whose length == end)
    exhausted = [i for i, l in enumerate(lengths) if l == end]
    lengths = np.delete(lengths, exhausted)
    offsets = np.delete(offsets, exhausted)
```

For lengths [3, 4, 3]:
- Chunk (0,3): take indices 0,1,2 from each of 3 datasets → [0,3,7,1,4,8,2,5,9]; datasets 0 and 2 exhausted
- Chunk (3,4): take index 3 from remaining dataset 1 → [6]
- Final: [0,3,7,1,4,8,2,5,9,6] — exactly 10 = 3+4+3 samples, each appearing once

#### Mode D: `probabilities` specified

Uses a random number generator (`np.random.default_rng(seed)`) to select which source to draw from next, according to the `probabilities` array. The map-style implementation draws samples one at a time from the concatenated table.

### Iterable Implementation

Two internal classes handle the iteration:

**`CyclingMultiSourcesExamplesIterable`** (for `probabilities=None`):

- Maintains an infinite cycle index via `itertools.cycle(range(num_sources))`
- Buffers one example ahead per source to detect exhaustion
- `bool_strategy_func`: `np.all` for oversampling strategies, `np.any` for `first_exhausted`
- Stateful: tracks `ex_iterable_idx`, `previous_states`, `is_exhausted` for checkpointing

**`RandomlyCyclingMultiSourcesExamplesIterable`** (for probabilities):

- Inherits from CyclingMultiSources
- Uses `np.random.Generator` for source selection:
  - Without probabilities: `rng.integers(0, num_sources, size=random_batch_size)` → uniform random
  - With probabilities: `rng.choice(num_sources, size=random_batch_size, p=probabilities)`
- Random batch size is 1000 for efficiency
- Fully serializable state: `bit_generator_state` + `bit_generator_index_offset`
- `reshard()` for parallelism preserves the source selection pattern

### Distributed Interleaving

When used in multi-node or multi-worker setups:

1. Each worker has its own copy of the `_interleave_iterable_datasets` state
2. `stopping_strategy` is applied **per process** — so `first_exhausted` can generate up to 1 fewer sample per dataset per worker
3. `IterableDataset.reshard()` should be called on datasets with few shards before interleaving to maximize parallelism

---

## 3. Practical Patterns

### Pattern 1: Balanced Multi-Language Training

```python
from datasets import load_dataset, interleave_datasets

en = load_dataset("allenai/c4", "en", split="train", streaming=True)
fr = load_dataset("allenai/c4", "fr", split="train", streaming=True)
de = load_dataset("allenai/c4", "de", split="train", streaming=True)

# Reshard for better parallelism
en = en.reshard()
fr = fr.reshard()
de = de.reshard()

# Oversample French/German at 2x
mixed = interleave_datasets(
    [en, fr, de],
    probabilities=[0.2, 0.4, 0.4],
    seed=42,
    stopping_strategy="first_exhausted"
)
```

### Pattern 2: Adding Columns via Horizontal Concat

```python
from datasets import Dataset, concatenate_datasets

base = Dataset.from_dict({"text": ["hello", "world"]})
labels = Dataset.from_dict({"label": [0, 1]})
augmented = Dataset.from_dict({"embedding": [[0.1, 0.2], [0.3, 0.4]]})

combined = concatenate_datasets([base, labels, augmented], axis=1)
# Result: Dataset with columns text, label, embedding — 2 rows
```

### Pattern 3: Exhaustive Interleaving Without Replacement

```python
# Each sample appears exactly once, interleaved round-robin
all_data = interleave_datasets(
    [dataset_a, dataset_b, dataset_c],
    stopping_strategy="all_exhausted_without_replacement"
)
# Result: sum(len(d)) samples — each from every dataset exactly once
```

### Pattern 4: Oversampling Small Datasets

```python
small = load_dataset("specialized/small", split="train", streaming=True)
large = load_dataset("general/large", split="train", streaming=True)

# small gets recycled while large exhausts
combined = interleave_datasets(
    [small, large],
    stopping_strategy="all_exhausted"
)
# Result: 2 * max(len(small), len(large)) samples — small wraps around
```

---

## 4. Performance Considerations

| Factor | Map-style (Dataset) | Iterable (IterableDataset) |
|--------|---------------------|----------------------------|
| Memory | Loads all rows into Arrow tables | Streams — O(1) memory per dataset |
| Concat axis=0 | Fast — Arrow `concat_tables` bulk op | Sequential chain of iterables |
| Concat axis=1 | Requires equal row count | Rebatch+horizontal concat iterable |
| Interleave | Pre-computes all indices, then `.select()` | On-the-fly source selection |
| Best for | Small/medium merged datasets | Large-scale streaming pipelines |

### Resharding for Parallelism

When using iterable interleaving with DataLoader workers:

```python
# Before interleaving: reshard to increase parallelism
d1 = d1.reshard()  # splits shards into more shards
d2 = d2.reshard()
combined = interleave_datasets([d1, d2])
```

`reshard()` returns a new dataset with `num_shards >= previous_num_shards`. The resulting interleave dataset's `num_shards` is the **minimum** of each dataset's `num_shards` — so low-shard datasets bottleneck parallelism.

---

## 5. Common Errors & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `ValueError: Unable to interleave a Dataset (at position 0) with a IterableDataset (at position 1)` | Mixed Dataset types | Convert all to same type |
| `ValueError: Number of rows must match for all datasets` | axis=1 concat with unequal row counts | Trim datasets to same length first |
| `ValueError: Expected a list of Dataset objects or a list of IterableDataset objects, but element at position 0 is an empty dataset dictionary` | Passed DatasetDict instead of Dataset | Select a split: `dataset['train']` |
| `ValueError: first_exhausted_with_replacement is not supported` | Invalid stopping_strategy string | Use one of: `first_exhausted`, `all_exhausted`, `all_exhausted_without_replacement` |
| Low parallelism in iterable interleave | One dataset has very few shards | Call `.reshard()` on the low-shard datasets |
| Output order non-deterministic after reload | Missed seed parameter | Always set `seed` for deterministic probabilistic interleaving |

---

## 6. Version History

- **v1.6.0** — `axis` parameter added to `concatenate_datasets`
- **v2.4.0** — IterableDataset support added to both functions; `info`, `split` params added
- **v4.5.0** — `all_exhausted_without_replacement` stopping strategy added
- **v5.0.0** — `reshard()` added for IterableDataset (improves parallelism before interleaving)
