# SakThai Skills Directory

**Curated specialized skills for the SakThai Agent — the Main Lead of the House of Sak.**

This directory contains the specialized overlay skills tailored for SakThai. Every skill is a reusable, deterministic procedure with YAML frontmatter, markdown instructions, and optional templates, workflows, or scripts.

---

## Structure & Domains

Skills are organized under the standardized `Sak<Agent>-<domain>-<topic>` taxonomy:

- **Autonomous AI Agents**: Codex, Claude Code, OpenCode, and Antigravity SDK workflows.
- **MLOps & Hugging Face**: Hugging Face Hub operations, Spaces, datasets, vLLM, and model publishing with break-glass safety verification.
- **Research & Data Science**: arXiv paper digestion, literature exploration, and research synthesis.
- **Software Development**: TDD disciplines, systematic debugging, code review, and planning.
- **Multi-Agent Coordination**: Cross-persona handoffs, task delegation, and memory synchronization.

---

## Discovery & Validation

Skills are automatically discovered and composed by `sakthai`:

```bash
# List all skills accessible to SakThai
uv run sakthai skills list

# Validate all skill frontmatter
uv run sakthai skills validate
```

---

## License

MIT — © 2026 Beer SakThai / House of Sak
