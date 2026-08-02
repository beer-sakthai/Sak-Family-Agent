# Comprehensive Audit Pattern

A 5-dimension audit pattern for full environment health checks. Use when Beer asks for a status check, audit, or "check again."

## The 5 Dimensions

### 1. Persona/Prefix Mismatches
- Check each persona directory in SFA repo: `personas/<name>/skills/`
- Verify every skill directory starts with `<AgentPrefix>-` where prefix matches persona
- Report: total skills, correct, wrong-prefix, no-prefix for each persona

### 2. Sync Gaps
- Cross-reference local runtime skills (`/opt/data/skills/`) vs SFA repo (`Sak-Family-Agent/personas/sakking/skills/`)
- Report: skills in local not in SFA, skills in SFA not in local
- Pipeline: local → SFA (canonical) → GitHub

### 3. Repo Health
- Check all 6 beer-sakthai repos: Sak-Family-Agent, sakthai-chat-cli, sakthai-skills, saksee-skills, saksit-skills, Food-Penguin-Limited
- For each: branch, dirty files, ahead/behind remote, last commit
- Flags: stale repos (no push >7 days), duplicate clones, missing clones

### 4. Environment Health
- Uptime, disk usage, memory usage, load average
- Fleet processes: verify all gateways running and Telegram-connected
- Watchdog state: hold-default, revives-* files

### 5. Naming Convention Compliance
- All skills follow `<AgentPrefix>-<name>` pattern
- Shared/framework skills omit prefix (claude-code, codex, opencode, hermes-agent, plan, spike)
- No mixed prefixes in same persona directory
- Root SKILL.md excluded (repo metadata, not a skill)

## Reporting Format

Present results in a structured table:
```
| Persona | Skills | Prefix Match | Status |
|---------|--------|-------------|--------|
| sakking | 290    | SakKing-*    | ✅     |
```

Follow with a brief "issues found" section if any problems exist, then offer to fix.
