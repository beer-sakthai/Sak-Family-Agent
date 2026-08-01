# Agent Health Diagnosis — SakSee (2026-07-25)

> Worked example of the Per-Agent Health Diagnosis checklist.
> Performed by SakSit on 2026-07-25.

## Results

| Step | Check | Result |
|------|-------|--------|
| 1 | Process running? | ✅ Gateway PID 610206, running since Jul 24 |
| 2 | Profile exists? | ✅ `/opt/data/profiles/saksee/` — 26 dirs, full structure |
| 3 | SOUL.md intact? | ✅ 84 lines, identity "Saksee · Master of Web", charge system defined |
| 4 | config.yaml | ✅ Model: `kimi-k2.7-code` (ollama-cloud), fallback: DeepSeek-V4-Flash (HF), vision: gemma4:31b, MCP Composio enabled |
| 5 | Memory | ✅ MEMORY.md + USER.md present, zero-cost policy, FPL info, vision-broken note |
| 6 | Cron jobs | ✅ `saksee-web-growth-loop` (daily 2am, 5 runs, last OK), `fpl-build-watchdog` (daily 8am, never run — new) |
| 7 | Skills count | ✅ 127 SKILL.md files |
| 8 | Gateway state | ✅ Running, Telegram connected, 1 active agent |
| 9 | Dashboard / services | ✅ saksee-models.py on port 3002, both GGUF models (0.5B + 1.5B) ready |
| 10 | Watchdog revive | ✅ `state/fleet-watchdog/revives-saksee` present (epoch 1784865805) |
| 11 | Docs vs config | 🔴 VISION_CONFIG.md says `ministral-3b` (broken), but config.yaml says `gemma4:31b` (fix applied but not active) |
| 12 | Compile report | **2 issues found** (see below) |

## Issues Found

### 🔴 Vision — Config patched, gateway not restarted

`config.yaml` shows `gemma4:31b` (vision-capable) but the gateway was
started before the change. The running process still uses the old model.
Fix: `setsid hermes -p saksee gateway run --replace`

### 🟡 VISION_CONFIG.md outdated

Describes the `ministral-3b` broken state and offers fix options, but the
actual fix (gemma4:31b) is already in config. Needs updating.

## Summary

```
Vitals:   ✅ Gateway UP | ✅ Model OK | ✅ MCP OK | 🔴 Vision broken
Skills:   127 loaded | Cron: 2 jobs | Dashboard: ✅
```

One actionable fix: restart gateway to activate vision patch. Then update
VISION_CONFIG.md to match reality.

---

## Resolution (same session)

After diagnosis, Beer approved the fix:

### Fix applied

| Action | Command / Detail |
|--------|-----------------|
| ✅ Restarted gateway | `setsid hermes -p saksee gateway run --replace` — PID 610206 → 1004595 |
| ✅ Verified new gateway | New PID running, Telegram reconnected, active agents: 1 |
| ✅ Updated VISION_CONFIG.md | Replaced broken-state doc with fixed-state doc referencing `gemma4:31b` |
| ✅ Updated MEMORY.md | Replaced stale entry *"vision is patched but needs restart"* with *"Vision fixed Jul 25"* |

### Cross-profile note

Beer was asked before editing SakSee's memory (SakSit editing SakSee's profile).
The `cross_profile=True` flag is required for cross-profile writes via `patch`
and `write_file` — explicitly confirm with the user first.

### Final state

```
Vitals:   ✅ Gateway UP | ✅ Model OK | ✅ MCP OK | ✅ Vision fixed
Skills:   127 loaded | Cron: 2 jobs | Dashboard: ✅
Memory:   ✅ Vision entry updated
Docs:     ✅ VISION_CONFIG.md matches config
```
