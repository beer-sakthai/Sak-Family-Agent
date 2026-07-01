# Personas

Six agent personas — **sakthai**, **sakking**, **saksee**, **saksit**, **saktan**, **sakjules** — each
formerly its own `*-skills` repository. They were ~90 % identical: the same
skill library copied five times. In the monorepo that shared content lives
**once**.

## Layout

```
personas/
├── shared/skills/      # the 446 skill files identical across all six personas
├── sakthai/
│   ├── SOUL.md         # the persona's identity (unique per persona)
│   ├── config/         # persona config (config.yaml, gateway_voice_mode.json, …)
│   └── skills/         # OVERLAY: only skills unique to or differing in this persona
├── sakking/  …
├── saksee/   …
├── saksit/   …
├── saktan/   …        # scaffolded from infra/hermes-agents/profiles/saktan/
└── sakjules/ …        # scaffolded from infra/hermes-agents/profiles/sakjules/
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

## Follow-up (not yet wired)

Rewiring the agent's skill loader / `sync-sakking` to read the
`shared + overlay` layout directly (rather than via `compose_persona.py`) is a
deliberate follow-up — see the monorepo README.
