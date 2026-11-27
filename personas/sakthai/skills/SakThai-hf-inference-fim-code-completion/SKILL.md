---
name: SakThai-hf-inference-fim-code-completion
version: 1.0.0
description: Deep reference for Fill-in-the-Middle (FIM) code completion through Hugging
  Face InferenceClient — model-specific token formats, text_generation vs chat_completion
  approaches, TGI/vLLM/SGLang endpoints, parameter tuning, and verification patterns.
category: mlops
tags:
- code
- completion
- fim
- hf
- huggingface
- inference
---

# HF InferenceClient: Fill-in-the-Middle (FIM) Code Completion

> **Fill-in-the-Middle (FIM)** is a code infilling pattern where a model generates code between a **prefix** (code before cursor) and a **suffix** (code after cursor). Also called code infilling, it powers IDE autocomplete features. This skill covers how to use FIM through Hugging Face's InferenceClient, TGI, vLLM, and SGLang.

## 1. How FIM Works

Standard FIM prompt structure:

```
[FIM_PREFIX_TOKEN] + prefix_text + [FIM_SUFFIX_TOKEN] + suffix_text + [FIM_MIDDLE_TOKEN]
```

The model generates the code that logically fills the gap between prefix and suffix. The suffix provides **future context** (code that follows the cursor), which is critical for high-quality completions — without it the model is just doing standard text continuation.

### Why suffix matters

- Prefix only = text generation (no awareness of what comes next)
- Prefix + suffix = true infilling (model sees the closing bracket, function call site, or closing tag)

## 2. FIM Token Formats by Model Family

| Model Family | Prefix Token | Suffix Token | Middle Token | Notes |
|---|---|---|---|---|
| **StarCoder/StarCoder2** | `<fim_prefix>` | `<fim_suffix>` | `<fim_middle>` | Explicit, consistent across versions |
| **CodeLlama** | `<CODE_PREFIX>` | `<CODE_SUFFIX>` | `<FILL_ME>` | Case-sensitive, angle brackets |
| **DeepSeek Coder** | `tokenizer.fim_prefix_id` | `tokenizer.fim_suffix_id` | `tokenizer.fim_middle_id` | Token IDs vary by model, use tokenizer |
| **Qwen2.5-Coder** | `<|fim_prefix|>` | `<|fim_suffix|>` | `<|fim_middle|>` | Pipe-delimited |
| **Granite Code** | `<fim-prefix>` | `<fim-suffix>` | `<fim-middle>` | Hyphen-separated |
| **Stable Code** | `<fim-prefix>` | `<fim-suffix>` | `<fim-mask>` | Same as Granite? |

**Always verify FIM tokens from the model card or tokenizer config.** Token names are not standardized across model families.

### Extracting FIM token IDs programmatically

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("bigcode/starcoder2-3b")
# For StarCoder2 the special tokens are in the tokenizer config
for attr in ["fim_prefix_id", "fim_suffix_id", "fim_middle_id"]:
    tid = getattr(tokenizer, attr, None)
    if tid is not None:
        token = tokenizer.decode([tid])
        print(f"{attr}: {tid} → {token!r}")
```

For models that expose these as added_tokens:

```python
# Check added_tokens for FIM-related entries
for token, tid in tokenizer.added_tokens_decoder.items():
    if "fim" in token.lower() or "fill" in token.lower():
        print(f"  Token: {token!r} → ID: {tid}")
```

## 3. Using FIM with HF InferenceClient

### 3A. `text_generation()` — Raw Prompt Format (Best for FIM)

The `text_generation()` method sends a raw text prompt, making it the most direct way to do FIM:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(model="bigcode/starcoder2-3b")

prompt = (
    "<fim_prefix>"
    "def fibonacci(n):\n"
    "    \"\"\"Return the nth Fibonacci number.\"\"\"\n"
    "    if n <= 1:\n"
    "        return n\n"
    "<fim_suffix>"
    "\n    print(fibonacci(10))  # should output 55\n"
    "\ndef main():"
    "<fim_middle>"
)

response = client.text_generation(
    prompt,
    max_new_tokens=150,
    temperature=0.2,
    stop=["\ndef ", "\nclass ", "\n#", "<|endoftext|>"],
)
print(response)
# Expected: fibonacci implementation using recursion/memoization
```

**Key parameters for FIM:**

| Parameter | Recommended Range | Effect |
|---|---|---|
| `max_new_tokens` | 50–500 | Code block length; longer for functions, shorter for expressions |
| `temperature` | 0.1–0.3 (code) | Lower = more deterministic, higher = more creative |
| `top_p` | 0.9–1.0 | Nucleus sampling threshold |
| `stop` | `["\n\n", "\ndef ", "\nclass ", "\n#", eos] | Stop at natural code boundaries |
| `repetition_penalty` | 1.0–1.1 | Mild penalty to avoid repetitive loops |
| `seed` | 42 (or None) | Deterministic generation |

### 3B. `chat_completion()` — Message-based (Limited FIM)

Some models support FIM through chat by framing it as a code completion task:

```python
client = InferenceClient(model="bigcode/starcoder2-3b")

response = client.chat_completion(
    messages=[
        {
            "role": "user",
            "content": (
                "Complete the function body. Here's the context:\n\n"
                "```python\n"
                "def fibonacci(n):\n"
                "    \"\"\"Return the nth Fibonacci number.\"\"\"\n"
                "    # <FILL_HERE>\n\n"
                "def main():\n"
                "    print(fibonacci(10))\n"
                "```"
            )
        }
    ],
    max_tokens=150,
    temperature=0.2,
    stop=["\ndef ", "\n```"],
)
code = response.choices[0].message.content
```

**Limitation:** Chat-based FIM is model-dependent — the model must understand the completion framing. It works well for instruct-tuned models but poorly for base code models.

### 3C. `extra_body` for provider-specific FIM parameters

```python
# Some providers accept additional FIM parameters via extra_body
response = client.chat_completion(
    messages=[...],
    max_tokens=150,
    extra_body={
        "fim": True,
        "prefix": code_before_cursor,
        "suffix": code_after_cursor,
    }
)
```

**Warning:** `extra_body` is **not standardized** — check provider documentation for supported fields.

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [FIM Serving Engines (TGI, vLLM, SGLang) & Benchmarks](./references/fim-serving-engines-and-benchmarks.md).
