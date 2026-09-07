---
name: SakThai-hf-agent-traces-datasets
description: "How to consume, convert, and inspect HF Agent Traces datasets in the wild — Pi-format trace corpora, row-level merged JSONL, and conversion mapping. Case study: Glint-Research/Fable-5-traces."
---

# HF Agent Traces Datasets (Pi format) — consumption & conversion

Reference for working with HF Hub **Agent Traces datasets** — corpora of agent sessions (Claude Code, Pi Agent, Codex, etc.) published in the Hub-supported agent-traces format. Covers: how these datasets are structured, how to load them, and how the row→trace conversion mapping works.

## Trigger

- A trending/notable dataset tagged `agent-traces`, `pi-agent`, or `claude-code` shows up on the Hub.
- You need to load, inspect, or convert agent trace corpora for SFT/distillation or tool-use policy research.

## Case study: Glint-Research/Fable-5-traces (tracked 2026-07-31)

A compact, high-signal corpus of **Fable 5** (`claude-fable-5`) coding-agent traces converted into Hugging Face Agent Traces / **Pi-compatible sessions**. 4,665 rows, 60 source sessions, 3,799 tool-use rows (81.44%), 866 assistant text rows. Median CoT 2,365 chars. AGPL-3.0. 686 likes / 50.9K downloads in ~1 month (lastModified 2026-06-29).

**Why it trended:** agent-traces datasets are the new hot category — they power reasoning/action distillation and tool-use policy learning. This one pairs the full Pi Agent Trace viewer experience (Data Studio) with a flat merged JSONL for SFT.

### Dataset anatomy (three surfaces)

| Surface | Location | Purpose |
|---|---|---|
| Agent Trace view | `pi-traces/*.jsonl` via config `pi_agent/train` | Pi-style traces for Hub Agent Traces viewer / Data Studio; `harness: "pi"` |
| Merged training rows | `fable5_cot_merged.jsonl` | Flat JSONL for SFT; fields: `uid, source_file, session, model, context, cot, output_type, output, completion, origin` |
| Raw logs | `/claude/` | Original session-level material for archival / custom converters |

### Verified Pi trace row schema (datasets-server)

Row keys: `harness, session_id, prompt, messages, tools, metadata, sent_at, num_user_messages, num_tool_calls, trace, file_path`.

- `harness: "pi"` — the Pi Agent harness identifier
- `messages[]` — user: `{role, content}`; assistant: `{role, content, reasoning_content, tool_calls}` (reasoning = CoT, tool_calls = structured tool invocations)
- `session_id` — synthetic stable UUID derived from row UID; cwd normalized to `/workspace`

### Row → Pi trace mapping (the conversion recipe)

Each merged row becomes one Pi-style trace file:
- `session` — synthetic stable UUID from row UID
- `model_change` — records the model id (e.g. `claude-fable-5`)
- `thinking_level_change` — `high` for viewer grouping
- user `message` — the merged row `context` (prompt + prior tool/result transcript)
- assistant `message` — a `thinking` item from `cot`, then either `text` or `toolCall` from `output`

### Loading patterns

```python
# Stream Pi agent traces
from datasets import load_dataset
ds = load_dataset("Glint-Research/Fable-5-traces", "pi_agent", split="train", streaming=True)
row = next(iter(ds))
print(row["harness"], row["session_id"], row["messages"][-1], row["file_path"])

# Load flat merged JSONL for training
merged = load_dataset("json", data_files="https://huggingface.co/datasets/Glint-Research/Fable-5-traces/resolve/main/fable5_cot_merged.jsonl", split="train")
print(merged.column_names, merged[0]["output_type"])
```

## Pitfalls

- **Don't assume rows = standalone runs.** Converted traces are a row-level projection of merged session data, not original Pi runs — faithful for visualization/distillation, not for session-continuity claims.
- **Context truncation.** Many merged `context` values are intentionally truncated (fixed upper bound); use raw `/claude/` files when full session continuity matters.
- **AGPL-3.0** — check compatibility before using in commercial/closed-source training pipelines.
- **Not a benchmark.** Agent-telemetry datasets are not hidden-eval sets; never use them alone to claim model capability.
- **Tool outputs not sanitized.** Treat as agent telemetry: may contain local paths, terminal output, work logs. Redact before redistributing.
- Dataset viewer can be pointed at traces (not the flat table) so the Hub renders trajectories — check `configs[].data_files` paths for `*.jsonl` globs like `pi-traces/*.jsonl` to find the trace config.

## Related

- `SakThai-hf-hub-agent-traces` — STS-Format ecosystem, upload/view/redact tooling
- `SakThai-hf-hub-agent-traces-session-traces-format` — session trace format details
- HF docs: https://huggingface.co/docs/hub/agent-traces
- External viewer example: tracehouse.ai
- Reference full-log source: `cfahlgren1/Fable-5-traces`
