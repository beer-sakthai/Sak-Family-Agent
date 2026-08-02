---
license: apache-2.0
language:
- en
library_name: transformers
pipeline_tag: text-generation
tags:
- qwen2.5
- qwen2.5-coder
- sakthai
- house-of-sak
- browser-automation
- web-agent
- tool-calling
- function-calling
- tool-use
- agent
- code-generation
- finetuned
- finetune
- sft
- text-generation
- merged
- conversational
- safetensors
- transformers
base_model: Qwen/Qwen2.5-Coder-1.5B-Instruct
datasets:
- Nanthasit/sakthai-combined-v8
- Nanthasit/sakthai-combined-v11
- Nanthasit/sakthai-irrelevance-supplement
- Nanthasit/cycle-bench
inference:
  parameters:
    temperature: 0.3
    max_new_tokens: 256
    top_p: 0.9
  widget:
    - text: "Search for the latest AI news and summarize the top story."
      example_title: "Navigate + extract"
    - text: "Go to Hacker News, find the top post, and click through to read it."
      example_title: "Multi-step navigation"
    - text: "Open google.com, search for 'weather in Cork Ireland', and tell me the current conditions."
      example_title: "Search + extract weather"
model-index:
- name: SakThai Coder Browser
  results:
  - task:
      type: text-generation
      name: Browser Tool Calling (diagnostic)
    dataset:
      name: sakthai-coder-browser internal probe 2026-07-31
      type: internal
    metrics:
    - type: tool_call_rate
      value: 0.0
      verified: true
      notes: Multi-trial llama.cpp GGUF Q4_K_M CPU probe, 2026-07-31 05:21 UTC. 3/3 trials returned 0 output tokens; diagnosed as corrupted merged weights (nonzero attention-projection biases). Not deployable until clean re-merge and re-verification.
    - type: valid_json_rate
      value: 0.0
      verified: true
      notes: No <tool_call> JSON emitted in any trial at temp <= 0.7.
---

# SakThai Coder Browser

<p align="center">
  <strong>Browser automation agent — Qwen2.5-Coder-1.5B-Instruct fine-tuned for web interaction</strong><br/>
  <em>Part of the <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02>SakThai Model Family</a></em>
</p>

<p align="center">
  <a href="https://huggingface.co/Nanthasit><img src="https://img.shields.io/badge/%F0%9F%A4%97-Nanthasit-6644cc" alt="Profile"/></a>
  <a href="https://github.com/beer-sakthai"><img src="https://img.shields.io/badge/GitHub-beer--sakthai-181717?logo=github" alt="GitHub"/></a>
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"><img src="https://img.shields.io/badge/%F0%9F%8F%A0-SakThai%20Family-6644cc" alt="Collection"/></a>
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2FNanthasit%2Fsakthai-coder-browser&query=%24.downloads&label=downloads&color=blue" alt="Downloads"/>
  <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"/>
  <img src="https://img.shields.io/badge/task-browser%20automation-ff6b6b" alt="Task"/>
  <img src="https://img.shields.io/badge/base-Qwen2.5--Coder--1.5B--Instruct-blueviolet" alt="Base"/>
</p>

> [!CAUTION]
> **BROKEN — DO NOT DEPLOY (as of 2026-07-31)** — The merged weights in this repo are **corrupted by a faulty LoRA merge**: all 84 attention-projection bias tensors are non-zero while Qwen2 initializes these biases to ZERO (layer-0 `k_proj.bias` absmean 27.7 / max 354). Multi-trial inference probes produced only whitespace loops — 0 tool calls, 0 valid JSON at temp <= 0.7. Full evidence: [`.eval_results/benchmark-20260731_052122.yaml`](https://huggingface.co/Nanthasit/sakthai-coder-browser/blob/main/.eval_results/benchmark-20260731_052122.yaml). The fault is in the **weights, not the GGUF conversion or the prompt format**. The [GGUF variant](https://huggingface.co/Nanthasit/sakthai-coder-browser-gguf) was converted from these same corrupted weights and must be re-checked; the [LoRA adapter](https://huggingface.co/Nanthasit/sakthai-coder-browser-lora) needs a clean re-merge. Treat this repo as **not deployable** until re-merged and re-verified.

---

## Model Description

SakThai Coder Browser transforms Qwen2.5-Coder-1.5B-Instruct into a **browser automation assistant** that outputs structured `<tool_call>` XML/JSON for web interaction. It can navigate pages, click elements, type text, and extract content — designed to work with browser automation frameworks.

**Available actions via `<tool_call>` XML:**

| Tool | Example |
|------|---------|
| `browser_navigate(url)` | `<tool_call>{"name": "browser_navigate", "arguments": {"url": "https://example.com"}}</tool_call>` |
| `browser_click(element)` | `<tool_call>{"name": "browser_click", "arguments": {"element": "#search-button"}}</tool_call>` |
| `browser_type(element, text)` | `<tool_call>{"name": "browser_type", "arguments": {"element": "#search-input", "text": "AI news"}}</tool_call>` |
| `browser_extract()` | `<tool_call>{"name": "browser_extract", "arguments": {}}</tool_call>` |

---

## Tool-Calling Format

The repo ships its own `chat_template.jinja` (Qwen2.5 tool-calling style). When tools are provided, the system prompt embeds function signatures inside `<tools></tools>` XML tags and the model replies with a `<tool_call>` JSON block:

```text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"type": "function", "function": {"name": "browser_navigate", "parameters": {...}}}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call><|im_end|>
<|im_start|>user
Search for the latest AI news.<|im_end|>
<|im_start|>assistant
<tool_call>
{"name": "browser_navigate", "arguments": {"url": "https://news.google.com"}}
</tool_call><|im_end|>
```

Tool results are wrapped in `<tool_response></tool_response>` blocks. Multi-turn loops are supported by the chat template.

---

## Quick Start

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "Nanthasit/sakthai-coder-browser",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("Nanthasit/sakthai-coder-browser")

messages = [
    {"role": "system", "content": "You are SakThai Browser Agent. Use <tool_call> blocks to control the browser."},
    {"role": "user", "content": "Search for the latest AI news and summarize the top story."},
]
inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.3)
print(tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True))
```

Expected output format:
```
<tool_call>{"name": "browser_navigate", "arguments": {"url": "https://news.google.com"}}</tool_call>
```

> Use the chat template. This model was trained with the Qwen2.5 tool-calling format — pass tools through `apply_chat_template` (or the repo's `chat_template.jinja`) rather than hand-rolling prompts.

### GGUF / llama.cpp variant

Prefer CPU inference or Ollama? Use the [GGUF build](https://huggingface.co/Nanthasit/sakthai-coder-browser-gguf) (F16, ~7.1 GB) with llama.cpp:

```bash
huggingface-cli download Nanthasit/sakthai-coder-browser-gguf \
  sakthai-coder-browser-f16.gguf --local-dir ./
./llama-cli -m sakthai-coder-browser-f16.gguf \
  -p "<|im_start|>system\nYou are a browser automation assistant.<|im_end|>\n<|im_start|>user\nGo to google.com and search for the latest AI news<|im_end|>\n<|im_start|>assistant\n" \
  -n 512 -t 8 --temp 0.3
```

---

## Architecture

Verified from this repo's `config.json` (transformers 5.14.1):

| Property | Value |
|----------|-------|
| **Base Model** | [Qwen/Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) |
| **Architecture** | Qwen2ForCausalLM (decoder-only transformer) |
| **Parameters** | 1,543,714,304 (1.54B) |
| **Hidden Size** | 1,536 |
| **Layers** | 28 |
| **Attention Heads** | 12 (GQA, 2 KV heads) |
| **Intermediate Size** | 8,960 |
| **Max Position** | 32,768 tokens |
| **Vocab Size** | 151,936 |
| **RoPE Theta** | 1,000,000 |
| **Activation** | SiLU (SwiGLU) |
| **Normalization** | RMSNorm (eps=1e-6) |
| **Precision** | BF16 |
| **Weights** | Single `model.safetensors` — 3,087,467,144 B (2.88 GB, API-verified) |
| **Tied embeddings** | yes (`tie_word_embeddings: true`) |

---

## Training Details

| Detail | Value |
|--------|-------|
| **Base model** | Qwen/Qwen2.5-Coder-1.5B-Instruct |
| **Method** | SFT via LoRA (r=16, alpha=32, dropout 0.05, rsLoRA) on all 7 linear projections, then merged to full weights |
| **Context length** | 32,768 tokens |
| **Precision** | BF16 |
| **Hardware** | Free T4 GPU (Kaggle / Colab) |
| **Budget** | $0 |

Training configuration mirrors the sibling [sakthai-coder-browser-lora](https://huggingface.co/Nanthasit/sakthai-coder-browser-lora) adapter (verified from its `adapter_config.json`: `peft` 0.20.0, `use_rslora: true`, `lora_dropout: 0.05`, target modules q/k/v/o/gate/up/down_proj).

---

## Evaluation & Status

**Honest status: inference benchmarks were attempted and did not produce output.** The repo's own `.eval_results/benchmark-20260731_052122.yaml` records a llama.cpp GGUF Q4_K_M run (3 trials, CPU, 2 threads, 2026-07-31 05:21 UTC, tool-calling browser prompt, 244 input tokens) in which **all 3 trials returned 0 output tokens** — no tool call, no valid JSON, no correct answer:

| Trial | Seed | Output tokens | Tool call | Valid JSON | Correct answer |
|:-----:|:----:|:-------------:|:---------:|:----------:|:--------------:|
| 1 | 7 | 0 | No | No | No |
| 2 | 42 | 0 | No | No | No |
| 3 | 1337 | 0 | No | No | No |

**Verdict — MODEL_BROKEN (bias corruption):** the repo's own eval YAML (updated 2026-07-31 05:50 UTC) includes **weight inspection** of `model.safetensors` that proves the fault is in the weights, not the harness:

- Qwen2 initializes attention-projection biases to **zero**; this merge left **all 84 bias tensors non-zero** (absmean > 0.01), e.g. layer-0 `k_proj.bias` absmean **27.7** / max **354**, layer-0 `q_proj.bias` absmean 1.17
- Degenerate generation at temp <= 0.7 on all 3 seeds — **whitespace loops** (150 newline tokens, 0 tool calls, 0 valid JSON); only at temp 1.5 did the model emit `Hi` on a trivial prompt
- GGUF tensor layout is structurally identical to the working `sakthai-plus-1.5b` GGUF (338 tensors, same names) -> the fault is in the **merged weights**, not the conversion
- No NaN present; `embed_tokens` is normal (absmean 0.0136) — corruption is isolated to the attention biases

**Recommended fix:** re-merge the LoRA adapter into `Qwen2.5-Coder-1.5B-Instruct` with correct bias handling (do not write adapter-state biases into the base where Qwen2 expects zeros), re-run the multi-trial probe, and update this card. Until then, this repo is **not deployable**.

**Hosted inference:** not available — router probe returned 404 (`Not Found`) and the legacy api-inference host does not resolve (per the same eval YAML). No `model-index` is published because there are no verified scores yet; publishing one would be misleading.

Ecosystem status from `.eval_results/cron-eval-sakthai-coder-browser-2026-07-30-1.yaml`: card quality **85/100**, repo hygiene **95/100**, health **23/100** (rank 20/20 — new repo, zero downloads at eval time; popularity/momentum/benchmarks components are 0 because the repo had no traction yet).

---

## Repo Contents

| File | Size | Purpose |
|------|-----:|---------|
| `model.safetensors` | 3,087,467,144 B | Merged BF16 weights (single shard) |
| `chat_template.jinja` | 2,507 B | Qwen2.5 tool-calling chat template |
| `config.json` | 1,373 B | Qwen2 config (32K ctx, GQA 2 KV heads) |
| `tokenizer.json` | 11,421,892 B | Tokenizer |
| `.eval_results/` | — | benchmark + cron-eval YAMLs |

---

## Sibling Models

| Variant | Repository |
|:--------|:-----------|
| **LoRA Adapter** (unmerged) | [sakthai-coder-browser-lora](https://huggingface.co/Nanthasit/sakthai-coder-browser-lora) |
| **GGUF** (llama.cpp / Ollama) | [sakthai-coder-browser-gguf](https://huggingface.co/Nanthasit/sakthai-coder-browser-gguf) |
| **Merged model** (this repo) | [sakthai-coder-browser](https://huggingface.co/Nanthasit/sakthai-coder-browser) |

---

## SakThai Model Family

One of **25 public model repos** in the [SakThai Model Family collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02) (plus companion repos [sakthai-bench-v3](https://huggingface.co/Nanthasit/sakthai-bench-v3), [sakthai-pipeline](https://huggingface.co/Nanthasit/sakthai-pipeline), [eval_results](https://huggingface.co/Nanthasit/eval_results), [sft-out](https://huggingface.co/Nanthasit/sft-out), and adapter pilots). Live download counts as of **2026-08-01**; this repo has 54 downloads.

| Model | Downloads |
|:------|----------:|
| [sakthai-context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | 1,855 |
| [sakthai-context-0.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | 1,692 |
| [sakthai-context-7b-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) | 1,024 |
| [sakthai-embedding-multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) | 627 |
| [sakthai-context-7b-128k](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | 610 |
| [sakthai-context-7b-tools](https://huggingface.co/Nanthasit/sakthai-context-7b-tools) | 489 |
| [sakthai-context-1.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) | 477 |
| [sakthai-context-1.5b-merged-v2](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged-v2) | 337 |
| [sakthai-vision-7b](https://huggingface.co/Nanthasit/sakthai-vision-7b) | 315 |
| [sakthai-plus-1.5b-lora](https://huggingface.co/Nanthasit/sakthai-plus-1.5b-lora) | 306 |
| [sakthai-context-0.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools) | 251 |
| [sakthai-tts-model](https://huggingface.co/Nanthasit/sakthai-tts-model) | 248 |
| [sakthai-plus-1.5b](https://huggingface.co/Nanthasit/sakthai-plus-1.5b) | 244 |
| [sakthai-context-1.5b-tools-v2](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools-v2) | 173 |
| [sakthai-coder-1.5b](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | 151 |
| **Coder Browser (this model)** ⬅ | 54 |
| [sakthai-coder-browser-gguf](https://huggingface.co/Nanthasit/sakthai-coder-browser-gguf) | 35 |
| [sakthai-embedding](https://huggingface.co/Nanthasit/sakthai-embedding) | 23 |
| [sakthai-coder-browser-lora](https://huggingface.co/Nanthasit/sakthai-coder-browser-lora) | 21 |
| [sakthai-plus-1.5b-coder](https://huggingface.co/Nanthasit/sakthai-plus-1.5b-coder) | 0 |
| [eval_results](https://huggingface.co/Nanthasit/eval_results) | 0 |
| [sakthai-bench-v3](https://huggingface.co/Nanthasit/sakthai-bench-v3) | 0 |
| [sakthai-pipeline](https://huggingface.co/Nanthasit/sakthai-pipeline) | 0 |
| [sakthai-context-0.5b-tools-sft](https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools-sft) | 0 |
| [sft-out](https://huggingface.co/Nanthasit/sft-out) | 0 |
| [sakthai-context-0.5b-tools-sft-v2](https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools-sft-v2) | 0 |

---

## Reproduce Evaluation

If you want to verify the broken-state diagnosis locally, run the same llama.cpp probe used for this card:

```bash
# Convert the current merged weights to GGUF Q4_K_M
python -m scripts.convert_hf_to_gguf --outfile sakthai-coder-browser-q4_k_m.gguf --quant-type Q4_K_M ./sakthai-coder-browser

# 3-trial probe, 2 threads, CPU only
for seed in 7 42 1337; do
  ./llama-cli -m sakthai-coder-browser-q4_k_m.gguf \
    -p "$(cat prompts/browser_tool_call.txt)" \
    -n 256 --temp 0.3 -t 2 --seed $seed
done
```

All 3 trials should return 0 output tokens if the weight corruption is still present.
If they produce normal `<tool_call>` JSON blocks, the repo has been repaired.

---

## Reproduce Training / Merge

The merged weights were produced by applying the LoRA adapter onto `Qwen/Qwen2.5-Coder-1.5B-Instruct`. To reproduce or repair:

```bash
git clone https://huggingface.co/Nanthasit/sakthai-coder-browser-lora adapter
python -m peft.merge_and_unload \
  --base_model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --adapter adapter \
  --output repaired-merged \
  --safe
```

Important: zero-out attention-projection biases after merge if the base initializes them to zero:

```python
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("repaired-merged", trust_remote_code=True)
for name, param in model.named_parameters():
    if "bias" in name and "attn" in name and "k_proj" in name:
        param.data.zero_()
```

Run the eval probe again before publishing.

---

## Limitations

- **BROKEN weights** — all 84 attention bias tensors are corrupted by a faulty LoRA merge (see [Evaluation & Status](#evaluation--status)); do not deploy until re-merged and re-verified
- **No verified benchmark scores yet** — `model-index` currently carries 0% `tool_call_rate` and 0% `valid_json_rate` from the 2026-07-31 diagnostic probe; these are failure signals from corrupted weights, not representative task scores
- **Text-only** — cannot see images or screenshots (use [sakthai-vision-7b](https://huggingface.co/Nanthasit/sakthai-vision-7b) for vision tasks)
- **English-only web actions** — training data is primarily English web interactions; non-English pages may yield lower-quality actions
- **Context-limited** — best results with page content <= 4K tokens per interaction; long pages can exceed the model's effective working memory
- **Not servable on HF serverless inference** — no provider supports this custom fine-tune (router 404 verified); run locally via Transformers or the GGUF build once weights are repaired

---

## Citation

If you use SakThai Coder Browser in your work, please cite the base model and the fine-tuning approach:

```bibtex
@misc{qwen25coder,
    title = {Qwen2.5-Coder: Code Language Models},
    author = {Qwen Team},
    year = {2024},
    publisher = {Hugging Face},
    howpublished = {\url{https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct}}
}

@misc{sakthai-model-family,
    title = {SakThai Model Family: Zero-Budget Fine-Tuned Language Models},
    author = {{Beer Nanthasit}},
    year = {2026},
    publisher = {Hugging Face},
    howpublished = {\url{https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02}}
}
```

---

*Part of the [SakThai Model Family](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02). Built with love, tears, and zero budget. From a shelter in Cork, Ireland, to the world.*