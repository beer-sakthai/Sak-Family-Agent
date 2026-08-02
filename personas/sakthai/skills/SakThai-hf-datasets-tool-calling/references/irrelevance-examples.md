# Irrelevance Examples for Tool-Calling Datasets

> Added: 2026-07-25
> Source: Practical experience with sakthai-combined-v6 0.5B training gap

## Overview

Irrelevance examples are single-turn general-knowledge Q&A pairs where the assistant answers **directly without calling any tool**. They fix a common failure mode in smaller models (0.5B–3B) that over-use tools or refuse to answer simple factual questions.

## When to Add Them

- Model frequently emits `<tool_call>` for trivia, history, or simple math it could answer from knowledge
- Model refuses with "I need to use a tool for that" on non-real-time questions
- Post-training eval shows high tool-call rate on categories where tools are unnecessary

## Dataset Format

Each example: single-turn `conversations` array with `system`/`user`/`assistant`, and a `tools` array matching the full tool set:

```json
{
  "conversations": [
    {"role": "system", "content": "You are a helpful assistant with access to tools. Use tool calls when needed and respond naturally after results."},
    {"role": "user", "content": "Who painted the Mona Lisa?"},
    {"role": "assistant", "content": "The Mona Lisa was painted by Leonardo da Vinci between 1503 and 1519."}
  ],
  "tools": [
    {"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}
  ]
}
```

## Key Rules

| Rule | Why |
|------|-----|
| Exactly 3 messages | Single-turn; no `tool` role |
| Assistant: no `<tool_call>` | Core signal — answer from knowledge |
| `tools` array present | Model learns to *choose* not to call, not to be in a different mode |
| Same system message as tool-call examples | Keeps distribution consistent |
| Questions answerable from pre-training data | History, literature, science, geography, math |
| Mix across ≥3 categories | Prevents category bias |

## Recommended Ratio

**5–15%** of total training dataset. Below 5%: model still over-refuses. Above 15%: model starts ignoring legitimate tool use.

## Validation Checklist

- [ ] Zero `<tool_call>` tags in any assistant response
- [ ] Exactly 3 messages per example (system / user / assistant)
- [ ] Roles match `['system', 'user', 'assistant']` exactly
- [ ] `tools` array non-empty, matches tool-calling examples
- [ ] Questions span ≥3 knowledge categories
- [ ] Tool-use examples still dominate the dataset
