# Claude Code CLI & Tmux Integration Reference Guide

This reference provides the comprehensive CLI subcommand manual, flag specifications, interactive tmux dialog handlers, JSON streaming schemas, and permissions settings for Claude Code.

---

## 1. Prerequisites & Health Checks

- **Install**: `npm install -g @anthropic-ai/claude-code`
- **Auth**: `claude auth login` (or `--console` for API billing, `--sso` for Enterprise)
- **Status**: `claude auth status` (returns JSON) or `claude auth status --text`
- **Doctor / Health**: `claude doctor`
- **Version**: `claude --version`

---

## 2. Orchestration Modes

### Mode 1: Non-Interactive Print Mode (`-p`)
```bash
claude -p "Analyze src/auth.py for security vulnerabilities" \
  --output-format json \
  --allowedTools "Read,Edit" \
  --max-turns 10
```
- Skips all interactive prompts and workspace trust dialogs.
- Emits structured JSON or streaming tokens.
- Ideal for automated scripts, CI/CD, and piped context (`cat diff.txt | claude -p ...`).

### Mode 2: Multi-Turn Interactive REPL (via Tmux)
```bash
tmux new-session -d -s claude-session -x 140 -y 40
tmux send-keys -t claude-session "claude" Enter
sleep 4 && tmux send-keys -t claude-session Enter  # Trust dialog acceptance
```

---

## 3. PTY Dialog Handling Rules

When running interactively:
1. **Workspace Trust Dialog**: Press `Enter` (Default is "Yes, I trust this folder").
2. **Permissions Bypass Dialog (`--dangerously-skip-permissions`)**: Send `Down` followed by `Enter` (default is "No, exit"; option 2 is "Yes, I accept"):
   ```bash
   tmux send-keys -t claude-session Down && sleep 0.3 && tmux send-keys -t claude-session Enter
   ```

---

## 4. Key CLI Flags Summary

| Category | Flag | Purpose |
|:---|:---|:---|
| **Execution** | `-p, --print` | Run one-shot and exit |
| **Session** | `-c, --continue` | Resume latest session in directory |
| **Session** | `-r, --resume <id>` | Resume session by ID |
| **Safety** | `--allowedTools <tools>` | Comma-separated whitelist (`Read,Edit,Bash(git *)`) |
| **Safety** | `--permission-mode <m>` | `default`, `acceptEdits`, `auto`, `bypassPermissions` |
| **Cost** | `--max-turns <n>` | Bound agentic loop iterations |
| **Cost** | `--max-budget-usd <n>` | Cap API dollar spend |
| **Format** | `--output-format <fmt>` | `text`, `json`, `stream-json` |
| **Schema** | `--json-schema <spec>` | Enforce structured output schema validation |
| **Context** | `--bare` | Minimal startup (no plugins, hooks, or CLAUDE.md) |

---

## 5. Structured JSON Output Schema

```json
{
  "type": "result",
  "subtype": "success",
  "result": "Analysis text...",
  "session_id": "75e2167f-...",
  "num_turns": 3,
  "total_cost_usd": 0.078,
  "duration_ms": 10276,
  "stop_reason": "end_turn",
  "terminal_reason": "completed",
  "usage": { "input_tokens": 5, "output_tokens": 603 }
}
```
