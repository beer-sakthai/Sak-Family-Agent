# Configuring multi-ecosystem Dependabot updates

> This file previously contained a pasted GitHub Copilot article about code
> readability, which had nothing to do with its filename. This is the document
> the name promises.

`.github/dependabot.yml` covers five package ecosystems across 22 directories in
this monorepo. This explains the shape it has, so the next person to add a
subproject knows where their entry goes and why the obvious approach is wrong.

## What is covered

| Ecosystem | Directories | Open-PR limit |
|---|---|---|
| `uv` | `/`, `/sakthai-chat-cli`, `/services/teams-copilot-mcp` | 5 |
| `pip` | 12 — the Poetry SDK copy, 3 × `agent-self-evolution`, 6 `requirements.txt` dirs, 2 gradio `templates/` dirs | 5 |
| `npm` | `/apps/sak_agent_dashboard` (pnpm), `/infra/pw-poc`, 2 × `SakSee-stitch-*` | 4 |
| `docker` | `/` (`Dockerfile.sandbox`), `/infra/sakthai-training-space` | 2 |
| `github-actions` | `/` | 3 |

Five entries, 19 simultaneous open version-update pull requests at worst.
The previous config had sixteen entries and allowed **95**.

That number is the real constraint. Every pull request into `main` needs an
approving review from someone other than its author
([`CONTRIBUTING.md`](CONTRIBUTING.md)), so an unbounded bump queue does not
merely make noise — it consumes the only review capacity the repository has.
`tests/test_dependabot_config.py` fails if the configured total exceeds 20.

## `uv` is not an alias for `pip`

Only three directories have a `uv.lock`. They get `package-ecosystem: uv`, which
resolves `[dependency-groups]` natively — the exact blind spot that hid
`sqlitedict` from `pip-audit`, because `uv export --all-extras` does not include
groups (see [`dependabot-sweep-2026-08-18.md`](dependabot-sweep-2026-08-18.md)).

Everything else Python is `pip`, including things that look like they should not
be:

- `apps/sak_agent_dashboard/microsoft_agents_m365copilot` is a **Poetry** project
  (`[tool.poetry.dependencies]`, no lock).
- The three `agent-self-evolution` copies are PEP 621 with no lock.

**Never list a directory under both.** Two ecosystems pointed at one
`pyproject.toml` open two competing pull requests for every bump. The test
enforces this, and it enforces that a `uv` directory has *both* `pyproject.toml`
and `uv.lock` — that pair is what distinguishes a uv project from a lock-less
one.

## Literal paths, never globs

`directories:` supports `*` and `**`. This repository must not use them:

- `/personas/*/skills/*` matches **826 directories**.
- `/personas/*/agent-self-evolution` matches **five symlinks** into
  `personas/shared/`. Dependabot's file fetchers select Contents-API entries of
  type `"file"`, so a symlinked directory yields a job that permanently finds no
  manifest — five dead entries that read as coverage.

Only `personas/sakthai/` and `personas/shared/` hold real
`agent-self-evolution` directories; the other five personas symlink to shared.
Same for `personas/{sakjules,saktan}/sakthai`. Check with `ls -la personas/*/`
before adding anything under `personas/`.

## Why `directories:` (plural) at all, then

Not for brevity — for **atomicity**. A group spanning several directories lands
as **one** pull request:

- The three `agent-self-evolution` `pyproject.toml` files are byte-identical and
  must move together.
- The two `SakThai-hf-gradio/templates/space-requirements.txt` copies likewise.

The 2026-08-18 sweep bumped each set by hand in one pass for exactly this
reason. Three separate pull requests needing three separate approvals was the
alternative. It also collapses twelve independent 5-PR budgets into one.

## `Dockerfile.sandbox` really is discovered

There is no file named `Dockerfile` at the root, yet `docker` at `/` works.
dependabot-core's docker fetcher uses:

```ruby
DOCKER_REGEXP = /dockerfile|containerfile/i
```

Unanchored and case-insensitive, matched against the bare filename in a flat,
non-recursive listing of the configured directory. `"Dockerfile.sandbox"`
contains `"dockerfile"`, so it matches. (dependabot-core#4449 says otherwise; it
is from 2021 and predates this regex.)

`tests/test_dependabot_config.py` mirrors that regex verbatim, so renaming the
file to something non-matching fails a test instead of silently ending coverage.

## No `target-branch`

`main` is already the default branch, so `target-branch: main` changes no
routing. It is not free, though: naming a target branch **scopes the entry to
version updates only**, so its labels, commit prefix and groups stop applying to
*security* pull requests — the ones that matter most. All cost, no benefit. The
test rejects it.

## Alerts ≠ updates

Dependabot *alerts* come from the dependency graph and scan the whole
repository. Version-update pull requests only reach directories in this config,
and **security-update pull requests ignore `open-pull-requests-limit`
entirely** — they arrive on top of the 19, and cannot be capped from this file.

A manifest that alerts but has no entry looks watched and is not. That is how
the six gradio advisories ended up being fixed by hand.

## Adding a new subproject

1. Add the directory to the matching entry's `directories:` list. Use the
   existing entry for that ecosystem rather than creating a new one — a new
   entry brings its own PR budget.
2. Run `uv run pytest tests/test_dependabot_config.py -q`.

The test tells you if you forgot: its completeness sweep walks the tree, finds
every directory holding a manifest, and fails naming any that no entry covers.

If an entry would genuinely be wrong, add the path to `UNCOVERED_BY_DESIGN` in
that test **with a reason about why it would be wrong** — not why it is
inconvenient. Three families are exempt today:

- **`*-requirements.in` with a hash-pinned `.lock` sibling.** Dependabot
  regenerates a `.txt` beside the `.in`, never a `.lock`, and `bandit.yml`
  installs from the `.lock` with `--require-hashes`. A bump to the `.in` alone
  changes nothing while looking like it did. Regenerate these with
  `scripts/gen_hash_lock.py` instead.
- **`*-google-workspace/scripts/setup.py`** — OAuth CLI scripts declaring
  `REQUIRED_PACKAGES = [...]` with no `setup()` call. Dependabot would accept
  the directory and extract zero dependencies.
- **`apps/agent_workflow_framework`** — has a CI job in `subprojects.yml` but no
  manifest at all. A real bug, not an exemption.

## The exported repos get a different config

`scripts/export_agent_repo.py` copies `.github/` into each standalone persona
repo, but it also *flattens* paths (`personas/sakthai/sakthai` → `sakthai`), so
none of this config's directories would resolve there. The exporter therefore
excludes `dependabot.yml` from the copy and renders a minimal two-entry config
(`uv` at `/`, `github-actions` at `/`) instead. Without that, this one correct
config becomes six broken ones. Covered by
`tests/test_export_agent_repo.py::test_export_replaces_the_monorepo_dependabot_config`.

`sakthai-chat-cli/.github/dependabot.yml` was deleted for the same class of
reason: `sakthai-chat-cli/` has no nested `.git`, so Dependabot never read it.

## The gh-aw lock files

Four workflows are gh-aw agentic sources compiled to `*.lock.yml` (`ci-doctor`,
`maintain-agents-md`, `maintain-docs`, `release`). The `uses:` pins inside those
lock files are **generated** from the neighbouring `.md`, which pins by tag.
Dependabot edits the `.lock.yml` and the next `gh aw compile` reverts it.

There is no per-file exclusion for the `github-actions` ecosystem, so this
cannot be configured away. When one of those shows up in a bump PR, bump the
`.md` and recompile — do not merge the `.lock.yml` half and assume it sticks.

## Related

- [`dependabot-setup.md`](dependabot-setup.md) — enabling the repository settings this file cannot
- [`../.github/INNERSOURCE.md`](../.github/INNERSOURCE.md) — advisory ownership and response times
- [`dependabot-sweep-2026-08-18.md`](dependabot-sweep-2026-08-18.md) — the sweep that motivated this
