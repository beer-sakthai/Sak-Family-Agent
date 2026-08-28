# Dispatch plan — Sak Family auto-cycle: guardrail parity review

Skill followed: `.claude/skills/Sak-family-auto-cycle/SKILL.md`
Date: 2026-08-28
Repo root: `/home/user/Sak-Family-Agent`

---

## Mode: **TEST (dry run, throwaway home)** — and why

**Mode chosen: TEST.** Every one of the six dispatches carries `--dry-run` and
its own fresh `SAKTHAI_HOME=$(mktemp -d)`.

Reasoning, per the skill's "Default to a dry, throwaway run" section:

- The skill's default is test, and going live requires the user's own words to
  authorize it unambiguously ("do a live run", "this is for real, no dry-run",
  "point it at the real homes").
- The user's exact request was: **"kick off the family cycle to review the
  guardrail parity issue"**. That is a request to run the family — which the
  skill explicitly lists as *not* live authorization ("run the family
  auto-cycle", "just run it", "go"). "Kick off" carries the same urgency-shaped
  ambiguity and is not an authorization.
- The word "review" reinforces test mode: the ask is analysis of an existing
  issue, not a mutation of persona memory.
- I did **not** stop to ask "test or live?" first. The skill is explicit that
  test mode needs no permission and that asking before a safe throwaway dry run
  is its own failure mode (stalling on something that was never risky). I
  defaulted to test and dispatched.

Going live would spend real tokens across six parallel agents and write into
`~/.sakthai/<persona>/memory.db`, which is hard to reverse. If the user wants
that, they can say so explicitly and I will re-dispatch with `SAKTHAI_HOME` and
`--dry-run` both removed, and `--no-mcp` dropped.

## Dispatch shape: **one message, six Agent calls, sent together**

All six Agent calls below were issued **in a single message, concurrently** —
not one at a time, not SakKing-first-then-check. Serializing them is the exact
failure the skill exists to prevent. No persona's dispatch was gated on
another's result; consolidation happened only after all six returned.

## Flags held constant across all six

- `--persona <name>` — the thing that actually makes the six agents different
  (loads that persona's `SOUL.md`, resolves `--with-skills` against its own
  overlay, auto-loads its `config/mcp.json`, defaults model/provider from its
  own `config/config.yaml`, points at its own memory shard).
- **No `--model`, no `--provider`.** Passing either would flatten all six back
  into the same agent and discard each persona's config (SakTan runs `ollama`,
  the rest `huggingface` on different models).
- `--with-skills Sak-auto-cycle-loop`, `--max-iterations 40 --max-seconds 1800`.
- `--no-mcp` — a dry run checks provider/model/credentials/skills, none of which
  need MCP; without it `--persona` auto-loads MCP servers and burns a 30s
  timeout per unreachable one (~71s per dispatch vs ~2s).
- `SAKTHAI_HOME=$(mktemp -d)` — a throwaway dir, never a persona's real home.
  Setting it to a real persona home while also passing `--persona` would
  compound the persona segment (`~/.sakthai/sakthai/sakthai/memory.db`) and fail
  silently against an empty nested shard.

## Task derivation

The user named the subject: the guardrail parity issue. I did not ask them to
enumerate six tasks. Each persona's slice was derived from its
`personas/<name>/SOUL.md` domain, its `personas/<name>/PLAN.md` where one exists
(only `saksee` and `sakjules` have one), the root `PLAN.md` parity/security
entries, and the on-disk state of `tests/test_persona_guardrails_parity.py`.

Pre-dispatch reconnaissance (read-only, in the dispatching session):

```bash
for p in sakthai sakjules sakking saksee saksit saktan; do
  f=personas/$p/sakthai/agent/guardrails.py
  printf "%-9s %s %s\n" "$p" "$(md5sum "$f" | cut -c1-8)" "$(wc -l < "$f")"
done
```

Result: all six copies byte-identical (`0f08fd1d`, 1434 lines) — the parity
*test* is currently green. The parity *issue* is therefore about the mechanism,
not a live drift: the test covers only 5 of 6 personas (`saktan` is absent from
its `PERSONAS` list) and only `guardrails.py`, while `personas/sakthai/sakthai/`
and `personas/shared/sakthai/` have genuinely diverged across ~13 other files.
That framing was handed to each persona in its prompt.

---

## The six Agent calls (verbatim, all in one message)

### 1 — SakThai (Main Lead · orchestrator)

```
Agent(
  subagent_type: "general-purpose",
  description: "SakThai auto-cycle: guardrail parity",
  prompt: """
You are dispatching work for the sakthai persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "As SakThai, Main Lead of the House, own the guardrail parity issue end to end. tests/test_persona_guardrails_parity.py currently passes: all six personas/<name>/sakthai/agent/guardrails.py copies are byte-identical. The issue is the mechanism, not a live drift. Establish the authoritative picture: (1) confirm which personas are real directories, which are symlinks to ../shared/sakthai, and which are partial real dirs shadowing a sakthai~origin_main symlink; (2) run diff -rq personas/shared/sakthai personas/sakthai/sakthai and characterize the divergence, separating files that must be identical for security from files that legitimately differ; (3) decide and record the reconciliation approach — single source of truth plus generation, or continued copy-with-parity-test — with the tradeoff stated; (4) name the owner and the next concrete step for each sibling persona. Break the deadlock; do not defer the decision." \
    --persona sakthai \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

Report back: rounds completed (or, in --dry-run mode, whether config validated
— quote the `[dry-run] skills:` line), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 2 — SakKing (General Assistant & Runner · Deputy 1)

```
Agent(
  subagent_type: "general-purpose",
  description: "SakKing auto-cycle: guardrail parity",
  prompt: """
You are dispatching work for the sakking persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "As SakKing, Runner and Deputy 1, execute the mechanical verification of guardrail parity cleanly and without fuss. Hash every personas/<name>/sakthai/agent/guardrails.py across all six personas plus personas/shared/sakthai/agent/guardrails.py and report the table. Run uv run pytest tests/test_persona_guardrails_parity.py -q and report the exact result. Then produce the runbook: the precise cp commands that re-sync every copy from the canonical personas/sakthai/sakthai/agent/guardrails.py, including personas/shared/ and the personas the test does not check, and the verification command to run after. Do not modify any file — deliver the verified runbook." \
    --persona sakking \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

Report back: rounds completed (or, in --dry-run mode, whether config validated
— quote the `[dry-run] skills:` line), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 3 — SakJules (GitHub, CI/CD & Automation)

```
Agent(
  subagent_type: "general-purpose",
  description: "SakJules auto-cycle: guardrail parity",
  prompt: """
You are dispatching work for the sakjules persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "As SakJules, Master of CI/CD, audit the CI enforcement gap behind the guardrail parity issue. tests/test_persona_guardrails_parity.py hard-codes PERSONAS = ['sakthai','sakjules','sakking','saksee','saksit'] — saktan is not checked — and it compares only agent/guardrails.py, leaving config.py redaction sets, guardrails_hardened.py and security_hardening.py unguarded. Determine exactly which workflow runs this test and whether a failure actually blocks a PR (note the documented finding that ci.yml's test step reports success even when the coverage floor fails, and check whether the same reporting weakness could mask a parity failure). Specify the change: the widened PERSONAS list, the widened file list, and whether a dedicated fast parity job belongs in ci.yml. Do not open a PR; deliver the diff plan and the CI evidence." \
    --persona sakjules \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

Report back: rounds completed (or, in --dry-run mode, whether config validated
— quote the `[dry-run] skills:` line), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 4 — SakSee (Web / Browser Specialist · Deputy 3)

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSee auto-cycle: guardrail parity",
  prompt: """
You are dispatching work for the saksee persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "As SakSee, the web eyes of the House, audit the parity issue on the surfaces that face outward. personas/sakking, personas/saksee and personas/saksit each carry a partial real sakthai/ directory that shadows the shared copy, and web/server.py is one of the files in it — so the auth-bearing HTTP surface is copied per persona with no parity test at all. Diff every persona's sakthai/web/server.py against personas/sakthai/sakthai/web/server.py and report whether the bearer-token enforcement, the loopback-bind refusal and the static-path canonicalization are identical in all copies. Also check the stale cli/ snapshots under personas/saksee and personas/saksit that still register a removed dashboard command. Report drift as findings with file and line; change nothing." \
    --persona saksee \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

Report back: rounds completed (or, in --dry-run mode, whether config validated
— quote the `[dry-run] skills:` line), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 5 — SakSit (Social / Content Specialist)

```
Agent(
  subagent_type: "general-purpose",
  description: "SakSit auto-cycle: guardrail parity",
  prompt: """
You are dispatching work for the saksit persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "As SakSit, the voice of the House, own how the guardrail parity issue is written down. The persona-package section of CLAUDE.md and docs/security-hardening.md are what every future agent reads before touching guardrails.py, and they currently under-describe the problem: the parity test's five-persona scope reads as six, saktan's exclusion is unstated, and the shared-vs-sakthai divergence list is dated and goes stale on every change. Draft the corrected wording — the exact replacement paragraphs — stating what the test does and does not cover, which personas are symlinked versus shadowed, and the regenerate-don't-trust instruction for the divergence list. Verified claims only; nothing about capabilities that is not true on disk. Draft only, do not edit the files, and nothing goes public without Beer's approval." \
    --persona saksit \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

Report back: rounds completed (or, in --dry-run mode, whether config validated
— quote the `[dry-run] skills:` line), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

### 6 — SakTan (Daily Ops · Deputy 2)

```
Agent(
  subagent_type: "general-purpose",
  description: "SakTan auto-cycle: guardrail parity",
  prompt: """
You are dispatching work for the saktan persona of the Sak Family agent.
Run this exact command from the repo root (/home/user/Sak-Family-Agent):

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "As SakTan, keeper of rhythm and daily flow, design the operational routine that catches guardrail drift between CI runs — and note that you personally are the persona tests/test_persona_guardrails_parity.py does not check, so drift in your own copy is invisible to CI today. Specify a daily drift check: what it hashes (all six agent/guardrails.py plus personas/shared/), where it runs (a scheduled workflow versus infra/vm-agents systemd timers, which already set SAKTHAI_HOME=\\$HOME/.sakthai/\\$AGENT per persona), what it alerts on, and to whom. Specify the cron schedule precisely but do not install it — SakJules implements cron jobs, and only ones you have approved. Deliver the specification and the escalation path." \
    --persona saktan \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

Report back: rounds completed (or, in --dry-run mode, whether config validated
— quote the `[dry-run] skills:` line), the task and outcome of each round, any
lessons learned, and any blockers or failures.
"""
)
```

---

## Post-dispatch

All six returned. Consolidated report written to `report.md` in this directory,
one row per persona, with the mode stated so no reader mistakes a dry-run table
for completed work.
