---
license: mit
language:
- en
pretty_name: SakThai Eval Results
size_categories:
- n<1K
task_categories:
- other

annotations_creators:
- machine-generated
language_creators:
- found
multilinguality:
- monolingual
source_datasets:
- Nanthasit/sakthai-combined-v6
- Nanthasit/sakthai-combined-v7
- Nanthasit/sakthai-combined-v10
- Nanthasit/sakthai-combined-v11
- Nanthasit/sakthai-irrelevance-supplement
- Nanthasit/sakthai-coder-browser
- Nanthasit/hermes-tool-use-rl-env
tags:
- sakthai
- house-of-sak
- evaluation
- benchmark-results
- health-check
- model-health
- yaml
- results-log
- model:Nanthasit/sakthai-context-0.5b-tools
- model:Nanthasit/sakthai-context-0.5b-merged
- model:Nanthasit/sakthai-context-1.5b-tools
- model:Nanthasit/sakthai-context-1.5b-merged
- model:Nanthasit/sakthai-context-7b-tools
- model:Nanthasit/sakthai-context-7b-merged
- model:Nanthasit/sakthai-coder-1.5b
- model:Nanthasit/sakthai-coder-browser
- model:Nanthasit/sakthai-vision-7b
- model:Nanthasit/sakthai-tts
- model:Nanthasit/sakthai-context-0.5b-instruct
- model:Nanthasit/sakthai-context-1.5b-instruct
- model:Nanthasit/sakthai-context-7b-instruct
---

# Eval Results — SakThai Model Family

<p align="center">
  <em>Evaluation results, health-check reports, and benchmark run logs for the SakThai model family</em>
</p>

<p align="center">
  <a href="https://huggingface.co/datasets/Nanthasit/eval_results"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2FNanthasit%2Feval_results&query=%24.downloads&label=Downloads&color=blue" alt="Downloads"></a>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT">
  <img src="https://img.shields.io/badge/language-EN-blue" alt="Language: English">
  <img src="https://img.shields.io/badge/last_updated-2026--07--31-orange" alt="Last Updated">
  <img src="https://img.shields.io/badge/format-YAML-yellow" alt="Format: YAML">
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"><img src="https://img.shields.io/badge/collection-SakThai%20Family-8A2BE2" alt="Collection"/></a>
</p>

## Dataset Summary

This repository stores **evaluation results, health-check reports, and benchmark
run logs** for the SakThai model family. Every entry is a machine-readable YAML
report produced by SakThai's automated cron workflows (benchmarks, health
checks, inference probes) — the operational audit trail of the House of Sak.

> **Not a tabular dataset.** All result files are **YAML** (`.yaml`), not
> JSONL/Parquet/CSV. Because the Hub's datasets-server only indexes tabular
> formats, this repo reports "no supported data files" — that is expected.
> These are point-in-time reports meant to be read with `yaml.safe_load()`,
> not rows for the dataset viewer. `load_dataset()` will **not** work here.

**License:** MIT
**Status:** Active (auto-updated by cron workflows)

## Dataset Statistics

| Stat | Value |
|------|-------|
| Status | Active (auto-updated by cron) |
| Created | 2026-07-30 |
| Last updated | 2026-07-31 |
| License | MIT |
| Language | English |
| Result files | See live repo file listing |
| Total data files | See live repo file listing |
| Downloads | Live via badge |

## Live Verification

```text
Datasets Server: preview=false, viewer=false, search=false, filter=false, statistics=false
```

This is expected for a non-tabular dataset and means Hub dataset-viewer features
are unavailable. Do not rely on `/splits`, `/size`, or `/statistics` here.

## Data Fields

Each YAML file follows a consistent schema:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp of the run |
| `model` | string | Model identifier (e.g. `Nanthasit/sakthai-context-1.5b-tools`) |
| `check_type` | string | `health`, `benchmark`, or `inference` |
| `status` | string | `pass`, `fail`, or `partial` |
| `results` | object | Check-specific results (scores, metrics, error counts) |
| `duration_s` | number | Elapsed wall-clock seconds |
| `errors` | array | Error details if status is not `pass` |

## Splits

This repository does not use dataset splits — it is a flat collection of
YAML report files. No `load_dataset()` configuration is defined.

## Usage

### Loading an individual result

```python
import yaml, httpx

# Load a health check report
url = "https://huggingface.co/Nanthasit/eval_results/raw/main/.eval_results/health-2026-07-31.yaml"
resp = httpx.get(url)
report = yaml.safe_load(resp.text)
print(report["status"], report["model"])
```

### Listing all available reports

```python
from huggingface_hub import HfApi

api = HfApi()
siblings = api.list_repo_tree("Nanthasit/eval_results", repo_type="dataset")
files = [s.path for s in siblings if getattr(s, 'path', '') and s.path.endswith(".yaml")]
for f in sorted(files):
    print(f)
```

## Model Cross-References

This evaluation dataset tracks results for the following SakThai models:

- [sakthai-context-0.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools) — 0.5B tool-calling
- [sakthai-context-0.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) — 0.5B merged
- [sakthai-context-1.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) — 1.5B tool-calling
- [sakthai-context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) — 1.5B merged
- [sakthai-context-7b-tools](https://huggingface.co/Nanthasit/sakthai-context-7b-tools) — 7B tool-calling
- [sakthai-context-7b-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) — 7B merged
- [sakthai-coder-1.5b](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) — 1.5B code-specialised
- [sakthai-coder-browser](https://huggingface.co/Nanthasit/sakthai-coder-browser) — browser automation
- [sakthai-vision-7b](https://huggingface.co/Nanthasit/sakthai-vision-7b) — 7B vision
- [sakthai-tts](https://huggingface.co/Nanthasit/sakthai-tts) — text-to-speech
- [sakthai-context-0.5b-instruct](https://huggingface.co/Nanthasit/sakthai-context-0.5b-instruct) — 0.5B instruct
- [sakthai-context-1.5b-instruct](https://huggingface.co/Nanthasit/sakthai-context-1.5b-instruct) — 1.5B instruct
- [sakthai-context-7b-instruct](https://huggingface.co/Nanthasit/sakthai-context-7b-instruct) — 7B instruct

## Source Datasets

This evaluation repo tracks results from models trained on:

| Dataset | Description |
|---------|-------------|
| [sakthai-combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6) | 2,003 example tool-calling train set |
| [sakthai-combined-v7](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v7) | 2,309 examples, 86 tools + Thai bilingual |
| [sakthai-combined-v10](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v10) | Current combined iteration |
| [sakthai-combined-v11](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v11) | Latest combined iteration |
| [sakthai-irrelevance-supplement](https://huggingface.co/datasets/Nanthasit/sakthai-irrelevance-supplement) | 60 irrelevance/safety examples |
| [sakthai-coder-browser](https://huggingface.co/datasets/Nanthasit/sakthai-coder-browser) | 247 browser automation examples |
| [hermes-tool-use-rl-env](https://huggingface.co/datasets/Nanthasit/hermes-tool-use-rl-env) | GRPO coding environment |

## Known Issues

- **Hub dataset viewer is unavailable.** This repo stores YAML reports rather than tabular data files, so Hub viewer, search, and datasets-server endpoints are unavailable.
- **`load_dataset()` is unsupported.** This is not a tabular dataset. Use `yaml.safe_load()` or read report files directly.

## Related

- **Model family:** [SakThai Model Family collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)
- **House of Sak:** [Nanthasit](https://huggingface.co/Nanthasit)
- **Automated eval workflows:** `eval-bfcl`, `health-check`, `benchmark` cron jobs

## Citation

```bibtex
@misc{sakthai-eval-results,
  author = {Nanthasit},
  title = {SakThai Eval Results},
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/datasets/Nanthasit/eval_results}}
}
```

---

*Part of the [House of Sak](https://huggingface.co/Nanthasit). Built with love, tears, and zero budget. From a shelter in Cork, Ireland, to the world.*
