# Agent Profile Mapping

Each Sak Family agent has its own profile directory and GitHub skills repo.
Use this table to target the right agent when running evolution.

| Agent | Profile Dir (`HERMES_AGENT_REPO`) | GitHub Skills Repo |
|-------|-----------------------------------|-------------------|
| `sakking` | `~/.hermes` | `beer-sakthai/sakking-skills` |
| `sakthai` | `~/.hermes/profiles/sakthai` | `beer-sakthai/sakthai-skills` |
| `saksee` | `~/.hermes/profiles/saksee` | `beer-sakthai/saksee-skills` |
| `saksit` | `~/.hermes/profiles/saksit` | `beer-sakthai/saksit-skills` |
| `saktan` | `~/.hermes/profiles/saktan` | `beer-sakthai/saktan-skills` |
| `sakjules` | `~/.hermes/profiles/sakjules` | `beer-sakthai/sakjules-skills` |

## Pipeline Location

The evolution pipeline lives in each agent's profile dir under `sak-family-agent/packages/`:

```
/opt/data/profiles/<agent>/sak-family-agent/packages/agent-self-evolution/
├── evolution/          # Python package (skills, tools, prompts, code optimizers)
├── evolve_agent.sh     # Wrapper script
├── pyproject.toml      # Deps: dspy, openai, click, rich, optuna, reportlab
├── tests/              # Test suite
├── output/             # Evolution results (previous runs)
├── datasets/           # Generated eval datasets
└── reports/            # Validation reports
```

NOTE: The standalone Sak-Family-Agent monorepo at `/opt/data/` was removed 2026-07-09.
Only per-profile copies survived. Verify existence before evolving for non-saksit agents.

## Notes

- All repos are created **private** by default
- `.env`, auth tokens, and secrets are **excluded** from every push
- Only the `skills/` tree is published to GitHub
