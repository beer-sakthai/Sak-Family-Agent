---
name: SakThai-hf-datasets-tool-calling
version: 1.0.0
description: Complete reference on how to structure tool-calling and function-calling
  datasets for fine-tuning Hugging Face Transformers models, covering OpenAI-compatible
  formats, chat templates, and validation.
category: mlops
tags:
- calling
- chat-templates
- datasets
- fine-tuning
- function-calling
- hf
- huggingface
- tool
- tool-calling
- transformers
author: SakThai
license: MIT
---

# HF Tool-Calling Dataset Structuring & Fine-Tuning

Learn how to structure, format, and validate tool-calling (function-calling) datasets for fine-tuning Hugging Face Transformers models.

## Overview

Tool-calling datasets teach models to invoke external tools or APIs deterministically during conversational generation. Hugging Face Transformers implements an OpenAI-compatible message structure combined with Jinja-based chat templates.

## Canonical Message Formats

### 1. Assistant Tool Call Message
```python
{
    "role": "assistant",
    "tool_calls": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": {"location": "Bangkok", "unit": "celsius"}
            }
        }
    ]
}
```

### 2. Tool Output Execution Response
```python
{
    "role": "tool",
    "content": "{\"temperature\": 32, \"condition\": \"sunny\"}"
}
```

## Chat Template Formatting Workflow

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_db",
            "description": "Query repository database for entries",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword"}
                },
                "required": ["query"]
            }
        }
    }
]

prompt = tokenizer.apply_chat_template(
    messages,
    tools=tools,
    add_generation_prompt=True,
    tokenize=False
)
```

## References & Deep-Dives
- See detailed schema specifications and multi-turn patterns in [`references/hf-learnings.md`](./references/hf-learnings.md).
- See negative/irrelevance filtering examples in [`references/irrelevance-examples.md`](./references/irrelevance-examples.md).
