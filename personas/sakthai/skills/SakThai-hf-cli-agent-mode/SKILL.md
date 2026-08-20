---
name: SakThai-hf-cli-agent-mode
description: 'HF hf CLI agent-optimized mode: auto-detection, dual-rendering, skill system, benchmarking.'
---

# HF hf CLI Agent-Optimized Mode

The `hf` CLI (v1.9.0+) auto-detects when a coding agent is driving it and switches to agent-optimized output: TSV instead of tables, no ANSI/truncation, ISO timestamps, complete tags, structured error messages. Ships an auto-generated skill for CLI reference. Benchmarked at 1.3–6× lower token cost vs curl/SDK.

## When to Use

- Agent (Claude Code, Codex, Cursor, OpenCode) needs to interact with Hugging Face Hub
- Comparing token efficiency of CLI vs REST API vs Python SDK
- Understanding how to make CLI tools agent-friendly
- Configuring agent skills for Hugging Face Hub access

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent auto-detection** | Detects CLAUDECODE, CODEX_SANDBOX, AI_AGENT, CURSOR env vars |
| **Dual rendering** | Same command → human (table/color) or agent (TSV/full) output |
| **Skill system** | Auto-generated from live command tree, one line per command |
| **Safe retry** | `--exist-ok`, `--yes`, `--dry-run` for idempotent operations |
| **Next-command hints** | Stderr hints with pre-filled IDs point to next action |
| **Composable output** | `-q` (one id per line), `--json`, `--quiet` for piping |
| **Resource+verb tree** | `hf <resource> <verb>` with aliases (ls/list, rm/remove) |

## Agent Detection

`hf` reads these environment variables:

- `CLAUDECODE` / `CLAUDE_CODE` — Claude Code
- `CODEX_SANDBOX` — Codex
- `CURSOR` — Cursor
- `AI_AGENT` — universal agent signal
- `GEMINI` — Gemini
- `PI` — Pi

When detected, output switches automatically: TSV format, no truncation, no ANSI, ISO 8601 timestamps, all tags listed. Overridable with `--format human|agent|json|quiet`.

## Skill Setup

```bash
# Install for Codex, Cursor, OpenCode, Pi
hf skills add

# Include Claude Code
hf skills add --claude

# Preview the skill content
hf skills preview
```

The skill is auto-generated from the live command tree on each `hf` release. Effect: ~30% fewer tool calls per task (10.4→6.9 on Sonnet, 10.1→7.3 on GPT-5.5).

## Benchmark Results

Tested on 18 Hub tasks × 3 tool configs × 10 reps × 2 agents (~1,000 graded runs):

| Agent | Tool | Success | Token Ratio |
|-------|------|---------|-------------|
| Claude Code (Sonnet 4.6) | `hf` CLI | **94%** | baseline |
|  | curl/Python SDK | 84% | **1.3–1.6×** |
| Codex (GPT-5.5) | `hf` CLI | **93%** | baseline |
|  | curl/Python SDK | 92% | **1.6–1.8×** |

Complex multi-step tasks: 2.4–6× token cost without CLI. Simple reads: near parity or cheaper via curl/SDK.

## References

- [Blog: Designing the hf CLI as an agent-optimized way to work with the Hub](https://huggingface.co/blog/hf-cli-for-agents)
- [hf CLI guide](https://huggingface.co/docs/huggingface_hub/guides/cli)
- [Register agent harness](https://huggingface.co/docs/hub/agents-overview#register-your-agent-harness)
- Source: `hf skills preview` output, live command tree
