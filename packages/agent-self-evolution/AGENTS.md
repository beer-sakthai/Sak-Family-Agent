# Self-evolution for the four sibling Hermes agents

`evolve_agent.sh` wires this framework to the four Telegram agents that run on
the local Hermes gateway, so each can evolve its own skills and commit/push the
result to its **own** private GitHub repo (one repo per agent).

| agent     | profile dir (`HERMES_AGENT_REPO`)        | GitHub repo                   |
|-----------|------------------------------------------|-------------------------------|
| `hermes`  | `~/.hermes`                              | `beer-sakthai/hermes-skills`  |
| `sakthai` | `~/.hermes/profiles/sakthai`            | `beer-sakthai/sakthai-skills` |
| `saksee`  | `~/.hermes/profiles/saksee`             | `beer-sakthai/saksee-skills`  |
| `saksit`  | `~/.hermes/profiles/saksit`             | `beer-sakthai/saksit-skills`  |

> Profile dirs were renamed on 2026-06-21 and now **match** identities
> (`sakthai`→SakThai, `saksee`→SakSee, `saksit`→SakSit). The lead, **SakKing**,
> lives on the reserved `default` profile (`~/.hermes`). "Hermes" is only the
> framework. Source of truth: `~/.hermes/shared/agents-roster.md`.

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
