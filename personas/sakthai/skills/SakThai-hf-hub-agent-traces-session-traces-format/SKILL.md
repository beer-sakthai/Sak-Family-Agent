---
name: SakThai-hf-hub-agent-traces-session-traces-format
description: "name: SakThai-hf-hub-agent-traces-session-traces-format"
---

# HF Hub Agent Traces & Session Traces Format

## Overview
The Hugging Face Hub natively supports **Agent Traces** from Claude Code, Codex, and Pi Agent — uploading raw JSONL session files to Datasets or Storage Buckets renders them in a dedicated trace viewer on the Hub. For custom agent harnesses, the **Session Trace Simple Format (STS-Format)** lets any agent produce renderable traces with a simple JSONL schema supporting tool calls, reasoning blocks, and multi-turn conversations.

**Zero-cost:** Uploading and viewing traces on the Hub is free. Use HF Datasets (free, forever) or Storage Buckets (free tier, 5GB) as the storage backend. No GPU, no paid plan needed.

## Quick Start (Upload Existing Traces)
```bash
# Find your agent's session files
# Claude Code: ~/.claude/projects
# Codex: ~/.codex/sessions
# Pi: ~/.pi/agent/sessions

# Upload to a Dataset
hf auth login
hf skills add
hf upload <username>/<dataset-name> ~/.codex/sessions . --repo-type dataset

# Or sync to a Bucket (auto-updates)
hf buckets sync ~/.codex/sessions hf://buckets/<username>/<bucket-name>/codex
```

## STS-Format for Custom Harnesses
Write `.jsonl` files with:
- **Line 1:** Session header `{"type":"session","harness":"my-agent","id":"unique-id","name":"optional title"}`
- **Lines 2+:** Messages `{"type":"message","message":{"role":"user|assistant|system|tool","content":"...","toolCalls":[...],"toolCallId":"..."}}`

Tool calls link via `toolCalls[].id` ↔ `toolCallId`. Reasoning shown via `reasoningContent` field.

## Key Features
- **Native support:** Claude Code, Codex, Pi — zero modification needed
- **Custom harnesses:** Any agent can emit STS-Format for the trace viewer
- **Tool call linking:** `toolCallId` stitches tool results to their calls
- **Reasoning blocks:** `reasoningContent` renders as separate thinking blocks
- **Dual storage:** Datasets (Data Studio) or Buckets (direct file open)
- **Auto-sync:** `hf buckets sync` keeps traces updated as new sessions land

See `references/hf-learnings.md` for complete format specification, harness integration guide, security best practices, and zero-cost patterns.
