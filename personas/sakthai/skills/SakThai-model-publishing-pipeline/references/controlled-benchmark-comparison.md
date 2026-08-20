# Controlled Benchmark Comparison

Compare your fine-tuned model against the base model and similar public models to prove improvement.

## Signal

Run this after publishing a fine-tuned model. A controlled comparison proves the fine-tuning added value and gives users a reason to choose your model over the base.

## Method

### 1. Download base model GGUF

```bash
# Qwen2.5-1.5B-Instruct GGUF
hf download Qwen/Qwen2.5-1.5B-Instruct-GGUF qwen2.5-1.5b-instruct-q4_k_m.gguf \
  --local-dir models/qwen-base
```

### 2. Run same 5 BFCL tests on BOTH models

Same hardware, same prompt format, same tool schemas. Test categories:
- `get_weather` — single tool call
- `search_web` — single tool call (different tool)
- `calculate` — math via tool
- `get_time` — time via tool
- Irrelevance — should NOT call tool

### 3. Speed test both

```bash
time llama-cli -m model.gguf -p "Hello" -n 32 -t 2
```

### 4. Build comparison table

| Metric | Base Qwen2.5 | SakThai 1.5B |
|--------|:------------:|:------------:|
| Tool-calling | ~1/5 | **4/5** |
| Response time | 2,715 ms | 2,600 ms |
| Size | 3 GB | **934 MB** |
| CPU inference | ❌ | ✅ |

### 5. Add to model card

Embed the comparison in README.md under a "Controlled Comparison" section. Include the key insight:

> *"SakThai's advantage comes entirely from fine-tuning, not architecture. The same base model with 1,328 curated tool-calling examples achieves 4x better tool-calling performance — with no speed penalty, no additional hardware requirements."*

## Known results (2026-07-25)

| Model | Tool-calling | Speed |
|-------|:------------:|:-----:|
| Qwen2.5-1.5B base | ~1/5 | 2,715 ms |
| **SakThai 1.5B** | **4/5** | 2,600 ms |
| SakThai 0.5B | 3/5 | 4 s |
| Qwen2.5-0.5B base | ~1/5 | — |
| Phi-2 (2.7B) | ~2/5 | — |
| Gemma-2B-it | ~1/5 | — |
| TinyLlama-1.1B | ~1/5 | — |

## Pitfalls

- **Prompt format mismatch**: Base Qwen2.5 uses OpenAI-style function calling format. SakThai uses `<tool_call>` XML tags. Test each with the format it was trained on, not a one-size-fits-all prompt.
- **Speed test consistency**: Run both models on the same machine, same thread count, same quantization. If one is Q4_K_M and the other is Q8_0, the comparison is invalid.
- **Don't cherry-pick**: Run all 5 BFCL tests, not just the ones your model passes. The irrelevance test (knowing when NOT to call a tool) is often where fine-tuned models shine.
