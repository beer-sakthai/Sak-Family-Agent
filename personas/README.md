# Personas

Six core agent personas — **sakthai**, **sakking**, **saksee**, **saksit**,
**saktan**, and **sakjules** — each formerly had its own `*-skills`
repository. 

Today, they collectively host **877 specialized skills** in their overlays
(counted as `SKILL.md` files on disk — see the per-persona counts in the
layout below), plus 3 shared skills. Most of that content
lives directly within each persona's own `skills/` folder (its overlay); a
small number of files that are byte-identical across **all six** personas
live once under `personas/shared/skills/` instead. This allows each agent to
maintain a perfectly tailored skill tree while securely sharing the same
monorepo base.

The dedicated business scaffold for quote generation and lead capture
workflows, **servicequotebot**, lives under `services/servicequotebot/`.

## Layout

```text
personas/
├── sakthai/
│   ├── SOUL.md         # the persona's identity (unique per persona)
│   ├── config/         # persona config (config.yaml, gateway_voice_mode.json, …)
│   └── skills/         # Contains the 175 skills mapped to SakThai
├── sakking/            # Contains the 355 skills mapped to SakKing (incl. its rollup of the other five)
├── saksit/             # Contains the 156 skills mapped to SakSit
├── saktan/             # Contains the 82 skills mapped to SakTan
├── sakjules/           # Contains the 57 skills mapped to SakJules
└── saksee/             # Contains the 52 skills mapped to SakSee
```

## Composition rule

A persona's full skill tree is `personas/shared/skills/` (laid down first)
plus that persona's own `skills/` directory (copied on top). On any path
collision, the persona's own **overlay wins** — the same "later wins"
precedence the agent's tool registry uses (`ToolRegistry.with_tools()`).

`personas/shared/skills/` only contains files that are byte-identical across
**all six** personas — currently 3 skills (`Sak-auto-cycle-loop`,
`Sak-dogfood`, `Sak-yuanbao`).
This is intentionally conservative: `compose()` applies `shared/skills/` to
every persona unconditionally, so promoting a file there is only safe if
every persona already has that exact content — otherwise it would add
content to personas that never had it. Most of the apparent overlap between
personas (including everything in `sakking`'s `SakXxx-`-prefixed rollup,
which deliberately aggregates the other five personas' skills — SakKing
"owns all skills" per `docs/SOUL.md`, while SakThai is the family's Lead &
Orchestrator) is only a **partial** match (2–5 personas, or one persona plus
sakking's copy of it),
so it stays in each persona's own overlay rather than being deduped.

Skill folder/frontmatter names follow the convention enforced by
`sakthai skills validate --naming`: shared skills get a `Sak-` prefix,
persona-owned skills get `Sak<Name>-` (e.g. `SakThai-`, `SakSit-`). Applied
across all layers via `scripts/rename_skills.py --apply` on 2026-07-07; 31
pre-existing name collisions (a differently-prefixed duplicate with
different content already occupying the target name) were deliberately left
unrenamed pending a human decision on which content wins.

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
