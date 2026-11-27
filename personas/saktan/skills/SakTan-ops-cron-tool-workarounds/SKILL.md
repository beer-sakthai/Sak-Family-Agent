---
name: SakTan-ops-cron-tool-workarounds
version: 1.1.0
description: Approved terminal and tool execution patterns complying with Tirith guardrails
  and sandbox boundaries.
category: operations
tags:
- automation
- cron
- daily-ops
- ops
- tool
- workarounds
---

# Approved Terminal & Execution Patterns

A concise reference of approved, compliant tool and terminal patterns for autonomous
and scheduled agent runs. Enforces alignment with House of Sak security rules and
Tirith guardrails without attempting to bypass security boundaries.

## Core Security Invariants

1. **Guardrails Are Not Obstacles**: Never attempt to bypass or circumvent `DataLossGuardrail`, `Tirith`, approval prompts, or sandboxes. If a command is blocked, halt and report.
2. **Deterministic Execution**: Always run CLI commands through `uv run` to ensure hermetic dependency resolution.
3. **No Dynamic Network Installs**: Avoid runtime package installation (`pip install`, `npm -y`, `curl | sh`). All dependencies must be pre-provisioned.

## 1. Safe Temporary File Handling

When generating transient test scripts or verification artifacts, avoid hardcoding paths or writing outside workspace boundaries. Use Python's standard `tempfile` module:

```bash
# Pattern: Hermetic verification script execution
python3 -c "
import tempfile, subprocess, sys
with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
    f.write('import sys; sys.stdout.write(\"Verification successful\\n\")\n')
    f.flush()
    res = subprocess.run([sys.executable, f.name], capture_output=True, text=True)
    sys.stdout.write(res.stdout)
"
```

## 2. API Fetching & Output Containment

When fetching telemetry, health metrics, or schema payloads:
- Avoid piping unvalidated network responses directly into bash execution.
- Use explicit output files or parse directly with `json.load`:
  ```bash
  curl -sSf "https://api.example.com/health" | python3 -c "import json, sys; d=json.load(sys.stdin); sys.stdout.write(str(d.get('status')) + '\n')"
  ```
- Set reasonable timeouts (`--max-time 10`) on all network operations to prevent hanging automated tasks.

## 3. Directory Traversal & Working Directory Stability

- Never rely on implicit current working directory (`cwd`) states in automated runs.
- Use explicit absolute or repo-relative paths anchored by `git rev-parse --show-toplevel` or known repository anchors:
  ```bash
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  ```

## 4. Error Handling & Silent Failures

Automated tasks must fail loudly and transparently:
- Use `set -euo pipefail` in shell scripts.
- Log specific error categories (network timeout, schema failure, auth missing).
- Write structured observations to SQLite memory rather than raw unparsed stack traces.
