# HF Learnings — Agent Traces & Session Traces Format (STS-Format)

## 2026-07-25: hf-hub-agent-traces-session-traces-format — Hugging Face Hub Agent Traces Ecosystem & Session Trace Simple Format (Topic #382)

### Summary
Deep dive into the Hugging Face Hub's **Agent Traces** ecosystem — a native trace viewer that renders agent/chat sessions from Claude Code, Codex, Pi Agent, and custom harnesses. The **Session Trace Simple Format (STS-Format)** defines a JSONL schema for any agent to produce Hub-renderable traces, supporting tool calls (`toolCalls`/`toolCallId` linking), reasoning blocks (`reasoningContent`), and multi-turn conversations. Traces can be stored in Datasets (Data Studio integration) or Storage Buckets (direct `.jsonl` open), with `hf buckets sync` for auto-updating.

### Key Findings

#### 1. Supported Agents (Native)

| Agent | Local Session Directory | Format | Auto-Detection |
|-------|------------------------|--------|----------------|
| **Claude Code** | `~/.claude/projects` | Native JSONL | Yes (out of box) |
| **Codex** | `~/.codex/sessions` | Native JSONL | Yes (out of box) |
| **Pi Agent** | `~/.pi/agent/sessions` | Pi session format | Yes (out of box) |

- **No conversion needed** — upload raw `.jsonl` files from these directories directly
- **Public example**: [`TeichAI/DeepSeek-v4-Pro-Agent`](https://huggingface.co/datasets/TeichAI/DeepSeek-v4-Pro-Agent) dataset shows the trace viewer in action
- **Discovery**: Browse datasets tagged with [`format:agent-traces`](https://huggingface.co/datasets?format=format%3Aagent-traces)

#### 2. Session Trace Simple Format (STS-Format)

The STS-Format is a **JSONL file** (one JSON object per line) consisting of:

**Line 1 — Session Header:**
```json
{ "type": "session", "harness": "my-agent", "id": "b1a2c3", "name": "Implementing a new API" }
```

| Field | Required | Notes |
|-------|----------|-------|
| `type` | yes | must be `"session"` |
| `harness` | yes | **identifies the agent harness** — determines renderer, icon, label |
| `id` | yes | unique session identifier |
| `name` | no | human-readable title |
| `…` | no | any extra metadata allowed, ignored by viewer |

**Lines 2+ — Messages:**
```json
{ "type": "message", "message": { "role": "assistant", "content": "…" } }
```

| Message field | Required | Notes |
|--------------|----------|-------|
| `role` | yes | `"user"` · `"assistant"` · `"system"` · `"tool"` |
| `content` | yes | text content (may be empty for tool calls) |
| `reasoningContent` | no | model reasoning, shown as a separate thinking block in the viewer |
| `toolCalls` | no | assistant tool calls: `[{ "id", "function": { "name", "arguments" } }]` (`arguments` is a JSON string) |
| `toolCallId` | no | on `role: "tool"` messages, links the result to the `toolCalls[].id` it answers |
| `timestamp` | no | epoch milliseconds |
| `model` | no | model name |

**Complete example:**
```jsonl
{"type":"session","harness":"my-agent","id":"abc123","name":"what time is it"}
{"type":"message","message":{"role":"user","content":"what time is it?"}}
{"type":"message","message":{"role":"assistant","content":"","toolCalls":[{"id":"t1","function":{"name":"get_time","arguments":"{}"}}]}}
{"type":"message","message":{"role":"tool","toolCallId":"t1","content":"2026-07-01T15:00:00Z"}}
{"type":"message","message":{"role":"assistant","content":"it is 15:00 UTC"}}
```

#### 3. Harness Registration

- `harness` field in the session header is the **key identifier** for rendering
- Currently recognized harness IDs: `llama.app`
- **Custom harness registration**: Ping the HF team to add an icon and label for your harness
- Alternative: Pi's session format is also supported natively — just add a `harness` field to Pi's session-header line

#### 4. Upload Methods

**Method A: Datasets** (best for Data Studio — browse, filter, search traces)
```bash
hf upload <username>/<dataset-name> ~/.codex/sessions . --repo-type dataset
```
- Traces appear in Data Studio where each row = one session
- Click a row to open the trace viewer with full timeline

**Method B: Storage Buckets** (best for continuous syncing)
```bash
hf buckets sync ~/.codex/sessions hf://buckets/<username>/<bucket-name>/codex
```
- Navigate to the `.jsonl` file and open it directly in the trace viewer
- `hf sync` is an alias for `hf buckets sync`
- Buckets auto-detect new/changed files on sync

#### 5. Security Considerations

- **Trace files can contain**: prompts, tool inputs, command output, local paths, screenshots, secrets, private code, personal data
- **Before publishing**: Review and redact sensitive content manually
- **Alternative**: Keep the dataset/bucket private if unsure
- **Pi Agent tool**: `pi-share-hf` helps collect project sessions, redact known secrets, run TruffleHog + LLM review, and upload only passing sessions
- **Ask your agent**: Point your coding agent at the session directory and tell it to upload — it can handle the redaction and upload workflow

#### 6. STS-Format vs Pi Session Format

| Aspect | STS-Format | Pi Session Format |
|--------|-----------|-------------------|
| Schema | Simple `session` + `message` lines | Pi's own format (`session-format.md`) |
| Custom harness | Add `harness` field to header | Add `harness` field to Pi's header line |
| Hub support | Native | Native (already supported) |
| Tool call linking | `toolCalls[]` + `toolCallId` | Pi's own tool call structure |
| Reasoning | `reasoningContent` field | Pi's own reasoning field |

#### 7. Existing Dataset Tags

- Browse agent trace datasets: `https://huggingface.co/datasets?format=format%3Aagent-traces`
- Datasets Server detects `format:agent-traces` from the directory/file structure
- Datasets with agent traces get a special badge/indicator in the Hub UI

### Zero-Cost Patterns

1. **HF Datasets**: Free, unlimited storage for datasets including agent traces
2. **Storage Buckets**: Free tier includes 5GB storage — enough for thousands of session files
3. **`hf` CLI**: Free CLI tool for uploads and bucket syncs
4. **`hf skills add`**: Free skill installation for HF CLI in your agent
5. **Automated uploads**: Ask your coding agent itself to upload traces — no manual work
6. **Security**: Private datasets/buckets are free — no cost to keep traces private

### Skill Created
`hf-hub-agent-traces-session-traces-format/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete format specification, supported agents, upload patterns, security best practices, and zero-cost patterns.

### Sources
- https://huggingface.co/docs/hub/en/agent-traces — Agent Traces overview
- https://huggingface.co/docs/hub/en/session-traces-format — Session Traces Format (STS-Format) specification
- https://huggingface.co/datasets/TeichAI/DeepSeek-v4-Pro-Agent — Public example dataset with traces
- https://huggingface.co/datasets?format=format%3Aagent-traces — Browse all agent trace datasets
