# Model Evaluation Honesty — Lessons from 2026-07-25

## What went wrong

Benchmarks claimed 1.5B scored 5/5 and 0.5B scored 4/5 on BFCL-style tool-calling. In reality, the model's tool-calling was inconsistent and the scores were misleading because:

1. **Format mismatch**: Training data uses OpenAl `tool_calls` JSON format. The benchmark tested for `<tool_call>` XML tags. These are different output representations — one is structured JSON in a `tool_calls` field, the other is text in the content field. The model was trained to produce one format but tested for another.

2. **Single-trial fallacy**: The benchmark ran each test once. A model scoring 5/5 on one run scored 0/5 on the next. Multi-trial (5+ runs) with pass-rate percentage is the minimum reliable methodology.

3. **Inference engine confusion**: The model's capability and the inference engine's capability are different questions. llama.cpp CLI generates free text — it cannot produce structured `tool_calls` JSON. Testing tool-calling with llama.cpp CLI tests whether the model outputs text that looks like a tool call, not whether it can produce proper function-calling output.

## Rules for future benchmarks

1. **Check training format first** — before designing any benchmark, inspect the training data's assistant message format (OpenAl tool_calls JSON vs XML tags vs plain text)

2. **Match format to training** — the benchmark must test for the SAME output format the model was trained to produce

3. **Multi-trial minimum** — 5 trials per test case, report pass rate as percentage (e.g., 3/5 = 60%)

4. **Document engine limitations** — always note which inference engine was used and what format was tested

5. **Cross-validate with engine changes** — if possible, test with HF Transformers pipeline (which applies chat templates correctly) as the reference

6. **Be conservative in claims** — when in doubt, report the lower score. Honest 2/5 is better than misleading 5/5

## Quick methodology checks

Before publishing any benchmark score, ask:
- "Did I verify the training data format matches my test format?"
- "Did I run at least 5 trials per test?"
- "Does my inference engine support the output format I'm testing for?"
- "Would I bet my reputation on this score being reproducible?"
