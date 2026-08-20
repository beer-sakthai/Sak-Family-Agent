---
name: SakThai-hf-datasets-configuration-system
description: "Hugging Face Datasets configuration system — BuilderConfig, BUILDER_CONFIGS, config IDs, dataset_infos.json, YAML metadata configs, packaged module configs, and config resolution at load time."
---

# HF Datasets Configuration System

Complete reference for the Hugging Face Datasets configuration system (v5.0.0
and huggingface_hub v1.24.0+). Covers the full lifecycle of dataset
configurations: definition in builder classes, YAML metadata in README.md,
serialization to `dataset_infos.json`, resolution during `load_dataset()`, and
impact on caching and data loading.

## Key Files

| File | Role |
|---|---|
| `builder.py` | `BuilderConfig` dataclass, `DatasetBuilder` with `BUILDER_CONFIGS` |
| `info.py` | `DatasetInfo` (per-config metadata), `DatasetInfosDict` |
| `utils/metadata.py` | `MetadataConfigs` — YAML `configs` field parsing |
| `load.py` | `create_builder_configs_from_metadata_configs()`, `BuilderConfigsParameters` |
| `config.py` | Constants: `DATASET_INFO_FILENAME`, `DATASETDICT_INFOS_FILENAME`, `METADATA_CONFIGS_FIELD` |

## Architecture

```
Dataset Repository README.md
└─ YAML frontmatter: configs: [...]   ← user-defined configs
        │
        ▼
  MetadataConfigs (dict[config_name → params])
        │
        ▼
  BuilderConfig objects (name, version, data_files, data_dir, description)
        │
        ▼
  DatasetBuilder._create_builder_config()
        │
        ├─ Pre-defined: matched from BUILDER_CONFIGS by name
        └─ Custom: instantiated with kwargs on the fly
        │
        ▼
  Config ID (= name + optional suffix hash for data_files/kwargs/features)
        │
        ▼
  Cache directory: {namespace}___{dataset_name}/{config_id}/{version}/{hash}/
```

## BuilderConfig

```python
@dataclass
class BuilderConfig:
    name: str = "default"
    version: Optional[Union[Version, str]] = Version("0.0.0")
    data_dir: Optional[str] = None
    data_files: Optional[Union[DataFilesDict, DataFilesPatternsDict]] = None
    description: Optional[str] = None
```

- **name** — Used to name the cache subdirectory. Validated against Windows-incompatible chars.
- **version** — Default `0.0.0`. Used in cache path.
- **data_dir** — Path to source data directory (local or remote).
- **data_files** — Patterns dict or resolved file dict. Accepted as patterns (str/list/dict) in YAML; resolved to `DataFilesDict` at load time.
- **description** — Human-readable description shown in dataset viewer.
- **create_config_id(config_kwargs, custom_features)** — Generates unique ID with suffix: URL-quoted kwargs (or hash if >32 chars), plus features hash if custom features provided.

## DatasetBuilder Configuration Attributes

```python
class DatasetBuilder:
    VERSION = None                    # builder-level default version
    BUILDER_CONFIG_CLASS = BuilderConfig  # subclass for custom configs
    BUILDER_CONFIGS = []              # list of predefined BuilderConfig objects
    DEFAULT_CONFIG_NAME = None         # which config to use when name=None
```

### Config Resolution in _create_builder_config()

1. If `config_name` is None and `BUILDER_CONFIGS` is non-empty:
   - Use `DEFAULT_CONFIG_NAME` if set
   - If >1 config and no kwargs → raise ValueError with example usage
   - If exactly 1 config → use it as default
2. If `config_name` is a string → look up in `builder_configs` dict
3. If no matching predefined config → instantiate `BUILDER_CONFIG_CLASS(**config_kwargs)`
4. If matching predefined config → deepcopy and apply config_kwargs overrides
5. Resolve data files patterns
6. Compute config ID via `create_config_id()`
7. If config_id is custom (not in BUILDER_CONFIGS and not "default") → log warning
8. If name collides with predefined config but params differ → raise ValueError

### builder_configs classproperty

```python
@classproperty
@classmethod
@memoize()
def builder_configs(cls) -> dict[str, BuilderConfig]:
    return {config.name: config for config in cls.BUILDER_CONFIGS}
```

Memoized, validates no duplicate names.

## MetadataConfigs — YAML Card Configs

Defined in `datasets/utils/metadata.py` as `dict[str, dict[str, Any]]`.

**YAML format in README.md `configs` field:**

```yaml
configs:
  - config_name: default
    data_files: data/*
    version: 1.0.0
  - config_name: filtered
    data_files:
      - split: train
        path: train/*.parquet
      - split: test
        path: test/*.parquet
    default: true
  - config_name: multilingual
    data_files: multilingual/*.csv
    features:
      - name: text
        dtype: string
      - name: label
        dtype:
          class_label:
            names:
              - pos
              - neg
```

**Parsing rules:**
- `from_dataset_card_data()`: Reads `configs` list from `DatasetCardData`, validates each entry has `config_name`, validates `data_files` format
- `to_dataset_card_data()`: Writes back to `DatasetCardData`, preserves order
- `get_default_config_name()`: Returns the single config that is either named "default" or has `default: true`, or is the only config; raises on multiple defaults
- `_from_exported_parquet_files_and_dataset_infos()`: Auto-generates configs from Parquet export (Datasets Server integration)

**data_files validation in YAML:**

```yaml
# Valid forms:
data_files: data.csv                              # single file
data_files: data/*.png                            # glob pattern
data_files:                                       # multiple patterns
  - part0/*
  - part1/*
data_files:                                       # split-based
  - split: train
    path: train/*
  - split: test
    path: test/*
data_files:                                       # multi-file per split
  - split: train
    path:
      - train/part1/*
      - train/part2/*
```

## create_builder_configs_from_metadata_configs()

```python
def create_builder_configs_from_metadata_configs(
    module_path, metadata_configs, base_path=None,
    default_builder_kwargs=None, download_config=None
) -> tuple[list[BuilderConfig], str]:
```

- Imports builder class from module
- Uses `builder_cls.BUILDER_CONFIG_CLASS` to instantiate configs
- For each config in metadata_configs:
  - Extracts `data_files`, `data_dir`, and extra kwargs
  - Resolves data files relative to `base_path + data_dir`
  - Passes `version` from metadata or falls back to builder `VERSION` or `"0.0.0"`
  - Creates `BuilderConfig(version, data_files, data_dir, **extra_kwargs)`
- Returns `(builder_configs, default_config_name)`

## BuilderConfigsParameters

```python
@dataclass
class BuilderConfigsParameters:
    metadata_configs: Optional[MetadataConfigs] = None
    builder_configs: Optional[list[BuilderConfig]] = None
    default_config_name: Optional[str] = None
```

Created by `_prepare_builder_configs_parameters()` during `load_dataset()`:
1. Tries to parse YAML frontmatter from dataset module files (`.py` script or packaged module)
2. Reads `configs` field from `DatasetCardData`
3. If YAML has `configs`:
   - Creates `MetadataConfigs.from_dataset_card_data(dataset_card_data)`
   - Calls `create_builder_configs_from_metadata_configs()`
   - Populates `BuilderConfigsParameters` with metadata_configs, builder_configs, default_config_name
4. Returns the parameters for later use in `_get_builder_cls()` → `configure_builder_class()`

## DatasetInfo and DatasetInfosDict

### DatasetInfo (per-config metadata)

```python
@dataclass
class DatasetInfo:
    description: str = ""
    citation: str = ""
    homepage: str = ""
    license: str = ""
    features: Optional[Features] = None
    supervised_keys: Optional[SupervisedKeysData] = None
    builder_name: Optional[str] = None
    dataset_name: Optional[str] = None
    config_name: Optional[str] = None
    version: Optional[Union[str, Version]] = None
    splits: Optional[SplitDict] = None
    download_checksums: Optional[dict] = None
    download_size: Optional[int] = None
    dataset_size: Optional[int] = None
    size_in_bytes: Optional[int] = None
```

- Serialized to `dataset_info.json` (per-config) via `write_to_directory()`
- Loaded from `dataset_info.json` via `from_directory()`
- `_INCLUDED_INFO_IN_YAML` controls which fields appear in YAML card: `config_name`, `download_size`, `dataset_size`, `features`, `splits`

### DatasetInfosDict (all configs)

```python
class DatasetInfosDict(dict[str, DatasetInfo]):
    # key = config_name, value = DatasetInfo
    def write_to_directory(dataset_infos_dir, overwrite=False, pretty_print=False)
```

Serialized to `dataset_infos.json` — the canonical file on the Hub that lists all configs with their features, splits, sizes, and versions.

## Config ID System

The config ID determines the cache subdirectory:

```
{namespace}___{dataset_name}/{config_id}/{version}/{hash}/
```

**Config ID = config.name + optional suffix** when:
- `config_kwargs` are passed (beyond name/version)
- `custom_features` is provided
- `data_files` is used

**Suffix generation:**
1. Remove `name` and `version` from config_kwargs
2. Canonicalize `data_dir` path via `os.path.normpath()`
3. Sort remaining kwargs alphabetically
4. If all values are str/bool/int/float → URL-encoded comma-separated string
5. If string length > 32 → SHA256 hash
6. If any non-primitive value → SHA256 hash via `Hasher`
7. If custom_features → hash everything including existing suffix
8. Final config_id = `name + "-" + suffix` (or truncated and re-hashed if >255 chars)

## Cache Directory Architecture

```
~/.cache/huggingface/datasets/
├── {dataset_name}/
│   ├── {config_id}/
│   │   ├── {version}/
│   │   │   ├── {hash}/
│   │   │   │   ├── dataset_info.json      # DatasetInfo
│   │   │   │   ├── state.json             # generation state
│   │   │   │   ├── {split}-00000-of-00001.arrow
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── downloads/...
└── ...
```

For packaged modules (csv, json, etc.), the hash is computed from module content hashes + config parameters. Legacy cache dirs (datasets <3.0.0) are auto-detected via `_check_legacy_cache()` and `_check_legacy_cache2()`.

## Packaged Modules Config Patterns

Packaged modules (csv, json, parquet, imagefolder, audiofolder, text) define their own BUILDER_CONFIG_CLASS subclasses:

| Module | BuilderConfig | Extra Fields |
|---|---|---|
| csv | `CsvConfig` | sep, header, names, skiprows, etc. |
| json | `JsonConfig` | field, features |
| parquet | `ParquetConfig` | features (optional) |
| imagefolder | `ImageFolderConfig` | features, drop_labels, drop_metadata |
| audiofolder | `AudioFolderConfig` | features, drop_labels, drop_metadata, sampling_rate |
| text | `TextConfig` | features, sample_by |

Each packaged module also has pre-defined config entries in its module definition that map to its BuilderConfig subclass.

## Dataset Card YAML → Config Flow

```yaml
---
# README.md YAML frontmatter
configs:
  - config_name: my_config
    data_files: data/**/*.jsonl
    version: 2.0.0
---
```

1. `load_dataset("user/repo")` reads the dataset module
2. YAML frontmatter is parsed → `DatasetCardData`
3. `configs` field extracted → `MetadataConfigs.from_dataset_card_data()`
4. `create_builder_configs_from_metadata_configs()` → `BuilderConfig[]`
5. `configure_builder_class()` patches `BUILDER_CONFIGS` onto the builder class
6. `DatasetBuilder.__init__()` calls `_create_builder_config()` which resolves against these configs
7. Data is downloaded and generated according to the resolved config

## Dataset Server Configs Integration

The Datasets Server (external service, not part of datasets library) exposes config information via:
- `/configs` endpoint: lists all configs
- `/parquet` endpoint: shows Parquet export per config
- `/first-rows` endpoint: preview data for a specific config

These are read from `dataset_infos.json` in the repo and from the `configs` field in the dataset card YAML.

## Key Constraints

- Config names: No Windows-incompatible chars (`\/:*?"<>|`)
- Config name uniqueness: `BUILDER_CONFIGS` must have unique names
- Default config: Only one config can be default
- Config ID max readable length: 255 chars (truncated and hashed if exceeded)
- LFS/regular file limits: 25k LFS files, 1GB regular payload per commit for data files
- Split naming: Dashes (`-`) not allowed in split names

## Practical Usage

```python
# Load with specific config
from datasets import load_dataset
ds = load_dataset("user/dataset", "config_name", split="train")

# Check available configs
from datasets import get_dataset_config_names
configs = get_dataset_config_names("user/dataset")

# Get splits for a config
from datasets import get_dataset_split_names
splits = get_dataset_split_names("user/dataset", "config_name")

# Check config metadata via Hub API
from huggingface_hub import HfApi
api = HfApi()
info = api.dataset_info("user/dataset")
# cardData.configs contains the YAML configs definition

# Load with custom data files (for packaged builders)
ds = load_dataset("json", data_files={"train": "train.jsonl", "test": "test.jsonl"})
# This creates a custom config with data_files → config ID = "default-{hash}"

# Get dataset_infos.json content
from datasets import get_dataset_infos
infos = get_dataset_infos("user/dataset")  # returns DatasetInfosDict
```

## Sources
- datasets v5.0.0 source: `builder.py` (BuilderConfig, DatasetBuilder._create_builder_config)
- datasets v5.0.0 source: `info.py` (DatasetInfo, DatasetInfosDict)
- datasets v5.0.0 source: `utils/metadata.py` (MetadataConfigs)
- datasets v5.0.0 source: `load.py` (create_builder_configs_from_metadata_configs, BuilderConfigsParameters)
- datasets v5.0.0 source: `config.py` (config constants)
- huggingface_hub v1.24.0 source: `repocard_data.py` (DatasetCardData)
- https://huggingface.co/docs/datasets/main/en/loading#configurations-and-splits
- https://huggingface.co/docs/datasets/main/en/dataset_script#multiple-configurations
