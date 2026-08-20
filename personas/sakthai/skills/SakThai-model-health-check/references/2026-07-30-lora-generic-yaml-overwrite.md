# Generic `health-check.yaml` overwritten by sibling subagent mid-session

**Date:** 2026-07-30
**Model:** Nanthasit/sakthai-plus-1.5b-lora (LoRA adapter health check)
**Symptom:** Local `.eval_results/health-check.yaml` contained wrong model's data after upload succeeded.

## Root Cause

Multiple cron subagents operate on **different models** but write to the same local path: `.eval_results/health-check.yaml`. This is a shared workspace file, not a model-specific one. A sibling subagent for a different model overwrote the generic file seconds after the first agent wrote it.

## Detection

Verification caught: `FAIL generic model_id=None` — the local `health-check.yaml` had a `target_model` section for `vision-7b` instead of the expected slim-schema for the LoRA adapter. The remote HF repo was correct (upload had already completed).

## Recovery

```bash
cp .eval_results/health-check-{slug}-{date}-{N}.yaml .eval_results/health-check.yaml
# Re-upload; huggingface_hub returns same commit if content already matches
```

## Lessons

1. **The generic `health-check.yaml` is a shared resource** — never assume it stays stable after a write. Multi-agent crons may overwrite it.
2. **Always verify model identity** in the generic file before treating it as your own output. The remote repo upload is the authoritative check.
3. **Consider dropping the generic YAML write** for cron health checks — the timestamped model-specific YAML is the definitive artifact. The generic `health-check.yaml` provides no unique value and creates a shared-state footgun.
4. **`upload_file` with identical content returns prior commit hash** (`No files have been modified since last commit. Skipping to prevent empty commit.`). Correct behavior — huggingface_hub skips no-op commits. Not an error.
