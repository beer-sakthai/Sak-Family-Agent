# Personas

Six core agent personas — **sakthai**, **sakking**, **saksee**, **saksit**,
**saktan**, and **sakjules** — each formerly had its own `*-skills`
repository. 

Today, they collectively host **999 specialized skills** in their overlays
(counted as skill directories and files on disk — see the per-persona counts in the
layout below), plus 36 shared skills. Most of that content
lives directly within each persona's own `skills/` folder (its overlay); files
that are byte-identical across **all six** personas live once under
`personas/shared/skills/` instead. This allows each agent to
maintain a perfectly tailored skill tree while securely sharing the same
monorepo base.

The dedicated business scaffold for quote generation and lead capture
workflows, **servicequotebot**, lives under `services/servicequotebot/`.

## Layout

```text
personas/
├── sakthai/            # Main Lead — HF master, ML, code, research
│   ├── SOUL.md         # Identity, charge system, principles
│   ├── config/         # persona config (config.yaml, gateway_voice_mode.json, …)
│   └── skills/         # Contains the 390 skills mapped to SakThai
├── sakking/            # Contains the 299 skills mapped to SakKing
├── saksit/             # Contains the 201 skills mapped to SakSit
├── sakjules/           # Contains the 8 skills mapped to SakJules
├── saksee/             # Contains the 87 skills mapped to SakSee
└── saktan/             # Contains the 14 skills mapped to SakTan
```

## Composition rule

A persona's full skill tree is `personas/shared/skills/` (laid down first)
plus that persona's own `skills/` directory (copied on top). On any path
collision, the persona's own **overlay wins** — the same "later wins"
precedence the agent's tool registry uses (`ToolRegistry.with_tools()`).

`personas/shared/skills/` only contains skills genuinely common to **all six**
personas — currently 36 (including `Sak-auto-cycle-loop`, `Sak-dogfood`,
`Sak-yuanbao`, plus 33 promoted in a 2026-08 reconciliation pass covering the
cycle-\* stage skills, dev-tool skills like `claude-code`/`codex`/`opencode`,
and integration skills like `google-workspace`/`notion`/`airtable`). This is
intentionally conservative: `compose()` applies `shared/skills/` to every
persona unconditionally, so promoting a file there is only safe if every
persona's content genuinely agrees. In practice, most personas' copies of a
"duplicated" skill had already drifted — truncated/corrupted copies, a
divergent methodology, or an outright bug (e.g. a script importing a helper
module that only existed in one persona's tree) — so promotion doubled as a
correctness pass: each promoted skill's canonical content was picked from
whichever persona(s) had the complete/correct version, not assumed from
whichever copy happened to be checked first. Skills that turned out to be
genuine forks with no single correct version (differing by more than
persona-specific naming) were left in each persona's own overlay rather than
force-merged. Most of the remaining apparent overlap between personas
(including everything in `sakking`'s `SakXxx-`-prefixed rollup, which
deliberately aggregates the other five personas' skills — SakKing "owns all
skills" per `docs/SOUL.md`, while SakThai is the family's Lead & Orchestrator)
is only a **partial** match (2–5 personas, or one persona plus sakking's copy
of it), so it stays in each persona's own overlay rather than being deduped.

The same 2026-08 pass also fixed a separate, sakthai-only bug: `personas/sakthai/skills/`
had accumulated a parallel category-nested tree (`mlops/`, `software-development/`, `github/`,
etc., ~130 folders) alongside the flat `SakThai-*` convention, left over from an earlier,
never-completed migration. Because `collect_skills()` walks recursively with no per-name
dedup, ~106 skills were being discovered twice — and the nested copy, not the flat one,
silently won at prompt-injection time. That tree has been flattened: overlapping pairs kept
the flat copy, nested-only skills were promoted to flat top-level, and `collect_skills()` now
skips dot-prefixed directories and dedupes by skill name as a backstop against this recurring.

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

## Memory

Each persona gets its own memory shard, `~/.sakthai/<persona>/memory.db`,
separate from the legacy unscoped `~/.sakthai/memory.db`. On the VM deployment
this falls out of `infra/vm-agents/sakthai-agent-run.sh` setting
`SAKTHAI_HOME=$HOME/.sakthai/$AGENT` per persona process; for local dev, pass
`--persona <name>` to `learn`/`recall`/`run`/`chat`/`memory <subcommand>`
instead of exporting `SAKTHAI_HOME` yourself. `sakthai memory family` opens a
read-only, deduplicated view across every persona's shard at once (`--personas
a,b,c` to scope it) — useful for seeing what the family collectively knows
without picking one persona's point of view. Full details, including why
`memory sync`/`memory pull`/`run --sandbox` don't accept `--persona`, are in
`CLAUDE.md`'s "Per-persona memory sharding" section.

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
