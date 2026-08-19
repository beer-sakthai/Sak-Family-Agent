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

### Running `sakthai` Locally

The heart of this repo is the `sakthai` CLI — a personal learning agent with persistent SQLite memory. It works four ways:
- **Agent loop**: `sakthai run "<your task>"` — single-turn agentic reasoning
- **Interactive chat**: `sakthai chat` — multi-turn REPL (sessions logged to `~/.sakthai/sessions/`)
- **MCP server**: `sakthai mcp` — JSON-RPC stdio server for connecting to external tools
- **Memory tools**: `sakthai learn`, `sakthai recall`, `sakthai memory <subcommand>` — direct fact management

All four share the same SQLite memory at `~/.sakthai/memory.db`. Start small:
```bash
sakthai run "What files exist in this repository?" --stream
sakthai memory stats  # Check what's in your memory already
sakthai chat          # Start an interactive session
```

### Skill Naming & Discovery

Every persona has its own skill overlay under `personas/*/skills/`. Shared skills live in `personas/shared/skills/` (3 skills identical across all personas). The naming convention:
- **Shared skills**: `Sak-` prefix (e.g., `Sak-family-auto-cycle`)
- **Per-persona skills**: `Sak<Name>-` prefix (e.g., `SakThai-environment-automation`, `SakSee-stitch-code-to-design`)

Validate the naming with: `sakthai skills validate --naming`

### Per-Persona Memory Sharding

Each persona gets its own memory shard at `~/.sakthai/<persona>/memory.db`, separate from the legacy unscoped `~/.sakthai/memory.db`. When working locally:
```bash
sakthai run "Task for SakThai" --persona sakthai
sakthai memory stats --persona sakking
sakthai memory family --personas sakthai,sakking,saksee  # Merged view across personas
```

The `memory family` command is particularly useful — it shows deduplicated facts and observations from every persona's shard at once.

### CI/CD Participation

- **27 GitHub Actions workflows** run automatically (see `README.md` for the full matrix)
- **Green CI is necessary, not sufficient** — PRs into `main` also need a **non-author approval**
- **Local reproduction**: before pushing, run the full validation locally (see `CONTRIBUTING.md` for the checklist)
- **Self-healing CI**: if a test fails, `sakthai heal run` can diagnose and propose a fix (read `docs/self-healing-ci.md` for safety gates)

## Get Started

### Welcome to the House of Sak 🏠

You're joining the workspace of **Six Personas, One Shared Runtime** — an autonomous AI family created by **Beer** during recovery. The team uses Claude Code intensively for building features, improving quality, and testing. Your first few steps:

### Task 1: Run Tests Locally (5 minutes)

Confirm your environment is set up correctly:
```bash
cd /home/user/Sak-Family-Agent
uv sync --all-extras
uv run pytest tests/test_memory_store.py -q  # Single fast test
uv run pytest tests/ -m "not integration" -q  # Full suite (may take a minute)
```

If all tests pass, you're ready. If not, check `CONTRIBUTING.md` for the full quality bar and `docs/workspace.md` for environment setup.

### Task 2: Explore a Persona

Meet one of the six agents. Each has a `SOUL.md` (identity) and skill overlay. SakThai is the lead:
```bash
sakthai run "Summarize what's in my memory right now" --persona sakthai --stream
cat personas/sakthai/SOUL.md  # Read SakThai's identity
ls personas/sakthai/skills/ | head -10  # Browse their skills
```

Or explore a different persona — SakKing (strategy), SakSee (vision), SakSit (research), SakJules (automation), SakTan (operations).

### Task 3: Create a Tiny Skill (10 minutes)

Skills are Markdown files with YAML frontmatter. Create one:
```bash
mkdir -p personas/sakthai/skills/my-first-skill
cat > personas/sakthai/skills/my-first-skill/SKILL.md <<'EOF'
---
name: my-first-skill
category: learning
description: My first test skill for the House of Sak
version: "1.0"
platforms: [linux, macos, windows]
metadata:
  sakthai:
    tags: [test, learning]
---

# My First Skill

This skill teaches me the basics of the House of Sak.

## Usage

Invoke this skill with `sakthai run --with-skills my-first-skill "your task"`.

## Resources

- Read more: [docs/plugins.md](../../docs/plugins.md)
EOF

# Validate it
sakthai skills validate --naming
sakthai skills show my-first-skill
```

### Need Help?

- **Architecture questions**: Read [`CLAUDE.md`](CLAUDE.md) (the definitive guide) or [`docs/architecture.md`](docs/architecture.md)
- **Security concerns**: Email **beer-sakthai@users.noreply.github.com** (see [`SECURITY.md`](SECURITY.md))
- **Contributing code**: Follow [`CONTRIBUTING.md`](CONTRIBUTING.md) — green CI + non-author approval required
- **Personas & skills**: Check [`AGENTS.md`](AGENTS.md) for agent-facing guidance
- **Running the agent**: `sakthai --help` or `sakthai run --dry-run "test"` to preflight
- **Memory & learning**: `sakthai memory --help` for the full command suite
- **Code of Conduct**: Read [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — Contributor Covenant v2.1

---

**You're now ready to explore, contribute, and learn.** Start with Task 1 and work through at your own pace. Welcome to the House! 🎉