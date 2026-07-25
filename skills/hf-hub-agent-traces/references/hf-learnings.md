# HF Learnings: hf-hub-agent-traces

**Date:** 2026-07-25
**Topic:** Comprehensive deep-dive into the Hugging Face Agent Traces ecosystem — uploading, viewing, standardizing, and registering agent sessions from Claude Code, Codex, Pi Agent, and custom harnesses using the Session Trace Simple Format (STS-Format) and the HF Hub trace viewer.

## Summary

HF Agent Traces is a first-class feature on the Hub that lets users upload agent/chat sessions from coding agents (Claude Code, Codex, Pi Agent) as JSONL files to Datasets or Storage Buckets, then view them in a dedicated trace viewer that renders session timelines, prompts, assistant messages, tool calls, and results. The Session Trace Simple Format (STS-Format) is an open standard for custom harnesses. A public harness registry in the `@huggingface/tasks` package attributes traffic by name and enables branded rendering.

---

## 1. Supported Agents (Out of the Box)

Three coding agents have native session directory support:

| Agent | Local Session Directory | Upload Method |
|-------|------------------------|---------------|
| **Claude Code** | `~/.claude/projects/` | Dataset or Bucket |
| **Codex** | `~/.codex/sessions/` | Dataset or Bucket |
| **Pi Agent** | `~/.pi/agent/sessions/` | Dataset or Bucket (also `pi-share-hf` helper) |

Trace files from these agents are supported without any conversion or modification.

---

## 2. Upload Methods

### 2.1 Via Datasets

```bash
# Install hf CLI (standalone installer)
curl -LsSf https://hf.co/cli/install.sh | bash
hf auth login

# Upload sessions to a dataset
hf upload <username>/<dataset-name> ~/.codex/sessions . --repo-type dataset
```

### 2.2 Via Storage Buckets (recommended for ongoing sync)

```bash
# Sync (one-way) — keeps updating as new sessions land
hf buckets sync ~/.codex/sessions hf://buckets/<username>/<bucket-name>/codex

# Shorter alias
hf sync ~/.codex/sessions hf://buckets/<username>/<bucket-name>/codex
```

Buckets are especially useful for continuous syncing — each new session written to the local directory is automatically reflected.

### 2.3 Using the HF CLI Skill

For coding agents to run `hf` commands themselves:

```bash
hf skills add
```

This installs the Hugging Face CLI Skill, giving the agent the ability to run `hf upload`, `hf sync`, and other CLI commands.

### 2.4 Optimized Upload for Pi Agent

Pi Agent has a dedicated helper tool `pi-share-hf` that:
- Collects project sessions
- Redacts known secrets
- Runs TruffleHog and LLM-based review
- Uploads only sessions that pass all checks

---

## 3. Viewing Traces

### 3.1 Dataset Traces

1. Navigate to the dataset on the Hub
2. Open **Data Studio**
3. Click any row to open the trace viewer

### 3.2 Bucket Traces

1. Navigate to the `.jsonl` file in the Storage Bucket
2. Open the file directly — the trace viewer renders it inline

### 3.3 Trace Viewer Features

The trace viewer shows:
- **Session timeline** — chronological view of the entire session
- **Prompts** — user and system messages with full content
- **Assistant messages** — model responses, including `reasoningContent` as a separate thinking block
- **Tool calls** — each function call with `id`, `name`, and `arguments`
- **Tool results** — stitched next to the call that produced them (matched by `toolCallId`)
- **Model name** — which model handled the message
- **Timestamps** — epoch milliseconds for each message

### 3.4 Public Example

**TeichAI/DeepSeek-v4-Pro-Agent** is a public example showing traces in action. Browse more datasets tagged with `traces`.

---

## 4. Session Trace Simple Format (STS-Format)

The STS-Format is the open standard for custom harnesses. Files are JSONL (one JSON object per line).

### 4.1 Session Header (First Line)

```json
{
  "type": "session",
  "harness": "my-agent",
  "id": "b1a2c3",
  "name": "Implementing a new API"
}
```

**Fields:**
| Field | Required | Notes |
|-------|----------|-------|
| `type` | yes | Must be `"session"` |
| `harness` | yes | The harness id — tells the Hub which renderer, icon, and label to use |
| `id` | yes | Unique session id |
| `name` | no | Human-readable title |
| `…` | no | Any extra metadata is allowed and ignored |

**Currently recognized harness ids:** `llama.app`.

Adding a new harness is straightforward: open a PR to `@huggingface/tasks` (see §5).

### 4.2 Messages (Every Following Line)

Each line is a message envelope:

```json
{
  "type": "message",
  "message": {
    "role": "assistant",
    "content": "…"
  }
}
```

**Message fields:**
| Field | Required | Notes |
|-------|----------|-------|
| `role` | yes | `"user"` · `"assistant"` · `"system"` · `"tool"` |
| `content` | yes | Text (may be empty) |
| `reasoningContent` | no | Model reasoning, shown as a separate thinking block |
| `toolCalls` | no | Assistant tool calls: `[{ "id", "function": { "name", "arguments" } }]` — `arguments` is a JSON string |
| `toolCallId` | no | On `role: "tool"` messages, links the result to the originating `toolCalls[].id` |
| `timestamp` | no | Epoch milliseconds |
| `model` | no | Model name |

**Tool result stitching:** Messages with `role: "tool"` carrying a `toolCallId` are automatically paired with the call that produced them in the viewer.

### 4.3 Full Example

```json
{"type":"session","harness":"my-agent","id":"abc123","name":"what time is it"}
{"type":"message","message":{"role":"user","content":"what time is it?"}}
{"type":"message","message":{"role":"assistant","content":"","toolCalls":[{"id":"t1","function":{"name":"get_time","arguments":"{}"}}]}}
{"type":"message","message":{"role":"tool","toolCallId":"t1","content":"2026-07-01T15:00:00Z"}}
{"type":"message","message":{"role":"assistant","content":"it is 15:00 UTC"}}
```

### 4.4 Alternative: Pi's Session Format

If adopting STS-Format is not feasible, Pi's existing session format (`session-format.md`) is also supported. Add `harness: "..."` to Pi's session-header line so the Hub can attribute the trace to the correct harness.

---

## 5. Harness Registry

### 5.1 What It Is

A public registry of agent harnesses (coding agents and tools that interact with the Hub) maintained in the `@huggingface/tasks` package at `agent-harnesses.ts`.

### 5.2 Why Register

- **Named attribution:** When `huggingface_hub` detects it is running inside your harness, it reports the harness id via the user agent on all Hub requests
- **Branded trace viewer:** Your sessions render with your icon, label, and name
- **Public dataset:** Your harness appears in the monthly agent usage dataset
- **Unregistered tools** are counted only in the aggregate "unknown" share

### 5.3 How to Register

Open a Pull Request adding an entry to `agent-harnesses.ts`:

```typescript
{
  // harness id (entry key) — lowercased, hyphen-separated
  "my-coding-agent": {
    prettyLabel: "My Coding Agent",       // user-friendly casing
    repoUrl: "https://github.com/org/repo",  // optional: source code
    docsUrl: "https://docs.example.com",     // optional: documentation
    description: "A short description",      // optional: one line
  }
}
```

### 5.4 Detection Strategy

Define how the harness is detected from the environment:

| Method | Configuration |
|--------|--------------|
| **Standard env var** | If your harness sets `AI_AGENT` or `AGENT`, the value is used directly as the identifier — no extra config needed |
| **Custom env var** | Set `envVars` mapping variable names to value patterns: `"*"` (any non-empty value), exact string, or `"prefix*"` for prefix matching |

### 5.5 What Happens After

Once merged:
- `huggingface_hub` traffic (including `hf` CLI) from your harness is attributed by name
- It appears in the agent usage dataset from the next monthly update
- The trace viewer picks up your icon and label

---

## 6. Privacy and Security

**Critical warnings from the official docs:**

> Trace files can include prompts, tool inputs, command output, local paths, screenshots, secrets, private code, and personal data.

**Best practices:**
1. **Review and redact** traces before publishing publicly
2. **Keep the dataset or bucket private** if unsure what's inside
3. For Pi Agent, use `pi-share-hf` which runs automated redaction (known secrets pattern matching + TruffleHog + LLM review)
4. Only sessions that pass all checks are uploaded

---

## 7. Integration with the Broader HF Agent Ecosystem

| HF Agent Feature | Relationship to Agent Traces |
|-----------------|------------------------------|
| **HF MCP Server** | Coding agents (Claude Code, Codex) use MCP to search/access Hub; their sessions can be captured as traces |
| **HF Agent Skills** | Skills give agents task-specific guidance; traces capture how agents used them |
| **HF CLI for Agents** | `hf upload` and `hf sync` are the primary upload mechanisms for traces |
| **Storage Buckets** | Buckets enable continuous sync for trace directories |
| **Data Studio** | Primary viewer for dataset-hosted traces |
| **Session Traces Format** | The standard for custom harness interoperability |

---

## 8. Key API Endpoints and Operations

While agent traces are primarily a CLI-driven workflow, the underlying Hub operations use:

- **Dataset creation/management** via `hf` CLI or Hub API
- **Storage Bucket sync** via `hf buckets sync` (native Xet-backed transport)
- **File rendering** — the trace viewer is automatically activated for `.jsonl` files matching the STS-Format schema when opened in the Hub UI or Data Studio

No special API endpoint is needed — any Dataset or Bucket containing valid STS-Format `.jsonl` files renders as traces automatically.

---

## References

- [HF Hub Docs: Agent Traces](https://huggingface.co/docs/hub/en/agent-traces)
- [HF Hub Docs: Session Traces Format](https://huggingface.co/docs/hub/en/session-traces-format)
- [HF Hub Docs: Agents Overview](https://huggingface.co/docs/hub/en/agents-overview)
- [Agent Harnesses Registry](https://github.com/huggingface/tasks/blob/main/packages/tasks/src/agent-harnesses.ts)
- [HF CLI Install](https://hf.co/cli/install.sh)
- [Public Trace Example: TeichAI/DeepSeek-v4-Pro-Agent](https://huggingface.co/datasets/TeichAI/DeepSeek-v4-Pro-Agent)
- [Pi Agent pi-share-hf](https://huggingface.co/docs/hub/en/agent-traces#find-your-traces)
