---
name: SakKing-coding-error-handling
category: coding
description: Handle failures the v2 way — surface tool errors to the model instead of raising, fail soft on external MCP servers, fail fast on bad input, and chain exceptions for context. Use when writing tool handlers, the agent loop, MCP wiring, or input validation.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - error-handling
      - resilience
      - validation
      - agent-loop
    related_skills:
      - sakthai-coding-mcp-tools
      - sakthai-coding-security
      - sakthai-coding-testing
---

# sakthai-coding-error-handling

`sakthai-agent-v2` has a consistent failure philosophy: **errors the model can
react to are returned, not raised; external dependencies fail soft; bad input
fails fast.** Match the surface you're editing rather than reaching for a generic
try/except.

## When to use this skill

- Writing or editing a tool handler (`agent/tools.py`)
- Touching the agent loop's tool dispatch (`agent/loop.py`)
- Wiring external MCP servers (`mcp/manager.py`)
- Validating model/user input before doing work
- Deciding between raising, returning an error, or skipping

## Rule 1 — Surface tool errors to the model, don't crash the loop

`_execute_tool` wraps each handler and returns `(output, is_error)`; an exception
becomes an error *result*, not a crash. The MCP server mirrors this with
`isError: true` content. The loop feeds that back as a `tool_result` so the model
can recover (retry, pick another tool, or report).

```python
# loop dispatch — errors are reported, not raised
try:
    return tool.handler(args, store), False
except Exception as exc:        # noqa: BLE001 — surfaced back to the model
    logger.debug("Tool %r raised %s: %s", tool.name, type(exc).__name__, exc)
    return f"{type(exc).__name__}: {exc}", True
```

In a handler, prefer returning a clear, actionable message for *expected* failure
(e.g. "`{path}` is outside the allowed roots. Add it to `SAKTHAI_READ_ALLOW`")
rather than raising a bare exception — the message goes straight to the model.
This is the one place a broad `except Exception` (with `# noqa: BLE001`) is
correct; everywhere else, catch narrowly.

## Rule 2 — Fail soft on external dependencies

`connect_servers()` starts each external MCP server and, if one won't start,
**logs and skips it** — the run continues with the tools that did come up. Apply
the same to any optional/remote integration: degrade, don't abort. Tests rely on
this (a missing endpoint self-skips rather than failing — see the `integration`
marker in [[sakthai-coding-testing]]).

## Rule 3 — Fail fast on bad input

Validate and bound *before* expensive or irreversible work. The tool layer does
this: `_coerce_limit` clamps to `[1, _RECALL_LIMIT_MAX]`; `read_file` resolves and
checks the allowlist before opening; `run_command` checks `SAKTHAI_SHELL_ALLOW`
before spawning. Reject early with a specific reason.

```python
def _coerce_limit(raw: Any, default: int) -> int:
    try:
        limit = int(raw) if raw else default
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, _RECALL_LIMIT_MAX))
```

## Rule 4 — Preserve context with `raise ... from`

When you do raise (in non-handler code — store, parsing, config), chain the cause
so the trail survives. `skills.py` does exactly this:

```python
try:
    front = yaml.safe_load(parts[1])
except yaml.YAMLError as exc:
    raise SkillParseError(f"{path}: invalid YAML — {exc}") from exc
```

Use a **specific exception type** with a message that says what failed and how to
fix it (path, key, expected vs actual). Define a domain exception
(`SkillParseError`, etc.) rather than raising bare `ValueError` where callers need
to distinguish it.

## Rule 5 — Partial failure in batch work

When processing many items (facts, servers, files), don't let one bad item abort
the batch — collect successes and failures separately and report both. This is
the same instinct as fail-soft, applied per-item.

## Choosing the strategy

| Situation | Strategy |
|-----------|----------|
| Tool handler hits an expected problem | **Return** an actionable error string |
| Tool handler hits an unexpected exception | Loop converts it to an `isError` result |
| Optional external server/endpoint down | **Fail soft** — log + skip, continue |
| Invalid model/user input | **Fail fast** — validate, clamp, reject early |
| Internal invariant broken (parse/config) | **Raise** a specific exception, `from exc` |

## Common pitfalls

1. **Don't let a tool raise out of the loop** — return `(msg, is_error)` /
   `isError`; the model can't recover from a crash.
2. **Don't swallow errors silently** — log at debug and surface a message;
   `except: pass` hides bugs.
3. **Don't use a broad `except Exception`** outside the deliberate
   loop/handler boundary — catch narrowly elsewhere.
4. **Don't `raise` without `from`** when re-wrapping — you lose the cause.
5. **Don't abort a batch on the first bad item** — track and report partial
   results.
