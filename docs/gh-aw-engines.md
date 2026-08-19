# gh-aw engines: Gemini and OpenCode

This repository runs eight [GitHub Agentic Workflows](https://github.github.com/gh-aw/)
(gh-aw). Each is authored as Markdown in `.github/workflows/` and compiled to a sibling
`.lock.yml` — the `.lock.yml` is what GitHub Actions actually executes, so **a change to a
`.md` source that is not recompiled changes nothing**.

As of 2026-08-18 they no longer run on Copilot. Seven run on Google **Gemini**, one runs on
**OpenCode** driving a Gemini model.

> **That was true of the sources on 2026-08-18 and of the compiled workflows only from
> 2026-08-19.** Switching a `.md` to `engine: gemini` does nothing on its own. Four of the
> eight — `ci-doctor`, `maintain-agents-md`, `maintain-docs`, `release` — kept running
> Copilot from lock files compiled by gh-aw **v0.86.2**, and failed every time with
> `400 The requested model is not supported` (issues #762, #877). The table below is
> therefore what the *lock files* now say, verified with the command under
> [Checking for a stale lock](#checking-for-a-stale-lock). Re-verify it there rather than
> trusting this page after editing any `.md`.

## Engine assignment

| Workflow | Engine | Model | Trigger |
|---|---|---|---|
| `ci-doctor.md` | `gemini` | engine default | `workflow_run` failure of CI / Pylint / Subproject tests on `main` |
| `maintain-agents-md.md` | `gemini` | engine default | weekly (Monday) + dispatch |
| `maintain-docs.md` | `gemini` | engine default | weekdays + dispatch |
| `release.md` | `gemini` | engine default | dispatch (admin/maintainer) |
| `security-audit.md` | `gemini` | engine default | weekly (Thursday) + dispatch |
| `shared-package-drift.md` | `gemini` | engine default | weekly (Tuesday) + dispatch |
| `skills-hygiene.md` | `gemini` | engine default | weekly (Wednesday) + dispatch |
| `opencode-smoke.md` | `opencode` (vendored) | `copilot/gemini-3.1-flash` | weekly (Monday) + dispatch |

Compiled with gh-aw **v0.87.0**; the Gemini CLI pins to `0.55.1` and OpenCode to `1.2.14`.

## Checking for a stale lock

The `.lock.yml` header carries the engine and compiler that produced it. This is the only
reliable answer to "what does this workflow actually run":

```bash
for f in .github/workflows/*.lock.yml; do
  printf "%-24s " "$(basename "$f" .lock.yml)"
  head -1 "$f" | python3 -c "import sys,json; d=json.loads(sys.stdin.read().split('gh-aw-metadata: ',1)[1]); print(d.get('compiler_version'), d.get('agent_id'), d.get('engine_versions'))"
done
```

A lock whose `agent_id` disagrees with its `.md`'s `engine:` is stale and is running the
old engine. So is one whose `frontmatter_hash` no longer matches its source — that is the
signal gh-aw itself uses, and it is what `[aw] … has stale lock file` issues report.

## Recompiling

`gh aw compile` is a `gh` extension, so the normal path is:

```bash
gh extension install github/gh-aw --pin v0.87.0
gh aw compile                       # or: gh aw compile ci-doctor maintain-docs
gh aw compile --validate
```

**Two flags are load-bearing in this repository** and the defaults are wrong for it:

```bash
gh aw compile --action-mode action --action-tag b77e0d501fd2d2243d1f72722617e80d513f674e
```

Without them the compiler emits `github/gh-aw-actions/setup@v0.87.0` — a *tag*, which
fails `tests/test_workflow_hygiene.py::test_actions_are_pinned_to_a_commit_sha`, since
that check covers the lock files too. `--action-tag` pins the same SHA the existing locks
carry. A release binary auto-detects `action` mode; a binary built from source defaults to
`dev` mode and emits local `./actions/...` paths plus a sparse-checkout of `github/gh-aw`,
which is wrong for every workflow here.

If `gh` is unavailable (it needs an authenticated API token to install an extension), build
the compiler from source instead — **both** ldflags matter, or the binary omits
`compiler_version` from every header it writes:

```bash
git clone --depth 1 --branch v0.87.0 https://github.com/github/gh-aw /tmp/gh-aw
cd /tmp/gh-aw && CGO_ENABLED=0 go build \
  -ldflags "-s -w -X main.version=v0.87.0 -X main.isRelease=true" -o /tmp/gh-aw-bin ./cmd/gh-aw
```

Verify any such build before trusting its output: recompile a workflow you are *not*
changing and confirm `git diff` is empty. `shared-package-drift` and `opencode-smoke`
reproduce byte-for-byte under the flags above, which is what proves the toolchain matches
the one that produced the existing locks.

The compiler's **safe-update gate** will refuse changes that introduce a restricted secret
until you pass `--approve` or record a review. That gate is working as intended — the
migration of the four Copilot locks onto Gemini tripped it for `GEMINI_API_KEY`, and the
review it demanded is in that commit's message. Do not reach for `--approve` without
writing the review down somewhere a human will read it.

## Secrets and variables

| Name | Kind | Needed by | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | secret | all seven Gemini workflows | Already used by `.github/workflows/self-healing-ci.yml`. gh-aw wires it automatically for `engine: gemini` — no `engine.env` block required. Each lock file validates its presence before invoking the CLI. |
| `GITHUB_TOKEN` | built-in | all | Ambient Actions token. |
| `GH_AW_GITHUB_TOKEN`, `GH_AW_GITHUB_MCP_SERVER_TOKEN` | secret (optional) | all | Optional overrides; every reference falls back to `GITHUB_TOKEN`. |
| `COPILOT_GITHUB_TOKEN` | built-in | all | Still present in the compiled manifest. It backs gh-aw's own threat-detection pass and the AWF API proxy, not the agent engine. The OpenCode workflow additionally routes its Gemini model through that proxy — see below. |
| `GH_AW_DEFAULT_MODEL_*`, `GH_AW_MODEL_AGENT_*`, `GH_AW_DEFAULT_MAX_*` | repo variable (optional) | all | gh-aw's standard per-engine model and budget overrides. |

`security-audit.md` was added on 2026-08-18 and introduces **no new secret**: its compiled
manifest carries exactly the same set as `skills-hygiene.md`
(`COPILOT_GITHUB_TOKEN`, `GEMINI_API_KEY`, `GH_AW_GITHUB_MCP_SERVER_TOKEN`,
`GH_AW_GITHUB_TOKEN`, `GITHUB_TOKEN`) and the same action set. The compiler's safe-update
gate still asked for `--approve`, because the *file* is new rather than the secret — that
is the gate working as intended, and the review it asks for is the one recorded here.

Gemini also supports keyless Google Workload Identity Federation instead of
`GEMINI_API_KEY`. This repository uses the API key; switching to WIF would mean adding the
WIF fields to each workflow's `engine:` block and recompiling.

## The vendored OpenCode engine

`.github/workflows/shared/opencode.md` is a **vendored copy** of the OpenCode shared engine
definition from `github/gh-aw` at tag **v0.87.0**
(`.github/workflows/shared/opencode.md` upstream).

### Why it is vendored rather than imported by URL

OpenCode is not a built-in gh-aw engine. ADR-50145 upstream retired `opencode` as a
first-class engine id — carrying it in every generated lock file cost too much across 280+
workflows — and it survives only as an importable Markdown definition. Upstream labels that
definition a **sample**, with no support or compatibility commitment:

> The OpenCode, Aider, Crush, Cursor, DeepSeek Harness, Kiro, and Pydantic AI integrations
> in this repository are **samples only**. They are not officially supported by gh-aw and
> have no compatibility or maintenance commitment.

Vendoring it means compilation does not depend on fetching a file from another repository,
and the exact bytes we compile against are reviewable in this repo's history. It also means
**breakage here is ours to fix, not a gh-aw bug**.

### The one local modification

Upstream's `opencode.jsonc` declares a single model under the `awf-proxy` provider:

```jsonc
"models": { "claude-sonnet-4.5": {} }
```

The vendored copy adds the Gemini aliases this repository runs on:

```jsonc
"models": {
  "claude-sonnet-4.5": {},
  "gemini-3.1-flash": {},
  "gemini-3.1-pro": {},
  "gemini-flash": {},
  "gemini-pro": {}
}
```

Nothing else differs from upstream except the trailing HTML comment, which was shortened to
point here. gh-aw's workflow security scanner rejects HTML comments containing code fences
or URLs (`[hidden-content] HTML comment contains suspicious content`), so the provenance
notes live in this file rather than inside the engine definition.

### How OpenCode ends up running Gemini

The workflow declares a `provider/model` pair:

```yaml
model: copilot/gemini-3.1-flash
engine:
  id: opencode
imports:
  - shared/opencode.md
```

At compile time the engine definition's `model-env-provider-prefix: awf-proxy` rewrites the
provider half, so the compiled workflow exports:

```
OPENCODE_MODEL=awf-proxy/gemini-3.1-flash
```

`awf-proxy` is the AWF (agentic workflow firewall) API proxy that gh-aw already starts for
every sandboxed run. Its `apiProxy.models` steering map contains a `gemini-3.1-flash` key
matching `copilot/gemini-3.1*flash*`, `google/gemini-3.1*flash*`, and
`gemini/gemini-3.1*flash*`, so the request is steered to Gemini. The model half must appear
in **both** places — the steering map (upstream's, not ours) and the vendored `models` map
above — or OpenCode will not recognise the model.

This path deliberately does **not** use `GEMINI_API_KEY`: it bills through the proxy rather
than a direct BYOK call to `generativelanguage.googleapis.com`. A native Google provider
block would need its own key handling and network allowlist entry; it is not configured.

### Refreshing the vendored copy

```sh
curl -sS -o .github/workflows/shared/opencode.md \
  https://raw.githubusercontent.com/github/gh-aw/<tag>/.github/workflows/shared/opencode.md
```

Then re-apply the `models` addition and the shortened trailing comment, and recompile.

### Known limitations

- `tools:` is **ignored** for `engine: opencode` — the compiler warns
  `'tools' section ignored when using engine: opencode (OpenCode doesn't support MCP tool
  allow-listing)`. The GitHub MCP server is still wired in; only per-tool allow-listing is
  unavailable. Do not add a `tools:` block to an OpenCode workflow expecting it to restrict
  anything.
- Every compile of an OpenCode workflow emits
  `⚠ Using experimental OpenCode support (engine: opencode)`. That warning is expected and
  is not a failure.

## Recompiling

The `gh` CLI and the `gh aw` extension are not required — the compiler is a plain Go binary.

```sh
git clone --depth 1 --branch v0.87.0 https://github.com/github/gh-aw.git /tmp/gh-aw-src
cd /tmp/gh-aw-src && go build \
  -ldflags "-s -w -X main.version=v0.87.0 -X main.isRelease=true" \
  -o /tmp/bin/gh-aw ./cmd/gh-aw
```

`go install github.com/github/gh-aw/cmd/gh-aw@v0.87.0` does **not** work — gh-aw's `go.mod`
carries `replace` directives, which `go install` refuses.

**Both ldflags are required.** `cmd/gh-aw/main.go` declares two release variables, and the
compiler reads them independently:

```go
var (
	version   = "dev"
	isRelease = "false" // Set to "true" during release builds
)
```

Setting only `main.version` makes `gh-aw --version` print `v0.87.0` while every compiled
workflow still emits `GH_AW_VERSION: dev`, because the engine writes that env var from
`IsRelease()`, not from the version string. The symptom is invisible in the compiler's
output and only shows up by grepping the lock files:

```sh
grep -h "GH_AW_VERSION:" .github/workflows/*.lock.yml | sort -u   # expect: v0.87.0
```

Then, from the repository root:

```sh
/tmp/bin/gh-aw compile \
  --action-mode action \
  --action-tag b77e0d501fd2d2243d1f72722617e80d513f674e \
  --validate --strict
```

Both flags matter:

- **`--action-mode action`** — without it the compiler auto-detects a *dev* build and emits
  `uses: ./actions/setup`, a local path that does not exist in this repository. The
  workflows would compile cleanly and then fail on every run.
- **`--action-tag <sha>`** — the 40-character commit SHA of the `github/gh-aw-actions` tag
  matching the compiler version (`b77e0d50…` is `v0.87.0`). `--action-tag v0.87.0` would
  emit the *tag*, and `tests/test_workflow_hygiene.py` requires every `uses:` to be pinned
  to a full SHA. Resolve a new one with:

  ```sh
  git ls-remote --tags https://github.com/github/gh-aw-actions | grep 'v0.87.0^{}'
  ```

  Take the **peeled** ref (`^{}`) — that is the commit the annotated tag points at. The
  bare `refs/tags/v0.87.0` line is the tag *object* (`d57bb28e…`), which is not a commit
  and is the wrong thing to pin. The repository's previous pin followed the same rule:
  v0.86.2 was pinned to `6aab9e5b…` (`v0.86.2^{}`), not to the tag object `64c928bd…`.

Add `--approve` when the compiler reports `safe update mode detected unapproved changes`
— but only after reading what it lists. It gates newly-introduced secrets and actions, and
the point of the gate is the review, not the flag.

### `.github/aw/actions-lock.json`

The compiler removed this file during the v0.87.0 upgrade. It caches tag→SHA resolutions,
and it is pruned of entries no longer referenced by any lock file; because
`--action-tag <sha>` supplies the SHA directly, nothing needs resolving and no entry is
written. The compiled workflows are still fully SHA-pinned — that is what
`tests/test_workflow_hygiene.py` checks, and it passes. The file will reappear on its own if
a future compile resolves a tag against the GitHub API.

### Recompiling touches every source, not just the one you edited

`gh-aw compile` regenerates all eight lock files, so read the whole diff rather than the
file you meant to change. The 2026-08-18 recompile emitted one unexpected hunk, identical
in `maintain-agents-md.lock.yml`, `maintain-docs.lock.yml` and `release.lock.yml`:

```diff
-permissions:
-  contents: read
+permissions: {}
```

That is the compiler recomputing the minimal top-level scope — a narrowing, and the same
output v0.87.0 produces from the current sources every time. It was committed rather than
reverted: leaving lock files that a clean recompile would change is exactly the
source-and-lock-disagree hazard this document exists to prevent. `permissions: {}` still
satisfies `tests/test_workflow_hygiene.py`, which requires the key to be present, not
non-empty — each generated job grants what it needs.

## Verifying a change

```sh
uv run pytest tests/test_workflow_hygiene.py -q
grep -h "GH_AW_VERSION:" .github/workflows/*.lock.yml | sort -u   # expect: v0.87.0
git diff --stat .github/workflows/                                # expect: only what you meant
```

That suite is the gate: every file in `.github/workflows/` must be a loadable workflow or a
`.md` with a compiled `.lock.yml` beside it, every workflow needs a top-level `permissions:`
block, and every `uses:` must be a 40-character SHA. Two further rules —
top-level `concurrency:` on pull-request workflows, and `timeout-minutes` on every job —
apply to the hand-written workflows only; the `.lock.yml` files are exempt because gh-aw
sets `timeout-minutes` on only one of each workflow's generated jobs, and holding generated
output to a rule its generator does not follow would fail on every recompile. Files under
`.github/workflows/shared/` are not scanned — the check does not recurse into
subdirectories, which is why the vendored engine definition can live there without needing
a `.lock.yml` of its own.

To confirm the engine split landed as intended:

```sh
for f in .github/workflows/*.lock.yml; do
  head -1 "$f" | python3 -c "import sys,json; d=json.loads(sys.stdin.read().split('gh-aw-metadata: ',1)[1]); print(d['agent_id'], d.get('agent_model',''), d['engine_versions'])"
done
```
