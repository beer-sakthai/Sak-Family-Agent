---
name: SakThai-hf-data-juicer
description: "Data-Juicer — the open-source data processing framework for foundation model data (text, image, audio, video, multimodal). 200+ operators (filters, mappers, deduplicators, selectors), cloud-native Ray execution, Hugging Face Datasets integration, and"
---

# Data-Juicer: Data Operating System for Foundation Models

Data-Juicer (DJ) is an open-source data processing framework by Alibaba Tongyi Lab that transforms raw data into AI-ready intelligence. It provides **200+ modular operators** (filters, mappers, deduplicators, selectors) for text, image, audio, video, and multimodal data, composable into reproducible YAML recipes. Scales from laptop to thousand-node Ray clusters.

NeurIPS 2025 **Spotlight** paper. v1.5.4 latest (July 2026).

## Key References

- **GitHub**: https://github.com/modelscope/data-juicer
- **Docs**: https://datajuicer.github.io/data-juicer/
- **PyPI**: `pip install py-data-juicer`
- **Operator Zoo**: https://datajuicer.github.io/data-juicer/en/main/docs/Operators.html
- **Recipes Hub**: https://github.com/datajuicer/data-juicer-hub
- **Paper**: https://arxiv.org/abs/2501.14755 (NeurIPS 2025 Spotlight)
- **HF Organization**: https://huggingface.co/datajuicer
- **DJ Copilot**: https://datajuicer.github.io/data-juicer/en/main/docs_index.html

## Core Concepts

### 1. NestedDataset — HF Datasets Native

Data-Juicer's `NestedDataset` wraps Hugging Face `datasets.Dataset` with operator chaining:

```python
from data_juicer.core.data import NestedDataset
from data_juicer.ops.filter import TextLengthFilter
from data_juicer.ops.mapper import WhitespaceNormalizationMapper

ds = NestedDataset.from_dict({
    "text": ["Short", "This passes.", "Text   with   spaces"]
})
res = ds.process([
    TextLengthFilter(min_len=10),
    WhitespaceNormalizationMapper()
])
```

Directly load/save from HF Hub:
```python
from datasets import load_dataset
from data_juicer.core.data import NestedDataset

hf_ds = load_dataset("your-org/your-dataset", split="train")
nested = NestedDataset(hf_ds)
clean = nested.process([...])
clean.to_hf_dataset().push_to_hub("your-org/your-dataset-clean")
```

### 2. Operator Taxonomy (200+ Operators)

| Category | Purpose | Examples |
|----------|---------|---------|
| **Filter** | Remove low-quality samples | `TextLengthFilter`, `LanguageIDFilter`, `PerplexityFilter`, `ImageAspectRatioFilter`, `AudioDurationFilter` |
| **Mapper** | Transform individual samples | `WhitespaceNormalizationMapper`, `ImageResizeMapper`, `VideoCaptionMapper`, `LLMExtractMapper` |
| **Deduplicator** | Remove near-duplicates | `MinHashDeduplicator`, `DocumentLineDeduplicator`, `VideoDeduplicator` |
| **Selector** | Pick top-K samples | `TopKSelector`, `RandomSelector` |
| **Pipeline** | Compose sub-pipelines | `PipelineOp` groups multiple OPs |

### 3. Recipe-First YAML Pipelines

```yaml
# process.yaml
dataset_path: path/to/data.jsonl
export_path: path/to/output.jsonl
process:
  - text_length_filter:
      min_len: 10
      max_len: 100000
  - language_id_filter:
      lang: en
  - whitespace_normalization_mapper: {}
  - minhash_deduplicator:
      num_bands: 20
      num_rows: 5
```

Run: `dj-process --config process.yaml`

### 4. Cloud-Native Ray Execution

- Scales from single process → multi-GPU → 1000-node Ray cluster
- Partitioned Ray Executor (v1.5.0): Fault-tolerant distributed execution
- Ray + vLLM pipelines for LLM/VLM inference at scale
- Auto OP fusion: 2-10x speedup
- Handles 70B samples in 2h on 50 Ray nodes (6400 cores)

### 5. Use Cases

| Domain | Examples |
|--------|---------|
| Pre-training | Web data cleaning, CC/RedPajama/FineWeb-style pipelines |
| Fine-tuning | SFT data filtering, instruction quality grading |
| RL/RLHF | Preference data curation, reward model data prep |
| Agent Systems | Tool interaction traces, quality gating, de-identification |
| RAG | Extraction, normalization, semantic chunking |
| VLA/Embodied AI | Camera calibration, action segmentation, LeRobot export |

### 6. Quick Install

```bash
uv pip install py-data-juicer           # core (text + basic image)
uv pip install "py-data-juicer[all]"    # full (audio, video, Ray)
uv pip install "py-data-juicer[minimal]" # text only
```

## Common Pitfalls

1. **Dependency conflicts**: Use `[minimal]` then add extras as needed
2. **ARM64**: Some audio/video deps don't compile; use Docker
3. **Ray memory**: Large clusters need careful memory planning
4. **JSONL format**: Default data format; also supports Parquet, Arrow, CSV
5. **HF Dataset conversion**: `to_hf_dataset()` may lose DJ-specific metadata
6. **LLM API costs**: Semantic operators call external LLMs; cache or use local vLLM
