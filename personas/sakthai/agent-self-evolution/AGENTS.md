# Self-evolution for the six Sak Family agents

`evolve_agent.sh` wires this framework to all six Sak Family agents, so each
can evolve its own skills and keep the result inside its standalone repo
export before it is published.

| agent      | skill source (composed automatically)        | standalone repo export        |
|------------|-----------------------------------------------|--------------------------------|
| `sakthai`  | `personas/sakthai` (+ `personas/shared`)       | `build/agent-repos/sakthai`   |
| `sakking`  | `personas/sakking` (+ `personas/shared`)       | `build/agent-repos/sakking`   |
| `saksee`   | `personas/saksee` (+ `personas/shared`)        | `build/agent-repos/saksee`    |
| `saksit`   | `personas/saksit` (+ `personas/shared`)        | `build/agent-repos/saksit`    |
| `saktan`   | `personas/saktan` (+ `personas/shared`)        | `build/agent-repos/saktan`    |
| `sakjules` | `personas/sakjules` (+ `personas/shared`)      | `build/agent-repos/sakjules`  |

> `evolve_agent.sh` materializes each agent's skill source itself, on every
> run, via `scripts/compose_persona.py <agent> --out $SAKTHAI_EVOLUTION_CACHE/<agent>/skills`
> (defaults to `~/.cache/sakthai-evolution/profiles/<agent>`) — the same
> shared+overlay composition every persona's runtime tree uses. This needs no
> installed Hermes CLI and no pre-existing `~/.hermes/profiles/*` — evolution
> only ever reads a `skills/` directory of `SKILL.md` files.
>
> **Not yet implemented:** a genuine `hermes`-CLI-managed profile per agent
> (`hermes profile create`, `infra/hermes-agents/`) is a separate, deferred
> initiative. "Hermes" here names the evolution framework this package is
> based on, not a currently-running gateway — the live deployment is
> Hermes-free (see `infra/vm-agents/README.md`).

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

# The three most recently added agents work the same way:
./evolve_agent.sh sakking  --skill <name> --dry-run
./evolve_agent.sh saktan   --skill SakTan-daily-briefing --dry-run
./evolve_agent.sh sakjules --skill SakJules-devsecops --dry-run
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
