---
name: sakthai-playwright-growth-loop
category: devops
description: Use when setting up a cron-driven loop that learns a new topic in a chosen
  domain on every tick, creates a fresh SKILL.md, logs a one-line summary, and attempts
  best-effort supermemory persistence. A generalized growth-loop pattern with Playwright
  as the initial implementation. Use for any domain that needs continuous, non-repeating
  skill generation.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    - devops
    related_skills: []
    source: hermes:playwright-growth-loop
---

# Playwright Growth Loop (generalized learning-loop pattern)

A reusable pattern for a recurring agent that learns one new topic per tick, emits a new `SKILL.md`, logs progress, and records a supermemory item when possible.

## When to Use

- You want continuous coverage growth in a documentation-heavy domain (testing frameworks, cloud APIs, SDKs, infra tools, etc.).
- The domain is large enough that one skill can’t capture it.
- You want new artifacts at every tick, with never-repeat guarantee, and optional cross-session recall via supermemory.
- Cron minimum is 1 minute — if you truly need sub-minute cadence, use a background terminal loop with `process(action='wait')`, but expect much higher token cost.

## Canonical Implementation: `playwright-growth-train`

Job: `playwright-growth-train`  
Job ID: `3677fe24dc88`  
Schedule: `* * * * *` (1 min)  
Delivery: origin  
Workdir: `/home/sakthai`  
Skills attached: `skills`, `terminal`, `web`, `file`  
Prompt file: `~/.hermes/cron/prompts/playwright-growth-train.md`  
Ledger/log: `~/.hermes/cron/output/playwright-growth.log`  
Skills dir: `~/.hermes/skills/playwright-growth/`

### Invariants

1. **Never-repeat guarantee:** before creating a skill, list existing skills in the target directory; if the proposed concept already exists, pick a new angle.
2. **One artifact per tick:** write exactly one new `SKILL.md` per run, even if research uncovered multiple topics. Put extras in the next tick so skills stay peer-quality and reviewable.
3. **Logging:** append one-log-line per tick to the domain log with `timestamp | skill_name | status`.
4. **Supermemory:** save a one-line entry summarizing the new skill. Treat supermemory writes as **best-effort** — if the tool isn’t loaded in the cron session, continue and rely on the on-disk skill and log for recovery.
5. **Discovery breadth:** rotate coverage across the domain (here: accessibility, E2E, mobile, tracing, auth flows, devtools protocol, performance, security, IME, cross-origin, service workers, etc.).
6. **Silent no-op:** if nothing genuinely new is available, respond `[SILENT]` and skip delivery. Do not send noise.

### Output Contract

Each new skill must include:
- `purpose` — what the skill automates or verifies
- `3+ tool calls` — concrete tool exemplars
- `prerequisites` — runtime deps, env vars, config
- `pitfalls` — known failure modes and workarounds
- `verification` — how to confirm the skill actually works

## Why Best-Effort Supermemory?

Cron sessions run with a reduced toolset. By default, `supermemory_store` is **not** included in cron tool sessions unless it’s explicitly loaded. Two safe patterns:

- Pattern A: Declare supermemory writes as best-effort in the prompt and recover from the skill file tree + log. Preferred in fast loops.
- Pattern B: Add `supermemory` to `enabled_toolsets` so `supermemory_store` is available. Preferred when cross-session recall is required, but it raises session cost.

If memory persistence matters more than token economy, prefer Pattern B.

## Anti-patterns

1. **Skill duplication.** Recreating an existing concept under a new slug breaks trust. Always list the target dir first.
2. **Stacking 10+ ideas per tick.** This produces un-reviewable low-quality skills. One solid skill per tick.
3. **Heavy network in cron.** Avoid hitting rate limits. Prefer lightweight discovery; push heavy reads to references, not the prompt.
4. **`deliver: 'all'`.** That announces every tick to every channel. Almost always wrong. Default to origin, then add channel targeting only when the user requests it.
5. **Skipping POC because package install seems blocked.** Don’t let an install mismatch silently block verification; expect alternative runtime paths (see `references/fallback-node-poc.md`).

## Generalized Mapping to Other Domains

To clone this for a new domain:
1. Create `<domain>-growth-loop` with the same prompt structure.
2. Set the discovery bucket list for the new domain.
3. Create the domain skills dir, e.g. `~/.hermes/skills/<domain>-growth/`.
4. Set the log path, e.g. `~/.hermes/cron/output/<domain>-growth.log`.
5. Keep the same skip/no-op/supermemory behavior.

## Cron Cadence Tradeoffs

| Cadence | Runs/day | Cost | Use when |
|---------|----------|------|----------|
| 30s background loop | 2880 | very high | truly never (prefer 1m cron) |
| 1m cron | 1440 | high | deep but fast coverage — strong diversification needed |
| 5m cron | 288 | moderate | research-heavy topics, balanced growth — **default** |
| 15m cron | 96 | low | real multi-source research per tick |
| 1h cron | 24 | minimal | daily digest style |

## Verification Checklist

- [ ] Job created with `cronjob(action='create', schedule='* * * * *', deliver='origin')`
- [ ] Job ID captured for pausing/removal later
- [ ] Prompt file exists at `~/.hermes/cron/prompts/<name>.md` and is self-contained
- [ ] Skills dir exists at `~/.hermes/skills/<domain>-growth/`
- [ ] Log path exists at `~/.hermes/cron/output/<domain>-growth.log`
- [ ] First tick produced a new SKILL.md and a single-line log entry
- [ ] No-op tick sent `[SILENT]`, not a verbose report
- [ ] Supermemory writes are best-effort, not blocking the loop

## Troubleshooting: Supermemory persistence in cron

If the growth-loop skill reports `supermemory_store tool not available in session`, the `enabled_toolsets` for the cron job are missing memory tooling. Fix:

1. Update the cron job: `cronjob(action='update', job_id='<id>', enabled_toolsets=['skills','terminal','web','file','supermemory','memory'])`
2. If that still fails with missing credentials, the supermemory backend is unavailable — fall back to **Best-effort Pattern A**: rely on the on-disk skill tree + cron log for recovery, and do not block the loop on memory writes.

## Reference Files

- `references/cron-self-heal-fix.md` — session-specific reproduction of the supermemory availability failure and the exact `cronjob update` fix applied on 2026-06-16.

Use existing `dogfood/playwright-*` skills as a seed/category map so the loop doesn’t duplicate coverage.

<=
## Related Skills

- `hf-learn-skill-loop` — same pattern applied to Hugging Face
- `hermes-agent-skill-authoring` — frontmatter/structure validator the emitted SKILL.md must satisfy
- `voice-delivery` — TTS delivery path if the domain produces voice artifacts
