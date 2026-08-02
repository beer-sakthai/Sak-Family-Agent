# Eval Results Workflow

Add Hugging Face Community Evals to model repos after publishing.

## Why

Every model should carry benchmark scores visible on its HF page. Results auto-appear on the model card and feed into benchmark leaderboards. Zero cost.

## Format

Create `.eval_results/*.yaml` files in the model repo:

```yaml
- dataset:
    id: Nexusflow/bfcl_v3    # Benchmark dataset ID (must have "Benchmark" tag)
    task_id: simple           # Task as defined in the dataset's eval.yaml
  value: 1.0                 # Score (0.0-1.0 for accuracy)
  date: "2026-07-29"         # ISO-8601
  source:
    url: https://github.com/your-org/repo
    name: "Your Eval Name"
  notes: "5/5 verified"
```

## Required fields

Only `dataset.id`, `task_id`, and `value` are required.

## Badges

- verified: verifyToken present (ran in HF Jobs with inspect-ai)
- community: Submitted via open PR (not merged)
- source: Links to external source

## Upload via Python

```python
from huggingface_hub import HfApi
api = HfApi(token=HF_TOKEN)

content = """\
- dataset:
    id: Nexusflow/bfcl_v3
    task_id: simple
  value: 1.0
  date: "2026-07-29"
  source:
    url: https://github.com/beer-sakthai/Sak-Family-Agent
    name: SakThai Internal
"""

api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo=".eval_results/bfcl-simple.yaml",
    repo_id="Nanthasit/your-model",
    repo_type="model",
)
```

## Best practices

- One YAML file per benchmark category
- Include source.url for reproducibility
- Date when evaluation ran, not upload time
- Scores 0.0-1.0 for accuracy
- Keep notes brief include trial count and prompt variant

## Applied 2026-07-29

Uploaded 25 eval files across all 12 SakThai models:
- 4 tool-calling: 4-5 BFCL files each (simple, multiple, parallel, irrelevance, multi-turn)
- 3 merged: text quality (IFEval)
- Coder 1.5B: HumanEval 5/6
- Vision 7B: ChartQA
- TTS: MOS 3.8
- Embedding: MTEB 0.62
