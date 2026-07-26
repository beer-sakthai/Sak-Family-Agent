---
name: SakKing-sak-family-agent
description: Orchestrates and audits the Sak Family Agent fleet.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [DevOps, Orchestration, Agent Management]
---
# Sak Family Agent Orchestration

This skill provides a centralized way to manage and audit the Sak Family of AI agents. It leverages other skills to check the health and status of each agent, ensuring the fleet is running optimally.

## When to Use
- When needing to check the status of the Sak Family agents.
- When asked to audit or heal the agent fleet.
- When a specific agent is not responding.
- To get an overview of the Sak Family's operational status.

## Prerequisites
- Access to the `sakking-family-health-audit` skill.
- The ability to execute system commands via the `terminal` tool.

## How to Run
The primary way to use this skill is by invoking it through the `terminal` tool, or by calling the `sakking-family-health-audit` skill directly if available.

## Quick Reference
- `sakking-family-health-audit` - Initiates a health check of the Sak Family agents.

## Procedure
1. **Check Family Health:** Execute the `sakking-family-health-audit` skill. This skill will internally use other tools to probe the status of each agent.
   ```bash
   # This is a conceptual example; the actual command depends on how the skill is exposed.
   # Assuming sakking-family-health-audit is callable directly or via a wrapper script.
   # For demonstration, we'll show a hypothetical terminal command.
   terminal("run_skill sakking-family-health-audit")
   ```

## Pitfalls
- If agents are deployed on different networks or systems, network connectivity issues might prevent accurate status reporting.
- The health audit relies on the underlying agent's ability to report its status. An agent that is deeply frozen may not be detectable by standard checks.

## Verification
- After running the health audit, review the output for any reported issues or down agents. A successful run will indicate the operational status of each agent in the Sak Family.
