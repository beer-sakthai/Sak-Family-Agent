# Personas

Six core agent personas — **sakthai**, **sakking**, **saksee**, **saksit**,
**saktan**, and **sakjules** — each formerly had its own `*-skills`
repository. They were ~90% identical, with the same skill library copied across
each. In this monorepo, that shared content lives **once**.

The repo also includes a dedicated business persona scaffold,
**servicequotebot**, for quote generation and lead capture workflows.

## Layout

```
personas/
├── shared/skills/      # the 446 skill files identical across all five personas
├── sakthai/
│   ├── SOUL.md         # the persona's identity (unique per persona)
│   ├── config/         # persona config (config.yaml, gateway_voice_mode.json, …)
│   └── skills/         # OVERLAY: only skills unique to or differing in this persona
├── sakking/  …
├── saksee/   …
├── saksit/   …
├── saktan/   …        # scaffolded from infra/hermes-agents/profiles/saktan/
└── servicequotebot/    # business quoting persona scaffold
```

`shared/skills/` + a persona's `skills/` overlay together reconstitute that
persona's complete, original skill tree.

## Composition rule

A persona's full skill set = **shared library first, then its own overlay on
top**. On any path collision the **overlay wins** — the same "later wins"
precedence the agent's tool registry uses (`ToolRegistry.with_tools()`).

To materialise a persona's full tree (e.g. for a runtime that expects one
directory):

```bash
python scripts/compose_persona.py sakthai --out /tmp/sakthai-skills
```

The composed tree is byte-for-byte identical to the persona's
pre-consolidation `skills/` directory. `compose_persona.py --check EXPECTED`
verifies a composed tree against a snapshot.

## How to add or change a skill

- **Affects every persona** → edit it under `shared/skills/`.
- **Specific to one persona** (or that persona needs a different version) →
  place/edit it under `personas/<name>/skills/`; it shadows the shared copy.

## Runtime artifacts

`.hub/`, `.curator_state`, `.usage.json`, and `.bundled_manifest` under a
persona's `skills/` are regenerated caches/state, not authored content. They are
git-ignored going forward (see root `.gitignore`); existing snapshots are kept
so each persona still round-trips exactly.

## Standalone exports

When you need a separate repo for one persona, use the export helper from the
source workspace:

```bash
python scripts/export_agent_repo.py sakjules --out build/agent-repos/sakjules
```

That export keeps the shared core plus the selected persona overlay and profile,
so the standalone repo can own its own skills, tools, and runtime settings.
