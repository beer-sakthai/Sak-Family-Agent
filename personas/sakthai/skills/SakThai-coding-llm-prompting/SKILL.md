---
name: SakThai-coding-llm-prompting
category: coding
description: Prompt and structure responses in sakthai-agent-v2's provider-agnostic agent loop — system-prompt assembly, the tool-result feedback cycle, chain-of-thought, and tool-shaped structured outputs. Use when editing the loop, tuning the system prompt, or designing tool/output schemas.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - llm
      - prompting
      - agent-loop
      - anthropic
    related_skills:
      - sakthai-coding-mcp-tools
      - sakthai-coding-testing
      - sakthai-personal
---

# sakthai-coding-llm-prompting

`sakthai-agent-v2`'s `agent/loop.py` is a **provider-agnostic, tool-using loop**:
it assembles a system prompt, exposes the tool registry, and drives a backend
(Anthropic, Gemini, or any OpenAI-compatible/Ollama endpoint). This skill is the
prompting playbook for that loop — re-derived for v2's real seams, not generic
prompt advice.

## When to use this skill

- Editing `_build_system` or what goes into the system prompt
- Designing a tool schema so the model calls it reliably (see also
  [[sakthai-coding-mcp-tools]])
- Eliciting step-by-step reasoning or consistent outputs
- Getting structured/parseable results out of a turn
- Debugging a loop that stops early, loops forever, or ignores memory

## How the loop prompts

`_build_system(store, skills_block, fast)` injects **`store.render_prompt_block()`**
— the live memory block — into the system prompt every turn. That is the
mechanism by which persisted facts/observations steer behavior; honor it silently
rather than re-asking the user (mirrors [[sakthai-personal]]).

The loop is a feedback cycle: model emits tool-use → `_execute_tool` runs it →
the result is fed back as a `tool_result` block → repeat until a **terminal
stop** (`end_turn`, `max_tokens`, `stop_sequence`, `refusal`). Tool *errors* are
returned to the model as `isError` content, not raised — the model can recover.

Implications for prompting:

- **Put durable behavior in the system prompt, transient task detail in the user
  turn.** The memory block is already systemic; don't duplicate it per message.
- **Make tools the structured-output mechanism.** A well-described tool schema
  (required fields, typed properties) is how you get reliable parsing in this
  loop — the model fills the schema, the handler validates. Prefer that over
  parsing free-text JSON out of prose.

## Patterns

### System-prompt design

State role, available capabilities, and constraints up front. v2's base prompt
already names the surfaces (memory, `read_file`, opt-in `run_command`). When
extending it: be explicit about output format and safety limits; keep it stable
so prompt-cache and behavior stay predictable.

### Chain-of-thought, when it earns its tokens

For multi-step reasoning, ask for explicit steps ("work through this step by
step") before the answer/tool call. Use sparingly — it costs output tokens and
the [[sakthai-understand-caveman]] economics still apply; reserve CoT for tasks
where a wrong first step is expensive.

### Few-shot via demonstrations

When a task has a precise output shape, one or two input→output examples in the
prompt beat a paragraph of instructions. Keep examples minimal and
representative; they consume context every turn.

### Structured outputs

Prefer a tool with a strict `input_schema` over "return JSON". If you genuinely
need a one-shot structured response (no tool round-trip), constrain tightly and
validate on receipt — never trust unparsed model JSON.

## Model selection

Default to the latest, most capable Claude models. IDs: **Opus 4.8**
`claude-opus-4-8`, **Sonnet 4.6** `claude-sonnet-4-6`, **Haiku 4.5**
`claude-haiku-4-5-20251001`, **Fable 5** `claude-fable-5`. The loop resolves the
client via `auth.py` (`ANTHROPIC_API_KEY` → `ANTHROPIC_AUTH_TOKEN` → Claude CLI
OAuth) — always go through `resolve_anthropic_client()`, never construct a client
inline. Pick the tier by task: Opus for hard reasoning, Sonnet/Haiku for cheap
high-volume tool turns.

## Testing prompts and the loop

`run_agent` takes injectable `client` and `store`, so tests never touch the
network (see [[sakthai-coding-testing]]). Drive prompting behavior with a stub
client returning canned turns; assert on dispatched tool calls and the session
log written to `~/.sakthai/sessions/`, not on a live model.

## Common pitfalls

1. **Don't re-ask what memory already holds** — the render block is in the system
   prompt; read it, honor it silently.
2. **Don't parse JSON out of prose** — define a tool schema and let the model fill
   it; validate in the handler.
3. **Don't bloat the system prompt per turn** — durable instructions are systemic;
   transient detail belongs in the user message.
4. **Don't hard-code a client or model string in the loop** — resolve via
   `auth.py`; keep the loop provider-agnostic.
5. **Don't assume `end_turn`** — handle every terminal stop (`max_tokens`,
   `refusal`, …) so the loop terminates cleanly.
