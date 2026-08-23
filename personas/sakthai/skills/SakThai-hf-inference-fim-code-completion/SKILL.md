---
name: SakThai-hf-inference-fim-code-completion
description: "Deep reference for Fill-in-the-Middle (FIM) code completion through Hugging Face InferenceClient — model-specific token formats, text_generation vs chat_completion approaches, TGI/vLLM/SGLang endpoints, parameter tuning, and verification patterns."
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

## 4. FIM Through TGI (Self-hosted)

TGI supports FIM via the OpenAI-compatible `/v1/completions` endpoint:

```bash
curl -s -X POST "http://localhost:8080/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bigcode/starcoder2-3b",
    "prompt": "<fim_prefix>def hello():\\n    print(\"before\")\\n<fim_suffix>\\n    print(\"after\")\\n<fim_middle>",
    "max_tokens": 100,
    "temperature": 0.2,
    "stop": ["\\n\\n", "<|endoftext|>"]
  }'
```

Or via TGI's native `/generate` endpoint:

```bash
curl -s -X POST "http://localhost:8080/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "<fim_prefix>def hello():\\n    print(\"before\")\\n<fim_suffix>\\n    print(\"after\")\\n<fim_middle>",
    "parameters": {
      "max_new_tokens": 100,
      "temperature": 0.2,
      "stop": ["\\n\\n"]
    }
  }'
```

**Start TGI with FIM support:** TGI enables FIM automatically when you use a model that supports it. No special flag needed.

**Note:** TGI is in maintenance mode (as of 2026). The HF team recommends vLLM or SGLang for new deployments.

## 5. FIM Through vLLM (Recommended)

vLLM supports FIM through its OpenAI-compatible API. Start the server:

```bash
vllm serve bigcode/starcoder2-3b --enable-prefix-caching
```

Then call the completion endpoint:

```bash
curl -s -X POST "http://localhost:8000/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bigcode/starcoder2-3b",
    "prompt": "<fim_prefix>def hello():\\n    print(\"before\")\\n<fim_suffix>\\n    print(\"after\")\\n<fim_middle>",
    "max_tokens": 100,
    "temperature": 0.2,
    "stop": ["\\n\\n"]
  }'
```

**Key vLLM FIM parameters:**
- `prompt` — Must be formatted with the model's FIM tokens
- No special flag needed — vLLM auto-detects FIM tokens in the prompt
- Supports streaming: set `"stream": True`

## 6. FIM Through SGLang

SGLang supports FIM:

```bash
python3 -m sglang.launch_server --model bigcode/starcoder2-3b --port 30000
```

```bash
curl -s -X POST "http://localhost:30000/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bigcode/starcoder2-3b",
    "prompt": "<fim_prefix>def hello():\\n    print(\"before\")\\n<fim_suffix>\\n    print(\"after\")\\n<fim_middle>",
    "max_tokens": 100
  }'
```

## 7. Model Selection for FIM

| Model | Size | FIM Quality | Speed | Notes |
|---|---|---|---|---|
| **StarCoder2-3B** | 3B | Good | Fast | Best small FIM model, well-proven |
| **StarCoder2-7B** | 7B | Better | Moderate | Better code understanding |
| **StarCoder2-15B** | 15B | Best | Slow | Only for dedicated inference |
| **Qwen2.5-Coder-1.5B** | 1.5B | Fair | Fastest | Lightweight, good for simple infills |
| **Qwen2.5-Coder-7B** | 7B | Very Good | Moderate | Strong multilingual support |
| **DeepSeek-Coder-6.7B** | 6.7B | Very Good | Moderate | Strong FIM, good at Python |
| **CodeLlama-7B** | 7B | Good | Moderate | Mature, well-documented |
| **Granite-Code-3B** | 3B | Good | Fast | IBM's code model, Apache 2.0 |
| **Stable-Code-3B** | 3B | Fair | Fast | Lightweight |

## 8. FIM for Small/Budget Models (Beer's Use Case)

For the 0.5B–1.5B range, FIM is less reliable but still usable:

```python
# Qwen2.5-Coder-1.5B with FIM
from huggingface_hub import InferenceClient

client = InferenceClient(model="Qwen/Qwen2.5-Coder-1.5B-Instruct")

prompt = (
    "<|fim_prefix|>"
    "def factorial(n):\n"
    "    if n == 0:\n"
    "        return 1\n"
    "<|fim_suffix|>"
    "\n    print(factorial(5))  # should print 120\n"
    "\ndef main():"
    "<|fim_middle|>"
)

result = client.text_generation(
    prompt,
    max_new_tokens=80,
    temperature=0.1,  # Lower temp is critical for small models
    stop=["\n\n", "<|endoftext|>", "def "],
)
```

**Tips for small-model FIM:**
- Use `temperature=0.1` for deterministic output (small models are more prone to drift)
- Set `max_new_tokens` conservatively (50–100 tokens max)
- Provide more prefix context (at least 5–10 lines before cursor)
- Use explicit `stop` tokens — small models tend to keep generating
- Expect lower quality on complex logic; good for boilerplate/patterns

## 9. Stopping Strategies for FIM

FIM generation needs careful stop handling:

```python
# Common stop sequences for code models
stop_list = []

# 1. Most models: stop at double newline (end of logical block)
stop_list.append("\n\n")

# 2. Stop at next function/class definition
stop_list.append("\ndef ")
stop_list.append("\nclass ")

# 3. Stop at model-specific EOS token
stop_list.append("<|endoftext|>")
stop_list.append("</s>")
stop_list.append("<eos>")

# 4. Stop at indentation decrease to column 0
# (Hard to encode as stop string; rely on \n\n as proxy)

# 5. Stop after specific code markers
stop_list.append("\n# ")  # Next comment = new section
stop_list.append('"""')   # End of docstring
```

**Note on stop tokens:** The `stop` parameter accepts a list of strings. TGI/vLLM compare each generated token against the full stop list and halt generation as soon as any stop string is produced.

## 10. Prompt Design Best Practices

### Good prefix

```python
# Include: imports, function signature, docstring, initial logic
prefix = (
    "import json\n"
    "from typing import Dict, Any\n\n"
    "def process_response(data: Dict[str, Any]) -> str:\n"
    '    """Extract the answer from the API response."""\n'
    '    if "error" in data:\n'
    "        raise ValueError(data[\"error\"])\n"
    "    result = data.get(\"result\", {})\n"
    "    answer = result.get(\"text\", \"\")\n"
)
```

### Good suffix

```python
# Include: code that follows the cursor (return, next function, call site)
suffix = (
    "\n    return answer.strip()\n\n\n"
    "def handle_request():"
)
```

### Full FIM prompt

```python
prompt = f"<fim_prefix>{prefix}<fim_suffix>{suffix}<fim_middle>"
```

**Rule of thumb:** The suffix should contain at least the closing delimiter, return statement, or next function call. Without this context, FIM degrades to standard text generation.

## 11. Provider Compatibility Matrix

| Provider | `text_generation` | `chat_completion` | FIM via API | Notes |
|---|---|---|---|---|
| hf-inference | ✅ | ✅ | ⚠️ Partial (TGI-backed models) | Depends on model backend |
| deepinfra | ✅ | ✅ | ✅ | Good code model support |
| fireworks-ai | ✅ | ✅ | ✅ | Via completions endpoint |
| together | ✅ | ✅ | ✅ | Good FIM support |
| groq | ✅ | ✅ | ⚠️ | Limited code model selection |
| replicate | ✅ | ✅ | ❌ | No FIM endpoint |
| fal-ai | ✅ | ✅ | ❌ | Image/video focused |
| cerebras | ❌ | ✅ | ❌ | Chat-only models |

**Testing provider FIM support:**

```python
def test_fim_support(provider: str, model: str = "bigcode/starcoder2-3b"):
    """Quick test to check if a provider supports FIM."""
    from huggingface_hub import InferenceClient
    
    client = InferenceClient(model=model, provider=provider)
    prompt = "<fim_prefix>x = 1\n<fim_suffix>\ny = x + 1\n<fim_middle>"
    
    try:
        result = client.text_generation(prompt, max_new_tokens=20, temperature=0.1)
        return bool(result and len(result) > 0)
    except Exception as e:
        return str(e)
```

## 12. Common Issues & Solutions

### Issue: Model returns prefix text repeated instead of infilled code
**Cause:** Model doesn't recognize FIM tokens (wrong format or model not trained for FIM)
**Fix:** Verify FIM tokens from the model card; try chat-based approach instead

### Issue: Generated code doesn't connect properly with suffix
**Cause:** Generated code ends at wrong point, typically too short or too long
**Fix:** Add explicit stop tokens; increase `max_new_tokens`; adjust temperature

### Issue: Provider returns 400 Bad Request for FIM prompt
**Cause:** Provider doesn't serve models with TGI/vLLM backend
**Fix:** Switch provider; use `chat_completion()` instead of `text_generation()`

### Issue: Small model keeps repeating the same token
**Cause:** Temperature too high for model size; repetition penalty not set
**Fix:** Set `temperature=0.1`, `repetition_penalty=1.05`, add strong stop tokens

### Issue: InferenceClient routes text_generation to chat endpoint
**Cause:** The provider routes all requests through chat completion
**Fix:** Check `get_endpoint_info()`; use provider that separates text_gen from chat

## 13. Verification Pattern

Test FIM works end-to-end:

```python
from huggingface_hub import InferenceClient

def verify_fim(model_id: str, provider: str = "hf-inference"):
    """Run a simple FIM test and verify the output makes sense."""
    client = InferenceClient(model=model_id, provider=provider)
    
    # Known test case: complete the factorial function
    prompt = (
        "<fim_prefix>"
        "def factorial(n):\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "<fim_suffix>"
        "\n    print(factorial(5))\n"
        "\ndef main():"
        "<fim_middle>"
    )
    
    result = client.text_generation(
        prompt,
        max_new_tokens=80,
        temperature=0.1,
        stop=["\n\n", "<|endoftext|>", "\ndef ", "\nclass "],
    )
    
    checks = {
        "has_output": len(result.strip()) > 10,
        "contains_return": "return" in result,
        "no_repetition": len(set(result.split())) / max(len(result.split()), 1) > 0.3,
    }
    
    print(f"FIM result: {result[:100]}...")
    print(f"Checks: {sum(checks.values())}/{len(checks)} passed")
    return all(checks.values())
```

## 14. References

- [HF InferenceClient Docs](https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client)
- [TGI GitHub (maintenance mode)](https://github.com/huggingface/text-generation-inference)
- [vLLM Documentation](https://docs.vllm.ai)
- [SGLang Documentation](https://docs.sglang.ai)
- [StarCoder2 Model Card](https://huggingface.co/bigcode/starcoder2-3b)
- [Qwen2.5-Coder Model Card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct)
- [DeepSeek Coder Model Card](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct)
