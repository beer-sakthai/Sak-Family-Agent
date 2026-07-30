---
name: SakThai-datasets-features-schema-casting
author: SakThai
license: MIT
description: >
  Comprehensive deep dive into the Hugging Face Datasets Features system —
  type mapping, schema casting, nested features, ClassLabel, Sequence, ArrayXD,
  Audio, Image features, and efficient dataset transformation.
version: 1.0.0
metadata:
  hermes:
    tags: [huggingface, datasets, features, schema, casting, pyarrow, data-processing]
    category: mlops
category: mlops
---

# HF Datasets Features & Schema Casting — Deep Dive

## Overview

The `datasets.Features` class is the backbone of type management in HF Datasets. It defines the internal structure of a dataset as a typed dictionary mapping column names to feature types backed by Apache Arrow. This reference covers the entire Features system, including type mapping, schema casting, flattening, and best practices.

### The Type Hierarchy

```
Features (dict subclass)
├── Value(dtype)           — Scalar types (int32, string, float64, etc.)
├── ClassLabel             — Integer-coded categorical labels
├── List(feature)          — Variable-length list (32-bit offsets)
├── LargeList(feature)     — Large list (64-bit offsets for >2B elements)
├── Sequence(feature)      — Auto-converting wrapper (see Sequence vs List)
├── Json()                 — Free-form JSON objects
├── Array2D/3D/4D/5D       — Fixed-shape multi-dimensional arrays
├── Audio                  — Lazy-decoded audio files
├── Image                  — Lazy-decoded image files
├── Video                  — Lazy-decoded video (torchcodec)
├── Pdf                    — Lazy-decoded PDF (pdfplumber)
├── Nifti                  — Lazy-decoded NIfTI neuroimaging
├── Mesh                   — 3D mesh data
├── Translation            — Text translation pairs
└── TranslationVariableLanguages — Multi-language translation
```

---

## 1. `Value` — Scalar Types

`Value(dtype)` is the most fundamental feature type. It wraps a single pyarrow data type specified by string name.

### Supported dtypes

| Category | dtypes |
|----------|--------|
| Null | `null` |
| Boolean | `bool` |
| Integers (signed) | `int8`, `int16`, `int32`, `int64` |
| Integers (unsigned) | `uint8`, `uint16`, `uint32`, `uint64` |
| Floats | `float16`, `float32` (alias: `float`), `float64` (alias: `double`) |
| Time | `time32[s]`, `time32[ms]`, `time64[us]`, `time64[ns]` |
| Timestamp | `timestamp[s]`, `timestamp[ms]`, `timestamp[us]`, `timestamp[ns]`, `timestamp[us, tz=America/New_York]` |
| Date | `date32`, `date64` |
| Duration | `duration[s]`, `duration[ms]`, `duration[us]`, `duration[ns]` |
| Decimal | `decimal128(10,2)`, `decimal256(38,0)` |
| Binary | `binary`, `large_binary`, `binary_view` |
| String | `string`, `large_string`, `string_view` |

### Internal Mechanics

`Value` stores `dtype: str` and resolves it to a `pa.DataType` at init time via `string_to_arrow()`:

```python
def __post_init__(self):
    if self.dtype == "double": self.dtype = "float64"
    if self.dtype == "float":  self.dtype = "float32"
    self.pa_type = string_to_arrow(self.dtype)
```

The `string_to_arrow()` function:
1. First checks if the dtype string directly names a pyarrow factory (e.g. `pa.string()`)
2. Falls back to `pa.__dict__[dtype + "_"]()` if not found
3. Parses complex types via regex: `timestamp[us, tz=...]`, `time32[s]`, `decimal128(p,s)`, `duration[us]`
4. Raises `ValueError` with helpful examples if no match

### `encode_example()` behavior

```python
def encode_example(self, value):
    if pa.types.is_boolean(self.pa_type):  return bool(value)
    elif pa.types.is_integer(self.pa_type): return int(value)
    elif pa.types.is_floating(self.pa_type): return float(value)
    elif pa.types.is_string(self.pa_type):   return str(value)
    # ... etc
```

---

## 2. `ClassLabel` — Categorical Labels

`ClassLabel` stores labels as integers internally but supports string ↔ int conversion.

### Construction (3 ways)

| Method | Example |
|--------|---------|
| `num_classes` only | `ClassLabel(num_classes=5)` — creates labels `['0','1','2','3','4']` |
| `names` list | `ClassLabel(names=['neg', 'pos'])` — labels from list |
| `names_file` | `ClassLabel(names_file='/path/to/labels.txt')` — labels from file, one per line |

### Key API

| Method | Signature | Description |
|--------|-----------|-------------|
| `str2int(values)` | `str\|Iterable → int\|Iterable` | Convert label names to integers |
| `int2str(values)` | `int\|Iterable → str\|Iterable` | Convert integers to label names |
| `encode_example(value)` | `str\|int → int` | Auto-detect and encode |
| `cast_storage(storage)` | `pa.Array → pa.Int64Array` | Arrow-level casting |

### Internal Data

- `dtype = "int64"`, `pa_type = pa.int64()`
- `_str2int: dict[str, int]` — for fast string→int lookup
- `_int2str: list[str]` — ordered list index→name mapping
- Unknown/missing labels: -1 is allowed (denotes no label)
- Deduplication: raises `ValueError` if names are duplicated

### `cast_storage()` logic

```python
if isinstance(storage, pa.IntegerArray):
    # Validate max value is within num_classes
elif isinstance(storage, pa.StringArray):
    # Convert each string via str2int
return array_cast(storage, self.pa_type)
```

---

## 3. `Sequence`, `List`, `LargeList` — List Features

### `List(feature, length=-1)`

Backed by `pyarrow.ListType` (32-bit offsets, max ~2B elements per list).

- `length=-1`: variable-length lists
- `length=N`: fixed-length lists (backed by `pyarrow.FixedSizeListType`)

### `LargeList(feature)`

Backed by `pyarrow.LargeListType` (64-bit offsets, for >2B elements).

### `Sequence(feature, length=-1)`

**`Sequence` is NOT a concrete type.** It's a factory that auto-converts:

```python
def __new__(cls, feature=None, length=-1, **kwargs):
    if isinstance(feature, dict):
        # dict → dict of Lists (for TFDS compatibility)
        return {key: List(value, length=length) for key, value in feature.items()}
    else:
        # single feature → List
        return List(feature, length=length)
```

| Input | Output | Use Case |
|-------|--------|----------|
| `Sequence(Value("int32"))` | `List(Value("int32"))` | Simple list of scalars |
| `Sequence({"a": Value("int32"), "b": Value("string")})` | `{"a": List(Value("int32")), "b": List(Value("string"))}` | Dictionary → columns of lists |
| `List(Value("int32"))` | `List(Value("int32"))` | Direct, no conversion |

**Use `List` directly** unless you need TFDS compatibility behavior.

### Arrow Type Resolution

```python
elif isinstance(schema, LargeList):
    return pa.large_list(get_nested_type(schema.feature))
elif isinstance(schema, List):
    return pa.list_(get_nested_type(schema.feature), schema.length)
```

---

## 4. `ArrayXD` — Multi-Dimensional Arrays

| Class | Dimensions | Notes |
|-------|------------|-------|
| `Array2D(shape, dtype)` | 2D | e.g. `(32, 32)` grayscale image |
| `Array3D(shape, dtype)` | 3D | e.g. `(32, 32, 3)` RGB image |
| `Array4D(shape, dtype)` | 4D | e.g. batch of images |
| `Array5D(shape, dtype)` | 5D | e.g. video frames |

Backed by custom `pa.ExtensionType` subclasses (`Array2DExtensionType`, etc.) that store data as flattened arrays with shape metadata.

---

## 5. `Audio` Feature

| Property | Description |
|----------|-------------|
| `sampling_rate` | Target sample rate (None = native) |
| `num_channels` | Target channels: None (source), 1 (mono), 2 (stereo) |
| `decode` | `True` = decode to AudioDecoder, `False` = return `{"path": ..., "bytes": ...}` |

Accepts: file path, bytes dict, `{"array": ..., "sampling_rate": ...}` dict, or `torchcodec.decoders.AudioDecoder`.

Output: `torchcodec.decoders.AudioDecoder` when decode=True.

---

## 6. `Image` Feature

| Property | Description |
|----------|-------------|
| `mode` | PIL mode to convert to (None = native) |
| `decode` | `True` = decode to PIL Image, `False` = return `{"path": ..., "bytes": ...}` |

Accepts: file path, bytes dict, `np.ndarray`, `PIL.Image.Image`.

Output: `PIL.Image.Image` when decode=True.

Arrow storage type: `pa.struct({"bytes": pa.binary(), "path": pa.string()})`

---

## 7. `Features` Class (dict subclass)

### Construction

```python
from datasets import Features, Value, ClassLabel, Audio

# Simple
features = Features({"text": Value("string"), "label": ClassLabel(names=["neg", "pos"])})

# Nested
features = Features({
    "id": Value("string"),
    "answers": {
        "text": List(Value("string")),
        "answer_start": List(Value("int32"))
    },
    "audio": Audio(sampling_rate=16000),
    "image": Image(mode="RGB"),
})

# From existing schema
features = Features.from_arrow_schema(pa_schema)
features = Features.from_dict(serialized_dict)
```

### Key Properties & Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `.type` | `pa.DataType` | Nested Arrow type (StructType) |
| `.arrow_schema` | `pa.Schema` | Full Arrow schema with HF metadata |
| `.from_arrow_schema(pa_schema)` | `Features` | Reconstruct from Arrow schema |
| `.from_dict(dict)` | `Features` | Reconstruct from serialized dict |
| `.to_dict()` | `dict` | Serialize to JSON-compatible dict |
| `.copy()` | `Features` | Deep copy |
| `.flatten(max_depth=16)` | `Features` | Flatten nested structs to dot-separated columns |
| `.reorder_fields_as(other)` | `Features` | Reorder columns to match another Features |
| `.encode_example(example)` | `dict` | Encode a row dict for Arrow |
| `.encode_batch(batch)` | `dict` | Encode a batch dict for Arrow |
| `.decode_example(example)` | `dict` | Decode a row (audio/image lazy loading) |
| `.decode_batch(batch)` | `dict` | Decode a batch |
| `_to_yaml_list()` | `list` | YAML-compatible serialization |

### Arrow Schema Metadata

When `arrow_schema` is built, HF adds metadata:

```python
hf_metadata = {"info": {"features": self.to_dict()}}
return pa.schema(self.type).with_metadata({"huggingface": json.dumps(hf_metadata)})
```

When reconstructing from Arrow schema, `from_arrow_schema` first checks this metadata for exact feature types. If the metadata matches the schema fields, the original features are preserved. Otherwise, `generate_from_arrow_type` is used as fallback.

---

## 8. Dataset Transformation Methods

### `cast(features)`

Convert the entire dataset to a new `Features` schema.

```python
ds = ds.cast(new_features)
# batch_size=1000, num_proc=None available
```

- **Validation**: column names must be identical (same set)
- **Process**: batched `map` calling `table_cast(schema)` per batch
- **Use when**: changing multiple columns or their types

### `cast_column(column, feature)`

Cast a single column to a new feature type.

```python
ds = ds.cast_column("label", ClassLabel(names=["bad", "good"]))
ds = ds.cast_column("audio", Audio(sampling_rate=44100))
```

- **Fast path**: for features with `decode_example`, just updates schema and casts Arrow data
- **Slow path**: falls back to full `cast()` for other changes

### `flatten(max_depth=16)`

Flattens nested struct columns into dot-separated column names.

```python
# Before: answers: {"text": [...], "answer_start": [...]}
# After:  answers.text, answers.answer_start
ds = ds.flatten()
```

- Works on Arrow table's struct columns directly
- Iteratively flattens up to `max_depth`
- Updates Features accordingly

### `remove_columns(column_names)`

Remove one or more columns without copying remaining data.

```python
ds = ds.remove_columns("unnecessary_column")
ds = ds.remove_columns(["col1", "col2", "col3"])
```

- **Fast**: doesn't copy remaining columns' data
- Accepts single string or list of strings

### `rename_column(original_name, new_name)` / `rename_columns(mapping)`

Rename columns in the dataset.

```python
ds = ds.rename_column("old_name", "new_name")
ds = ds.rename_columns({"old1": "new1", "old2": "new2"})
```

---

## 9. Arrow ↔ Datasets Type Mapping

### Key Functions

| Function | Direction | Description |
|----------|-----------|-------------|
| `string_to_arrow(datasets_dtype)` | str → `pa.DataType` | Resolves dtype strings like `"int32"`, `"timestamp[us]"` |
| `_arrow_to_datasets_dtype(arrow_type)` | `pa.DataType` → str | Maps pyarrow types back to dtype strings |
| `get_nested_type(schema)` | `FeatureType` → `pa.DataType` | Converts any Features dict/tree to Arrow type |
| `generate_from_arrow_type(pa_type)` | `pa.DataType` → `FeatureType` | Converts Arrow type to minimal Features type |
| `generate_from_dict(obj)` | `dict` → `FeatureType` | Reconstructs from serialized `{_type: ..., ...}` dicts |

### Type Mapping Table

| Arrow Type | Datasets Type | Notes |
|------------|---------------|-------|
| `pa.int32()` | `Value('int32')` | |
| `pa.string()` | `Value('string')` | |
| `pa.large_string()` | `Value('large_string')` | |
| `pa.struct(...)` | `dict` / `Features` | Nested columns |
| `pa.list_(type)` | `List(feature)` | Variable length |
| `pa.large_list(type)` | `LargeList(feature)` | 64-bit offsets |
| `pa.fixed_size_list(type, N)` | `List(feature, length=N)` | Fixed length |
| `pa.timestamp(unit, tz)` | `Value('timestamp[unit, tz=...]')` | |
| `pa.json()` | `Json()` | |
| `ArrayXDExtensionType` | `ArrayXD(shape, dtype)` | Multi-dim arrays |
| Custom extension | `Audio`, `Image`, etc. | Via `from_arrow_schema` metadata |

---

## 10. Performance & Backward Compatibility

### Encoding Pipeline

When building a dataset:

```
Example (dict) → encode_example() → Arrow RecordBatch → Arrow Table
                                        ↓
                              cast_to_python_objects() converts
                              torch/tf/np → native Python
```

### Decoding Pipeline

When accessing data:

```
Arrow Table → decode_example() → decoded Python dict
                        ↓
           Audio/Image lazily decoded only
           when the column is accessed
```

### `require_decoding()` and `require_storage_cast()`

These helper functions determine at feature construction time whether decoding or storage casting is needed per column, avoiding unnecessary work.

### `_is_zero_copy_only(pa_type)`

For certain pyarrow types, data can be shared without copying. The function `_is_zero_copy_only()` determines this based on the arrow type.

### Backward Compatibility — `_fix_for_backward_compatible_features()`

The `_fix_for_backward_compatible_features()` function handles old-style feature definitions where `list` instead of `List` was used. It ensures old datasets load correctly.

---

## 11. Best Practices

1. **Use `List` not `Sequence`** — Unless you specifically need TFDS compatibility. `Sequence` adds indirection and confusion.

2. **Specify `Audio(sampling_rate=N)` when loading** — This avoids having to recast and re-download later. Downsampling at load time is more efficient.

3. **Use `Image(decode=False)` for selective decoding** — If you need to inspect paths/bytes without decoding all images, pass `decode=False` and decode on demand.

4. **`cast_column()` for single columns, `cast()` for bulk** — `cast_column()` is faster for one-off changes as it avoids the `map` overhead.

5. **`flatten()` before `to_csv()` or `to_parquet()`** — Nested struct columns are not always well-supported in flat formats.

6. **Use `remove_columns()` instead of `map(remove_columns=...)`** — The former doesn't copy data of remaining columns.

7. **Store as `decimal128(10,2)` not `float`** for financial data — Avoids floating-point rounding.

8. **Check `Features.from_arrow_schema()` for Round-Trip Safety** — When loading saved Arrow files, verify features are reconstructed via metadata.

---

## 12. Key Code References

| File | Lines | Content |
|------|-------|---------|
| `features/features.py` | 494–576 | `Value` class |
| `features/features.py` | 993–1188 | `ClassLabel` class |
| `features/features.py` | 1190–1255 | `Json` class |
| `features/features.py` | 1281–1360 | `Sequence`, `List`, `LargeList` |
| `features/features.py` | 578–750 | `_ArrayXD`, Array2D-5D |
| `features/features.py` | 1408–1438 | `get_nested_type()` |
| `features/features.py` | 1441–1478 | `encode_nested_example()` |
| `features/features.py` | 1565–1600 | `generate_from_dict()` |
| `features/features.py` | 1603–1629 | `generate_from_arrow_type()` |
| `features/features.py` | 1856–2356+ | `Features` class |
| `features/audio.py` | 24–84 | `Audio` feature |
| `features/image.py` | 47–93 | `Image` feature |
| `arrow_dataset.py` | 2316–2360 | `Dataset.flatten()` |
| `arrow_dataset.py` | 2362–2444 | `Dataset.cast()` |
| `arrow_dataset.py` | 2447–2487 | `Dataset.cast_column()` |
| `arrow_dataset.py` | 2491–2515 | `Dataset.remove_columns()` |

---

## 13. Related Resources

- [datasets Features API Documentation](https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.Features)
- [PyArrow Data Types](https://arrow.apache.org/docs/python/api/datatypes.html)
- [datasets Table Module](https://github.com/huggingface/datasets/blob/main/src/datasets/table.py) — `array_cast()` and table operations
