---
name: SakTan-ops-hf-ecosystem-health
version: 1.1.0
description: Multi-source health snapshot, telemetry audit, and gap analysis for Hugging
  Face ecosystem assets.
category: operations
tags:
- daily-ops
- ecosystem
- hf
- huggingface
- ops
- portfolio
- telemetry
---

# Hugging Face Ecosystem Health Audit

A comprehensive operational guide for auditing and monitoring Hugging Face Hub assets
(models, datasets, spaces, and collections) under the `Nanthasit` organization.

## Purpose & Scope

- Periodic portfolio health check across models, datasets, spaces, and collections.
- Telemetry gathering: download metrics, likes, pipeline tags, and metadata completeness.
- Detecting repository gaps (missing READMEs, missing evaluation results, unlinked collections).
- Operating under strict $0.00 USD financial spend using public APIs and read-only endpoints.

## 1. Quick Audit Execution

Run the canonical portfolio health check script from the repository root:

```bash
uv run python3 scripts/hf-portfolio-health.py
```

The script evaluates:
- **Models**: Validates `pipeline_tag`, library tags (`transformers`, `sentence-transformers`), and card metadata.
- **Datasets**: Audits documentation and tag taxonomy.
- **Spaces**: Verifies container runtime status and SDK configuration (`gradio`, `docker`, `static`).
- **Collections**: Verifies asset aggregation in `sakthai-model-family`.

## 2. Telemetry & Metric Endpoints

Query Hugging Face Hub public REST endpoints with standard headers:

```bash
# 1. Fetch author model catalog
curl -sSf "https://huggingface.co/api/models?author=Nanthasit&full=true" \
  | python3 -c "import json, sys; models = json.load(sys.stdin); sys.stdout.write(f'Total Models: {len(models)}\n')"

# 2. Check specific model card & sibling files
curl -sSf "https://huggingface.co/api/models/Nanthasit/sakthai-context-7b-tools" \
  | python3 -c "import json, sys; m = json.load(sys.stdin); sys.stdout.write('Siblings: ' + str([f['rfilename'] for f in m.get('siblings', [])]) + '\n')"

# 3. Check Space runtime status
curl -sSf "https://huggingface.co/api/spaces/Nanthasit/sakthai-chat" \
  | python3 -c "import json, sys; s = json.load(sys.stdin); sys.stdout.write('Stage: ' + str(s.get('runtime', {}).get('stage')) + '\n')"
```

## 3. Operational Gaps & Remediation Patterns

| Gap Detected | Diagnostic Signal | Remediation Action |
|--------------|-------------------|-------------------|
| Missing `pipeline_tag` | Model cannot run inference widget | Propose PR or draft card update with valid tag |
| Space in `STOPPED` state | Inactivity sleep or hardware crash | Verify build logs, restart space via API |
| Unlinked model in Collection | Model absent from `sakthai-model-family` | Hand off to SakThai for collection indexing |
| Download metrics drop | Telemetry delta negative or flat | Check README search tags and documentation |

## 4. Cross-Persona Coordination

- **SakTan (Ops & Telemetry)**: Executes read-only telemetry audits, identifies gaps, and logs findings.
- **SakThai (Hub Master)**: Has write authority to update model cards, create releases, or modify collections.
- **SakSit (Storytelling & Cards)**: Drafts enriched markdown copy, benchmarks, and usage guides.

```bash
# Log portfolio audit outcome to SakTan's memory shard:
sakthai learn --persona saktan "HF AUDIT: models: <count> | downloads: <sum> | gaps: <summary>" \
  --kind observation --tag hf-audit --tag saktan
```
