# HF Learnings Log

## 2026-07-25: datasets-features-schema-casting-deep-dive

### Summary
Deep dive into the Hugging Face Datasets Features system — the type definition layer that maps dataset column schemas to Apache Arrow types. Covers the full type hierarchy (Value, ClassLabel, Sequence, List, LargeList, ArrayXD, Audio, Image, Json, Translation), the Features dict class, cast/cast_column/flatten/remove_columns transformations, and the bidirectional mapping between datasets FeatureType and pyarrow DataType.

### Key Findings

#### Value Scalar Types
- 26+ supported scalar dtypes mapped via `string_to_arrow()`: null, bool, int8-64, uint8-64, float16/32/64, time32/64, timestamp (with timezone), date32/64, duration, decimal128/256, binary/large_binary/binary_view, string/large_string/string_view
- `float` maps to `float32`, `double` maps to `float64` — fixed in `__post_init__`
- Complex types parsed via regex: `timestamp[us, tz=America/New_York]`, `decimal128(10, 2)`, `time32[s]`

#### ClassLabel
- 3 construction methods: `num_classes`, `names` list, `names_file` path
- Arrow storage as `pa.int64()` with -1 reserved for unknown/missing
- `str2int()` with 3-attempt resolution: raw lookup → stripped → int parse
- `cast_storage()` accepts `pa.StringArray` or `pa.IntegerArray` as input

#### Sequence vs List vs LargeList
- `Sequence` is a factory function, not a concrete type — it converts to `List` (for scalars) or `dict` of `List`s (for sub-features)
- `List` uses 32-bit offsets (`pa.list_()`), max ~2B elements
- `LargeList` uses 64-bit offsets (`pa.large_list()`), for huge lists
- Fixed-length lists: `List(feature, length=N)` backed by `pa.fixed_size_list()`

#### Features Class Internals
- `Features` is a dict subclass with synced mutations (via `keep_features_dicts_synced` decorator)
- `arrow_schema` embeds HF metadata: `{"huggingface": json.dumps({"info": {"features": ...}})}`
- `from_arrow_schema()` first checks metadata for exact feature types, falls back to `generate_from_arrow_type()`
- Encode/decode pipeline: `encode_example()` → Arrow, `decode_example()` ← Arrow (lazy Audio/Image decoding)

#### Casting Operations
- `cast(features)`: full dataset recast via batched `map(table_cast)` — column names must match
- `cast_column(column, feature)`: single-column fast path when feature has `decode_example`
- `flatten()`: iteratively flattens struct columns (max_depth=16), producing dot-separated names
- `remove_columns()`: no-copy removal of columns

#### Arrow↔Datasets Type Mapping
- `get_nested_type(FeatureType)` → `pa.DataType` (recursive, handles dict/list/List/LargeList + callables)
- `generate_from_arrow_type(pa_type)` → `FeatureType` (struct→dict, list→List, extension→ArrayXD, primitive→Value)
- `string_to_arrow(str)` → `pa.DataType` (resolves dtype strings via `pa.__dict__` + regex)
- `_arrow_to_datasets_dtype(pa_type)` → `str` (inverse of string_to_arrow)

#### Audio Feature
- Accepts: file path, bytes dict, `{"array":..., "sampling_rate":...}`, or `AudioDecoder`
- Output: `torchcodec.decoders.AudioDecoder` (when `decode=True`)
- Key params: `sampling_rate`, `num_channels` (mono/stereo), `decode`, `stream_index`

#### Image Feature
- Accepts: file path, bytes dict, `np.ndarray`, `PIL.Image.Image`
- Output: `PIL.Image.Image` (when `decode=True`)
- Arrow storage: `pa.struct({"bytes": pa.binary(), "path": pa.string()})`
- Key params: `mode` (PIL mode), `decode`

### Skill Created
`datasets-features-schema-casting/` — complete deep-dive reference with type hierarchy, casting operations, and pyarrow type mapping.

---
