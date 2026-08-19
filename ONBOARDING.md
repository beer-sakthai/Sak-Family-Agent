# Welcome to Sak Family

## How We Use Claude

Based on beer-sakthai's usage over the last 30 days:

Work Type Breakdown:
  Build Feature       ████████████████░░░░  80%
  Improve Quality     ████░░░░░░░░░░░░░░░░  20%

Top Skills & Commands:
  /reload-plugins                          ████████████████████  8x/month
  /plugin                                  ████████████████████  8x/month
  /reload-skills                           ███████████████░░░░░  6x/month
  /superpowers:using-superpowers           █████████████░░░░░░░  5x/month
  /skills                                  ██████████░░░░░░░░░░  4x/month
  /superpowers:finishing-a-development-branch  ████████░░░░░░░░░░░░  3x/month
  /mcp                                     █████░░░░░░░░░░░░░░░  2x/month
  /agents                                  █████░░░░░░░░░░░░░░░  2x/month

Top MCP Servers:
  No MCP server tool calls recorded in the last 30 days.
  (stepsecurity is configured for this workspace — see Setup Checklist.)

## Your Setup Checklist

### Codebases
- [ ] Sak-Family-Agent — https://github.com/beer-sakthai/Sak-Family-Agent

### MCP Servers to Activate
- [ ] stepsecurity — CI/CD & supply-chain security posture and detections (anomalous outbound network calls, blocked egress, secrets in build logs, imposter-commit actions, run-level process/file events). Configured with `claude mcp add --transport http stepsecurity <endpoint>`; get the endpoint URL and tenant access from beer-sakthai.

### Skills to Know About
- /superpowers:using-superpowers — the entry point to the Superpowers skills; makes Claude invoke the relevant skill before it acts, instead of freewheeling.
- /superpowers:finishing-a-development-branch — the standard "I'm done, now what?" flow: run tests, then choose merge-locally / push-and-PR / keep-branch, then clean up the worktree.
- /superpowers:requesting-code-review — dispatch a read-only code-reviewer subagent over a diff before you merge; only the findings come back.
- /superpowers:using-git-worktrees — isolate each piece of work in its own worktree off main before implementing.
- /plugin + /reload-plugins + /reload-skills — install/enable plugins and hot-reload skills after editing them. This team ships its own plugins (sak-security, ci-cd-doctor), so you'll reload often while developing them.
- /plugin-dev:plugin-structure — the directory layout and `plugin.json` manifest conventions for Claude Code plugins.
- /update-config — edit `settings.json` (hooks, permissions, env vars) by merging with existing settings rather than overwriting.
- /skills — list every available skill in the current session.

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