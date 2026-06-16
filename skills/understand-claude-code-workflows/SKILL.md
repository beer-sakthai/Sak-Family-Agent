---
name: understand-claude-code-workflows
category: sakthai
description: Navigate and leverage the claude-code-workflows extension (84 plugins, 192 agents, 156 skills, 102 commands). Use when exploring available plugins, invoking subagents, running slash commands, or combining multi-domain agentic workflows.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - extensions
      - plugins
      - agents
      - workflows
      - claude-code
    related_skills:
      - understand-caveman
---

# understand-claude-code-workflows

The **claude-code-workflows** extension (by wshobson) is a multi-harness agentic
plugin marketplace installed at `~/.gemini/extensions/claude-code-workflows/`.
It provides 84 plugins, 192 subagents, 156 skills, and 102 slash commands —
all consumable natively from Gemini CLI / Antigravity.

## When to use this skill

- User asks "what plugins/agents/skills are available?"
- User needs a domain-expert subagent (security, ML, infra, testing, etc.)
- User wants to scaffold, review, deploy, or debug using structured workflows
- User asks about slash commands or plugin capabilities
- Combining multiple plugins for complex multi-domain tasks

## Architecture — single source of truth

All authoring lives under `plugins/<name>/`. Adapters transform source files
into harness-native artifacts. **Never hand-edit generated files.**

```
~/.gemini/extensions/claude-code-workflows/
├── AGENTS.md                    # Canonical context (loaded every session)
├── GEMINI.md                    # Gemini-specific setup guide
├── plugins/                     # SOURCE OF TRUTH — 82 local plugins
│   └── <name>/
│       ├── agents/*.md          # Domain-expert subagents
│       ├── commands/*.md        # Slash commands
│       └── skills/<n>/SKILL.md  # Modular knowledge packages
├── docs/                        # Detailed reference docs
│   ├── plugins.md               # Full 84-plugin catalog
│   ├── agents.md                # 192 agents reference
│   ├── agent-skills.md          # Skill reference
│   ├── usage.md                 # Commands, workflows, examples
│   ├── authoring.md             # Portable-content style guide
│   └── harnesses.md             # Per-harness capability matrix
└── tools/adapters/gemini.py     # Gemini adapter (tool remapping, model mapping)
```

## Discovering available resources

### Plugins (84 total)

Browse the full catalog:

```bash
ls ~/.gemini/extensions/claude-code-workflows/plugins/
```

Or read the structured reference:
`~/.gemini/extensions/claude-code-workflows/docs/plugins.md`

Key domains covered:

| Domain | Example plugins |
|--------|----------------|
| Languages | `python-development`, `javascript-typescript`, `jvm-languages`, `julia-development`, `systems-programming`, `shell-scripting` |
| Backend | `backend-development`, `api-scaffolding`, `api-testing-observability` |
| Frontend | `frontend-mobile-development`, `ui-design`, `brand-landingpage` |
| Infrastructure | `cloud-infrastructure`, `kubernetes-operations`, `cicd-automation`, `deployment-strategies` |
| Data | `data-engineering`, `database-design`, `database-migrations`, `data-validation-suite` |
| Security | `security-compliance`, `security-scanning`, `backend-api-security`, `frontend-mobile-security` |
| ML/AI | `machine-learning-ops`, `llm-application-dev` |
| Testing | `tdd-workflows`, `unit-testing`, `performance-testing-review` |
| DevOps | `incident-response`, `observability-monitoring`, `deployment-validation` |
| Business | `business-analytics`, `startup-business-analyst`, `content-marketing` |
| Docs | `code-documentation`, `documentation-generation`, `documentation-standards` |
| Special | `game-development`, `blockchain-web3`, `quantitative-trading`, `reverse-engineering` |

### Subagents (192 total)

Invoke with `@<agent>`. Find agents for a plugin:

```bash
ls ~/.gemini/extensions/claude-code-workflows/plugins/<plugin>/agents/
```

Full reference: `~/.gemini/extensions/claude-code-workflows/docs/agents.md`

### Skills (156 total)

Skills are loaded on demand via progressive disclosure. Find skills for a plugin:

```bash
ls ~/.gemini/extensions/claude-code-workflows/plugins/<plugin>/skills/
```

Full reference: `~/.gemini/extensions/claude-code-workflows/docs/agent-skills.md`

### Slash commands (102 total)

Use `/<plugin>:<command>`. Full usage reference:
`~/.gemini/extensions/claude-code-workflows/docs/usage.md`

## Gemini-specific differences

| Capability | Claude Code | Gemini CLI / Antigravity |
|---|---|---|
| Plugin install | `/plugin install` | `gemini extensions install <url>` |
| Context file | reads `CLAUDE.md` | reads via `gemini-extension.json` → `AGENTS.md` |
| Tool allowlist | `tools:` always | `tools:` honored, remapped to Gemini-native names |
| Skill/agent discovery | native | native (`skills/`, `agents/` at extension root) |
| Model assignment | per-agent | session-level (override via `model:` frontmatter) |
| `TodoWrite` tool | yes | no equivalent |

## Regenerating artifacts

If plugin sources change, regenerate Gemini-native artifacts:

```bash
cd ~/.gemini/extensions/claude-code-workflows
make generate HARNESS=gemini                         # all plugins
make generate HARNESS=gemini PLUGIN=python-development  # one plugin
make clean-generated HARNESS=gemini                  # remove output
```

## Quality gates

Run before trusting changes to plugin sources:

```bash
make validate STRICT=1     # structural validation
make garden                # drift detection (dead links, stale artifacts)
make test                  # full pytest suite
make smoke-test            # real CLI subprocess tests
```

## Progressive disclosure model

Context loading follows a hierarchy to minimize token usage:

1. **AGENTS.md** (~77 lines) — map/table-of-contents, loaded every session
2. **Skills** — loaded on demand when the agent determines relevance
3. **docs/** — loaded when an agent navigates for reference detail
4. **references/details.md** — supplementary detail within skills (8KB body cap)

Keep this in mind: don't dump entire plugin catalogs. Navigate incrementally.

## Combining plugins for multi-domain tasks

Example workflow — "deploy a secure Python API":

1. `python-development` → scaffold FastAPI project
2. `backend-api-security` → security audit
3. `unit-testing` + `tdd-workflows` → test coverage
4. `cicd-automation` → CI/CD pipeline
5. `deployment-strategies` → deploy with rollback
6. `observability-monitoring` → monitoring and alerting

## Common pitfalls

1. **Don't hand-edit generated files** — always modify source in `plugins/` then
   `make generate`.
2. **Don't confuse top-level `skills/`** with `plugins/*/skills/`. Top-level is
   Gemini output; source-of-truth is `plugins/`.
3. **Don't load everything at once** — use progressive disclosure. Navigate to
   relevant docs/skills on demand.
4. **Model aliases differ** — Gemini doesn't support per-agent model tiers the
   same way Claude Code does. Session-level model applies unless overridden.
