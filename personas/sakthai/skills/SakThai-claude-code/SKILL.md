---
name: SakThai-claude-code
author: SakThai
license: MIT
description: Delegate coding tasks to Claude Code CLI.
version: 0.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Claude, Coding-Agent, Automation, Code-Review]
---

# Claude Code — Hermes Orchestration

Delegate coding tasks to [Claude Code](https://code.claude.com/docs/en/cli-reference) (Anthropic's autonomous coding agent) through the Hermes `terminal` tool. Supports both one-shot (print mode) and interactive (tmux) sessions.

## When to Use

- You need to review a PR diff for bugs or security issues.
- A complex refactor spans multiple files and needs subagent coordination.
- You want to generate a PR description from recent commits.
- You need structured JSON output from a code analysis task.
- CI automation that runs Claude Code in bare mode.

## Prerequisites

- `npm install -g @anthropic-ai/claude-code` (v2.x+).
- Run `claude` once to authenticate (browser OAuth, or `claude auth login --console` for API key billing).
- Verify with `claude auth status --text`.
- The `tmux` package for interactive sessions (`apt install tmux` on Linux).

## How to Run

Two modes:

- **Print mode** (`-p`): one-shot task, returns result, exits. No PTY needed.
- **Interactive mode** (tmux): multi-turn conversation with follow-ups.

## Quick Reference

```bash
# One-shot code review
claude -p 'Review this diff for bugs' --max-turns 1

# One-shot with JSON output
claude -p 'List all functions in src/' --output-format json --max-turns 5

# Interactive REPL
claude "Refactor the auth module"

# Continue last session
claude -c

# Bare mode for CI (fastest startup)
claude --bare -p 'Run tests' --allowedTools 'Read,Bash' --max-turns 10
```

## Procedure

### 1. Print Mode (One-Shot)

Pass the task with `-p` and a turn limit:

```
terminal(command="claude -p 'Add error handling to src/api.ts' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

Best for: fixing a bug, reviewing a diff, generating a summary, CI/CD automation.

### 2. Structured JSON Output

Request JSON for programmatic consumption:

```
terminal(command="claude -p 'Analyze security.ts for vulnerabilities' --output-format json --max-turns 5", workdir="/project", timeout=120)
```

The JSON result includes `session_id`, `num_turns`, `total_cost_usd`, and the analysis under `result`.

### 3. Interactive Mode via tmux

For multi-turn tasks that need follow-up prompts:

```
# Start session
terminal(command="tmux new-session -d -s claude-session -x 140 -y 40")

# Launch Claude Code inside it
terminal(command="tmux send-keys -t claude-session 'cd /path/to/project && claude' Enter")

# Handle workspace trust dialog (press Enter for default "Yes")
terminal(command="sleep 5 && tmux send-keys -t claude-session Enter")

# Send the task
terminal(command="sleep 3 && tmux send-keys -t claude-session 'Refactor auth to use JWT' Enter")

# Wait for work, then capture output
terminal(command="sleep 20 && tmux capture-pane -t claude-session -p -S -40")

# Exit when done
terminal(command="tmux send-keys -t claude-session '/exit' Enter")
```

**Dialog handling:** The first launch shows a workspace trust prompt. The default is "Yes, I trust this folder" — send `Enter` to accept. When using `--dangerously-skip-permissions`, a second dialog requires `Down` then `Enter`.

### 4. PR Review Pattern

```
# Quick review from diff
terminal(command="cd /repo && git diff main...branch | claude -p 'Review for bugs, security, style' --max-turns 1", timeout=60)

# Deep review from PR number
terminal(command="claude -p 'Review PR fully' --from-pr 42 --max-turns 10", workdir="/repo", timeout=120)
```

### 5. Session Continuation

```
# Save session ID
terminal(command="claude -p 'Start refactoring DB' --output-format json --max-turns 10 > /tmp/session.json", workdir="/project", timeout=180)

# Resume with that ID
terminal(command="claude -p 'Add pooling' --resume $(cat /tmp/session.json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"session_id\"])') --max-turns 5", workdir="/project", timeout=120)
```

## Pitfalls

- **Print mode exits after `--max-turns`.** Increase the limit for large tasks.
- **Interactive dialogs.** The workspace trust prompt appears once per directory. The permissions dialog appears every time `--dangerously-skip-permissions` is used.
- **`--dangerously-skip-permissions` bypasses safety prompts.** Only use in trusted CI environments. For normal work, prefer `--permission-mode acceptEdits`.
- **Cost control.** Set `--max-budget-usd` for automation scripts. Claude Code bills per turn.
- **Bare mode skips CLAUDE.md.** Use `--append-system-prompt` to inject context in CI.

## Verification

Confirm Claude Code is installed and authenticated:

```
terminal(command="claude --version && claude auth status --text", timeout=10)
```
