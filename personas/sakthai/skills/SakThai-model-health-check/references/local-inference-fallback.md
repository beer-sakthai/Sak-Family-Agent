# Local Inference Fallback — Transformers CPU Benchmarking

When a model has zero provider coverage on HF Inference (router returns `model_not_supported`), fall back to local inference with `AutoModelForCausalLM` on CPU. Verified 2026-07-31 on `Nanthasit/sakthai-context-0.5b-merged`.

## When To Use

- Router returns HTTP 400 `model_not_supported`
- `HfApi.model_info(model, expand=['inferenceProviderMapping'])` returns empty/None
- Available RAM ≥ 2× model fp16 weight size (loading buffers eat ~1×)
- 0.5B models (~1GB fp16) reliably work in ~5GB available RAM; 1.5B is tight

## Implementation Pattern

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load
tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    token=hf_token,
    torch_dtype="auto",
    low_cpu_mem_usage=True,
)

# Generate (tool-calling prompt)
inputs = tokenizer(tool_prompt, return_tensors="pt")
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=128,
        do_sample=True,
        temperature=0.7,
        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
    )

response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
```

## Tool-Calling Prompt Template

The `sakthai-context` models were trained on `<tools>` XML format:

```
<tools>
[
  {"name": "calculator", "description": "...", "parameters": {...}},
  {"name": "get_weather", "description": "...", "parameters": {...}}
]
</tools>

What is 3 * 12 + 5? Use the calculator tool.

<tool_call>
```

The model generates structured JSON tool calls as continuation.

## Metrics to Record

| Metric | Source |
|--------|--------|
| Load time | `time.time()` around `from_pretrained` |
| Generation time | `time.time()` around `model.generate()` |
| Input tokens | `inputs.input_ids.shape[1]` |
| Output tokens | `outputs[0][input_len:].shape[0]` |
| Tool call present | String match for `<tool_call>` or function name in response |
| Response preview | First 150 chars |

## Report Upload

Upload results as YAML to the model repo:

```python
api.upload_file(
    path_or_fileobj=yaml.dump(report, sort_keys=False).encode(),
    path_in_repo=f".eval_results/benchmark-{ts}.yaml",
    repo_id=model_id,
    repo_type="model",
)
```

## Tracker JSON

Maintain a local tracker at `~/profiles/sakthai/cron/hf-benchmarked.json` to rotate through untested models across cron runs. Schema:

```json
{
  "version": 2,
  "last_run": "20260731_012451",
  "runs": [
    {"timestamp": "...", "model": "...", "status": 200, "total_time_s": 8.21, ...}
  ],
  "summary": {"total_runs": 5, ...}
}
```

## Reusable Script

See `scripts/hf-benchmark-runner.py` under this skill for a self-contained implementation that:
1. Reads the tracker
2. Loads the model via transformers on CPU
3. Runs tool-calling inference
4. Uploads results to the model repo
5. Updates the tracker
