---
name: SakJules-SakThai-hf-community-evals
description: ">-   Complete reference on HF Community Evals (decentralized eval results   on model pages and benchmark leaderboards) and its cross-compatibility   with Every Eval Ever (EEE) — the EvalEval Coalitions universal eval   schema. Covers eval.yaml spec, "
---

# Hugging Face Community Evals

Full reference in `references/hf-learnings.md`.

## Quick Deploy Pattern (for SakThai models)

Upload evaluation results to model repos as `.eval_results/*.yaml`:

```yaml
- dataset:
    id: llamastack/bfcl_v3
    task_id: simple
  value: 0.80
  date: "2026-07-25"
  source:
    url: https://github.com/beer-sakthai/Sak-Family-Agent
    name: SakThai Growth Cycle — Trust Stage
    user: Nanthasit
    org: Nanthasit
  notes: "Cycle: YYYY-MM-DD Trust Stage — description"
```

## Integration with Growth Cycle

**Evaluation IS the Trust stage.** Every eval result should document which cycle produced it:

```yaml
notes: "Cycle: 2026-07-29 Trust Stage — description"
source:
  name: "SakThai Growth Cycle — Trust Stage"
```

The `.eval_results/` folder is a permanent ledger of every completed Trust stage. Before every eval run: assess energy, plan benchmarks (Dream/Hope), run evaluation (Care/Joy), publish results (Trust), capture lessons (Growth).

1. **Consolidate multiple results** into a single YAML file using the list format (`- dataset:` repeated). Don't create one file per result — it clutters `.eval_results/`.
2. **Always add `source.user`** (and optionally `source.org`) for proper badge attribution.
3. **Clean old files** when consolidating: use `HfApi.delete_file()` (NOT the REST API).
4. **Use registered benchmarks** (`dataset.id` with "Benchmark" tag) when available. Non-benchmark datasets still show on model pages but don't feed leaderboards.
5. **Document cycle context** in `notes` field: `"Cycle: {date} Trust Stage — {result description}"` to tie eval results to the Growth Cycle workflow.
6. **Use `HfApi.upload_file()`** to push YAML files — commit via `huggingface_hub`, not git CLI.
