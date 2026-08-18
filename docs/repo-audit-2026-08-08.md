# Repository Audit & Cleanup Plan — 2026-08-08

Audit of `beer-sakthai/Sak-Family-Agent` at commit `cc6a2572`.

> **Status: executed 2026-08-08.** [§6](#6-execution-commands) has been applied to
> the repository; [§7](#7-verification-results) records the result. The commands
> are kept below as the record of what was run.
>
> **Rollback point: commit `6f470820`** — the last commit before the cleanup,
> which added this document and nothing else. `git revert` the cleanup commit, or
> `git reset --hard 6f470820`. The `pre-cleanup-2026-08-08` tag points at the same
> commit.

**Scale:** 6,172 tracked files, 65.9 MB tracked, 94 MB `.git`, 75 MB working tree.

**Headline:** the most valuable finding is not bloat — it is a `.gitignore` rule
that silently shadows the installed Python package. Fix that before anything
else. See [§1](#1-critical-gitignore-shadows-the-installed-package).

Every command in [§6](#6-execution-commands) was executed end-to-end on a
throwaway clone before this document was written; the results are in
[§7](#7-verification-results). The full suite passes on the cleaned tree
(**1,970 passed, 2 skipped**), and two bugs in an earlier draft of this plan were
caught that way — see [§7](#7-verification-results).

---

## 1. CRITICAL: `.gitignore` shadows the installed package

`.gitignore` line 15 is `personas/*/sakthai/`. That glob matches
`personas/sakthai/sakthai/` — **the package `pyproject.toml` installs**
(`[tool.setuptools.packages.find] where = ["personas/sakthai"]`), the one mypy,
bandit, pylint and coverage all point at.

The existing files survive only because they were committed before the rule
landed; git ignores the rule for already-tracked paths. But **any new file added
to the package is invisible to git**:

```console
$ touch personas/sakthai/sakthai/__ignore_probe.py
$ git status --short personas/sakthai/sakthai/
                       # ← empty. The new module would never be committed.
$ git check-ignore -v --no-index personas/sakthai/sakthai/agent/newfile.py
.gitignore:15:personas/*/sakthai/	personas/sakthai/sakthai/agent/newfile.py
```

Add a module, run the tests locally (they pass — the file is on disk), push, and
CI fails on a fresh clone with `ImportError`. The negation on line 16
(`!personas/shared/sakthai/`) rescues the shared copy but not the real one.

The same class of bug hits `personas/saktan/` (line 10, the whole persona is
ignored). `tests/test_soul_consistency.py` reads `personas/saktan/SOUL.md` off
disk, so a fresh clone that respected that rule would fail CI.

A third instance: `personas/sakthai/skills/.gitignore` contains
`skills/.bundled_manifest`. Patterns containing a slash are anchored to the
`.gitignore`'s own directory, so that rule only ever matches
`personas/sakthai/skills/skills/.bundled_manifest` — a path that does not exist.
The four curator files it was meant to ignore sit one level up and are all
tracked, in every persona.

**112 files are currently "ignored but tracked"** — every one a file that cannot
be updated by a normal `git add`:

| Area | Ignored-but-tracked | Should be |
|---|---:|---|
| `personas/sakthai/` (the installed package) | 73 | **tracked** — un-ignore |
| `personas/saktan/` (a real persona, CI reads it) | 21 | **tracked** — un-ignore |
| `personas/saksee,saksit,sakking/sakthai/` (shadow copies) | 10 | tracked — parity test enforces them |
| `skills/` (orphaned content) | 6 | untrack + delete |
| `.superpowers/` (stale PID files) | 2 | untrack + delete |

The fix narrows the rule to the copies that really are regenerated rather than
untracking the package. Patch in [§5](#5-gitignore-patch).

---

## 2. Reorganization: what to move where

### On the `src/` question

The brief asked for a standard `src/ tests/ docs/ config/` layout. **Don't do
that here, and the reason is specific rather than stylistic.** This is not a
single-package repo wearing an odd layout; it is a monorepo where the package
path is load-bearing:

- `pyproject.toml` pins it twice (`packages.find.where`, `mypy.files` +
  `mypy_path`)
- four CI workflows hard-code `personas/sakthai/sakthai` (`ci.yml`,
  `pylint.yml`, `ossar.yml`, `auto-dependency-update.yml`)
- `scripts/export_agent_repo.py` and `scripts/compose_persona.py` build persona
  snapshots from it
- **10 on-disk symlinks** point at `personas/shared/sakthai/` and
  `../shared/agent-self-evolution` — `git mv` of a target silently breaks them
- `tests/test_persona_guardrails_parity.py` asserts byte-identity between
  `personas/sakthai/sakthai/agent/guardrails.py` and four persona copies

A `src/` move is roughly 20 coordinated edits plus a symlink rebuild, and buys
nothing at runtime — `import sakthai` already resolves correctly via the editable
install. `personas/<name>/` **is** this repo's `src/`, one directory per agent.
Leave it.

What genuinely needs reorganizing is the **repo root**, which carries 41 tracked
files including 5 scratch Python scripts and 5 loose JSON blobs. The target
directories already exist, so this is a pure move.

### Root file → destination

| File(s) | → | Rationale |
|---|---|---|
| `_check_models.py`, `_check_spaces.py`, `_parse_datasets.py`, `_parse_models.py`, `_parse_spaces.py` | `scripts/hf/` | One-off HF scrapers; `scripts/` is already ruff-excluded, so no lint debt |
| `hf-topics-covered.json` | `data/` | Data, not config; `data/` already holds `sample-memory.jsonl` |
| `hf-learnings.md` (368 KB) | `docs/reference/` | A reference document, not a root README |
| `eval_sakthai_bench_colab.ipynb` | `training/notebooks/` | A notebook belongs with the training assets |
| `_cron007_append.md`, `_hf_report_008.md` | *delete* | Zero references anywhere; dated one-off run reports |
| `new_combined_v6_readme.md` | *delete* | Zero references; superseded draft of an HF model card |
| `ci_runs.json` (76 KB) | *delete* | An API-response cache. The skill that consumes it reads `/opt/data/ci_runs.json` on the VM, never the repo copy |
| `hf_dataset.json`, `hf_ds_size.json`, `hf_embed_check.json` | *delete* | 0 bytes each — empty placeholders |
| `LEARNING_JOURNAL.md` (96 KB) | keep at root | 52 inbound references; moving it costs more than it gains |

This matches the `SCRATCH_ORGANISATION_PLAN` already queued in `PLAN.md`, and
extends it to the generated state in [§3](#3-bloat-inventory).

### Docs: resolve the root ↔ `docs/` duplication

Four files exist in **both** the root and `docs/`, and all four **differ**:

| File | Root | `docs/` |
|---|---:|---:|
| `CODE_OF_CONDUCT.md` | 3,364 B | 3,766 B |
| `CONTRIBUTING.md` | 1,135 B | 4,446 B |
| `SECURITY.md` | 4,906 B | 7,707 B |
| `LEARNING_JOURNAL.md` | 98,259 B | 23,892 B |

GitHub renders the **root** copies in its community-health UI, so those are the
ones contributors actually see — and for `CONTRIBUTING.md` and `SECURITY.md` the
root copy is the *thinner* one. This violates the "no duplication — link, don't
copy" working rule in `PLAN.md` in four places.

**Recommended:** merge the richer `docs/` content into the root copy, then
replace each `docs/` file with a one-line pointer. Flagged rather than scripted —
merging prose is a judgment call, not a `mv`.

### Directories that are fine as they are

`personas/`, `tests/`, `library/`, `infra/`, `services/`, `apps/`, `training/`,
`evaluation_tasks/`, `docs/`, `scripts/`, `security/`, `product/` all match the
structure documented in `CLAUDE.md`. No changes proposed.

---

## 3. Bloat inventory

Every candidate below was checked for inbound references. **No test, Makefile
target, or CI workflow references any of them** — verified with:

```bash
git grep -nE "scratch/|assets/|workflow_runs|curator_backups|migrated-repos-archive|ci_runs|_check_models" \
  -- tests scripts Makefile .github
# → no matches
```

### Generated runtime state committed as source — 8.5 MB, ~1,500 files

The Hermes curator and the workflow framework write state into the repo, and it
got committed. `.gitignore` already tries to ignore some of it — the rules are
just mis-anchored (see [§1](#1-critical-gitignore-shadows-the-installed-package)).

| Path | Size | What it is |
|---|---:|---|
| `apps/agent_workflow_framework/.workflow_runs/` | **5.4 MB, 1,394 files** | Per-run JSON logs. The single largest cleanup item in the repo |
| `personas/saksee/skills/SakSee-.curator_backups/` | 2.0 MB | A `skills.tar.gz` snapshot inside a persona skill tree |
| `.curator_backups/` | 0.7 MB | 2 dated `skills.tar.gz` snapshots + manifests |
| `.workflow_runs/` (root) | 0.3 MB, 86 files | Same run logs, root copy |
| `personas/*/skills/.usage.json{,.lock}`, `.bundled_manifest`, `.curator_state` | 0.2 MB, 16 files | Curator state in 4 persona skill trees — what the broken nested `.gitignore` was meant to catch |
| `.usage.json`, `.usage.json.lock`, `.bundled_manifest`, `.curator_state` (root) | 34 KB | Curator run state; `.curator_state` embeds `/opt/data/...` VM paths |
| `.superpowers/brainstorm/*/state/server.pid` | 8 KB | A stale PID (`131940`) from a long-dead process |
| `personas/sakthai/sakthai_agent.egg-info/` | 24 KB, 6 files | setuptools build metadata, regenerated by every editable install — it churns against `README.md` on each `uv sync`. Found during execution, not the initial survey |

### Unreferenced binary assets — 7.5 MB

`assets/sak_family_banner_v3.png` (4.4 MB) and
`assets/core_data_flow_diagram.png` (3.2 MB) are the two largest tracked files in
the repo. `git grep` finds **zero** references — `README.md` embeds no images at
all. 11% of tracked bytes, referenced by nothing.

*(These are branding assets, so confirm they aren't used off-repo — an HF model
card, a Space, a slide deck — before deleting. Step 6 untracks rather than
deletes, keeping both files on disk.)*

### `migrated-repos-archive/` — 2.1 MB, 181 files

Referenced only by `.gitleaks.toml` (an allowlist entry) and `CLAUDE.md` (a
directory listing). Contains `hf-learnings.md`, `hf-learnings.md.bak`, and
`references/hf-learnings.md` — three near-copies of the same 380 KB file — plus a
training log. Git history preserves migrated repos; a directory named "archive"
in a live tree does not need to.

### `skills/` (root) — orphaned, 6 files

`CLAUDE.md` states this is not a skill-discovery root, and `skills.py` confirms
it: `default_skill_roots()` returns `personas/<p>/skills`,
`personas/shared/skills`, `library/`, `~/.sakthai/extensions` — never root
`skills/`. `.gitignore` line 30 already ignores `/skills/`; 6 files predate it.
Dead content the agent can never load.

### `scratch/` — 7 files

Self-described scratch: `fix_all_branch_conflicts.py`,
`force_fix_all_remote_branches.py`, `untitled_prompt.py`,
`get_request_executor.txt`. Two `.txt` files are pasted code fragments. No
inbound references.

### Flagged, not scheduled: `hf-learnings.md` × 187 copies — 5.6 MB

The same reference file is duplicated **187 times** across persona skill trees
(`SakThai-huggingface-hub/references/`, `SakSee-hf-hub-jobs-api/references/`, …),
8.5% of the repo. Per-persona skill overlays are duplicated by design, so this is
not straightforwardly deletable — but it is the largest remaining consolidation
opportunity, and a shared `personas/shared/skills/` reference would collapse it.
**Separate task; deliberately out of scope here.**

---

## 4. Keep vs Delete

### DELETE — zero references, nothing in CI touches them

| Path | Size |
|---|---:|
| `apps/agent_workflow_framework/.workflow_runs/` | 5.4 MB |
| `migrated-repos-archive/` | 2.1 MB |
| `personas/saksee/skills/SakSee-.curator_backups/` | 2.0 MB |
| `.curator_backups/` | 0.7 MB |
| `.workflow_runs/` | 0.3 MB |
| `personas/*/skills/` curator state (16 files) | 0.2 MB |
| `skills/` (root, orphaned) | 0.1 MB |
| `ci_runs.json` | 76 KB |
| `.usage.json`, `.usage.json.lock`, `.bundled_manifest`, `.curator_state` | 34 KB |
| `scratch/` | 32 KB |
| `_cron007_append.md`, `_hf_report_008.md`, `new_combined_v6_readme.md` | 16 KB |
| `.superpowers/` | 8 KB |
| `personas/sakthai/sakthai_agent.egg-info/` | 24 KB |
| `hf_dataset.json`, `hf_ds_size.json`, `hf_embed_check.json` | 0 B |

**Total: ~10.9 MB, ~1,700 files.**

### UNTRACK BUT KEEP ON DISK — verify before removing

| Path | Size | Why not a hard delete |
|---|---:|---|
| `assets/*.png` | 7.5 MB | Branding assets; may be referenced outside the repo |

### MOVE — see [§2](#2-reorganization-what-to-move-where)

`_check_models.py`, `_check_spaces.py`, `_parse_datasets.py`, `_parse_models.py`,
`_parse_spaces.py`, `hf-topics-covered.json`, `hf-learnings.md`,
`eval_sakthai_bench_colab.ipynb`.

### KEEP — explicitly not bloat

| Path | Why |
|---|---|
| `personas/**` | The source tree. Six agents; skill-overlay duplication is by design |
| `tests/` | The single suite — 1,970 tests, 96% coverage floor |
| `library/` | A live skill-discovery root (`CURATED_LIBRARY_DIR`) |
| `sakthai-chat-cli/` (9.8 MB) | Deliberately unmerged fork per `CLAUDE.md`; has a Textual TUI the canonical package lacks |
| `apps/`, `services/`, `infra/`, `training/`, `evaluation_tasks/` | Live subprojects (minus the run logs above) |
| `.specify/`, `.githooks/`, `.claude/`, `.agents/`, `.jules/` | Tooling config, checked in on purpose |
| `LEARNING_JOURNAL.md` | 52 inbound references |
| `bin/omp` | 4 KB shell script, referenced by `.claude/skills/Sak-family-auto-cycle` |
| `uv.lock` (804 KB) | Required; the pre-commit hook verifies it against `pyproject.toml` |
| `profiles/`, `dataset-cards/`, `product/`, `security/`, `data/` | Small, referenced, purposeful |

---

## 5. `.gitignore` patch

Apply **first** — it stops the deleted state from returning and fixes the
package-shadowing bug from [§1](#1-critical-gitignore-shadows-the-installed-package).

Replace lines 10–21 (the `personas/saktan/` rule and the whole
`personas/*/sakthai/` block, including its negations) with:

```gitignore
# Legacy per-persona duplicate package copies. Scoped explicitly rather than
# with `personas/*/sakthai/`: that glob also matched personas/sakthai/sakthai/ —
# the package pyproject.toml installs — which made new modules there invisible
# to `git add`. personas/saktan/ was likewise fully ignored even though
# tests/test_soul_consistency.py reads its SOUL.md from disk.
personas/sakjules/sakthai/
personas/sakking/sakthai/
personas/saksee/sakthai/
personas/saksit/sakthai/
personas/saktan/sakthai/
# Never track regenerated Python caches inside the shared canonical copy.
personas/shared/sakthai/**/__pycache__/
personas/shared/sakthai/**/*.pyc
```

The three *partial* shadow directories under `sakking/`, `saksee/`, `saksit/`
stay tracked — `tests/test_persona_guardrails_parity.py` enforces their contents.
The rules above only stop *new* files appearing there.

Then append:

```gitignore
# --- Generated runtime state -------------------------------------------------
# Hermes curator state, at the repo root and inside every persona skill tree.
# (The pre-existing `skills/.bundled_manifest` rules — here and in
# personas/sakthai/skills/.gitignore — are anchored to their own directory and
# so only ever matched a `skills/skills/` path that does not exist.)
**/.bundled_manifest
**/.curator_state
**/.usage.json
**/.usage.json.lock
**/.curator_backups/
**/*-.curator_backups/

# agent_workflow_framework per-run logs (root copy and the app's own dir).
.workflow_runs/

# HF scratch output — anchored to the root so these can never shadow a real
# data file of the same name deeper in the tree.
/ci_runs.json
/hf_dataset.json
/hf_ds_size.json
/hf_embed_check.json
```

**Anchoring matters more than it looks.** In an earlier draft these were written
unanchored, which pulled 1,394 unrelated files under `apps/` into the ignore set
and (via a bare `assets/`) two persona `.gitkeep` files. Both were caught only by
running the plan — see [§7](#7-verification-results). Keep the `/` prefixes.

---

## 6. Execution commands

Run from the repo root, on a branch, in order. Every command is scoped to a
listed path — no wildcard reaches further than intended.

### Step 0 — safety net

```bash
git status --porcelain          # must be clean before starting
git checkout -b chore/repo-cleanup
git tag pre-cleanup-2026-08-08  # rollback: git reset --hard pre-cleanup-2026-08-08
```

### Step 1 — apply the `.gitignore` patch

Edit `.gitignore` per [§5](#5-gitignore-patch), then prove the package is no
longer shadowed:

```bash
git check-ignore -v --no-index personas/sakthai/sakthai/agent/newfile.py personas/saktan/SOUL.md
# → must print NOTHING and exit 1. If it prints a rule, the patch didn't take.
```

### Step 2 — delete generated runtime state

```bash
git rm -r --cached --quiet .curator_backups .workflow_runs .superpowers \
    personas/saksee/skills/SakSee-.curator_backups \
    apps/agent_workflow_framework/.workflow_runs
git rm --cached --quiet .usage.json .usage.json.lock .bundled_manifest .curator_state \
    personas/*/skills/.usage.json personas/*/skills/.usage.json.lock \
    personas/*/skills/.bundled_manifest personas/*/skills/.curator_state

rm -rf .curator_backups .workflow_runs .superpowers \
    personas/saksee/skills/SakSee-.curator_backups \
    apps/agent_workflow_framework/.workflow_runs
rm -f .usage.json .usage.json.lock .bundled_manifest .curator_state \
    personas/*/skills/.usage.json personas/*/skills/.usage.json.lock \
    personas/*/skills/.bundled_manifest personas/*/skills/.curator_state
```

`git rm --cached` first, then `rm`: the working-tree delete happens only after
git has released the paths, so an interrupted run still leaves a consistent
index. These paths are gitignored by Step 1, which is why they need `--cached`
plus a manual `rm` rather than a plain `git rm`.

### Step 3 — delete orphaned and scratch content

```bash
git rm -r --cached --quiet skills && rm -rf skills
git rm -r --quiet scratch migrated-repos-archive
```

`scratch/` and `migrated-repos-archive/` are normally tracked, so plain
`git rm -r` clears index and disk in one step.

### Step 4 — delete dead root files

```bash
git rm --quiet ci_runs.json hf_dataset.json hf_ds_size.json hf_embed_check.json \
               _cron007_append.md _hf_report_008.md new_combined_v6_readme.md
```

### Step 5 — reorganize the root

```bash
mkdir -p scripts/hf docs/reference training/notebooks

git mv _check_models.py _check_spaces.py _parse_datasets.py \
       _parse_models.py _parse_spaces.py  scripts/hf/
git mv hf-topics-covered.json               data/
git mv hf-learnings.md                      docs/reference/
git mv eval_sakthai_bench_colab.ipynb       training/notebooks/
```

### Step 6 — untrack the unreferenced assets (reversible)

Only after confirming the PNGs aren't used by an HF card, a Space, or a deck.
Both files stay on disk:

```bash
git rm -r --cached --quiet assets
printf '\n# Large unreferenced branding assets — kept locally, not tracked\n/assets/\n' >> .gitignore
```

Note the leading `/`: a bare `assets/` would also ignore
`personas/*/skills/*/assets/`, which is real tracked content. To delete outright
instead: `git rm -r --quiet assets`.

### Step 7 — REQUIRED: fix the persona skill counts

`tests/test_soul_consistency.py::test_personas_readme_skill_counts_match_disk`
counts **every** entry in each `personas/<slug>/skills/` directory, including the
curator dotfiles Step 2 removes. Those counts were inflated by exactly the junk
just deleted, so `personas/README.md` must be corrected or the suite fails:

| Persona | README (old) | Disk (after cleanup) |
|---|---:|---:|
| SakThai | 306 | **302** |
| SakKing | 110 | **106** |
| SakSit | 47 | **43** |
| SakSee | 187 | **182** |
| SakJules | 180 | 180 (unchanged) |
| SakTan | 13 | 13 (unchanged) |
| **Total** | 843 | **826** |

```bash
sed -i -e 's/the 306 skills mapped to SakThai/the 302 skills mapped to SakThai/' \
       -e 's/the 110 skills mapped to SakKing/the 106 skills mapped to SakKing/' \
       -e 's/the 47 skills mapped to SakSit/the 43 skills mapped to SakSit/' \
       -e 's/the 187 skills mapped to SakSee/the 182 skills mapped to SakSee/' \
       -e 's/collectively host \*\*843 specialized skills/collectively host **826 specialized skills/' \
       personas/README.md
```

The corrected figures for SakKing (106), SakSit (43), SakSee (182), SakJules
(180) and SakTan (13) now match the per-persona counts documented in `CLAUDE.md`
exactly — independent confirmation that the old numbers were counting junk.

### Step 8 — verify, then commit

```bash
uv sync --all-extras
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run pytest tests/ -q -m "not integration"

git ls-files -i -c --exclude-standard | wc -l   # was 112; expect 11
ls *.py *.json 2>/dev/null                      # expect: no matches

git add -A
git commit -m "chore: remove generated state, reorganize root, fix gitignore package shadowing"
git push -u origin chore/repo-cleanup
```

The `git ls-files -i -c` check is the regression test for
[§1](#1-critical-gitignore-shadows-the-installed-package): the only
ignored-but-tracked files left should be the 10 persona shadow-copy files the
parity test requires, plus one pre-existing `agent-self-evolution/output/` file.

### Deliberately not scripted

- **Merging the duplicated `docs/` files** ([§2](#2-reorganization-what-to-move-where)) — prose merges need a human read.
- **Deduplicating the 187 `hf-learnings.md` copies** — needs a shared-reference
  design first; worth ~5 MB.
- **`git gc` / history rewrite** — deleting files shrinks the working tree but
  not `.git` (94 MB). Only a `filter-repo` rewrite reclaims that, and it breaks
  every existing clone and open PR. Not worth it at this size.

---

## 7. Verification results

The whole of [§6](#6-execution-commands) was run against a throwaway clone. Two
bugs in an earlier draft surfaced only by doing so:

1. **Unanchored ignore patterns over-matched.** A bare `.workflow_runs/` also
   swallowed `apps/agent_workflow_framework/.workflow_runs/` (1,394 files), and a
   bare `assets/` swallowed two persona `.gitkeep` files. The first turned out to
   be a genuine 5.4 MB find, now an explicit delete; the second is fixed with a
   `/assets/` anchor.
2. **The skill-count test broke.** `personas/README.md` was counting the curator
   dotfiles as skills. Step 7 exists because of this.

A third item surfaced during the real run rather than the rehearsal:
`personas/sakthai/sakthai_agent.egg-info/` is tracked setuptools build metadata
that `uv sync` rewrites on every install, so it had been silently churning
against `README.md`. Untracked and ignored.

Final state of the repository (measured after execution, not projected):

| Metric | Before | After |
|---|---:|---:|
| Tracked files | 6,172 | **4,454** |
| Tracked size | 65.9 MB | **47.5 MB** |
| Root-level tracked files | 41 | **22** |
| Ignored-but-tracked files | 112 | **11** |
| Loose `*.py` / `*.json` at root | 10 | **0** |

CI gates on the cleaned tree:

```
pytest  1970 passed, 2 skipped, 6 deselected, 121 subtests passed
ruff    All checks passed!
format  166 files already formatted
mypy    Success: no issues found in 69 source files
```
