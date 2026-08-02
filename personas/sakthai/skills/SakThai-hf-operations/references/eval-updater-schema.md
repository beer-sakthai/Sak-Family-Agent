# Eval-Updater Schema (`llm_cron_v1`)

The `hf-eval-updater` cron job uploads a metadata-based eval snapshot to
`.eval_results/` on one Nanthasit model per run. The schema below is the
`llm_cron_v1` format — a comprehensive self-contained health-and-context
snapshot that does NOT require live inference.

## File naming

```
.eval_results/cron-eval-{model-slug}-{YYYY-MM-DD}-{run-n}.yaml
```

Example: `.eval_results/cron-eval-sakthai-coder-browser-2026-07-30-1.yaml`

## Full schema

```yaml
target_model:
  id: Nanthasit/{repo}
  pipeline_tag: text-generation
  library_name: transformers
  base_model: Qwen/Qwen2.5-1.5B-Instruct
  downloads: <int>
  likes: <int>
  private: false
  gated: false
  last_modified: <ISO-8601>
  model_age_days: <float>
  model_type: llm | peft-lora-adapter
  has_weights: true

architecture:
  base_model_type: qwen2
  base_architectures: ["Qwen2ForCausalLM"]
  base_hidden_size: <int>
  base_num_hidden_layers: <int>
  base_num_attention_heads: <int>
  base_num_key_value_heads: <int>
  base_intermediate_size: <int>
  base_vocab_size: <int>
  base_max_position_embeddings: <int>
  base_total_parameters: <int>
  base_dtype: bfloat16
  # PEFT-specific (omit for full models):
  peft_type: LORA
  lora_r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  use_rslora: true
  target_modules: ["o_proj", "k_proj", ...]

repo_summary:
  siblings_count: <int>
  total_repo_bytes: <int>
  has_weights: true
  weight_file_count: <int>
  weight_files: ["model.safetensors"]
  # Booleans for key files:
  adapter_config_present: true
  tokenizer_present: true
  chat_template_present: true
  readme_present: true
  readme_size_bytes: <int>

benchmarks:
  model_index_count: <int>      # 0 unless model-index present
  metrics_count: <int>
  all_verified: false
  pending_metrics: 0
  entries: []                   # populated from model-index if any
  notes: "..."                  # free-text assessment and recommendations

training:
  dataset: Nanthasit/{dataset}
  dataset_size: <int>
  training_method: QLoRA + SFT via TRL
  eval_split: <str>             # e.g. "113 held-out examples"
  key_improvements_v2:          # optional, version-specific
    - "200+ edge-case examples"
    - "Multi-turn support"

card_quality:
  license: apache-2.0
  base_model_documented: true
  base_model: Qwen/Qwen2.5-1.5B-Instruct
  tags_count: <int>
  tags: [list, of, tags]
  datasets_cited: ["Nanthasit/{dataset}"]
  model_index_present: false
  readme_size_bytes: <int>
  widget_example: <str>         # e.g. "What's the weather in Dublin?"
  deductions: ["No model index — benchmarks cannot be displayed"]
  score: <0-100>

health_score:
  overall: <0-100>             # weighted composite
  components:
    popularity: <0-100>        # 20% weight
    momentum: <0-100>          # 20%
    benchmarks: <0-100>        # 25%
    card_quality: <0-100>      # 20%
    repo_hygiene: <0-100>      # 15%
  weights:                     # mirror for transparency
    popularity: 0.20
    momentum: 0.20
    benchmarks: 0.25
    card_quality: 0.20
    repo_hygiene: 0.15

sibling_comparison:
  rank_by_downloads: <int>     # position among author's models
  total_author_models: <int>
  max_sibling_downloads: <int>
  models_with_positive_downloads: <int>
  velocity_rank: <int>
  max_sibling_velocity: <float>  # downloads/day of top sibling
  our_velocity: <float>         # this model's downloads/day

eval_type: metadata_cron
eval_note: >
  Free-text narrative of the model's status, what was done,
  and recommendations for the next cycle.

eval_metadata:
  model: Nanthasit/{repo}
  eval_date: <YYYY-MM-DD>
  eval_time: "<HH:MM:SSZ>"
  schema: llm_cron_v1
  age_days: <float>
  days_since_last_update: <float>
  download_velocity: <float>
  cron_run: <int>
```

## Data sources

| Field | Source |
|-------|--------|
| `target_model` | `curl -s "https://huggingface.co/api/models/Nanthasit/{repo}"` |
| `architecture` | `config.json` from API or raw fetch |
| `repo_summary` | `siblings` array from API — NOTE: `size` is 0 there; fetch `/api/models/Nanthasit/{repo}/tree/main?recursive=true` for real byte sizes (`total_repo_bytes`, `readme_size_bytes`, weight file sizes) |
| `benchmarks` | `model-index` from cardData |
| `training` | card README (YAML frontmatter + body) |
| `card_quality` | cardData fields + README size |
| `sibling_comparison` | `curl -s "https://huggingface.co/api/models?author=Nanthasit"` sorted by downloads |
| `health_score` | computed from components with weights |

## Computation rules

- **download_velocity**: `downloads / max(1, days_since_creation)` — if 0 downloads, 0.0
- **model_age_days**: `(now - created_at) / 86400`
- **health_score.overall**: weighted sum of 5 components using the declared weights
- **popularity**: `min(100, downloads / 100)` — 0 if no downloads
- **momentum**: `min(100, download_velocity * 10)` — 0 if no velocity
- **benchmarks**: 100 if all metrics verified, 50 if some, 0 if none
- **card_quality**: subjective score based on README detail, tags, datasets cited, model-index presence
- **repo_hygiene**: 100 if all expected files present, deduct for missing files
