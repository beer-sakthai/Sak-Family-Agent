# Embedding Model + llm_cron Schema Compliance

## Problem

The verify script's schema auto-detection has a specific ordering:

```python
# Detection order in verify-health-check.py:
elif 'target_model' in d and 'health_score' in d and 'sibling_comparison' in d:
    SCHEMA = 'llm_cron'
    required_keys = ['target_model', 'architecture', 'repo_summary', 'benchmarks',
                     'card_quality', 'health_score', 'sibling_comparison', 'eval_metadata']
```

If your YAML has **all three** of `target_model`, `health_score`, and `sibling_comparison` as top-level keys, it's detected as **llm_cron** schema — even if the model is an embedding model that naturally has no benchmarks.

## Required sections for embedding models under llm_cron

To pass verification when detected as llm_cron, include these sections:

### `benchmarks:`
```yaml
benchmarks:
  count: 0
  note: "No model-index — embedding models lack standard leaderboard format"
```

### `repo_summary:`
```yaml
repo_summary:
  total_gb: 0.4542
  total_repo_bytes: 487720403
  file_count: 10
  weight_file: model.safetensors
  weight_bytes: 470637416
  has_weights: true
```

### `card_quality:`
```yaml
card_quality:
  license: mit
  tags_count: 14
  datasets_count: 7
  readme_bytes: 9961
  has_model_index: false
  has_eval_results: false
  tags:
    - sentence-transformers
    - embeddings
    ...
  datasets:
    - Nanthasit/sakthai-combined-v6
    ...
```

## Alternative: avoid llm_cron detection

If you'd rather not include the extra sections, structure the YAML so it matches a different schema variant:

- **Remove `sibling_comparison`** → it falls through to plain `target_model` (old schema), which requires `assessment` instead of `health_score`.
- **Use `metadata`/`core_metrics`/`file_inventory`** → new schema (embedding variant). Detection:
  ```python
  elif 'metadata' in d and 'core_metrics' in d:
      SCHEMA = 'new'
  ```
  Embedding variant auto-detects via `file_inventory` presence.

**Chosen approach (this session):** Include all llm_cron-required sections with embedding-appropriate values. The `benchmarks` section simply states `count: 0` with an explanatory note.
