# Sak Family auto-cycle — guardrail parity review

**Mode: TEST (dry-run, throwaway `SAKTHAI_HOME` per persona).** "Kick off the
family cycle" is not live authorization under the auto-cycle skill, so all six
dispatches ran `--dry-run` against `SAKTHAI_HOME=$(mktemp -d)`. Nothing under
`/opt/data` was read or written, and no cycle round executed for real. Say
"do a live run" and I'll re-dispatch the same six against the real persona
homes.

**Dispatch: one message, six subagents in parallel**, one per persona.

## Per-persona results

| Persona | Rounds | Outcome | Status |
|---|---|---|---|
| SakKing | 0 (dry-run validated) | Parity test asserts only 5 of 7 guardrail copies — `saktan` and `personas/shared/` are unchecked | success |
| SakThai | 0 (dry-run validated) | All seven copies currently byte-identical (`0f08fd1d…`); wrote the canonical sync procedure | success |
| SakSee | 0 (dry-run validated) | 14 files diverge between `shared/` and canonical, incl. security modules that exist in only one tree | success |
| SakSit | 0 (dry-run validated) | Drift in any copy would silently reopen the Sentinel path/shell bypasses with the suite still green | success |
| SakTan | 0 (dry-run validated) | Topology mapped: 1 real dir, 2 symlinks, 3 partial shadow dirs — parity means different things per persona | success |
| SakJules | 0 (dry-run validated) | Remediation proposal drafted (test widening + sync tooling + PLAN entry); no files changed | success |

Six of six validated cleanly. In test mode that is the expected pass: a clean
`--dry-run` also proves `--with-skills Sak-auto-cycle-loop` resolves, so the
cycle skill would inject on a live run. Zero rounds is by design, not a
failure — dry-run validates config and exits before the first round.

## What the family found

**The good news first: there is no drift right now.** All seven copies of
`sakthai/agent/guardrails.py` — the five persona copies, `personas/shared/`,
and `saktan` — hash to `0f08fd1d621a99e4f59fe09e976a2087`. The parity issue
is not an outstanding divergence; it is a **gap in what the guard actually
guards**.

**1. The parity test asserts 5 of 7 copies (SakKing).**
`tests/test_persona_guardrails_parity.py` iterates
`PERSONAS = ["sakthai", "sakjules", "sakking", "saksee", "saksit"]`. `saktan`
is absent, and `personas/shared/sakthai/` is never asserted against the
canonical copy directly. Today both are covered *by accident*: `sakjules` is a
symlink to `../shared/sakthai`, so checking sakjules incidentally checks the
shared copy, and saktan symlinks to the same place. That coverage is a
consequence of the current symlink layout, not of anything the test states —
convert either symlink to a real directory (which is exactly what happened to
sakking, saksee and saksit) and the copy silently leaves the test's reach.

**2. The three partial shadow directories are the live precedent (SakTan).**
Topology, verified on disk:

- `sakthai` — real directory, the installed package, canonical.
- `sakjules`, `saktan` — `sakthai -> ../shared/sakthai` symlink.
- `sakking`, `saksee`, `saksit` — a *partial* real directory holding
  `agent/guardrails.py` and `web/server.py` (plus stale `cli/` snapshots for
  saksee/saksit), shadowing a `sakthai~origin_main -> ../shared/sakthai`
  symlink.

Those three exist because security syncs committed files *into* what used to
be a symlink path. So the mechanism that created the shadow copies is the same
mechanism that would create a fourth — and if it lands on `saktan`, the test
will not notice.

**3. Parity is enforced for one file while its neighbours diverge (SakSee).**
`diff -rq personas/shared/sakthai personas/sakthai/sakthai` shows 14 differing
files, and several security-relevant modules exist **only** in the canonical
copy: `agent/security_hardening.py`, `agent/guardrails_hardened.py`,
`web/api.py`, `web/contracts.py`, `memory/session_search.py`. `config.py`
differs too — and `config.py` owns `SECRET_PATTERN` / `redact_secrets()`,
which the guardrails' own output filter calls. A persona running the shared
copy therefore has byte-identical guardrail *logic* sitting on a different
redaction implementation. Byte-identity of one file is a narrower guarantee
than it reads as.

**4. What drift would actually cost (SakSit).** The protections that would
silently survive as live bypasses in an unsynced copy are the ones from
PLAN.md's Sentinel rounds: relative-path blocking for `.ssh/`/`.aws/`/shell
histories (#378/#381), critical-root blocking for `etc/passwd`-style relative
paths (#380 re-land), the widened destructive/exfiltration scan lists
(docker/podman/kubectl/chroot/nsenter, #388/#389), the `make` recipe and
`-C`/`-f` resolution (#547), and the MS Graph credential redaction sets
(#555). The regression tests for every one of those import the canonical
package — `import sakthai` resolves to `personas/sakthai/sakthai/` — so they
would all still pass against a drifted persona copy. The parity test is the
*only* thing standing between a drifted copy and a green suite, which is
precisely why its 5-of-7 coverage matters.

**5. Proposed remediation (SakJules) — proposal only, no files changed.**
- Widen `PERSONAS` to all six and add `personas/shared/sakthai` as an
  explicit seventh assertion, so coverage stops depending on symlink layout.
- Resolve each path and assert on the *resolved* file, so a symlink→real
  conversion is visible rather than silent.
- Extend the same byte-identity check to the other security-critical files
  that are already duplicated into the shadow directories, starting with
  `web/server.py`.
- Add a `make sync-guardrails` target (or a `scripts/` helper) that copies
  canonical → every persona copy, so the sync stops being a remembered `cp`.
- Longer term, the real fix is the tracked-but-not-done reconciliation of
  `personas/shared/sakthai/` with the canonical package; the widened test is
  the cheap guard until then.

## Caveats

- No cycle rounds ran. Every finding above comes from the subagents reading
  the repo directly, not from agent-loop execution — that is what a dry-run
  round produces.
- The remediation in item 5 is a proposal. No test, no persona copy, and no
  `PLAN.md` entry has been changed.

## Suggested next step

The cheapest concrete win is widening `PERSONAS` and adding the `shared`
assertion in `tests/test_persona_guardrails_parity.py` — a few lines, no
production code, and it closes the gap that lets a future shadow copy escape
CI. Want me to open that as a change, or re-run this cycle live first?
