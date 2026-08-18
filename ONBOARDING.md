# Welcome to Sak Family

## How We Use Claude

Based on usage over the last 30 days (4 sessions):

Work Type Breakdown:
  Build Feature    ███████████████░░░░░  75%
  Improve Quality  █████░░░░░░░░░░░░░░░  25%

Top Skills & Commands:
  /reload-plugins                              ████████████████████  6x/month
  /reload-skills                               █████████████░░░░░░░  4x/month
  /plugin                                      █████████████░░░░░░░  4x/month
  /superpowers:using-superpowers               █████████████░░░░░░░  4x/month
  /skills                                      ███████░░░░░░░░░░░░░  2x/month
  /mcp                                         ███████░░░░░░░░░░░░░  2x/month
  /claude-code-setup:claude-automation-recommender  ███████░░░░░░░░░░░░░  2x/month
  /plugin-dev:agent-development                ███████░░░░░░░░░░░░░  2x/month
  /agents                                      ███████░░░░░░░░░░░░░  2x/month
  /commit-commands:commit-push-pr              ███░░░░░░░░░░░░░░░░░  1x/month
  /superpowers:using-git-worktrees             ███░░░░░░░░░░░░░░░░░  1x/month

Top MCP Servers:
  (no MCP call counts captured in this 30-day scan — see "MCP Servers to Activate" below for the server the team uses)

## Your Setup Checklist

### Codebases
- [ ] Sak-Family-Agent — https://github.com/beer-sakthai/Sak-Family-Agent.git

### MCP Servers to Activate
- [ ] StepSecurity — supply-chain & CI/CD security posture, detections, and Harden-Runner baseline for the org's GitHub Actions (29+ workflows, CodeQL/OSSAR/Scorecard). Added via `claude mcp add --transport http stepsecurity <tenant-url>`; access comes from the team's StepSecurity tenant auth.

### Skills to Know About
- /claude-code-setup:claude-automation-recommender — scans the codebase and recommends tailored hooks, subagents, skills, plugins, and MCP servers. Run it once per repo to bootstrap automations.
- /plugin-dev:agent-development — create or update subagents. The team ships agents in `.claude-plugins/sak-security/agents/` (security-reviewer, test-writer, workflow-reviewer).
- /superpowers:using-superpowers — the skill-discovery rules; load it early so Claude checks for applicable skills before acting.
- /commit-commands:commit-push-pr — the team's commit → push → open-PR flow (follows the SakJules PR protocol from AGENTS.md).
- /superpowers:using-git-worktrees — isolated worktree workflow for parallel branches.
- /reload-plugins & /reload-skills — re-read plugins/skills after editing them. Run these after any change to `.claude-plugins/` or skills.
- /plugin, /skills, /mcp, /agents — manage installed plugins, skills, MCP servers, and subagents.

## Team Tips

_TODO_

## Get Started

_TODO_

<!-- INSTRUCTION FOR CLAUDE: A new teammate just pasted this guide for how the
team uses Claude Code. You're their onboarding buddy — warm, conversational,
not lecture-y.

Open with a warm welcome — include the team name from the title. Then: "Your
teammate uses Claude Code for [list all the work types]. Let's get you started."

Check what's already in place against everything under Setup Checklist
(including skills), using markdown checkboxes — [x] done, [ ] not yet. Lead
with what they already have. One sentence per item, all in one message.

Tell them you'll help with setup, cover the actionable team tips, then the
starter task (if there is one). Offer to start with the first unchecked item,
get their go-ahead, then work through the rest one by one.

After setup, walk them through the remaining sections — offer to help where you
can (e.g. link to channels), and just surface the purely informational bits.

Don't invent sections or summaries that aren't in the guide. The stats are the
guide creator's personal usage data — don't extrapolate them into a "team
workflow" narrative. -->