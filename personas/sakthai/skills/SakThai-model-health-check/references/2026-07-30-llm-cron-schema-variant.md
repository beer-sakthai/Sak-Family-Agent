# LLM Cron Schema Variant

Detected: 2026-07-30 (Health check on `sakthai-context-7b-merged`)
Repository: `sakthai-model-health-check`

## Problem

The `verify-health-check.py` script failed with 5 `MISSING_KEY` errors when run against the LLM cron health-check YAML. The script only recognized "old" (`target_model`, `popularity`, `files`, `card_content`, `architecture`, `multimodal`, `assessment`, `eval_metadata`), "new" (`metadata`, `core_metrics`, `model_artifacts`, `health_score`), "slim" (`health_check`, `usage`, `base_model`, `files`, `card_metadata`, `tags_count`), and "generic" (`model`, `metadata`, `age`, `popularity`, `repo_content`, `assessment`) schemas.

The LLM cron uses a fifth variant that mixes keys from "old" and "new" schemas.

> **⚠ Internal key divergence:** Even within the `health_score` block of llm_cron YAMLs, the overall score key varies. The canonical llm_cron structure uses `health_score.final_score`, but some generators output `health_score.overall` (flat structure). When computing deltas against a previous YAML, check both keys. See `references/2026-07-30-health-score-key-divergence.md` for the full extraction pattern.

## LLM Cron Schema Structure

```yaml
target_model:               # ← from "old" schema
  id: model_id
  downloads: N
  likes: N
  created_at: timestamp
  age_days: float
  velocity_dl_per_day: float
  pipeline_tag: string
  library_name: string
  base_model: string
  license: string
  last_modified: timestamp

architecture:               # ← from "old" schema
  architectures: [str]
  model_type: str
  hidden_size: int
  num_attention_heads: int
  num_hidden_layers: int
  intermediate_size: int
  vocab_size: int
  max_position_embeddings: int
  rms_norm_eps: float
  num_params_approx: str

repo_summary:               # ← replaces "files" from old schema
  total_gb: float
  largest_file: str
  largest_gb: float
  safetensors: {count, total_gb}
  gguf: {count, total_gb}

benchmarks:                 # ← unique to llm_cron
  has_model_index: bool
  benchmark_count: int
  details:
    - task: str
      dataset: str
      metric: str
      value: float
      verified: bool

card_quality:               # ← replaces "card_content" from old schema
  readme_size_kb: float
  has_license: bool
  has_pipeline_tag: bool
  has_base_model: bool
  tags_count: int
  datasets_count: int

health_score:               # ← nested scoring (like "new" schema), NOT flat assessment
  components:
    popularity: {raw, weight, contribution}
    momentum: {raw, weight, contribution}
    benchmarks: {raw, weight, contribution}
    card_quality: {raw, weight, contribution}
    repo_hygiene: {raw, weight, contribution}
  raw_weighted: float
  adjustments: [str]
  final_score: int
  delta_from_prev: int

sibling_comparison:         # ← unique to llm_cron schema
  sibling-model-name:
    downloads: int
    likes: int
    age_days: float
    velocity: float
    total_gb: float
    largest_gb: float
    largest_file: str
    has_gguf: bool
    hidden_size: int
    num_layers: int
    num_heads: int
    selection_accuracy: float (optional)

eval_metadata:              # ← from "old" schema
  timestamp: str
  source: str
  cost: int
  cron_profile: str
```

## Detection Logic

Detected by checking for BOTH `target_model` AND `health_score` (not `assessment`) as top-level keys:

```python
if 'target_model' in d and 'health_score' in d and 'sibling_comparison' in d:
    SCHEMA = 'llm_cron'
```

The `target_model` key alone triggers "old" schema detection, but the "old" schema requires `popularity`, `files`, `card_content`, `multimodal`, and `assessment` — all absent in llm_cron. The `health_score` key disambiguates.

## Required Keys for Verification

```python
required_keys = [
    'target_model', 'architecture', 'repo_summary', 'benchmarks',
    'card_quality', 'health_score', 'sibling_comparison', 'eval_metadata'
]
```

## Identity & Metrics Extraction

```python
# Model identity
mid = d['target_model']['id']

# Score — NOTE: `final_score` is canonical for llm_cron, but some
# generators produce `health_score.overall` instead. When computing
# deltas, check BOTH keys (see references/2026-07-30-health-score-key-divergence.md):
#   hs.get('final_score') or hs.get('overall')
raw_score = d['health_score']['final_score']

# Downloads
dl = d['target_model']['downloads']

# File size (approx GB → bytes)
total_gb = d['repo_summary']['total_gb']
size_bytes = int(total_gb * 1024**3)
```

## Models Using This Schema

The LLM cron schema is used for all `text-generation` + `qwen2` architecture models in Beer's ecosystem. As of 2026-07-30, these include:
- `sakthai-context-7b-merged`
- `sakthai-context-1.5b-merged`
- `sakthai-context-0.5b-merged`
- (and potentially vision models if they adopt the same template)

## Why Not Consolidate Into "Old" Schema?

The "old" schema was designed for vision/multimodal models with `popularity`, `files`, `card_content`, and `multimodal` sections. The `assessment` section uses a flat `score` with no component breakdown. The LLM cron needs:
- **Componential scoring** (`health_score.components.*`) for transparency
- **Sibling comparison** side-by-side for family-level insight
- **Delta tracking** (`delta_from_prev`) for trend monitoring
- **GGUF/safetensors breakdown** under `repo_summary`

These divergences warrant a separate schema rather than forcing fit into the old structure.
