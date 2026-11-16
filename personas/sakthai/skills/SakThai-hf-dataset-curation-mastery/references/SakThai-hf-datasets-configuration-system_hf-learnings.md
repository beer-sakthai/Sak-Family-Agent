# HF Learnings Log

## 2026-07-25: hf-datasets-configuration-system-complete-reference

### Summary
Comprehensive deep dive into the Hugging Face Datasets configuration system (v5.0.0). Covers the full lifecycle of dataset configurations: `BuilderConfig` base class, `BUILDER_CONFIGS` predefined configs, `DEFAULT_CONFIG_NAME` selection, config ID generation with suffix hashing, YAML metadata configs from README.md, `dataset_infos.json` serialization, config resolution in `load_dataset()`, cache directory architecture, packaged module configs, and integration with the Datasets Server.

### Key Findings

**BuilderConfig (@dataclass):**
- 5 fields: `name` (default: "default"), `version` (default: "0.0.0"), `data_dir`, `data_files`, `description`
- Validates Windows-incompatible chars in name
- `create_config_id()` generates unique cache ID with suffix from config_kwargs, custom_features, data_files

**Config Resolution (3 paths):**
1. No config specified → DEFAULT_CONFIG_NAME or single config or raise
2. String config_name → lookup in builder_configs dict
3. Custom → instantiate BUILDER_CONFIG_CLASS with kwargs
Plus override path: deepcopy predefined config + apply kwargs

**Config ID:**
- Base = config.name
- Suffix added when config_kwargs/fatures/data_files differ from predefined
- URL-encoded string if all primitive values and ≤32 chars; SHA256 hash otherwise
- Max readable length: 255 chars (truncated + hashed if exceeded)

**MetadataConfigs (YAML `configs` field):**
- Dict[config_name → params] parsed from DatasetCardData
- Validates data_files format (str, list of str, or split-based list)
- Auto-generates default detection via name="default" or `default: true`
- `_from_exported_parquet_files_and_dataset_infos()` auto-creates configs from Parquet export

**Cache Directory:**
```
{dataset_name}/{config_id}/{version}/{hash}/
```
With namespace prefix `{namespace}___{dataset_name}` for Hub repos.
Supports legacy cache migration from datasets <3.0.0.

**Packaged Module Configs:**
Each packaged module defines its own BuilderConfig subclass:
csv→CsvConfig (sep, header), json→JsonConfig (field), parquet→ParquetConfig, imagefolder→ImageFolderConfig, audiofolder→AudioFolderConfig (sampling_rate), text→TextConfig (sample_by)

**Key Integration Points:**
- load_dataset() → BuilderConfigsParameters → configure_builder_class() → DatasetBuilder.__init__() → _create_builder_config()
- dataset_infos.json stores all config metadata on Hub
- Datasets Server reads both YAML `configs` field and dataset_infos.json

### Skill Created
`hf-datasets-configuration-system/` — complete reference with architecture, API surface, config ID system, YAML metadata format, cache layout, and practical usage examples.

### Sources
- datasets v5.0.0 source: `builder.py` (BuilderConfig: lines 100-212, DatasetBuilder._create_builder_config: lines 503-592)
- datasets v5.0.0 source: `info.py` (DatasetInfo: lines 91-280, DatasetInfosDict: lines 334-440)
- datasets v5.0.0 source: `utils/metadata.py` (MetadataConfigs: lines 46-189)
- datasets v5.0.0 source: `load.py` (create_builder_configs_from_metadata_configs: lines 320-374, BuilderConfigsParameters: lines 377-392)
- datasets v5.0.0 source: `config.py` (constants: lines 236-248)
- huggingface_hub v1.24.0 source: `repocard_data.py` (DatasetCardData constructor)
- https://huggingface.co/docs/datasets/main/en/loading#configurations-and-splits
- https://huggingface.co/docs/datasets/main/en/dataset_script#multiple-configurations

---
