# HF Learnings: Data-Juicer

## 2026-07-30: Data-Juicer v1.5.4 — Data Operating System for Foundation Models (Topic #412)

### Summary
Deep dive into Data-Juicer — the open-source data processing framework by Alibaba Tongyi Lab (NeurIPS 2025 Spotlight). Covers the full architecture: 200+ modular operators (filters, mappers, deduplicators, selectors), NestedDataset wrapping HF Datasets, recipe-first YAML pipelines, cloud-native Ray execution (70B samples / 2h on 50 nodes), LLM-powered semantic operators (v1.5.2+), and integration with Hugging Face Hub for dataset I/O and pre-processed dataset publishing. Latest v1.5.4 adds HumanVBench video operators and batch-local stage fusion.

### Key Findings

#### 1. Architecture Layers
- **Data layer**: NestedDataset (wraps HF datasets.Dataset) with operator chaining via `.process([...])`
- **Operator layer**: 200+ OPs in 4 types (Filter, Mapper, Deduplicator, Selector) + PipelineOp for composition
- **Config layer**: YAML recipes (`dj-process --config process.yaml`)
- **Execution layer**: single-process → multi-worker → Ray distributed (Partitioned Ray Executor v1.5.0)
- **LLM layer**: Semantic operators using vLLM, OpenAI API, or DashScope for LLM-based extraction/filtering

#### 2. Key Differentiators vs Other Tools
- **vs datatrove**: DJ is broader (multi-modal, not just text), has HF native integration, 200+ OPs vs datatrove's ~20
- **vs HF Datasets.map()**: DJ provides composable operator chains with hot-reload, Ray distributed execution, and full-spectrum data intelligence (filtering, dedup, LLM extraction)
- **vs Distilabel**: DJ focuses on raw data processing/cleaning at scale, Distilabel focuses on synthetic data generation and annotation pipelines

#### 3. HF Integration Points
- **NestedDataset** wraps `datasets.Dataset` directly — load any HF dataset
- `push_to_hub()` / `to_hf_dataset()` for round-trip with HF Hub
- The `datajuicer` HF org hosts 35+ refined datasets (RedPajama, The Pile, Alpaca-CoT, LLaVA-Pretrain)
- Agent data quality toolkit supports HuggingFace meta loading for agent trace datasets
- Semantic LLM operators can use HF Inference API

#### 4. Practical Usage Patterns
- **Pre-training data cleaning**: Filter by language, length, perplexity; dedup with MinHash
- **SFT data preparation**: Normalize whitespace, filter short/low-quality, dedup
- **Agent trace processing**: Use agent_bad_case_signal_mapper, structure context, quality gate
- **Video/MM data**: Caption via VLM, filter by aspect ratio/duration, dedup near-duplicate frames

#### 5. Operator Categories (200+)
| Type | Count | Examples |
|------|-------|---------|
| Text Filter | ~50 | length, language, perplexity, special chars, stopwords |
| Text Mapper | ~40 | normalization, cleaning, expansion, translation |
| Image Filter | ~30 | aspect ratio, resolution, NSFW, blur, aesthetic score |
| Image Mapper | ~20 | resize, caption, watermark removal |
| Audio Filter | ~15 | duration, silence, sample rate, SNR |
| Video Filter | ~20 | duration, motion, face count, scene cut |
| Deduplicator | ~15 | MinHash, exact, document-line, video |
| Selector | ~5 | top-k, random, stratified |
| Pipeline | ~5 | sub-pipeline composition |

### Resources Created
- Skill: `mlops/hf-data-juicer/SKILL.md` — Comprehensive reference with code examples and architecture overview
