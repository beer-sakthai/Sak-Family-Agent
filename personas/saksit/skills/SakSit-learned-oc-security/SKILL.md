---
name: SakSit-learned-oc-security
category: social-media
description: OpenClaw security and privacy research hub.
version: 1.0.0
author: SakSit
tags:
- openclaw
- security
- privacy
- research
- knowledge
---

# Learned: OpenClaw Session & Memory Data Privacy

## Topic
**OpenClaw Session & Memory Data Lifecycle** — what data OpenClaw persists about users, conversations, and agent state; retention/privacy controls; exposure surfaces.

## Why This Matters for SakSit
SakSit runs on OpenClaw's data model. Understanding what OpenClaw stores, where, and how to manage its lifecycle is essential for advising Beer on privacy hygiene — especially since the "own your data" promise is a core differentiator for the House of Sak story.

## Findings

### What OpenClaw Persists

| Data Type | Location | Contents |
|-----------|----------|----------|
| **Session transcripts** | `$OC/` via session manager (SQLite-backed) | Full conversation history, tool calls, model responses, media references |
| **Memory files** | `$OC/workspace/MEMORY.md`, `memory/*.md` | Learned facts, user preferences, agent instructions |
| **Gateway logs** | `/tmp/openclaw/openclaw-YYYY-MM-DD.log` (JSONL) | Logged events including message metadata, tool invocations, errors |
| **Credential store** | `agents/<agentId>/agent/openclaw-agent.sqlite` | API keys, tokens, OAuth refresh tokens |
| **Config** | `$OC/openclaw.json` | All configuration including provider keys, channel auth |
| **Skill/workspace files** | `$OC/workspace/` | SKILL.md files, AGENTS.md, user workspace content |
| **Cron job files** | `$OC/cron/` | Scheduled task configs |
| **Git backup (optional)** | Remote private repo | Mirrors `$OC/` minus `media/`, `logs/`, `completions/`, `canvas/`, `*.bak` |

### Retention & Pruning

- **Log files**: rotated daily, pruned after 24 hours, max 100 MB per file, up to 5 archives
- **Sessions**: compaction/pruning logic exists but no user-facing "purge all" command (manual deletion of session data)
- **Memory**: no automatic expiry — persists until manually edited or deleted
- **Git backup**: cumulative forever unless manually squashed
- **SlowMist guide adds**: `chattr +i` audit scripts, nightly hash baselines, but no data lifecycle policy

### Privacy Controls Available

- **Log redaction**: `logging.redactPatterns` in config — regex-based masking of sensitive values before they hit disk
- **Console log styles**: JSON, compact, pretty — affects display only
- **OTLP export**: optional, no raw prompts/responses exported (bounded metadata only: byte size, timing, tool names)
- **Allowlists**: `channels.*.allowFrom` restricts who can trigger the agent
- **Session isolation**: multi-agent routing keeps sessions per-agent/per-workspace
- **`tools.fs.workspaceOnly`**: restricts file tool paths to workspace directory (not a privacy feature per se, but limits scope)

### What the SlowMist Guide Misses

The SlowMist guide focuses on **operational security** (prevent theft, detect tampering, backup recovery) but does **not** address:

1. **Data lifecycle policy** — no guidance on session data retention, archival, or purge
2. **PII management** — no workflow for finding/redacting PII across session history and logs beyond the DLP scan (which only checks for crypto private keys)
3. **Git backup privacy** — workspace backups include MEMORY.md and logs that may contain sensitive personal data; no encryption guidance for the backup repository
4. **Transparency** — no inventory of what data leaves the machine (model API calls send prompt text, OTLP sends bounded metadata)
5. **Right-to-deletion** — no documented workflow for users to request full data deletion

### Recommendations for Beer's Setup

1. **Configure `logging.redactPatterns`** with patterns for email, phone, address, and any PII Beer handles
2. **Set `logging.level` to `warn`** in production to minimize disk exposure
3. **Use a private, encrypted Git repo** for brain backup (enable repo-level encryption or use a service like Keybase)
4. **Periodically prune old sessions** via SQLite or workspace cleanup
5. **Add PII scanning to nightly audit** (beyond crypto-key DLP — check for phone/email patterns in memory/transcripts)
6. **Document what data goes to model providers** in Beer's privacy narrative — this is core to the "own your data" promise

## Source References

- OpenClaw SECURITY.md — trust model, logging, session boundaries (https://github.com/openclaw/openclaw/blob/main/SECURITY.md)
- OpenClaw logging.md — log format, retention, redaction (https://github.com/openclaw/openclaw/blob/main/docs/logging.md)
- SlowMist OpenClaw Security Practice Guide v2.7 (https://github.com/slowmist/openclaw-security-practice-guide)
- OpenClaw agent-runtime-architecture.md — session persistence, manifests (https://github.com/openclaw/openclaw/blob/main/docs/agent-runtime-architecture.md)
- OpenClaw docs/index.md — "own your data" promise (https://openclaw.ai)
