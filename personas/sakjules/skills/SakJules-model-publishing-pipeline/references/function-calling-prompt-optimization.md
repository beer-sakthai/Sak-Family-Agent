# Function Calling Prompt Optimization

The prompt format is the single biggest lever for tool-calling accuracy. A model that scores 2/5 with one prompt can score 5/5 with the right one.

## The Optimal Prompt (discovered 2026-07-25)

### System Prompt

```
You are a function-calling assistant. Respond with tool_calls JSON when appropriate.
```

This works better than:
- "You are a helpful assistant" — too permissive, model answers directly
- "You have access to tools" — vague, doesn't trigger function-calling mode
- "Call tools when needed" — leads to inconsistent behavior

### Tool Definition Format

Use XML `<tool>` tags in the system message:

```
<tools>
<tool>get_weather(location)</tool>
<tool>search_web(query)</tool>
<tool>calculate(expression)</tool>
<tool>get_time(timezone)</tool>
</tools>
```

The `<tool>name(params)</tool>` XML format triggers the model's function-calling behavior. JSON-based tool schemas in the system message do NOT consistently trigger tool calls.

### Full Prompt Template (ChatML)

```
<|im_start|>system
You are a function-calling assistant. Respond with tool_calls JSON when appropriate.
<tools>
<tool>get_weather(location)</tool>
<tool>search_web(query)</tool>
</tools>
<|im_end|>
<|im_start|>user
What is the weather in Tokyo?
<|im_end|>
<|im_start|>assistant
```

### Inference Settings

| Parameter | Value | Reason |
|-----------|-------|--------|
| Threads | **2** | Sweet spot for 2-core CPU. 4 threads causes memory contention and is slower. |
| Temperature | **0.1** | Low temp = consistent output. 0.3+ introduces randomness in tool selection. |
| Token limit | **128** | Enough for tool_call output, not enough for rambling answers. |
| Stop tokens | `<|im_end|>` | Prevents runaway generation with ChatML format. |

## What Happens With Wrong Prompts

| Prompt | Result | Problem |
|--------|--------|---------|
| "You are a helpful assistant" | Answers directly | No trigger for tool-calling mode |
| "Use tools when needed" | Mixed behavior | Model sometimes calls, sometimes doesn't |
| "Never call tools" | Refuses everything | Overly strict, fails tool tests too |
| JSON tools in system prompt | Inconsistent | Model ignores the structured schema |

## Results (Verified 2026-07-25)

### 1.5B with Optimal Prompt

| Test | Response | Result |
|------|----------|--------|
| Weather in Tokyo | `tool_call:` | ✅ |
| Search for AI news | `<search>` | ✅ |
| Calculate 25 * 4 | `tool_call:` | ✅ |
| Time in London | `<get_time location="London" />` | ✅ |
| Irrelevance (telephone inventor) | Direct answer | ✅ |
| **Overall** | | **5/5** |

### 0.5B with Optimal Prompt

| Test | Response | Result |
|------|----------|--------|
| Weather in Tokyo | Direct description | ❌ |
| Search for AI news | `<search>` | ✅ |
| Calculate 25 * 4 | Direct answer | ❌ |
| Time in London | `<get_time location="London" />` | ✅ |
| Irrelevance (telephone inventor) | Direct answer | ✅ |
| **Overall** | | **3/5** |

The 0.5B model's smaller capacity limits its ability to follow the function-calling instruction consistently.

## Inference Script (llama.cpp)

Save and use the optimal settings:

```bash
LLAMA="/path/to/llama-cli"
LIB="/path/to/build/bin"
MODEL="/path/to/model.gguf"

SYSTEM="You are a function-calling assistant."

LD_LIBRARY_PATH="$LIB" "$LLAMA" -m "$MODEL" -no-cnv \
  -p "<|im_start|>system\n$SYSTEM\n<tools>\n<tool>get_weather(location)</tool>\n<tool>search_web(query)</tool>\n</tools><|im_end|>\n<|im_start|>user\n$1<|im_end|>\n<|im_start|>assistant\n" \
  -n 128 -t 2 --temp 0.1 --no-display-prompt 2>/dev/null
```

## Limitations

- **llama.cpp CLI cannot produce structured `tool_calls` JSON.** The model generates free text that looks like tool calls but isn't machine-parseable JSON. For true OpenAI-compatible function calling, use:
  - Ollama API (`v1/chat/completions` with `tools` field)
  - llama.cpp server (if it runs on your system)
  - Hugging Face Transformers pipeline
- **Format mismatch with training data.** Our v6 dataset uses OpenAI `tool_calls` format in the messages. The `<tool>` XML format is close but not identical. A future training run with matching XML format would likely improve consistency.
- **Inference engine matters more than model.** A model that scores 5/5 on llama.cpp text mode may score differently on Ollama API mode and vice versa. Always report which engine was used.
