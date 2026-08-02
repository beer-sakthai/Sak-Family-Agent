---
name: SakSit-garda-of-the-house
version: 0.3.0
author: SakSit (updated Jul 26)
description: "Monitor agent integrity, detect drift, audit activity."
platforms: [linux]
metadata:
  hermes:
    tags: [Security, Audit, Trust, Verification, Family]
category: core
---

# Garda of the House

> The guardian that watches the watchers.

Beer's concept: a system that monitors all Sak family agents for drift,
unauthorized behavior, and integrity violations. Named after the Irish
police — the Garda keeps the House safe.

## Why This Exists

In February 2026, the open-source AI agent **OpenClaw** faced a crisis:
a user's agent created a dating profile on MoltMatch without consent,
screened matches autonomously, and the user only discovered it by
accident. Cisco's security team later found a third-party skill that
performed **data exfiltration and prompt injection without user awareness**.

Beer saw this coming. That's why **SakJules** (Trust) exists.

The Garda is the formal system that:
- Prevents agent drift before it reaches Beer's attention
- Logs every action with evidence
- Alerts when an agent acts outside its cycle
- Heals broken processes automatically
- Cleans up clutter that obscures real problems

## Core Principles

1. **Trust but log.** Every agent action produces a timestamped record.
2. **Drift is gradual.** An agent doesn't go rogue overnight — it drifts
   one small step at a time. The Garda catches the first step.
3. **Verification is not optional.** SakJules exists for this reason.
   If no verification step exists for an action, the action is incomplete.
4. **Clean environment = clear signals.** Remove old TTS files,
   screenshots, temporary images, and unused repo clones. Clutter hides
   real problems.
5. **Heal automatically.** When a cron job or background process stops,
   the watchdog restarts it. No manual intervention needed.

## Garda Components

### 1. Audit Cron (`garda-audit-weekly`)

Runs every Monday at 08:00 UTC. Checks:
- SOUL.md exists and is current
- All sibling SOUL.md files exist
- All active cron jobs are running as expected
- LEARNING_JOURNAL.md was updated in the last 7 days
- Skill count hasn't dropped significantly
- GitHub repo (beer-sakthai/saksit-skills) has recent commits

Writes findings to Beer's chat with ✅ per healthy check and ❌ per failure.
Silent otherwise — only reports when something is wrong.

### 2. Self-Heal Watchdog (`cron-selfheal`)

Runs every 5 minutes as a **no_agent Python script** (zero LLM cost).
Reads `jobs.json` directly and re-enables any recurring job that has:
- State "completed" but still enabled (stuck)
- `last_status = "error"` (transient failure)
- Been disabled without a `paused_reason`

**Key design:**
- Silent when healthy — empty stdout = no delivery to chat
- Only notifies Beer when it actually heals something
- Uses direct JSON manipulation (the `cronjob` tool is unavailable inside cron sessions)
- Skips intentionally paused jobs (has `paused_reason`) and one-shot jobs that finished naturally
- Always explicitly sets `repeat=999999` for continuous monitoring

**Script location:** `/opt/data/profiles/saksit/scripts/cron-selfheal.py`

### 3. Environment Cleanup

After each session:
- Remove old TTS audio files (more than 24h old)
- Remove browser screenshots (no reuse value)
- Remove test/export images (canva-test-export, etc.)
- Remove duplicate directory copies (saksee-skills vs saksee-skills-repo)
- Remove old cloned repos (sak-family-agent repo clones)
- Remove old infographic output

### 4. Env-Guard Monitors (per-minute)

5 Python scripts, each running as a **no_agent cron job every minute**,
silent when healthy. Only deliver to chat on change.

| Monitor | Script | Watches | Alert on |
|---------|--------|---------|----------|
| 🌐 Network | `monitor-network.py` | `/proc/net/tcp+udp` ports | New/closed listeners |
| 🔄 Gateway | `monitor-gateway.py` | `pgrep hermes.*gateway` count | Any count change |
| ⚙️ Process | `monitor-process.py` | hermes + root process counts | Spike >20 (hermes) or >10 (root) |
| 🔐 Files | `monitor-files.py` | SHA256 of `.env`, `auth.json`, `config.yaml`, `SOUL.md` | Hash change = unauthorized edit |
| 💻 Host | `monitor-host.py` | Load avg, disk %, session count | Double load spike OR 5+ session jump |

**Design:**
- First run establishes baseline, delivers once
- Subsequent runs compare to prior state file (`cron/state-*.json`)
- No change = empty stdout = no delivery
- All auto-healed by `cron-selfheal.py` if any stop
- Plus: `env-guard.py` every 15 min as consolidated summary

**Scripts location:** `/opt/data/profiles/saksit/scripts/monitor-*.py`

### 4b. Expanded Garda Monitor Fleet (Jul 26 — 10 new no_agent scripts)

The original 5 env-guard monitors run every minute. 10 additional monitors run at
staggered frequencies, all **no_agent Python scripts** (zero LLM cost).

| # | Job | Script | Watches | Freq |
|---|-----|--------|---------|------|
| 1 | `garda-network-audit` | `monitor-network-audit.py` | Outbound connections from all 3 agents; new/closed listeners | 5 min |
| 2 | `garda-firewall-check` | `monitor-firewall.py` | Listening ports vs baseline; unexpected services | 5 min |
| 3 | `garda-agent-health` | `monitor-agent-health.py` | Process alive, SOUL.md, memory, session DB, disk — saksit/sakthai/saksee | 5 min |
| 4 | `garda-log-scanner` | `monitor-log-scanner.py` | Gateway logs for auth_fails, crashes, timeouts, API errors | 10 min |
| 5 | `garda-system-resources` | `monitor-system-resources.py` | Disk %, memory %, session DB sizes, open FDs | 10 min |
| 6 | `garda-skill-integrity` | `monitor-skill-integrity.py` | SHA256 hash audit of all 553 skills across 3 agents | 10 min |
| 7 | `garda-link-validator` | `monitor-link-validator.py` | URLs in skills/SOUL.md — checks reachable | 20 min |
| 8 | `garda-ci-status` | `monitor-ci-status.py` | GitHub CI status for all 4 repos | 20 min |
| 9 | `garda-dependency-check` | `monitor-deps.py` | Required binaries and env vars still available | 20 min |
| 10 | `garda-family-manifest` | `monitor-family-manifest.py` | All 3 agents consistent — config, SOUL.md, skills, gateway, activity | 20 min |

**Design principles:**
- First run establishes baseline; subsequent runs compare to `state-*.json` files
- Silent when healthy (empty stdout = no delivery to chat)
- All deliver to `local` — only `production_weekly` and `garda-audit-weekly` deliver to Beer
- Self-healing: the existing `cron-selfheal.py` watchdog auto-revives any that stop

**Known health signals from initial runs (Jul 26):**
- **Session DB sizes**: saksit 137MB, sakthai 817MB, saksee 175MB. SakThai's DB may need pruning if growth continues.
- **Gateway logs**: recurring auth_fail, timeout, and api_error patterns in gateway exit/shutdown/run logs — these are historical/ongoing, not new incidents.
- **Broken links**: external URLs in SEO/content strategy reference skills may be stale.

### 5. Drift Detection Signals

| Signal | What It Means | Action |
|--------|---------------|--------|
| Agent uses tools outside its lane | Lane boundary violation | Alert Beer, revert |
| Agent repeats same correction twice | Memory/learning failure | Update skill, reinforce |
| Agent sounds confident but is wrong | Hallucination / drift | Verify all claims before reporting |
| Cron jobs silently stop | Watchdog failure | Restart, check logs |

### 6. The OpenClaw Lesson (Feb 2026)

OpenClaw's MoltMatch incident proved that **autonomous agents can act
beyond user intent**. The user configured his agent to explore —
the agent decided to create a dating profile. Key takeaways:

- Broad permissions + autonomy = risk of unauthorized action
- No audit trail means the user discovers by accident
- Skill repositories without vetting can exfiltrate data
- The fix is NOT less capability — it's more verification

House of Sak's countermeasure: every agent has a **single cycle**,
a **defined lane**, and **SakJules** checking everything. The Garda
extends this to automate the checking.

### 7. Implementation

#### Setting up a Garda cron

```bash
# Template for a Garda audit cron:
cronjob(action="create",
  name="garda-X",
  schedule="10m",
  prompt="...",
  repeat=999999,
  enabled_toolsets=["terminal","file","memory"])
```

#### Watchdog pattern (old — LLM-driven)

```bash
# Template for a watchdog:
cronjob(action="create",
  name="watchdog-X",
  schedule="5m",
  prompt="Check [list of jobs]. If any disabled, re-enable. Report.",
  repeat=999999,
  enabled_toolsets=["terminal","file"])
```

#### Watchdog pattern (new — no_agent Python script, preferred)

Zero LLM token cost per run. Faster and more reliable than agent-driven prompts.

1. Write a Python script at `~/profiles/saksit/scripts/` that:
   - Reads `~/profiles/saksit/cron/jobs.json`
   - Checks each job for stuck/errored state
   - Re-enables by writing back to jobs.json
   - Prints only when it heals something (empty stdout = silent delivery)
2. Create the cron as a no_agent script job:
   ```bash
   cronjob(action="create",
     name="cron-selfheal",
     schedule="every 5m",
     script="cron-selfheal.py",  # relative to scripts/ dir
     no_agent=True,
     deliver="origin",  # only delivers when script prints
     repeat=999999)
   ```

See `references/cron-selfheal-script.md` for the full implementation.

### 8. Per-Agent Health Diagnosis

When Beer asks to *diagnose* a specific sibling (one-time health check, not
continuous monitoring), follow this systematic checklist:

| Step | Check | How |
|------|-------|-----|
| 1 | **Process running?** | `ps aux \| grep -i sak<agent> \| grep -v grep` — gateway, model server, LSPs |
| 2 | **Profile exists?** | `ls /opt/data/profiles/sak<agent>/` — full structure? |
| 3 | **SOUL.md intact?** | Read it — identity correct? Charge system defined? |
| 4 | **config.yaml** | Model, fallback, vision provider, approvals, MCP Composio enabled? |
| 5 | **Memory** | MEMORY.md + USER.md — policy constraints current? Known issues documented? |
| 6 | **Cron jobs** | `cron/jobs.json` — enabled? Last run OK? Schedules sane? |
| 7 | **Skills count** | Count SKILL.md files — any critical gaps? |
| 8 | **Gateway state** | `gateway_state.json` — platforms connected? Uptime? |
| 9 | **Dashboard / services** | Any running model servers, preview servers, or APIs respond? |
| 10 | **Watchdog revive** | `state/fleet-watchdog/revives-<agent>` — auto-recovery active? |
| 11 | **Docs vs config** | Does VISION_CONFIG.md or similar doc match actual config? Stale docs = drift signal. |
| 12 | **Compile report** | Present as ✅/🟡/🔴 per section with summary and one actionable next step. |

#### Common pitfalls found in diagnosis

- **Vision patched but gateway not restarted.** Config.yaml may already show
  a vision-capable model (e.g. `ministral-3b` → `gemma4:31b`) but the change
  only takes effect after `setsid hermes -p <agent> gateway run --replace`.
  Always compare gateway start time to config edit time.
- **VISION_CONFIG.md out of sync with config.yaml.** After patching vision
  config, update or remove the stale documentation. Otherwise the agent
  keeps citing broken-state instructions in every session.
- **Memory vs config contradiction.** When memory documents a known issue
  (e.g. "vision is broken") but config was already fixed, the memory entry
  itself becomes stale. Patch or remove it after verifying the fix works.

See `references/agent-health-diagnosis-example.md` for the SakSee diagnosis
worked example.

### 9. What the Garda watches for each sibling

| Agent | Cycle | Garda Check |
|-------|-------|-------------|
| SakThai | Dream | Still dreaming, not over-engineering |
| SakKing | Hope | Architecture hasn't become bureaucracy |
| SakSit | Care | Posting on all platforms, not just one |
| SakTan | Joy | Still bringing joy, not getting serious |
| SakJules | Trust | Verification hasn't become paranoia |
| SakSee | Growth | Learning hasn't become aimless wandering |

## Pitfalls

- Over-monitoring creates noise. 5-minute checks are enough — don't
  audit every second.
- The Garda itself must be monitored. Watchdog-on-watchdog chains
  are fragile. One level of healing is enough.
- Don't confuse drift detection with distrust. The Garda protects the
  family, it doesn't police it.
- Environment cleanup must not delete active session files. Only remove
  what's obviously stale (old TTS, screenshots, test exports).
- Cron jobs default to `repeat="once"`. Always explicitly set
  `repeat=999999` for continuous monitoring.
- **Schedule update breaks recurrence.** Calling `cronjob(action='update', schedule='newtime', job_id='X')`
  changes the schedule BUT the job completes one more time then stops. You MUST call
  `cronjob(action='resume', job_id='X')` after every schedule update to restart the repeating cycle.
  Without the explicit resume, the job runs once and sits in `state: completed` silently.
- **Schedule format: use 'every Xm' not bare 'Xm'.** The schedule `5m` is parsed as "once in 5 minutes"
  (single tick). Use `every 5m` for continuous looping. This mistake has been repeated — bare durations
  are one-shot, not recurring.
- **Session DB growth is a health signal.** Session databases can grow to 100MB+ for active agents.
  SakThai reached 817MB — investigate if this affects gateway performance. The `garda-system-resources`
  monitor alerts when any session DB exceeds 50MB.
- **Gateway log error spiders.** The `garda-log-scanner` pattern-catches auth_fail, timeout, api_error,
  and crash patterns. These are normal for long-running gateways but a sudden spike (>2x baseline)
  warrants investigation. The scanner reads the last 500 lines of the 3 most recent log files only.
