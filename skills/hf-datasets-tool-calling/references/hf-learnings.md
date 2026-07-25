# Tool-Calling Dataset Formats — HF Learning

> Research date: 2026-07-24
> Source: Hugging Face Transformers docs (v5.14.0), `chat_extras`, `chat_templating`, `chat_response_parsing`

## Overview

Tool-calling (also called function-calling) datasets teach models to invoke external functions as part of their response. This document covers the canonical dataset structure, JSON schema format, chat template integration, and training data preparation patterns as implemented in Hugging Face Transformers.

---

## 1. The Canonical Message Format

Hugging Face Transformers uses an OpenAI-compatible message dict structure for tool-calling, extended with Hugging Face-specific conventions:

### Assistant tool-call message

```python
{
    "role": "assistant",
    "tool_calls": [
        {
            "type": "function",
            "function": {
                "name": "get_current_temperature",
                "arguments": {"location": "Paris, France", "unit": "celsius"}
            }
        }
    ]
}
```

**Key rules:**
- `tool_calls` is a **list of dicts** (OpenAI uses a JSON string — HF Transformers uses dicts directly)
- Each tool call has `type: "function"` and a `function` dict with `name` (str) and `arguments` (dict)
- Most models emit only a **single tool call** at a time; multi-call models are rarer and need tool_call_ids

### Tool response message

```python
{"role": "tool", "content": "22"}
```

- The `tool` role carries the result back
- `content` is **always a string** (even if the tool returned a number/bool)
- No `tool_call_id` needed unless the model explicitly requires it (check model card)

### Conversation lifecycle

```
User → (tool definitions supplied via `tools=` param) → Assistant tool_call → Tool result → Assistant text reply
```

---

## 2. Tool Definition Format (JSON Schema)

Tools are passed to `apply_chat_template()` as either Python functions or JSON schema dicts.

### Python function format (recommended for development)

```python
def get_current_temperature(location: str, unit: str):
    """
    Get the current temperature at a location.

    Args:
        location: The location to get the temperature for, in the format "City, Country"
        unit: The unit to return the temperature in. (choices: ["celsius", "fahrenheit"])
    """
    return 22.  # Actual call would do real API work
```

**Docstring rules:**
- Only **Google-style** docstrings are parsed
- The parser reads: function name, argument names, argument types, docstring description
- `Returns:` blocks are ignored by most models
- The actual function code is never executed — only the signature and docstring matter
- Methods with `self`/`cls` auto-ignore the receiver argument

### JSON schema format (recommended for production/datasets)

```json
{
    "type": "function",
    "function": {
        "name": "get_current_temperature",
        "description": "Get the current temperature at a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get the temperature for, in the format 'City, Country'"
                },
                "unit": {
                    "type": "string",
                    "description": "The unit to return the temperature in.",
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["location", "unit"]
        }
    }
}
```

### Programmatic conversion

```python
from transformers.utils import get_json_schema

def multiply(a: float, b: float):
    """Multiply two numbers.
    Args:
        a: The first number
        b: The second number
    """
    return a * b

schema = get_json_schema(multiply)
# Returns JSON schema dict as shown above
```

---

## 3. Dataset Structure for Fine-Tuning

When building a tool-calling dataset for training, use this structure:

### Recommended columns

| Column | Type | Description |
|--------|------|-------------|
| `messages` | list[dict] | Complete conversation including tool calls |
| `tools` | list[dict] | Tool definitions as JSON schemas |
| `source` | str (optional) | Data provenance tag |

### Example row

```python
{
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to weather tools."
        },
        {
            "role": "user",
            "content": "What's the temperature in Paris?"
        },
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_temperature",
                        "arguments": {"location": "Paris, France", "unit": "celsius"}
                    }
                }
            ]
        },
        {
            "role": "tool",
            "content": "22"
        },
        {
            "role": "assistant",
            "content": "The temperature in Paris is currently 22°C."
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_current_temperature",
                "description": "Get current temperature at a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City, Country format"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location", "unit"]
                }
            }
        }
    ]
}
```

### Training prep with `apply_chat_template`

```python
from transformers import AutoTokenizer
from datasets import Dataset

tokenizer = AutoTokenizer.from_pretrained("HuggingFaceH4/zephyr-7b-beta")

def preprocess(example):
    # Format the conversation with tools
    formatted = tokenizer.apply_chat_template(
        example["messages"],
        tools=example["tools"],
        tokenize=False,
        add_generation_prompt=False  # CRITICAL for training!
    )
    return {"text": formatted}

dataset = Dataset.from_list(data)
dataset = dataset.map(preprocess)
# Now train with SFTTrainer or similar
```

**Training caveats:**
- ❌ `add_generation_prompt=False` — DO NOT add assistant prompts during training
- ✅ Tokenize the full message (prompt + completion) for causal LM training
- ✅ Use `loss_mask` or `response_template` in SFTTrainer to only compute loss on assistant responses
- ❌ Do NOT pass tools during inference if they were in the training template — the template must handle them

---

## 4. Chat Template Rendering

Tool-calling chat templates render tools into the model's specific special-token format.

### Common rendering patterns

**Hermes-2-Pro style** (tool calls wrapped in XML-like tags):
```
<|im_start|>system
You are a bot that responds to weather queries.<|im_end|>
<|im_start|>user
Hey, what's the temperature in Paris right now?<|im_end|>
<|im_start|>assistant
<tool_call>
{"arguments": {"location": "Paris, France", "unit": "celsius"}, "name": "get_current_temperature"}
</tool_call><|im_end|>
<|im_start|>tool
22<|im_end|>
<|im_start|>assistant
The temperature in Paris, France right now is 22°C.<|im_end|>
```

**Tool definition encoding** is model-specific:
- Some models encode tool definitions in the system prompt
- Others encode them in a special `tools` section before the first user message
- The model card specifies the exact format — always check it

---

## 5. Response Parsing in v5.14.0

Transformers v5.14 introduced `parse_response()` for structured output parsing, including tool calls:

```python
# One-shot parsing
out_text = tokenizer.decode(outputs[0, input_ids.shape[1]:])
parsed = tokenizer.parse_response(out_text, prefix=input_ids[0])
# Returns: {"role": "assistant", "thinking": "...", "tool_calls": [...]}

# Streaming parsing
parser = tokenizer.get_response_parser(prefix=input_ids[0])
for chunk in model_output:
    for event in parser.feed(chunk):
        # Events: region_open, region_chunk (with dirty=True for JSON), region_close
        pass
message, final_events = parser.finalize()
```

### Response template internals

Response templates define how raw model output is structured back into dicts:

```python
{
    "defaults": {"role": "assistant"},
    "fields": {
        "thinking": {"open": "<think>", "close": "</think>", "content": "text"},
        "tool_calls": {
            "open": "<tool_call>",
            "close": "</tool_call>",
            "repeats": True,
            "content": "json",
            "transform": {"type": "function", "function": "{content}"},
        },
        "content": {
            "close": "<|im_end|>",
            "content": "text",
        },
    },
}
```

---

## 6. Best Practices Summary

| Practice | Why |
|----------|-----|
| Store tools as JSON schema in dataset | Portable, language-agnostic, inspectable |
| Keep `arguments` as dict (not JSON string) | HF expects dict; OpenAI uses string — be explicit |
| Use `tool` role for results | Required by all HF tool-use chat templates |
| Always stringify `content` in tool results | Non-string may cause template errors |
| Validate against model card | Every model has unique special-token format |
| Test with `apply_chat_template(tokenize=False)` first | Debug formatting before running training |
| Use `continue_final_message` for prefill | Prefill assistant JSON/thinking to guide generation |
| Batch `parse_response` or stream per-sequence | No batch streaming; one parser per sequence |
| Register tools per-conversation, not globally | Different turns may have different available tools |

---

## 7. Key Source Files in Transformers

| File | Purpose |
|------|---------|
| `src/transformers/tokenization_utils_base.py` | `apply_chat_template()`, `parse_response()` |
| `src/transformers/utils/chat_template_utils.py` | `get_json_schema()`, template rendering helpers |
| `src/transformers/utils/response_parser.py` | Response parsing and streaming logic |
