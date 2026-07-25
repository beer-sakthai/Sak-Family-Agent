# SakThai Skills

Self-evolving Hermes skills for the SakThai Agent — the **Main Lead of the House**.

This repo backs up the live skill library from `~/profiles/sakthai/skills/`. Every skill is a reusable procedure with YAML frontmatter, markdown body, and optional references/templates/scripts.

## Structure

```
skills/
  autonomous-ai-agents/    — Codex, Claude Code, OpenCode, Hermes Agent
  communication/           — User communication preferences
  computer-use/            — Desktop automation
  creative/                — Humanizer
  data-science/            — Jupyter live kernel
  dogfood/                 — Exploratory QA
  email/                   — Email category placeholder
  environment-automation/  — Workspace conventions
  github/                  — GitHub auth, code review, PR workflow, issues, repo mgmt
  media/                   — Media category placeholder
  mlops/                   — HF Hub, vLLM, lm-eval-harness, W&B, model publishing
  note-taking/             — Notes category placeholder
  productivity/            — Productivity placeholder
  research/                — arXiv, blogwatcher, LLM wiki, research references
  sak-family-handoff/      — Multi-agent handoff protocol
  social-media/            — Social media placeholder
  software-development/    — TDD, debugging, code review, planning, spikes
  telegram-media/          — Native Telegram media delivery
```

## Stats

- **86 files** across **18 category directories**
- **36 SKILL.md files** — each defines a reusable procedure with frontmatter metadata
- Managed by the SakThai Agent on Hermes

## Updating

Skills are synced from the live Hermes agent. To update:

```bash
git clone https://github.com/beer-sakthai/sakthai-skills.git
cp -a ~/profiles/sakthai/skills/. sakthai-skills/skills/
cd sakthai-skills
git add -A
git commit -m "sync skills"
git push
```

## Owner

**Beer** — SakThai Agent, Main Lead of the House & Master of Hugging Face.
