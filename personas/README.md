# Personas

Six core agent personas — **sakthai**, **sakking**, **saksee**, **saksit**,
**saktan**, and **sakjules** — each formerly had its own `*-skills`
repository. 

Today, they collectively host **671 specialized skills** directly within their individual persona folders. This allows each agent to maintain a perfectly tailored skill tree while securely sharing the same monorepo base.

The dedicated business scaffold for quote generation and lead capture
workflows, **servicequotebot**, lives under `services/servicequotebot/`.

## Layout

```text
personas/
├── sakthai/
│   ├── SOUL.md         # the persona's identity (unique per persona)
│   ├── config/         # persona config (config.yaml, gateway_voice_mode.json, …)
│   └── skills/         # Contains the 181 skills mapped to SakThai
├── saksit/             # Contains the 172 skills mapped to SakSit
├── sakking/            # Contains the 119 skills mapped to SakKing
├── saktan/             # Contains the 85 skills mapped to SakTan
├── sakjules/           # Contains the 59 skills mapped to SakJules
└── saksee/             # Contains the 55 skills mapped to SakSee
```

## Composition rule

A persona's full skill tree is built directly from its `skills/` directory alongside the core framework. On any path collision, the specific **overlay wins** — the same "later wins"
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

Place or edit the skill directly under the respective `personas/<name>/skills/` folder so it is picked up by that specific agent at runtime.

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
