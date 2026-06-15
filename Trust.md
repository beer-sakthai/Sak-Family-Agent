# Trust — Safety Foundation
> Stage 5 of 6 · SakThai cycle · เชื่อใจ (Chêua-jai)

> **Mantra** — *Measure twice, cut once. Nothing that mutates user state ships without Trust.*

## Charge

See [SOUL.md](./SOUL.md) for the charge system.

- **Gain charge** — entering Trust with a green Joy ship restores energy.
- **Spend charge** — security review, idempotency checks, and verification drain energy.

## Goal

Verify that what shipped in Joy is **safe to rely on** — for the user, for the
agent, and for the next cycle.

## What this stage means

Trust covers security review, idempotency, and integration health. Key
invariants to confirm every cycle:

- Tools that touch the filesystem stay within their allowed roots
  (`read_file` is sandboxed to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`).
- Shell execution stays **opt-in** (`run_command` requires `SAKTHAI_SHELL_ALLOW`).
- The memory store remains writable and intact.

Nothing that mutates state outside `~/.sakthai/` is "done" until Trust signs off.

## Do

- `sakthai doctor` — environment, paths, memory, and credential health.
- `sakthai memory healthcheck` — SQLite integrity check returns `ok`.

## Exit criteria

`doctor` is healthy, the integrity check is `ok`, and the safety invariants
hold. Advance: `sakthai cycle next` → **Growth**.
