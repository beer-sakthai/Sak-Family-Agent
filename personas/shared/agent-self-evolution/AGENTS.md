# Self-evolution for the six Sak Family agents

`evolve_agent.sh` wires this framework to the six Sak Family agents that run on
the local Hermes gateway, so each can evolve its own skills and keep the result
inside its standalone repo export before it is published.

| agent      | profile dir (`HERMES_AGENT_REPO`)        | standalone repo export                    |
|------------|------------------------------------------|-------------------------------------------|
| `sakking`  | `~/.hermes`                              | `build/agent-repos/sakking`               |
| `sakthai`  | `~/.hermes/profiles/sakthai`             | `build/agent-repos/sakthai`               |
| `saksee`   | `~/.hermes/profiles/saksee`              | `build/agent-repos/saksee`                |
| `saksit`   | `~/.hermes/profiles/saksit`              | `build/agent-repos/saksit`                |
| `saktan`   | `~/.hermes/profiles/saktan`              | `build/agent-repos/saktan`                |
| `sakjules` | `~/.hermes/profiles/sakjules`            | `build/agent-repos/sakjules`              |

> The lead, **SakKing**, lives on the reserved default profile (`~/.hermes`).
> "Hermes" is only the framework. Source of truth for repo export is the
> `Sak-Family-Agent` workspace and its `personas/` plus `infra/hermes-agents/`
> profile trees.

## Six-stage workflow

Each agent uses self-evolution inside the family cycle:

1. **Dream** — choose the skill, prompt, or tool behavior to improve.
2. **Hope** — define the eval source, iterations, and expected improvement.
3. **Care** — run evolution with guardrails and preserve semantic intent.
4. **Joy** — package the winning variant as a repo change or PR.
5. **Trust** — run tests and review before changing live behavior.
6. **Growth** — merge the learning back into the agent's own repo and profile.

## Usage

```bash
# Validate setup for free (no API spend):
./evolve_agent.sh saksit --skill github-auth --dry-run

# Real evolution → opens a PR on beer-sakthai/saksit-skills for review:
export OPENAI_API_KEY=sk-...          # GEPA default models are openai/*
./evolve_agent.sh saksit --skill github-auth --iterations 8

# Evolve, auto-merge the PR, AND apply the result to the live profile:
./evolve_agent.sh sakthai --skill arxiv --merge --apply

# Just (re)sync an agent's current skills as the baseline on main:
./evolve_agent.sh saksee --bootstrap
```

## Flags added by the wrapper

- `--apply`  also copy the evolved skill into the **live** profile (changes agent behavior).
- `--merge`  squash-merge the PR after pushing (default: open PR only, for review).
- `--no-push`  do everything locally; skip GitHub.
- `--bootstrap`  only create the repo + push current skills, then exit.
- `--dry-run`  forwarded to `evolve_skill` — validate, no API calls.

Everything else (`--iterations`, `--optimizer-model`, `--eval-source`,
`--run-tests`, …) is forwarded verbatim to `python -m evolution.skills.evolve_skill`.

## Safety

- The live agent is **never** modified unless you pass `--apply`. By default the
  evolved skill only lands as a PR on the agent's repo for review.
- Only the `skills/` tree is published; `.env`, auth, tokens, and secrets are
  excluded from every push. Repos are created **private**.
