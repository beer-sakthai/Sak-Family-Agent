---
name: sakthai-hf-learn-skill-loop
category: devops
description: Use when setting up a cron-driven loop that researches Hugging Face topics
  on a schedule and writes a fresh peer-quality SKILL.md to ~/.hermes/skills/mlops/
  each tick. Encodes the topic ledger, bucket rotation, HF-only scope rules, and Beer-specific
  notification policy.
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
    source: hermes:hf-learn-skill-loop
---

# HF Learn-and-Skill Cron Loop

A reusable pattern for a recurring agent that learns one new Hugging Face topic per tick and emits a new `SKILL.md` into the local Hermes skills tree.

## When to Use

- Setting up a self-perpetuating learning loop for a documentation-heavy domain (HF, AWS, GCP, an internal API, etc.).
- Cron minimum is 1 minute — if the user wants sub-minute cadence, use a background terminal loop instead and pair with `notify_on_complete=true` for completion, or `process(action='wait')` for bounded runs.
- Pair with `hermes-agent-skill-authoring` — that skill defines the validator rules the new SKILL.md must pass.

## Invariants

1. **Never-repeat guarantee:** maintain a plain-text ledger of past topics so each run picks something genuinely new. Always list the target skills dir before deciding direction.
2. **One artifact per tick:** write exactly one new `SKILL.md` per run, even if research uncovered multiple topics. Keep quality peer-reviewable.
3. **Logging:** append one-log-line per tick to the domain log with `timestamp | skill_name | status`.
4. **Supermemory writes are best-effort in cron.** The `supermemory_store` tool is usually NOT loaded in cron sessions. If the agent sees `supermemory_store tool not available in session`, it must continue without memory persistence — don't abort the tick. Session can always recover from the skill tree + ledger.
5. **Notification policy:** notify only on real artifact creation. No-op ticks must be silent.
6. **Domain scope:** hard-code the domain boundary in the prompt. For HF that means Hub API, datasets, training, inference, tokenizers, spaces, model cards, safety, CLI — not local training or env mutations.

## Pattern: Topic Ledger + Bucket Rotation

The prompt maintains a plain-text ledger of past topics so each run picks something genuinely new. The ledger format is:

```
<ISO-date> | <topic> | <skill-name-created> | <chars-in-skill-md>
```

The prompt rotates through topic *buckets* so the skill tree grows balanced across the domain, not lopsided toward whatever the LLM is currently curious about.

## Pattern: Hard Constraints Inside the Prompt

Copy these into any similar loop build:

- **HF-only scope:** no local training scripts, no env mutations, no `pip install` from this host. Skills describe HF-platform workflows (AutoTrain, Spaces GPUs) or concepts only.
- **Write-side HF auth (per `hf-write-from-environment`):** if a topic would require uploading to HF, the skill must note that a token with the `write` role is required; the agent itself does NOT attempt uploads.
- **No fabrication:** every CLI flag, endpoint, and code snippet in the emitted skill must come from a real source actually read in that run. If uncertain, omit the example.
- **No GPU work:** assume no local GPU/training runtime; design skills around HF-hosted workflows or pure documentation.

## Pattern: Notification Policy

Notify only on real artifact creation:

- Success path → final response is `✅ Skill created: <skill-name>`, delivered to origin.
- No-op (all topics covered, no skill written) → stay silent. Do not deliver a message.

## Cron Cadence Tradeoffs

| Cadence | Runs/day | Cost | Use when |
|---------|----------|------|----------|
| 30s background loop | 2880 | very high | truly never (prefer 1m cron) |
| 1m cron | 1440 | high | deep but fast coverage — strong diversification needed |
| 5m cron | 288 | moderate | deep research per tick, balanced growth — **default** |
| 15m cron | 96 | low | each tick can do real multi-source research |
| 1h cron | 24 | minimal | daily digest style |

## Common Pitfalls

1. **Using `skill_manage(action='create')` inside the cron agent.** It writes to `~/.hermes/skills/` (correct tree for user-local skills), but the validator runs on write, so a malformed frontmatter fails silently. Have the agent use `write_file` to an explicit path and verify with `python3 -c \"import yaml,re,pathlib; ...\"` from the skill-authoring recipe.
2. **Forgetting to clear the topic ledger after a domain change.** If you pivot from HF to, say, AWS, archive the old ledger to `hf-learn-topics.bak-YYYYMMDD.txt` and start a new one.
3. **Attaching too many skills to the cron job.** Each attached skill costs input tokens on every tick. For a fast loop, attach only the strictly-required ones.
4. **Setting `deliver: 'all'`.** That fans out to every connected channel — usually wrong for a learning loop. Default to `origin` and let the success message land in the main chat.
5. **Supermemory write failure in cron.** The `supermemory_store` tool may be unavailable inside cron contexts. Treat it as best-effort; keep the on-disk skill and ledger as source of truth.
6. **`playwright growth` divergence.** When generalizing this pattern to non-HF domains, extract a reusable learning-loop skill instead of hard-coding HF buckets.

## Verification Checklist

- [ ] Job created with `cronjob(action='create', schedule='...', deliver='origin')`
- [ ] Job ID captured (so it can be paused/removed later)
- [ ] Prompt file at `~/.hermes/cron/prompts/<name>.md` is self-contained and best-effort on supermemory writes
- [ ] Ledger at `~/.hermes/cron/output/<name>-topics.txt` exists and is empty on first run
- [ ] Only the strictly-required skills are attached to the job
- [ ] Workdir is the user's home (`/home/sakthai`) so prompt file paths resolve
- [ ] First tick confirmed: a SKILL.md appears under target skills dir
- [ ] First tick delivered only the success line to Telegram, not a full report
- [ ] On no-op tick, response is exactly `[SILENT]`

## Cross-Domain Pattern: generalized learning loop

This skill is now maintained alongside `playwright-growth-loop`. The generalized pattern is:

1. One new concept per tick.
2. Always check workspace for duplicates.
3. Always log locally.
4. Always attempt supermemory write; if unavailable, continue.
5. Always prefer silence over noise.

For Hugging Face, this remains the canonical form.  
For Playwright, see `playwright-growth-loop`.  
For any new domain, start from `playwright-growth-loop` and keep the same invariants.

## Deployment Notes (2026-06-16)

First deployment of this pattern: job `hf-learn-and-skill` (ID `5f879d1cfafe`), schedule `every 5m`.

**Result:** First tick returned error and no skill was produced before user removal.

**Likely causes on next deployment:** validator-side frontmatter issues, prompt syntax, missing web toolset, ledger permissions, cron session tool restrictions.

**Fix for next deployment:** explicitly enable `web` toolset on the cron job:
```bash
cronjob action=create ... enabled_toolsets=["web","file","terminal"]
```

**Reference files:**
- `references/hf-learn-and-skill-prompt.md` — the exact prompt file used for the first deployment, preserved for debugging/iteration.
- Related domain skill: `playwright-growth-loop/SKILL.md` — same learning-loop pattern applied to Playwright.
