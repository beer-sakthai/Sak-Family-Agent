---
name: SakThai-coding-security
category: coding
description: Keep sakthai-agent-v2 secure — pass the bandit gate, honor the read_file allowlist and opt-in run_command sandbox, and threat-model new tool surfaces. Use when adding tools that touch the filesystem/shell/network, widening the sandbox, or resolving a bandit finding.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - security
      - sandbox
      - bandit
      - threat-modeling
    related_skills:
      - sakthai-coding-mcp-tools
      - sakthai-coding-error-handling
      - sakthai-coding-type-safety
---

# sakthai-coding-security

`sakthai-agent-v2` ships an agent that can read files and (opt-in) run shell
commands, so its security posture is **deliberate, not incidental**. Two things
enforce it: the `bandit` scan in CI and the sandbox built into `agent/tools.py`.
Don't loosen either without a reason you can defend.

## When to use this skill

- Adding a tool that touches the filesystem, shell, or network
- Considering widening `SAKTHAI_READ_ALLOW` or enabling `run_command`
- Resolving (or justifiably skipping) a bandit finding
- Threat-modeling a new external surface (an MCP server, a new endpoint)

## The bandit gate

Run the exact CI check:

```bash
uv run bandit -c pyproject.toml -r sakthai
```

Config (`[tool.bandit]`): `exclude_dirs = ["tests"]` and a **small, intentional**
skip list — `B101, B404, B603, B606, B607`. These exist because the agent
*legitimately* shells out:

- `B404` (import subprocess), `B603` (subprocess without shell), `B607` (partial
  exe path) — the `run_command` tool runs argv lists via `subprocess`, **never**
  `shell=True`. That's the safe form bandit flags conservatively.
- `B606` (process without shell) — same family.
- `B101` (assert) — allowed in non-test internal invariants.

**Don't add new skips to dodge a real finding.** A new `shell=True`, an
`eval`/`exec`, an unparameterized SQL string, or a `yaml.load` (use
`yaml.safe_load`, as `skills.py` does) is a bug, not a skip candidate.

## The sandbox model

### `read_file` — allowlisted roots only

`_allowed_read_roots()` permits **cwd + `~/.sakthai`**, plus any path in
`SAKTHAI_READ_ALLOW` (os-pathsep list). The handler:

1. `resolve(strict=True)` the candidate (follows symlinks, fails if missing),
2. rejects non-regular files,
3. requires the resolved path to be under an allowed root via
   `path == root or path.is_relative_to(root)`.

This is what stops `../../etc/passwd` and symlink escapes — the check is on the
**resolved** path, not the raw input. Preserve that ordering if you touch it.

### `run_command` — opt-in, no shell

Disabled unless `SAKTHAI_SHELL_ALLOW` is set, so a stray model tool-call can't
execute anything by default. When enabled it runs an **argv list** (no pipes,
no redirection, no `shell=True`) with an output cap (`MAX_CMD_OUTPUT_CHARS`) and
a bounded timeout (`_CMD_TIMEOUT_DEFAULT`/`_CMD_TIMEOUT_MAX`).

### Rules for new tools

- **Validate and bound first.** Cap output size; bound timeouts; reject inputs
  outside an allowlist before doing work (fail-fast — see
  [[sakthai-coding-error-handling]]).
- **Resolve before you trust.** Any path/identifier from the model is untrusted;
  canonicalize and check membership before use.
- **No `shell=True`, no string-built SQL, no `eval`.** Pass argv lists; go
  through `MemoryStore` for data (it parameterizes).
- **Don't widen the sandbox silently.** New env-var allowances belong in
  `config.py` and the docs, with a stated reason.

## Threat-modeling a new surface (STRIDE lens)

Before exposing a new tool or wiring an external MCP server, sweep STRIDE:

| Category | Ask for this surface |
|----------|----------------------|
| **S**poofing | Can the model/peer impersonate a trusted source? (auth on the endpoint?) |
| **T**ampering | Can inputs alter data at rest? (path/SQL injection, unvalidated args) |
| **R**epudiation | Is the action logged? (session logs in `~/.sakthai/sessions/`) |
| **I**nfo disclosure | Can it read outside the allowlist? leak secrets into output/logs? |
| **D**enial of service | Output/time bounds present? (caps + timeouts) |
| **E**levation | Can it run code or reach creds it shouldn't? (`run_command` gate) |

External MCP servers connect **failing-soft** and are namespaced `<server>__<tool>`
so they can't shadow built-ins — but they're still untrusted code paths; apply
the same lens.

## Common pitfalls

1. **Don't skip a bandit finding to go green** — the existing skips are for the
   safe-subprocess pattern only; a real finding is a fix.
2. **Don't check the raw path** — always resolve first, then test
   `is_relative_to`; raw checks miss `..` and symlinks.
3. **Don't enable `run_command` in tests or defaults** — it's opt-in by design.
4. **Don't build SQL by string** — go through `MemoryStore`.
5. **Don't log secrets** — session logs persist; keep tokens/keys out of tool
   output and prompts.
