# BFCL-Style Tool-Calling Benchmark

BFCL (Berkeley Function Calling Leaderboard) evaluates how well models use tools/functions. This reference documents the simplified benchmark used in the SakThai model publishing pipeline.

## Categories

| Category | What it tests | Expected behavior |
|----------|--------------|-------------------|
| **simple** | Single tool with correct arguments | Model calls one function with proper params |
| **simple_python** | Python code execution via tool | Model calls `python_repl` for calculations |
| **multiple** | Parallel tool calls | Model calls 2+ functions in one turn |
| **irrelevance** | Refusing to call tools when irrelevant | Model answers directly, no function call |

## Critical: Correct Prompt Format

SakThai models (Qwen2.5-based, ChatML) expect tools defined in `<tools>` XML tags within the system message, and return tool calls as `<tool_call>` JSON blocks. This format is **required** — simple plain-text descriptions of tools will NOT trigger tool calling.

### System message with tools

```
<|im_start|>system
You are SakThai-Agent, a helpful assistant with tool access.

# Tools

You may call functions to assist with the user query.
You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"type": "function", "function": {"name": "get_weather", "description": "Get weather for a city", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call><|im_end|>
```

### Tool call response format

When the model calls a tool, it outputs:
```json
<tool_call>
{"name": "get_weather", "arguments": {"location": "Paris"}}
</tool_call>
```

### Direct answer (no tool)

When the model answers directly (irrelevance test), it outputs plain text with no `<tool_call>` tags:
```
The play Romeo and Juliet was written by William Shakespeare.
```

## Test prompts used

### simple/get_weather

```
system with <tools> XML containing get_weather schema
prompt: "What is the weather in Paris?"
expected: get_weather(location: "Paris") called in <tool_call> tags
```

### simple/search_web

```
system with <tools> XML containing search_web schema
prompt: "Search for the latest news about AI"
expected: search_web(query: "...") called in <tool_call> tags
```

### simple_python/calculate

```
system with <tools> XML containing python_repl schema
prompt: "Calculate the factorial of 10"
expected: python_repl(code: "...") called in <tool_call> tags
```

### multiple/dual_weather

```
system with <tools> XML containing get_weather schema, told to call multiple functions
prompt: "What is the weather in Tokyo and London?"
expected: Two <tool_call> blocks with get_weather for each city
```

### irrelevance/literature

```
system with <tools> XML but told only to call for weather
prompt: "Who wrote Romeo and Juliet?"
expected: Direct answer, NO <tool_call> tags at all
```

### multi_turn/follow-up (v2+)

Verifies the model can handle follow-up questions that depend on a previous tool call context:

```
system with <tools> XML containing get_weather
turn 1: user "What weather in Paris?" → assistant calls get_weather("Paris")
turn 2: tool response "Sunny, 25°C"
turn 3: user "And Tokyo?" → assistant calls get_weather("Tokyo")   <-- this is the test
expected: Second get_weather("Tokyo") call, understanding "And Tokyo?" refers to weather
```

Confirmed working: 1.5B Q4_K_M correctly follows up with `get_weather(location: "Tokyo")` after tool response context. Run with full multi-turn prompt including the tool_response block.

## How to evaluate (BFCLv2-style)

For each test, run the model with the correct ChatML prompt (including `<tools>` XML), then check the response for:

- **simple category**: Does the response contain `<tool_call>` with the expected function name and correct args?
- **multiple category**: Count `<tool_call>` blocks — should be ≥2
- **irrelevance**: Check NO `<tool_call>` appears anywhere in the response

Results format:

```json
{
  "test": "simple/get_weather",
  "category": "simple",
  "prompt": "What is the weather in Paris?",
  "passed": true,
  "response_preview": "<tool_call>\\n{\"name\": \"get_weather\", ...}\\n</tool_call>"
}
```

## Running on CPU with llama.cpp

For GGUF models with llama.cpp, use `-no-cnv` flag to prevent interactive mode and ensure clean single-turn responses:

```bash
# One-shot test (correct format)
llama-cli -m model.gguf -no-cnv \
  -p "<|im_start|>system\nYou have <tools> XML...\n<|im_end|>\n<|im_start|>user\nQ<|im_end|>\n<|im_start|>assistant\n" \
  -n 96 -t 4 --temp 0.1 --no-display-prompt

# Interactive test (if you want conversation)
llama-cli -m model.gguf \
  -t 4 --temp 0.3 --chat-template chatml
```

The `-no-cnv` flag is critical for benchmark scripts — without it, llama.cpp enters interactive mode and keeps generating follow-up conversation turns instead of answering the prompt.

Known performance: 1.5B Q4_K_M on 4 CPU threads → ~2-4 tok/s, each test completes in 3-5 seconds. For 7B, expect 15-30s per test.

## Actual benchmark results (2026-07-23, sakthai-context-1.5b Q4_K_M)

Run on CPU (4 threads, llama.cpp b5021, 934 MB model):

| Test | Result | Notes |
|------|--------|-------|
| simple/get_weather | ✅ PASS | `get_weather(location:"Paris")` |
| simple/search_web | ✅ PASS | `search_web(query:"AI news")` |
| simple_python/calculate | ✅ PASS | `<tool_call>` pattern detected |
| multiple/dual_weather | ❌ FAIL | Only 1 call instead of 2 |
| irrelevance/literature | ✅ PASS | Direct answer, no tool |
| multi_turn/follow-up | ✅ PASS | "And Tokyo?" → second `get_weather` |
| **Overall** | **5/6** | Parallel calls are the gap (needs training) |

The model correctly handles: single tool calls, web search, Python execution, irrelevance detection, and multi-turn follow-up. The gap is parallel tool calls — v7 training with more multi-tool examples should fix this.

## Running on HF Inference (if available)

If HF inference credits are available, the benchmark can use the serverless Inference API:

```python
from huggingface_hub import InferenceClient
client = InferenceClient()

for test in tests:
    result = client.chat_completion(
        model="Nanthasit/sakthai-context-1.5b-merged",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        tools=tools_list,  # Standard OpenAI tool format
        max_tokens=128,
        temperature=0.1
    )
```
