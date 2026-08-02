---
name: SakKing-sak-family-agent
description: Orchestrates and audits the Sak Family Agent fleet.
version: 0.2.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [DevOps, Orchestration, Agent Management]
---
# Sak Family Agent Orchestration

This skill provides a centralized way to manage and audit the Sak Family of AI agents. It leverages sibling skills to check the health and status of each agent, ensuring the fleet is running optimally.

## When to Use
- When needing to check the status of the Sak Family agents.
- When asked to audit or heal the agent fleet.
- When a specific agent is not responding.
- To get an overview of the Sak Family's operational status.

## Prerequisites
- Access to the `SakKing-family-health-audit` skill (loaded via `skill_view`).
- The ability to execute system commands via the `terminal` tool.
- Access to the `/opt/data/profiles/` directory for local inspection.

## How to Use
Load the `SakKing-family-health-audit` skill and follow its audit checklist:

```
skill_view(name="SakKing-family-health-audit")
```

Then use `terminal` for process inspection and `search_files` for filesystem probes as directed by that skill.

## Quick Reference
- `SakKing-family-health-audit` — full audit checklist for all sibling agents.
- `SakKing-infrastructure-drift-protocol` — pre-audit step to verify local state before trusting external logs.
- `SakKing-sak-family-profile-audit` — per-profile filesystem and process deep-dive.

## Procedure
1. **Load the audit skill:** `skill_view(name="SakKing-family-health-audit")` to get the checklist.
2. **Check Infrastructure Drift:** Run `SakKing-infrastructure-drift-protocol` to confirm local state before trusting remote health probes.
3. **Run the Audit:** Follow `SakKing-family-health-audit` checklist step by step.
4. **Deep-dive if needed:** For a silent agent, use `SakKing-sak-family-profile-audit` to inspect its profile directory, logs, and process state.
5. **Report:** Summarise findings per agent in a status table.

## Pitfalls
- **Skill name casing:** Skill names are case-sensitive. Use `SakKing-family-health-audit` (CamelCase), not `sakking-family-health-audit` (lowercase). Hermes will not find the skill with wrong casing.
- **Skills are loaded, not executed:** Hermes skills are content loaded via `skill_view()`, not shell commands. Do not use `terminal("run_skill ...")`.
- **Two-copy divergence:** The repo copy (`Sak-Family-Agent/personas/sakking/skills/`) and runtime copy (`~/.hermes/skills/` or `/opt/data/skills/`) can diverge. Always verify which copy you are editing and apply fixes to both.
- **Directory ≠ process:** A profile directory in `/opt/data/profiles/` does not mean the agent is running. Always verify process state with `ps aux | grep hermes`.
- If agents are deployed on different networks or systems, network connectivity issues might prevent accurate status reporting.
- The health audit relies on the underlying agent's ability to report its status. An agent that is deeply frozen may not be detectable by standard checks.

## Verification
- After running the audit, review the output for any reported issues or down agents. A successful run will indicate the operational status of each agent in the Sak Family.
