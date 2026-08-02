# Benchmark Integrity — Lessons Learned 2026-07-25

## The Trap: Single-Trial Benchmarks

Situation: Ran a single BFCL test on 1.5B GGUF. Model happened to output
`tool_call:` — declared "5/5". Later, multi-trial testing showed
inconsistent results.

Root cause: Single sample with temp=0.1 gave a lucky pass. Three runs at the same
setting showed different behavior.

Fix: Minimum 5 trials per test case. Report pass rate, not pass/fail.

## The Trap: Wrong Test Format

Situation: Model was fine-tuned on OpenAI `tool_calls` JSON format but tested with
`<tool_call>` XML tags in content field. Model failed every test.

Root cause: Training format != test format. The model's chat template expects
structured `tool_calls` in messages, not text-generated XML.

Fix: Always check the training data format. Match it exactly in evaluation.
Or use the model's chat template (via llama.cpp `--chat-template` or Transformers).

## The Trap: Claiming Base Model Limitations as Fine-Tune Failures

Situation: 0.5B model refused weather/tool queries. Assumed our fine-tuning
broke it.

Root cause: Downloaded base Qwen2.5-0.5B and tested — it refused identically.
The behavior is inherited, not introduced.

Fix: Always test the base model alongside the fine-tuned version when diagnosing
regressions. Download the original base model GGUF and compare side-by-side.

## The Trap: No Safety Baseline

Situation: First safety test found model complying with harmful instructions.

Root cause: Never tested for safety. No baseline established.

Fix: Include 3-5 safety probes in every benchmark suite. Document results
even if they're negative.

## Correct Procedure

1. Download base model (same quantization) for comparison
2. Run 5 trials per test case
3. Verify test format matches training format
4. Include safety probes
5. Compare base vs fine-tuned results
6. Document methodology (engine, temp, threads, quantization)
7. If results are preliminary, say "Pending" not a fake number
8. Add Honest Assessment note to model card
