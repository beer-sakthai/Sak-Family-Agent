# ADR-0001: Managing the six-persona package code duplication

**Status:** Proposed
**Date:** 2026-11-22
**Deciders:** SakThai (lead) · repo maintainer (Beer)

## Context

The repo ships six personas under `personas/` (sakking, sakthai, saksee, saksit,
sakjules, saktan). Exactly one of them is a build target: `personas/sakthai/` is
what `pyproject.toml` installs (`[tool.setuptools.package-dir] sakthai =
"personas/sakthai"`), what `import sakthai` resolves to, and what
mypy/ruff/bandit/pytest run against.

The other five persona directories each carry a **full, real copy** of the
package tree (`agent/`, `cli/`, `memory/`, `mcp/`, `web/`, …) next to their own
`SOUL.md`, `skills/`, `config/`, and `evolution/`. Only `personas/sakthai/` is
installed and run; the five copies are never imported.

**Measured on 2026-11-22 at the current checkout:**

- 184 `.py` files in the canonical package.
- All five copies are **byte-identical in code** to canonical (`diff -rq … -x
  skills -x config -x '*.md' -x evolution`). The only non-match is a binary
  `reports/phase1_validation_report.pdf` in sakjules — not source.
- **Content parity is CI-enforced for only three files:**
  `agent/guardrails.py` (`test_persona_guardrails_parity.py`), `web/server.py`
  (`test_persona_web_server_parity.py`), and `agent/eval.py`
  (`test_persona_eval_parity.py`).
- `test_persona_structure_parity.py` checks that every persona has the **same
  set** of top-level items, and `test_skills_organization_parity.py` covers
  skill layout — but **no test compares the content of the other ~181 `.py`
  files.**

### Forces at play

- **Silent drift is the core risk.** A change to a canonical file outside the
  three parity-pinned ones must be hand-copied to five places or the copies
  diverge with nothing failing CI. The three pinned files are precisely the
  ones where a one-copy-only fix already bit us (guardrails bypasses; the
  cookie-construction autofixes #1214/#1219 that landed in one copy; web/server
  drifting 147 lines behind before its parity test existed).
- **The copies cost real bytes and review noise** — ~181 files × 5 = ~905
  redundant tracked files, every one of which shows up in a tree-wide diff.
- **A repo-native precedent already exists for "generate, don't duplicate."**
  `scripts/compose_persona.py` does exactly this for the *skills* tree: shared
  files live once under `personas/shared/skills/`, each persona keeps only an
  overlay, and the full runnable tree is reconstituted byte-for-byte on demand
  (`make compose-personas`). The package code has not been given the same
  treatment.
- **Whatever we choose must preserve what makes a persona a persona:** its own
  `SOUL.md`, `skills/`, `config/` (model/provider defaults, `mcp.json`), and
  `evolution/`. Those are genuinely per-persona and are *not* duplication.
- **Runtime is unaffected either way** — only `personas/sakthai/` is ever
  installed. This decision is about source-tree maintainability, not behavior.

## Decision

Adopt a two-step path: **immediately close the silent-drift gap (Option B), and
commit to migrating the package code onto the existing overlay/compose model
(Option C) as the durable end state.** Keep the per-persona `SOUL.md`, `skills/`,
`config/`, and `evolution/` exactly as they are — they are not duplication.

Rationale: Option B is cheap, reversible, and stops the bleeding this week;
Option C removes the duplication at the root and reuses machinery the repo
already trusts for skills. Doing B first de-risks C by guaranteeing the copies
are identical at the moment we switch to generating them.

## Options Considered

### Option A: Status quo — hand-sync, three parity-pinned files

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low (nothing to build) |
| Cost | Low upfront, high ongoing (manual sync forever) |
| Scalability | Poor — risk grows with every new shared module |
| Team familiarity | High |

**Pros:** No work. Copies are runnable/inspectable in place.
**Cons:** ~181 files per copy can drift silently; relies on author discipline;
the failure mode (a security fix in one copy only) is exactly the high-severity
one.

### Option B: Full-tree content parity test

Extend the parity suite to assert every `.py` file in each copy is byte-identical
to canonical (the same mechanism the three existing parity tests use, widened
to the whole package tree). Hand-sync continues, but **drift can no longer land
silently** — CI fails the moment any copy diverges.

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low (one generalised test; precedent in-tree) |
| Cost | Low |
| Scalability | Medium — catches drift but doesn't remove the duplication |
| Team familiarity | High |

**Pros:** Closes the silent-drift hole immediately; tiny diff; fully reversible;
no change to packaging or developer workflow.
**Cons:** The duplication (and its review noise / byte cost) remains; a legitimate
canonical change now makes CI red until the author copies it five times (a
`make sync-personas` helper mitigates this).

### Option C: Single source + generated copies (overlay/compose model)

Treat the package code the way `compose_persona.py` already treats skills:
canonical code lives once; each persona keeps only its genuinely-own files
(`SOUL.md`, `skills/`, `config/`, `evolution/`) plus any true per-persona code
override as an overlay. The full per-persona tree becomes a **build artifact**
produced by `make compose-personas` / `export-agent-repo`, not committed source.

| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium–High (migration + update generators, .gitignore, CI) |
| Cost | Higher upfront, lowest ongoing |
| Scalability | Best — duplication removed at the root |
| Team familiarity | Medium (compose machinery already exists for skills) |

**Pros:** Eliminates ~900 redundant files; one place to change code; reuses a
pattern the repo already trusts; export/standalone snapshots still work via the
generators.
**Cons:** Larger migration; must confirm nothing depends on the copies existing
as committed files (exports, `diagnose_personas.py`, any path that reads a
non-sakthai copy); changes what contributors see on disk.

### Option D: Symlink the package into each persona

Replace each copy with a symlink to `personas/sakthai/`'s package subdirs.

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | Low |
| Scalability | Medium |
| Team familiarity | Medium |

**Pros:** Zero duplication; trivially always-in-sync.
**Cons:** Symlinks are fragile across Windows checkouts (the skills declare
`platforms: [..., windows]`), archive/export tooling, and some CI runners; and a
symlink can't express a genuine per-persona code override the way an overlay can.
Rejected as the primary path for cross-platform fragility; usable as a dev-only
convenience.

## Trade-off Analysis

The decisive trade-off is **time-to-safety vs. root-cause removal.** Option B
buys safety almost immediately at near-zero cost but leaves the duplication;
Option C removes the duplication but is a multi-step migration with a real risk
surface (export tooling, path assumptions). They are complementary, not
competing: B is the guardrail that makes C safe to attempt, because it proves
the copies are identical at the cut-over and keeps them honest during the
transition. Option D's always-in-sync appeal is real but its Windows/export
fragility disqualifies it as the committed-source mechanism in a repo that
targets Windows.

## Consequences

- **Easier:** security/behavior fixes apply once and can't silently miss a
  copy; tree-wide diffs shrink; new shared modules stop multiplying the risk.
- **Harder (short term, Option B):** a canonical change turns CI red until synced
  — mitigated by a `make sync-personas` target that copies canonical → the five.
- **Harder (Option C migration):** must audit everything that assumes the copies
  exist as committed files (`scripts/export_agent_repo.py`,
  `scripts/diagnose_personas.py`, any non-sakthai import path) before deleting
  them from source control.
- **To revisit:** if Option C's migration proves too invasive, Option B alone is
  an acceptable long-term resting point — it removes the dangerous failure mode
  even though it keeps the bytes.

## Action Items

1. [x] 2026-11-22 **(Option B, now)** Generalise the parity suite to a full-tree
   byte-identity check over every `.py` in each persona copy; add a
   `make sync-personas` helper that copies canonical → the five and verify CI
   goes green. — `tests/test_persona_package_parity.py` walks the whole canonical
   package tree (excluding the per-persona `skills/`/`config/`/`evolution/` and
   the non-runtime `tests/` copy), and `scripts/sync_personas.py`
   (`make sync-personas`) mirrors the canonical code.
2. [x] 2026-11-22 Confirm the three existing parity tests become a subset of the
   new check. — The new walk subsumes `test_persona_structure_parity.py`'s
   hard-coded 15-subpackage byte check and adds the top-level modules and
   `scripts/` it missed; the existing tests are kept as-is (they still pass).
3. [x] 2026-11-22 **(Option C, scoped follow-up)** Spike `compose_persona.py`-style
   code composition for one persona into a throwaway dir; `diff -rq` it against the
   committed copy to prove byte-for-byte equivalence. — **Feasible, proven for all
   five copies.** A throwaway composer laying down canonical shared code and then a
   persona's own overlay reproduced each committed tree with **zero diffs**. The
   per-persona overlay is a bounded 12-item set — `SOUL.md`, `PLAN.md`, `CYCLE.md`,
   `MEMORY.md`, `HANDOFF.md`, `BACKPACK.md`, `README.md`, `AGENTS.md`, `config/`,
   `evolution/`, `reports/`, `skills/` — and everything else (all package `.py`,
   `evolve_agent.sh`, `pyproject.toml`, `tests/`, the library overlay dirs) is
   byte-identical duplication of canonical that Option C can generate from one
   source. This confirms the overlay/compose model carries over cleanly from the
   skills tree to the package code; the remaining risk is in the migration
   mechanics (items 4–5), not the concept.
4. [ ] Audit `export_agent_repo.py` / `diagnose_personas.py` / CI for assumptions
   that the copies exist as committed source.
5. [ ] If the spike holds, migrate copies → overlays, `.gitignore` the generated
   trees, and wire `make compose-personas` into the export path. Land behind its
   own PR with the parity check from step 1 still guarding the transition.
6. [ ] Update `CLAUDE.md`'s "persona package copies" section to describe whichever
   end state ships.
