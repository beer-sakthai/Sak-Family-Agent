# CodeQL in this repository

Three things make up the CodeQL setup. Each is here because the previous
arrangement failed in a way that was invisible from the outside.

| File | What it is |
|---|---|
| [`.github/workflows/codeql.yml`](../workflows/codeql.yml) | The analysis that runs in CI and uploads to code scanning |
| [`codeql-config.yml`](./codeql-config.yml) | The scope — which trees are analysed and which are not |
| [`scripts/codeql_local.sh`](../../scripts/codeql_local.sh) | The same analysis, on your machine, before you push |

## Advanced setup, not default setup

CodeQL runs here as an **advanced setup** — a workflow file — and the
repository setting for *default setup* is **off**. The two cannot coexist: an
advanced analysis fails to upload with `CodeQL analyses from advanced
configurations cannot be processed when the default setup is enabled`, which is
how remediation bots that added `codeql.yml` twice produced nothing but red
jobs.

Do not re-enable default setup without deleting `codeql.yml` first, and do not
delete `codeql.yml` expecting default setup to pick the work back up — it is
disabled, and nothing would analyse the repository at all.

The reason for advanced setup is `config-file:`. Default setup reads a config
file only when an administrator sets the `codeql-config-file` custom repository
property; it cannot be given one by path. `codeql-config.yml` therefore spent
its first day inert, and CodeQL analysed the whole tree: 788 open alerts on
2026-08-18, of which 545 were in vendored skill scripts, the folded-in
`sakthai-chat-cli` copy of a separate repository, and the test suite. Excluding
those is what makes the remaining ~243 first-party alerts legible. It closes
none of them.

`tests/test_workflow_hygiene.py::test_codeql_workflow_uses_the_scope_config`
asserts the `config-file:` reference still exists, because dropping it is a
silent no-op — the scope just stops applying.

## Query suites are per language, and only `actions` is widened

`python` and `javascript-typescript` run the **default** suite. Widening them
to `security-extended` before the ~243 first-party alerts have been read buys
noise, not coverage.

`actions` runs `security-extended`, which is a different judgement about a
different backlog rather than an exception to that one. The extended suite for
the `actions` language is the workflow-security rule set — untrusted checkout,
expression injection into `run:` blocks, secrets in scope where contributor
code executes, over-broad `permissions:`. That is the failure mode this
repository has actually been bitten by: commit `93e306a` reverted the
`self-healing-ci.yml` fork guard inside a commit whose message described
something else, and nothing noticed until a test was written to assert that one
condition by name. A hand-written assertion covers the bypass someone thought
to write down. The suite covers the shape.

Because a config file's `queries:` applies to every language at once, the
suites are set on the workflow's `matrix.include` entries and passed through to
`codeql-action/init` as `queries: ${{ matrix.queries }}`.

## Running it locally

```bash
scripts/codeql_local.sh --check          # is the CLI usable?
scripts/codeql_local.sh actions          # analyse one language
scripts/codeql_local.sh                  # all three
scripts/codeql_local.sh --sarif python   # keep the SARIF file
```

You need the CodeQL **bundle** on `PATH`, not the bare CLI — the bundle ships
the query packs, and a bare CLI will fail to resolve the suites above. Download
it from the [`codeql-action` releases](https://github.com/github/codeql-action/releases).

The script passes `--codescanning-config` so `paths-ignore` applies locally
exactly as it does in CI; without that flag a local run reproduces all 545
alerts the scope exists to keep off the dashboard. Databases are cached in
`.codeql/` (gitignored) and reused until you pass `--rebuild`.

**Keep the `SUITES` table in the script in step with `matrix.include` in the
workflow.** A language analysed locally with a different suite than CI uses
either invents findings that will never appear on the dashboard or hides ones
that will.
