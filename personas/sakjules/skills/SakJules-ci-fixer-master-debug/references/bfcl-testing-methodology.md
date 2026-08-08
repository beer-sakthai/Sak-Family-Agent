# BFCL False-Positive Trap

## The problem

Testing tool-calling with `grep -qi "get_weather"` produces FALSE POSITIVES because the model's free-text response contains the word "weather" in plain English:

```bash
# Output: "The weather in Tokyo is sunny and warm."
grep -qi "get_weather" <<< "The weather in Tokyo is sunny and warm."
# → ✅ passes (WRONG — no tool was called)
```

The grep found the substring "weather" inside "the weather" — not a tool call at all.

## The fix

Check the FIRST LINE of output for exact tool-call syntax:

```bash
# Correct: first line must start with a tool construct
head -1 <<< "$output" | grep -qiE "^(<tool|<function|tool_call:|{\\\"name)"
```

## Real test methodology (proven this session)

1. Use `transformers` pipeline with the model's actual chat template (not llama.cpp CLI)
2. Define tools as OpenAI `{"type":"function","function":{"name":"...","parameters":{...}}}` 
3. Apply tokenizer's `apply_chat_template(messages, tools=tools, tokenize=False)`
4. Generate with `model.generate()`
5. Check output for `<functioncall>` or `tool_calls` JSON

This proved our 0.5B model produces proper `<functioncall> {"name":"get_weather","arguments":{...}}` — while llama.cpp CLI testing showed false 0/4.

> `⚠️ Cardinal Rule` — the correct sequence is: check status → read log → identify error → root cause → fix → verify. Never guess. Never skip diagnosis.

**llama.cpp CLI cannot prove or disprove tool-calling.** It generates free text only. Proper function calling requires a server with grammar-constrained output or the transformers pipeline.
