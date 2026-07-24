
# HF Learnings — Datasets Builder API

## 2026-07-24: hf-datasets-builder-advanced-patterns — Deep Dive (Topic #124)

### Summary
Deep-dive into the `datasets` library's Builder API — the foundation for creating custom datasets that integrate seamlessly with Hugging Face's caching, streaming, and Hub publishing workflows. Covers the `DatasetBuilder` base class, `GeneratorBasedBuilder` pattern, `BuilderConfig` for multi-config datasets, `DatasetInfo` metadata, `SplitGenerator` and split specifications, packaged modules, and real-world patterns for packaging and distributing custom datasets.

### Core Architecture

The builder system has four main components:

| Component | Purpose | Location |
|-----------|---------|----------|
| `DatasetBuilder` | Abstract base class; defines the lifecycle | `datasets/builder.py` |
| `GeneratorBasedBuilder` | Convenience subclass for dict-generator datasets | `datasets/builder.py` |
| `BuilderConfig` | Configuration dataclass for multi-variant datasets | `datasets/builder.py` |
| `DatasetInfo` | Metadata container (features, splits, citation, etc.) | `datasets/info.py` |

### Builder Lifecycle

```
1. __init__()        → Sets cache_dir, config, features, token, data_files
2. download_and_prepare() → Downloads source data, generates Arrow cache files
3. info              → DatasetInfo property (features, splits, citation)
4. as_dataset()      → Returns Dataset or DatasetDict from cached Arrow files
5. as_streaming_dataset() → Returns IterableDataset (no local cache needed)
```

The full lifecycle is managed by `load_dataset()` and `load_dataset_builder()`:

```python
# load_dataset_builder() separates config from download
builder = load_dataset_builder("my_dataset", config_name="v1")
print(builder.info)               # inspect before download
builder.download_and_prepare()    # download + process
ds = builder.as_dataset()         # get Dataset/DatasetDict

# load_dataset() does everything in one call
ds = load_dataset("my_dataset", name="v1")
```

### DatasetBuilder — Class Attributes

Every builder subclass can set these class-level attributes:

```python
class MyDataset(DatasetBuilder):
    VERSION = "1.0.0"                    # Default version
    BUILDER_CONFIG_CLASS = BuilderConfig  # Config class (or custom subclass)
    BUILDER_CONFIGS = []                  # List of predefined BuilderConfig objects
    DEFAULT_CONFIG_NAME = None            # Default config when name=None
    DEFAULT_WRITER_BATCH_SIZE = None      # ArrowWriter batch size
```

These control how the dataset is identified, configured, and cached.

### The Three Abstract Methods

Every custom dataset builder must implement **three key methods**:

#### 1. `_info()` — Define DatasetInfo (Features, Citation, Splits)

```python
def _info(self) -> DatasetInfo:
    return DatasetInfo(
        description="My custom dataset",
        features=Features({
            "text": Value("string"),
            "label": ClassLabel(names=["pos", "neg"]),
            "id": Value("int32"),
        }),
        supervised_keys=None,
        homepage="https://example.com",
        citation="@article{...}",
    )
```

`DatasetInfo` fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `features` | `Features` | Yes | Schema of each example |
| `description` | `str` | No | Human-readable description |
| `citation` | `str` | No | BibTeX citation |
| `homepage` | `str` | No | Dataset homepage URL |
| `license` | `str` | No | License info |
| `version` | `Version` or `str` | No | Version specifier |
| `splits` | `SplitDict` | No | Defined by `_split_generators` |
| `download_size` | `int` | No | Size of downloads in bytes |
| `dataset_size` | `int` | No | Size of generated dataset in bytes |

#### 2. `_split_generators()` — Define Splits and Download Sources

```python
def _split_generators(self, dl_manager: DownloadManager) -> list[SplitGenerator]:
    # dl_manager handles downloads, caching, and extraction
    data_dir = dl_manager.download_and_extract("https://example.com/data.zip")

    return [
        SplitGenerator(
            name=Split.TRAIN,
            gen_kwargs={"data_path": data_dir / "train.jsonl", "split": "train"},
        ),
        SplitGenerator(
            name=Split.TEST,
            gen_kwargs={"data_path": data_dir / "test.jsonl", "split": "test"},
        ),
    ]
```

`SplitGenerator` takes:
- `name` — split name (Split.TRAIN, Split.TEST, Split.VALIDATION, or custom string)
- `gen_kwargs` — dict passed to `_generate_examples()`
- `split_info` — optional `SplitInfo` for explicit metadata

The `dl_manager` (DownloadManager) provides:
- `download(url_or_urls)` — download files, returns local paths
- `extract(path_or_paths)` — extract archives
- `download_and_extract(url_or_urls)` — download + extract in one step
- `download_custom(url, ...)` — custom download with progress
- `iter_archive(path)` — iterate over archive entries without extracting

#### 3. `_generate_examples()` — Yield Examples

```python
def _generate_examples(self, data_path, split):
    """Yield (key, example) tuples."""
    import json
    with open(data_path, "r") as f:
        for idx, line in enumerate(f):
            data = json.loads(line)
            yield idx, {
                "text": data["text"],
                "label": 0 if data["sentiment"] == "pos" else 1,
                "id": data.get("id", idx),
            }
```

**Critical rules:**
- Yields `(key, example_dict)` tuples — **key must be unique** and deterministic
- Key is used for deterministic shuffling (hashed + sorted)
- Example dict keys must match `self.info.features`
- Can use `self.info.features.encode_example(dict)` for automatic encoding

### GeneratorBasedBuilder — Full Example

```python
import datasets
from datasets import DatasetInfo, Features, Value, ClassLabel, Split, SplitGenerator
from datasets import GeneratorBasedBuilder, DownloadManager

class MyTextDataset(GeneratorBasedBuilder):
    """Custom text classification dataset."""

    VERSION = "1.0.0"

    def _info(self) -> DatasetInfo:
        return DatasetInfo(
            description="My text classification dataset",
            features=Features({
                "text": Value("string"),
                "label": ClassLabel(names=["negative", "positive"]),
            }),
            homepage="https://example.com",
        )

    def _split_generators(self, dl_manager: DownloadManager) -> list[SplitGenerator]:
        # For local data: no download needed
        return [
            SplitGenerator(
                name=Split.TRAIN,
                gen_kwargs={"filepath": "data/train.jsonl"},
            ),
            SplitGenerator(
                name=Split.TEST,
                gen_kwargs={"filepath": "data/test.jsonl"},
            ),
        ]

    def _generate_examples(self, filepath):
        import json
        with open(filepath, "r") as f:
            for idx, line in enumerate(f):
                data = json.loads(line)
                yield idx, {
                    "text": data["text"],
                    "label": data["label"],
                }
```

### Loading the Custom Builder

**Method 1: Module path (for packaged datasets)**
```python
ds = load_dataset("path/to/dataset_script.py", split="train")
```

**Method 2: From the Hub**
```python
# Push builder to hub first, then load
ds = load_dataset("username/dataset", split="train")
```

**Method 3: Packaged module (csv, json, parquet, etc.)**
```python
ds = load_dataset("json", data_files="data.jsonl", split="train")
ds = load_dataset("csv", data_files="data.csv", delimiter="\t", split="train")
ds = load_dataset("parquet", data_files="data.parquet", split="train")
ds = load_dataset("text", data_files="*.txt", split="train")
```

**Method 4: Using load_dataset_builder with manual control**
```python
builder = load_dataset_builder("path/to/dataset_script.py")
print(builder.info)              # inspect features & splits
print(builder.builder_configs)   # inspect available configs
builder.download_and_prepare()   # manual lifecycle control
ds = builder.as_dataset()
```

### BuilderConfig — Configurable Datasets

When a dataset has multiple variants, subclass `BuilderConfig` and register them:

```python
from dataclasses import dataclass
from typing import Optional
import datasets

@dataclass
class MyConfig(datasets.BuilderConfig):
    """Configuration for MyTextDataset."""
    max_length: Optional[int] = None
    language: str = "en"

class MyTextDataset(datasets.GeneratorBasedBuilder):
    BUILDER_CONFIG_CLASS = MyConfig
    BUILDER_CONFIGS = [
        MyConfig(name="en_short", language="en", max_length=128,
                 description="English, max 128 tokens"),
        MyConfig(name="en_full", language="en", max_length=None,
                 description="English, full length"),
        MyConfig(name="fr_short", language="fr", max_length=128,
                 description="French, max 128 tokens"),
    ]
    DEFAULT_CONFIG_NAME = "en_short"

    def _generate_examples(self, filepath):
        # Access config via self.config
        lang = self.config.language
        max_len = self.config.max_length
        ...
```

**Config properties available in all builders:**
- `self.config.name` — configuration name
- `self.config.version` — configuration version
- `self.config.data_dir` — source data directory
- `self.config.data_files` — source data files specification

With configs, users load different variants:
```python
ds = load_dataset("username/dataset", "en_short")
ds = load_dataset("username/dataset", "fr_short")
```

### Config ID System (Cache Key)

Each builder instance generates a **config ID** — the config name plus an optional hash suffix for:
- Custom features
- Data files
- Config kwargs overrides

```python
builder = load_dataset_builder(
    "json",
    data_files="my_data.jsonl",
    features=Features({"text": Value("string")}),
)
# Config ID = "default" + hash(custom_features + data_files)
```

This ensures that different configurations produce **separate cache directories** and never collide.

### Split Specifications

The `splits.py` module provides the split infrastructure:

**Named splits (predefined):**
```python
Split.TRAIN     # "train"
Split.TEST      # "test"
Split.VALIDATION  # "validation"
```

**Custom split names** — any string works:
```python
SplitGenerator(name="train_small", ...)
SplitGenerator(name="calibration", ...)
```

**SplitInfo** — explicit metadata for each split:
```python
from datasets import SplitInfo

split_info = SplitInfo(
    name="train",
    num_examples=100000,       # optional, auto-computed
    num_bytes=1234567890,      # optional, auto-computed
)
```

**ReadInstruction** — slicing syntax for `.as_dataset()`:
```python
# Integer indices
ds = builder.as_dataset(split="train[0:100]")       # first 100
ds = builder.as_dataset(split="train[10%:90%]")     # middle 80%

# Named splits
ds = builder.as_dataset(split=["train", "test"])     # returns DatasetDict
```

### DatasetInfo — Metadata Deep Dive

```python
from datasets import DatasetInfo, Features, Value, ClassLabel, SplitDict, SplitInfo, Version

info = DatasetInfo(
    description="...",
    citation="""@article{..., year=2024}""",
    homepage="https://example.com",
    license="MIT",
    features=Features({...}),
    version=Version("2.0.0"),
    splits={
        "train": SplitInfo(name="train", num_examples=1000),
    },
    download_size=1024**3,      # bytes
    dataset_size=2048**3,       # bytes
)
```

`DatasetInfo` is serializable via YAML — it produces the content shown on the Hub's dataset card. Loading an existing dataset's info:
```python
ds = load_dataset("...", split="train")
print(ds.info)           # full metadata
print(ds.features)       # just the schema
print(ds.info.splits)    # split metadata
```

### Packaged Modules (Built-in Builders)

The `datasets/packaged_modules/` directory contains pre-built builders for common formats:

| Module | Builder | Description | Config Parameters |
|--------|---------|-------------|-------------------|
| `csv` | `CsvConfig` + `csv` | CSV files | `sep`, `header`, `names`, `usecols`, `quoting`, `encoding` |
| `json` | `JsonConfig` + `json` | JSON/JSONL files | `field`, `use_metadata_thread` |
| `parquet` | `ParquetConfig` + `parquet` | Parquet files | `batch_size`, `columns`, `filters` |
| `text` | `TextConfig` + `text` | Text files (line-by-line) | `encoding`, `chunksize` |
| `imagefolder` | `ImageFolderConfig` | Image classification folders | `drop_labels`, `drop_metadata` |
| `audiofolder` | `AudioFolderConfig` | Audio datasets | `drop_labels`, `drop_metadata` |
| `videofolder` | `VideoFolderConfig` | Video datasets | `drop_labels`, `drop_metadata` |
| `pandas` | `PandasConfig` | Pandas DataFrames | `features`, `split` |
| `arrow` | Arrow files | Direct Arrow reading | `streaming`, `in_memory` |
| `sql` | SQL query results | `con`, `sql`, `index_col` |
| `spark` | PySpark DataFrames | Direct PySpark conversion |
| `webdataset` | TAR archives | Streaming from TAR |
| `conll` | CONLL format | `column_names` |
| `xml` | XML files | `xpath` |
| `hdf5` | HDF5 files | `key` |
| `lance` | Lance format | Direct Lance reading |
| `iceberg` | Apache Iceberg | Table reference |

Each packaged module exposes a config class (subclass of `BuilderConfig`) that users can pass to `load_dataset()`:

```python
# CSV with custom delimiter
ds = load_dataset("csv", data_files="data.tsv", sep="\t", split="train")

# Parquet with column projection + filters
import pyarrow.dataset as ds_expr
ds = load_dataset("parquet", data_files="data.parquet",
                  columns=["text", "label"],
                  filters=[("date", ">=", "2024-01-01")])

# Pandas DataFrame
import pandas as pd
df = pd.DataFrame({"text": ["hello"], "label": [0]})
ds = load_dataset("pandas", data_files=df, split="train")

# JSON with specific field
ds = load_dataset("json", data_files="data.jsonl",
                  field="data", split="train")
```

### The `_generate_tables` Pattern (Arrow-Level Builder)

For builders that produce Arrow tables directly (not example dicts), use `_generate_tables` instead of `_generate_examples`. This is the advanced path used by packaged modules:

```python
def _generate_tables(self, filepath, split) -> Iterator[pa.Table]:
    """Yield PyArrow tables directly."""
    import pyarrow as pa
    import pyarrow.json as paj
    table = paj.read_json(filepath)
    yield table
```

When `_generate_tables` is defined, `_prepare_split` uses it instead of `_generate_examples`. This is **faster** for data that's already tabular (Parquet, Arrow, Pandas DataFrames).

The default `_generate_shards` method can be overridden to track original shard-to-Arrow-file mappings for the Dataset Viewer:

```python
def _generate_shards(self, filepath):
    for shard_path in sorted(Path(filepath).glob("shard-*.parquet")):
        yield str(shard_path)
```

### Creating Dataset Scripts for the Hub

To share a custom dataset on the Hub, create a **dataset script** (a Python file with a builder class):

**File: `my_dataset.py`**
```python
import datasets

class MyDataset(datasets.GeneratorBasedBuilder):
    """Documentation for MyDataset."""
    
    VERSION = datasets.Version("1.0.0")

    def _info(self):
        return datasets.DatasetInfo(
            description="...",
            features=datasets.Features({
                "text": datasets.Value("string"),
                "label": datasets.ClassLabel(names=["neg", "pos"]),
            }),
        )

    def _split_generators(self, dl_manager):
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={"filepath": dl_manager.download(URL)},
            ),
        ]

    def _generate_examples(self, filepath):
        with open(filepath) as f:
            for i, line in enumerate(f):
                yield i, {"text": line.strip(), "label": 0}
```

**Upload to Hub:**
```python
from huggingface_hub import HfApi
api = HfApi()
api.create_repo("username/my_dataset", repo_type="dataset")
api.upload_file(
    path_or_fileobj="my_dataset.py",
    path_in_repo="my_dataset.py",
    repo_id="username/my_dataset",
    repo_type="dataset",
)
```

Users then load it:
```python
ds = load_dataset("username/my_dataset", split="train")
```

### Best Practices

1. **Deterministic keys** — Always use stable, deterministic keys in `_generate_examples()`. Keys should uniquely identify examples across re-generations. Bad: random UUIDs. Good: line numbers, IDs from source data.

2. **Avoid side effects** — `_generate_examples()` should be pure: given the same `gen_kwargs`, it should yield the same examples. This enables caching and multiprocessing.

3. **Use dl_manager for all downloads** — Never hardcode local paths. Always use `dl_manager.download()` / `dl_manager.download_and_extract()` — this enables cache invalidation and the `DownloadMode` system.

4. **Streaming-friendly** — Design splits to work with streaming by yielding examples one at a time. Avoid operations that require full dataset in memory.

5. **Config for variants** — Use `BuilderConfig` subclasses for datasets with multiple processing options (languages, sizes, filtering). Never create separate builders for each variant.

6. **Commit complete DatasetInfo** — Fill in description, citation, homepage, and license. These appear on the Hub's dataset card.

7. **Test locally first** — Before uploading to Hub:
```python
builder = load_dataset_builder("my_dataset.py")
builder.download_and_prepare()
ds = builder.as_dataset(split="train")
print(len(ds))
print(ds[0])
```

8. **Version your data** — Use `VERSION` (or per-config versions) to track changes. Increment when source data or processing changes.

9. **Shard responsibly** — Use `max_shard_size` in `download_and_prepare()` for large datasets. Default is now configurable via `datasets.config.MAX_SHARD_SIZE`.

10. **Use `num_proc` for speed** — `download_and_prepare(num_proc=N)` splits `gen_kwargs` across N processes. Each process gets a separate set of shards from `_split_generators`.

### Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Non-deterministic keys | Different cache fingerprints every run | Use stable IDs, not random values |
| Missing `_info()` | AttributeError on load | Always define features |
| Wrong features in `_info()` vs `_generate_examples()` | Arrow schema mismatch | Match exactly or use `features` parameter in `load_dataset()` |
| Hardcoded local paths | Broken on other machines | Use `dl_manager.download()` |
| Null values not declared | Arrow cast errors | Use `Value("string")` with null, or `Sequence(Value("int32"))` for nullable lists |
| No `DEFAULT_CONFIG_NAME` when `BUILDER_CONFIGS` is populated | ValueError on loading without name | Set `DEFAULT_CONFIG_NAME` or require `name` parameter |
| `_generate_examples` returns dict with extra keys | Warning/ignored silently | Match keys to `Features` exactly |
| Streaming + multiprocess | Deadlock | Streaming mode disables `num_proc` automatically |

### Key Takeaways

1. Three methods to implement: `_info()`, `_split_generators()`, `_generate_examples()`
2. `GeneratorBasedBuilder` is the standard class for 90% of custom datasets
3. `BuilderConfig` enables multi-variant datasets without code duplication
4. Packaged modules (csv, json, parquet, etc.) cover most common formats without custom code
5. Always use `dl_manager` for downloads to enable caching and streaming
6. Dataset scripts on the Hub are Python files with a builder class
7. `load_dataset_builder()` gives fine-grained lifecycle control
8. The config ID system ensures cache isolation between variants

### Sources
- datasets v5.0.0 installed at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/`
- Builder source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/builder.py` (1916 lines)
- Info source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/info.py` (440 lines)
- Docs: https://huggingface.co/docs/datasets/en/dataset_script
- Docs: https://huggingface.co/docs/datasets/en/package_reference/builder_classes
- Dataset creation guide: https://huggingface.co/docs/datasets/en/create_dataset
