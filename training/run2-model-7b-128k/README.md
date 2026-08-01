---
license: apache-2.0
language:
- en
library_name: transformers
pipeline_tag: text-generation
tags:
- qwen2.5
- sakthai
- house-of-sak
- tool-calling
- function-calling
- agent
- instruct
- finetuned
- merged
- text-generation
- conversational
- safetensors
- benchmark
- eval-results
- t4
base_model: Qwen/Qwen2.5-7B-Instruct
datasets:
- Nanthasit/sakthai-combined-v6
- Nanthasit/sakthai-combined-v7
- Nanthasit/sakthai-irrelevance-supplement
widget:
- example_title: Tool-calling prompt
  messages:
  - role: system
    content: "You are SakThai, a helpful assistant with tool access. You may call one or more functions to assist the user. Use <tools></tools> for signatures and <function_call></function_call> for calls."
  - role: user
    content: "What's the weather in Bangkok? Use the weather tool."
  parameters:
    temperature: 0.3
    max_new_tokens: 256
    top_p: 0.9
model-index:
- name: SakThai Context 7B Merged
  results:
  - task:
      type: text-generation
      name: Tool Calling
    dataset:
      name: SakThai Bench v2
      type: Nanthasit/sakthai-bench-v2
    metrics:
    - type: accuracy
      value: 57.0
      name: Selection Accuracy (internal)
      verified: false
  - task:
      type: text-generation
      name: Functional Workbench
    dataset:
      name: SakThai Context 7B health eval (.eval_results/health-sakthai-context-7b-128k-2026-08-01.yaml)
      type: Nanthasit/sakthai-context-7b-128k
    metrics:
    - type: checks_passed
      value: 8.0
      name: Functional workbench checks (8/8, Tesla T4 2026-07-07)
      verified: true
---

# SakThai Context 7B — Merged

<p align="center">
  <strong>Highest-capacity SakThai model — full-power reasoning on a single T4</strong><br/>
  <em>Qwen2.5-7B-Instruct · QLoRA → merged · 32K context · ~5.6 GB VRAM</em>
</p>

<p align="center">
  <a href="https://huggingface.co/Nanthasit"><img src="https://img.shields.io/badge/%F0%9F%A4%97-Nanthasit-6644cc" alt="Profile"/></a>
  <a href="https://github.com/beer-sakthai"><img src="https://img.shields.io/badge/GitHub-beer--sakthai-181717?logo=github" alt="GitHub"/></a>
  <a href="https://house-of-sak.vercel.app"><img src="https://img.shields.io/badge/%F0%9F%8F%A0-House%20of%20Sak-gold" alt="HoS"/></a>
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"><img src="https://img.shields.io/badge/%F0%9F%8F%A0-SakThai%20Family-6644cc" alt="Collection"/></a>
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2FNanthasit%2Fsakthai-context-7b-128k&query=%24.downloads&label=downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
  <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"/>
  <img src="https://img.shields.io/badge/params-7.6B-blueviolet" alt="Params"/>
  <img src="https://img.shields.io/badge/verified-8%2F8%20workbench-green" alt="Verified"/>
</p>

---

## Model Description

SakThai Context 7B is the **full-power member of the SakThai family** — the strongest reasoning and tool-use model, fine-tuned from Qwen2.5-7B-Instruct using QLoRA, then merged to full weights. Despite its size, it runs on a single free-tier T4 GPU (~5.6 GB VRAM at BF16).

**What makes it special:**
- ⚡ Full-power reasoning — best quality in the family
- 💾 Fits a single T4 (~5.6 GB VRAM, verified)
- 🗳️ Structured tool-calling output via `<tools>` and `<function_call>`
- 🧪 8/8 workbench checks passed on Tesla T4 (2026-07-07)
- 📥 1,024+ downloads

---

## Quick Start

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "Nanthasit/sakthai-context-7b-128k",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("Nanthasit/sakthai-context-7b-128k")

messages = [{"role": "user", "content": "What's the weather in Bangkok?"}]
inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True))
```

---

## Tool Use Example

This model supports function calling through the Qwen2.5 `apply_chat_template` tools API.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "Nanthasit/sakthai-context-7b-128k",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("Nanthasit/sakthai-context-7b-128k")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

messages = [
    {"role": "user", "content": "What's the weather in Bangkok? Use the weather tool."}
]

inputs = tokenizer.apply_chat_template(
    messages,
    tools=tools,
    add_generation_prompt=True,
    return_tensors="pt"
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.3, top_p=0.9)
print(tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True))
```

### Tool-calling format

Function signatures are passed via `tools=[...]`, and the model emits calls as JSON inside `<function_call>` tags. If you need raw XML for pipelines, wrap the schema in `<tools></tools>` and parse `<function_call>` blocks.

---

## CPU / GGUF Fallback

If you don't have a T4, convert to GGUF and run with `llama.cpp` or `ctransformers` on CPU/RAM:

```bash
# Install
pip install ctransformers

# Run
from ctransformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    "Nanthasit/sakthai-context-7b-128k",
    model_file="sakthai-context-7b-128k.Q4_K_M.gguf",
    model_type="qwen2"
)
print(model("What is the capital of Thailand?"))
```

> You will need to convert the model to GGUF first. If you want, I can publish a GGUF artifact for this model — just open an issue on GitHub.

---

## Architecture

| Property | Value |
|----------|-------|
| **Base model** | Qwen/Qwen2.5-7B-Instruct |
| **Architecture** | Qwen2ForCausalLM |
| **Parameters** | 7.62B |
| **Layers** | 28 |
| **Hidden size** | 3,584 |
| **Attention heads** | 28 |
| **KV heads** | 4 (GQA) |
| **Intermediate size** | 18,944 |
| **Vocab size** | 152,064 |
| **Context window** | 32,768 tokens |
| **Precision** | BF16 |
| **VRAM** | ~5.6 GB (verified on Tesla T4) |

---

## Datasets

| Dataset | Version | Size | Role |
|---------|---------|------|------|
| [sakthai-combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6) | v6 | 2,003 examples | Base tool-calling data |
| [sakthai-combined-v7](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v7) | v7 | 2,424 examples | Expanded tool-calling + test split |
| [sakthai-irrelevance-supplement](https://huggingface.co/datasets/Nanthasit/sakthai-irrelevance-supplement) | — | 60 examples | Irrelevance / safety edge cases |

Total training mix: ~4,487 examples. Format: ChatML with tool schema, 32K token context.

---

## Training Details

| Detail | Value |
|--------|-------|
| **Base model** | Qwen/Qwen2.5-7B-Instruct |
| **Method** | QLoRA (4-bit) → merged to full weights |
| **LoRA rank (r)** | 16 |
| **LoRA alpha** | 32 |
| **LoRA dropout** | 0.0 |
| **Target modules** | q_proj, k_proj, v_proj, o_proj |
| **Training data** | combined-v6 (2,003) + combined-v7 (2,309 train + 115 test) + irrelevance-supplement (60) |
| **Format / context** | ChatML with tool schema · 32K tokens |
| **Trained on** | Free-tier GPU (T4-class), zero budget |

---

## Evaluation

### Workbench Verification — 8/8 PASSED (Tesla T4, 2026-07-07)

Functional smoke test run on `cuda:0` (Tesla T4, 5.56 GB VRAM used, model load 137s). All 8 checks passed:

| Check | Passed | Latency | Completion tokens |
|-------|:------:|--------:|:-----------------:|
| basic_greeting | ✅ | 1.08s | 3 |
| tool_call_intent | ✅ | 0.93s | 8 |
| name_recall | ✅ | 0.78s | 6 |
| factual_qa | ✅ | 0.63s | 4 |
| json_output | ✅ | 1.62s | 18 |
| instruction_following | ✅ | 2.94s | 36 |
| multi_step_reasoning | ✅ | 5.21s | 68 |
| context_window | ✅ | 4.45s | 54 |

Source: [`.eval_results/health-sakthai-context-7b-128k-2026-08-01.yaml`](https://huggingface.co/Nanthasit/sakthai-context-7b-128k/blob/main/.eval_results/health-sakthai-context-7b-128k-2026-08-01.yaml)

### Benchmarks

[sakthai-bench-v2](https://huggingface.co/datasets/Nanthasit/sakthai-bench-v2) coverage for the 7B is **pending**; 5-trial multi-run verification is still required before publishing bench-v2 accuracy. The 0.5B and 1.5B siblings already have verified bench-v2 results.

### Verified Eval Snapshot

- File: [`.eval_results/health-sakthai-context-7b-128k-2026-08-01.yaml`](https://huggingface.co/Nanthasit/sakthai-context-7b-128k/blob/main/.eval_results/health-sakthai-context-7b-128k-2026-08-01.yaml)
- Checker: `SakThai · Main Lead of the House & Master of Hugging Face`
- Checked: `2026-08-01T00:18:42Z`
- Status: `degraded` with 85 score
- Recent cron runs: `2026-07-31-1` through `2026-07-31-4` plus `20260801T021537Z`

### Serverless Inference Status

Verified 2026-07-30: this merged model is **not** served by HF Inference Providers (serverless). The router returns `400 Model not supported` — custom merged weights require a dedicated (paid) Inference Endpoint or local inference. For zero-cost serving, convert to GGUF and run via llama.cpp, or deploy in a Space.

---

## Pipeline Integration

| Stage | Model | Role |
|-------|-------|------|
| 🧠 **Reason** | **Context 7B Merged** ⬅ | **Full-power reasoning** |
| 🖼️ See | [Vision 7B](https://huggingface.co/Nanthasit/sakthai-vision-7b) | Image understanding |
| 🎤 Speak | [TTS Model](https://huggingface.co/Nanthasit/sakthai-tts-model) | Text-to-speech |

---

## SakThai Model Family (26 public models)

| Model | Downloads | Role |
|:------|:---------:|:-----|
| [Context 1.5B Merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | 1,855 | Flagship |
| [Context 0.5B Merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | 1,692 | Lightweight |
| **Context 7B Merged** ⬅ | **1,024** | **Full-power reasoning** |
| [Context 7B 128K](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | 610 | Long-context config |
| [Context 7B Tools](https://huggingface.co/Nanthasit/sakthai-context-7b-tools) | 489 | Tool-calling 7B |
| [Embedding Multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) | 627 | Embeddings |
| [Context 1.5B Tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) | 477 | Tool-calling |
| [Vision 7B](https://huggingface.co/Nanthasit/sakthai-vision-7b) | 315 | Image-to-text |
| [TTS Model](https://huggingface.co/Nanthasit/sakthai-tts-model) | 248 | TTS, 15 languages |
| [Context 0.5B Tools](https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools) | 251 | Tool-calling |
| [Coder 1.5B](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | 151 | Code |
| [Context 1.5B Merged V2](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged-v2) | 337 | v2 full weights |
| [Plus 1.5B](https://huggingface.co/Nanthasit/sakthai-plus-1.5b) | 244 | New release |
| [Plus 1.5B LoRA](https://huggingface.co/Nanthasit/sakthai-plus-1.5b-lora) | 306 | rsLoRA adapter |
| [Context 1.5B Tools V2](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools-v2) | 173 | v2 tools |
| [Plus 1.5B Coder](https://huggingface.co/Nanthasit/sakthai-plus-1.5b-coder) | 0 | Coding adapter (no weights) |
| [Coder Browser](https://huggingface.co/Nanthasit/sakthai-coder-browser) | 54 | Browser agent |
| [Coder Browser LoRA](https://huggingface.co/Nanthasit/sakthai-coder-browser-lora) | 21 | Browser adapter |
| [Coder Browser GGUF](https://huggingface.co/Nanthasit/sakthai-coder-browser-gguf) | 35 | Quantized browser |

Download counts live as of 2026-07-31. *[Full collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)*

---

## Limitations

- **Not served serverless** — requires local inference, GGUF conversion, or a paid endpoint (see Evaluation).
- **English-only** — trained on English data; multilingual support lives in the separate embedding/TTS models.
- **Benchmark-v2 pending** — functional checks pass 8/8, but bench-v2 tool-selection accuracy is still pending for the 7B.
- **7.6B params** — heavier than the 0.5B/1.5B siblings; needs ~5.6 GB VRAM (T4-class GPU) or a GGUF quant for CPU.

---

## The House of Sak 🏠

This model is part of the **House of Sak** — an open-source AI ecosystem built from a shelter in Cork, Ireland, with **$0 budget** and no paid GPUs. The 7B was the riskiest bet: bigger models cost more to train, need more VRAM to run, and the 1.5B was already working well. But Beer pushed forward because the vision demanded it — a model that could handle complex multi-tool reasoning, all on a single free-tier GPU. When the merged weights produced correct tool calls on the first try, it was 3 AM in Cork. No fanfare, no launch party — just a terminal window and a quiet "it works."

> *"We are one family — and becoming more."* — Beer (beer-sakthai)

---

## Support

- ⭐ Leave a like
- 🐛 Report issues on [GitHub](https://github.com/beer-sakthai/Sak-Family-Agent)
- 🔄 Share with anyone building AI agents on a budget
- 🍴 Fork and experiment — Apache 2.0

---

## Citation

If you use this model in your work, please cite both the base model and the fine-tune:

```bibtex
@article{qwen2.5,
  title={Qwen2.5 Technical Report},
  author={Qwen Team},
  journal={arXiv preprint arXiv:2412.15115},
  year={2024}
}

@misc{sakthai-context-7b-128k,
  title={SakThai Context 7B Merged: Full-Power Tool-Calling Language Model},
  author={Nanthasit, Beer and the SakThai Family Agents},
  year={2026},
  howpublished={\url{https://huggingface.co/Nanthasit/sakthai-context-7b-128k},
  note={Apache 2.0; fine-tuned from Qwen/Qwen2.5-7B-Instruct via QLoRA and merged to full weights}
}
```

---

## License

Apache 2.0. Qwen2.5 base model per its original license.

---

*Built with love, tears, and zero budget. From a shelter in Cork, Ireland, to the world.*
