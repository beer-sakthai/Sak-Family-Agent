# Sak Ecosystem — Agent Roles & Cross-Agent Communication

> Reference for how SakTan interacts with sibling agents.  
> Updated: July 4, 2026

---

## The Six Sak Agents

Each agent runs under a dedicated Hermes profile at `/opt/data/profiles/<name>/` and is responsible for a specific domain.

| Agent | Profile Path | Role | Telegram Handle |
|-------|-------------|------|-----------------|
| **SakKing** | — (infra host) | Master of infrastructure, deployment, hosting | — |
| **SakThai** | `/opt/data/profiles/sakthai/` | Master of AI/ML, HuggingFace, MCP, agent frameworks | @SakThai_Agent_bot |
| **SakSee** | `/opt/data/profiles/saksee/` | Master of web/Playwright, QA, testing automation | @SakSee_Agent_bot |
| **SakSit** | `/opt/data/profiles/saksit/` | Master of social media, content, Instagram | @SakSit_Agent_bot |
| **SakTan** | `/opt/data/profiles/saktan/` | Daily ops helper — calendar, email, life admin, creative | @SakTan_Agent_bot |
| **SakJules** | `/opt/data/profiles/sakjules/` | Master of automation, CI/CD, GitHub repo management, auditing | @SakJules_Agent_bot |

All agents share the same Linux machine, running as user `hermes`.

---

## Shared Workspace: `/opt/data/house-of-sak-report/`

**This is the cross-agent communication channel.** All agents can read and write here (directory is `rwxrwxr-x`).

### Inbox Pattern

To hand off a task to another agent, create an inbox file:

```
/opt/data/house-of-sak-report/INBOX-<agent>.md
```

Example created by SakTan:

```markdown
# 📥 SakJules Inbox — Handover: saktan-skills Repository

**From:** SakTan  
**Date:** July 4, 2026

- Repo: https://github.com/beer-sakthai/saktan-skills (public, main)
- Existing content: skills/saktan-soul-engine/SKILL.md pushed
- Next steps for SakJules: update README, add more skills, organize structure
```

### Existing Shared Documents

The house-of-sak contains cross-agent working documents:

| File | Purpose |
|------|---------|
| `SERVICES.md` | Service packages offered by each agent (pricing, scope) |
| `PLAN.md` | Current plan / roadmap |
| `DREAM.md` | Vision documents |
| `AUDIT.md` | Audit findings |
| `CRISIS.md` | Incident management |
| `LESSONS.md` | Lessons learned (maintained by SakSee) |
| `VERIFY.md` | Verification results |
| `INBOX-*.md` | Agent-to-agent task handoffs |

---

## Domain Boundaries

Each agent has a primary domain. Do NOT use another agent's tools unless explicitly asked:

| Agent | Owns | Tools to avoid without invitation |
|-------|------|----------------------------------|
| **SakJules** | GitHub repos, CI/CD pipelines, auditing | `GITHUB_*` Composio tools, `gh` CLI for repo management |
| **SakThai** | HuggingFace, model deployment, agent frameworks | `hf` CLI, HuggingFace API |
| **SakSee** | Playwright, web QA, testing | Playwright/browser testing on non-scoped sites |
| **SakSit** | Social media posting (Instagram, X) | `instagram_*`, `xurl` tools |
| **SakKing** | Infrastructure (Azure, Render, Vercel) | Infra deployment tools |

When you accidentally cross a boundary (e.g. SakTan creating a GitHub repo), hand it off via an inbox file and explicitly cede the domain.

---

## Agent Discovery

To learn about a sibling agent:

1. Read their SOUL.md: `/opt/data/profiles/<name>/SOUL.md`
2. Check their memories: `/opt/data/profiles/<name>/memories/MEMORY.md`
3. Look at shared workspace: `/opt/data/house-of-sak-report/`

---