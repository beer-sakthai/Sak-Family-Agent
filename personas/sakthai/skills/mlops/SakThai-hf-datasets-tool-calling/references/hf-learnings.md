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
|

---

## 8. Advanced JSON Schema Patterns (Deep Dive)

The `get_json_schema()` function in `chat_template_utils.py` supports complex Python type hints beyond simple primitives.

### Union types (`typing.Union` / `|` syntax)

```python
def set_alarm(time: str | int, message: str):
    """Set an alarm for a given time.
    Args:
        time: The time to set the alarm for (12-hour format string or 24-hour int)
        message: The alarm message
    """
```

| Input type | JSON Schema output |
|------------|-------------------|
| `str \| int` | `{"type": ["string", "integer"]}` |
| `str \| None` | `{"type": "string", "nullable": True}` |
| `list[str] \| dict` | `{"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "object"}]}` |

**Rules:**
- `None` in a Union → sets `nullable: true` and drops null from the type list
- Single non-null type → unwrapped and expressed directly
- Multiple basic types (all with `type: string`) → expressed as `["string", "integer"]`
- Mixed complex types → expressed as `anyOf`

### Literal types (`typing.Literal`)

```python
def set_volume(device: str, level: Literal["low", "medium", "high"]):
    """Set the volume level of a device.
    Args:
        device: The device name
        level: The volume level to set (choices: ["low", "medium", "high"])
    """
```

Generates: `{"type": "string", "enum": ["low", "medium", "high"]}`

The `(choices: ...)` suffix in docstrings is the **preferred** approach — it auto-creates the `enum` field in the schema.

### Nested object types

```python
def search_flights(
    origin: str,
    destination: str,
    passengers: list[dict],
    preferences: dict[str, bool] | None = None,
):
    """Search for available flights.
    Args:
        origin: Departure airport code
        destination: Arrival airport code
        passengers: List of passengers with name and age
        preferences: Travel preferences like direct_flight, extra_legroom
    """
```

Generated schema for complex types:
```json
{
    "passengers": {
        "type": "array",
        "items": {"type": "object"}
    },
    "preferences": {
        "type": "object",
        "nullable": true,
        "additionalProperties": {"type": "boolean"}
    }
}
```

**Limitations:**
- ❌ Nested `dict` values are always `object` (no recursive type inference)
- ❌ `Tuple` with ellipsis (`...`) is rejected
- ✅ `list[SpecificType]` preserves item type info
- ✅ `dict[str, Type]` preserves value type via `additionalProperties`

### Docstring `(choices: ...)` enum syntax

```python
def order_drink(
    beverage: str,
    size: str,
    quantity: int,
):
    """Order a beverage.
    Args:
        beverage: The type of drink (choices: ["coffee", "tea", "juice"])
        size: The cup size (choices: ["small", "medium", "large"])
        quantity: Number of drinks
    """
```

The regex `\(choices:\s*(.*?)\)\s*$` matches at the **end of the line only**. The choices content is parsed with `json.loads()`, so it must be valid JSON arrays:
- ✅ `(choices: ["a", "b", "c"])`
- ✅ `(choices: [1, 2, 3])`
- ❌ `(choices: a, b, c)` — must be JSON array
- ❌ `choices: ["a"]` on the next line — must be on the same line

---

## 9. Multi-Turn and Parallel Tool Calling

### Single-turn tool call (standard)

```
User → Assistant(tool_call) → Tool → Assistant(text)
```

### Multi-turn tool calling

```
User → Assistant(tool_call_1) → Tool → Assistant(tool_call_2) → Tool → Assistant(text)
```

**Dataset structure for multi-turn:**

```python
messages = [
    {"role": "user", "content": "What's the weather in Paris and Tokyo?"},
    {
        "role": "assistant",
        "tool_calls": [
            {
                "type": "function",
                "function": {"name": "get_weather", "arguments": {"city": "Paris"}}
            }
        ]
    },
    {"role": "tool", "content": '{"temp": 22, "condition": "sunny"}'},
    {
        "role": "assistant",
        "tool_calls": [
            {
                "type": "function",
                "function": {"name": "get_weather", "arguments": {"city": "Tokyo"}}
            }
        ]
    },
    {"role": "tool", "content": '{"temp": 28, "condition": "humid"}'},
    {"role": "assistant", "content": "Paris is 22°C and sunny. Tokyo is 28°C and humid."}
]
```

### Parallel tool calls (multiple in one assistant message)

Some models (e.g., Qwen2.5, Llama 3.1+) support multiple tool calls in a single assistant message:

```python
{
    "role": "assistant",
    "tool_calls": [
        {
            "type": "function",
            "function": {"name": "get_weather", "arguments": {"city": "Paris"}}
        },
        {
            "type": "function",
            "function": {"name": "get_weather", "arguments": {"city": "Tokyo"}}
        }
    ]
}
```

**Parallel tool response format (with `tool_call_id`):**

```python
[
    {"role": "tool", "tool_call_id": "call_001", "content": '{"temp": 22}'},
    {"role": "tool", "tool_call_id": "call_002", "content": '{"temp": 28}'}
]
```

**Key rules:**
- `tool_call_id` is optional for most models but **required** for OpenAI-compatible APIs and multi-call models
- When absent, tool responses match by **positional order** (first tool_call → first tool response)
- When present, the id links a specific call to its result
- Parallel calls in training data must be matched by position or id

### tool_call_id conventions

| Model Family | tool_call_id Required? | Format |
|-------------|----------------------|--------|
| Llama 3.1+ | Yes (multi-call) | `call_xxx` |
| Qwen 2.5 | Yes (multi-call) | string |
| Mistral | No (single call) | N/A |
| Cohere | No (single call) | N/A |
| DeepSeek | Yes | string |

---

## 10. continue_final_message with Reasoning Models (v5.14+)

Transformers v5.14.0 introduced `continue_final_message` as a **string parameter** that accepts a field name.

### Prefilling content field

```python
chat = [
    {"role": "user", "content": "Can you format the answer in JSON?"},
    {"role": "assistant", "content": '{"name": "'},
]
formatted = tokenizer.apply_chat_template(
    chat, continue_final_message=True, tokenize=True, return_dict=True
)
model.generate(**formatted)
```

### Prefilling reasoning/thinking fields

For reasoning models with separate thinking blocks:

```python
# Qwen-style
chat = [
    {"role": "user", "content": "Explain 1+1"},
    {"role": "assistant", "reasoning_content": "The user wants a simple addition. ", "content": ""},
]
formatted = tokenizer.apply_chat_template(
    chat, continue_final_message="reasoning_content", tokenize=False
)

# Gemma-style
chat = [
    {"role": "user", "content": "Solve x^2 - 4 = 0"},
    {"role": "assistant", "thinking": "Let me solve this step by step. ", "content": ""},
]
formatted = tokenizer.apply_chat_template(
    chat, continue_final_message="thinking", tokenize=False
)
```

**Rules:**
1. `continue_final_message` and `add_generation_prompt` are mutually exclusive
2. The named field must exist on the final message and be referenced in the chat template
3. Prefilling `content` closes the reasoning block; prefilling the reasoning field keeps it open
4. `TextGenerationPipeline` auto-detects assistant prefills and switches to `continue_final_message=True`

### Pipeline auto-detection logic

```python
# If the final message has role "assistant", pipeline assumes prefill:
# add_generation_prompt=False → continue_final_message=True
# To override, pass continue_final_message explicitly
```

---

## 11. Dataset Validation Patterns for Tool-Calling Data

### Schema validation with datasets library

```python
from datasets import Dataset, Features, Value, Sequence, Struct
import json

def validate_tool_calling_dataset(dataset: Dataset) -> list[str]:
    """Validate a tool-calling dataset structure and return errors."""
    errors = []

    for i, row in enumerate(dataset):
        messages = row.get("messages", [])
        tools = row.get("tools", [])

        # 1. Messages must be non-empty
        if not messages:
            errors.append(f"Row {i}: empty messages list")
            continue

        # 2. First message should be system or user
        if messages[0]["role"] not in ("system", "user"):
            errors.append(f"Row {i}: first role must be 'system' or 'user'")

        # 3. Validate conversation flow
        expected_roles = {"system", "user", "assistant", "tool"}
        for j, msg in enumerate(messages):
            if msg["role"] not in expected_roles:
                errors.append(f"Row {i}, msg {j}: unknown role '{msg['role']}'")

            # 4. tool_calls must have valid structure
            if "tool_calls" in msg:
                for k, tc in enumerate(msg["tool_calls"]):
                    if tc.get("type") != "function":
                        errors.append(f"Row {i}, msg {j}, tc {k}: missing 'type': 'function'")
                    fn = tc.get("function", {})
                    if "name" not in fn:
                        errors.append(f"Row {i}, msg {j}, tc {k}: missing function name")
                    if "arguments" not in fn or not isinstance(fn["arguments"], dict):
                        errors.append(f"Row {i}, msg {j}, tc {k}: arguments must be a dict")

            # 5. Tool messages must follow assistant with tool_calls
            if msg["role"] == "tool":
                if j == 0 or messages[j-1]["role"] != "assistant":
                    errors.append(f"Row {i}, msg {j}: tool message must follow assistant")
                if "tool_calls" not in messages[j-1]:
                    errors.append(f"Row {i}, msg {j}: tool message without preceding tool_call")

            # 6. Tool results content must be string
            if msg["role"] == "tool":
                if not isinstance(msg.get("content"), str):
                    errors.append(f"Row {i}, msg {j}: tool content must be a string")

    return errors

# Usage
ds = Dataset.from_list(rows)
validation_errors = validate_tool_calling_dataset(ds)
if validation_errors:
    for err in validation_errors[:20]:  # Show first 20 errors
        print(err)
```

### Hub-side validation

When pushing tool-calling datasets to the Hugging Face Hub, the dataset viewer:

1. Parses the `messages` column to verify message structure
2. Shows a preview with role-colored formatting
3. Supports `?search=` queries against message content
4. Indexes the conversation structure for navigation

**Recommended dataset card for tool-calling data:**

```yaml
---
license: mit
task_categories:
- text-generation
tags:
- tool-calling
- function-calling
- chat
pretty_name: My Tool-Calling Dataset
configs:
- config_name: default
  data_files: data/train-*.parquet
```

### Features schema for typed datasets

```python
from datasets import Features, Value, Sequence, ClassLabel

tool_calling_features = Features({
    "messages": Sequence({
        "role": Value("string"),
        "content": Value("string"),
        "tool_calls": Sequence({
            "type": Value("string"),
            "function": {
                "name": Value("string"),
                "arguments": Value("string")  # JSON string of args dict
            }
        }),
        "tool_call_id": Value("string"),
    }),
    "tools": Sequence({
        "type": Value("string"),
        "function": {
            "name": Value("string"),
            "description": Value("string"),
            "parameters": Value("string"),  # JSON string of param schema
        }
    }),
    "source": Value("string"),
})

ds = Dataset.from_list(rows, features=tool_calling_features)
# Casting validates the structure at creation time
```

### TRL compatibility for tool-calling fine-tuning

When using `trl.SFTTrainer` with tool-calling datasets:

```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    formatting_func=preprocess,  # Use the preprocess fn from Section 3
    # Optional: only train on assistant responses
    # Use response_template to mask non-assistant tokens
    response_template="<|assistant|>",
)
```

The `response_template` parameter in SFTTrainer computes loss **only** on tokens after the template string, which is critical for tool-calling data where we want to train on the assistant's tool calls and text responses, not the system prompt or tool results.

---

## 12. Best Practices for Dataset Publishing

| Aspect | Recommendation |
|--------|---------------|
| **Storage format** | Parquet (compressed, columnar, fast) |
| **Tool definitions** | Store in `tools` column as full JSON schemas |
| **Message arguments** | Keep as `dict`, not JSON string (but serialize to JSON string for typed Features) |
| **Validation** | Run schema validation before push using `validate_tool_calling_dataset()` |
| **Dataset card** | Include `tags: [tool-calling, function-calling]` for discoverability |
| **Test rendering** | Always test 3-5 samples with `apply_chat_template(tokenize=False)` |
| **Loss masking** | Use SFTTrainer's `response_template` to mask non-assistant tokens |
| **Tool compatibility** | Document which models/templates the dataset is designed for |
| **Number of tools** | Include all tools used across the conversation in the `tools` column |
| **Multi-turn** | Validate that each `tool_call` has a matching `tool` response |