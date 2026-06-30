# Security Policy

## Reporting a Vulnerability

**Do not open public GitHub issues for security vulnerabilities.**

Email **beernanthasit@gmail.com** with subject `[SECURITY] sakthai-agent-v2`.

Include:
- A clear description of the issue
- Steps to reproduce or a minimal proof of concept
- The potential impact you see

Response timeline:
- **Acknowledgement**: within 3 business days
- **Initial assessment**: within 7 days
- **Fix or mitigation**: coordinated with the reporter; disclosed publicly after a patch is available

## Supported Versions

| Version | Security fixes |
|---------|---------------|
| 2.x (current, `main`) | Yes |
| 1.x (OG, archived) | No |

Only the `main` branch of this repository (v2.x) receives security patches.

## Security Architecture

### Tool sandbox

The agent and MCP server share a single tool registry (`sakthai/agent/tools.py`). Each tool that touches the filesystem or network enforces its own access boundary:

| Tool | Boundary |
|------|----------|
| `read_file` | Restricted to `cwd`, `~/.sakthai`, and any paths in `SAKTHAI_READ_ALLOW`. Symlinks resolved with `Path.resolve(strict=True)` before the allowlist check; output capped at 20,000 characters. |
| `run_command` | **Off by default.** Requires `SAKTHAI_SHELL_ALLOW=1` to activate. Runs with `shell=False` via `shlex.split`; timeout bounded 1–120 s; output capped at 20,000 characters. |
| `send_telegram_message` | Requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`; 10-second network timeout. |
| `run_agent_loop` | Recursion guard via `SAKTHAI_AGENT_ACTIVE` environment flag; the nested loop excludes `run_agent_loop` from its own tool set. |

### Credential handling

Credentials are sourced from environment variables or local credential files — never hardcoded:

- **Anthropic**: `ANTHROPIC_API_KEY` → `ANTHROPIC_AUTH_TOKEN` → Claude CLI OAuth token (`~/.claude/.credentials.json`)
- **Google/Gemini**: Gemini CLI OAuth token (`~/.gemini/oauth_creds.json`)
- **OpenAI / Ollama**: `OPENAI_API_KEY` + `OPENAI_BASE_URL`/`OPENAI_API_BASE`; or `OLLAMA_HOST`

`resolve_anthropic_client()` raises `AuthError` when no usable credential is found. Tokens are never written to logs or session files.

### SQL safety

`MemoryStore` (`sakthai/memory/store.py`) is the only code that touches SQLite:

- All queries use `?` parameterized placeholders
- Dynamic `IN (...)` clauses are built as `",".join("?" for _ in ids)` — no string interpolation
- `LIKE` patterns use `ESCAPE '='` to prevent wildcard injection
- Schema migrations are additive (ALTER TABLE only) under `BEGIN IMMEDIATE`

### MCP stdio server

`sakthai mcp` is a dependency-free JSON-RPC 2.0 stdio server. It enforces the same tool sandbox as the agent loop. It does not listen on any TCP port and cannot be reached from outside the local process without explicit piping.

### Secrets in the repository

- `.env` is gitignored; only `.env.example` (empty values) is committed
- `uv.lock` pins all transitive dependencies
- Gitleaks scans the full git history on every push and pull request (see `.gitleaks.toml`); the allowlist covers `tests/`, `.env.example`, and `README.md`

## CI Security Checks

Every push to `main` and every pull request runs the following pipeline (`.github/workflows/ci.yml`) against Python 3.11 and 3.12:

1. **Secret scan** (Gitleaks v8.21.2) — scans full git history; must pass before any other job runs
2. **Lint** (`ruff check`) — catches unsafe patterns flagged by ruff's built-in security rules
3. **Format check** (`ruff format --check`)
4. **Type check** (`mypy sakthai` in strict mode)
5. **Static security analysis** (`bandit -c pyproject.toml -r sakthai`)
6. **Tests** (`pytest tests/ -q -m "not integration"`) — hermetic unit suite with no network access

Bandit skips: `B101` (assert in non-test code), `B404`/`B603`/`B606`/`B607` (subprocess flags — all subprocess calls use `shell=False` with fixed/parsed argument arrays).

## Environment Variables Controlling Security Gates

| Variable | Effect | Recommendation |
|----------|--------|---------------|
| `SAKTHAI_SHELL_ALLOW` | Enables `run_command`. Unset = disabled. | Do not set unless you explicitly need the agent to run shell commands. |
| `SAKTHAI_READ_ALLOW` | Adds extra filesystem roots the `read_file` tool can access (OS path-separator-delimited). | Specify exact paths, not broad directories like `/` or `$HOME`. |
| `SAKTHAI_HOME` | Overrides the data directory (default `~/.sakthai`). | Ensure the path is readable only by the owning user. |
| `ANTHROPIC_API_KEY` | Primary Anthropic credential. | Store in `.env` (gitignored) or a secrets manager. Never export in shared shell profiles. |
| `TELEGRAM_BOT_TOKEN` | Activates Telegram outbound messaging. | Treat as a secret; rotate if leaked. |

## Contributor Guidelines

### Adding a new tool

1. Define the tool in `sakthai/agent/tools.py`. Tools are shared by the agent loop and the MCP server — there is no separate registration.
2. Explicitly enumerate what the handler can access. If it reads files, use `_path_under_any_root(resolved, _allowed_read_roots())`. If it makes network requests, document the endpoints and add a configurable timeout.
3. Add an opt-in gate for any capability that can modify system state or reach external services (follow the `SAKTHAI_SHELL_ALLOW` pattern).
4. Write hermetic unit tests with an injected `MemoryStore` and no live network. Run `bandit` and `mypy` locally before opening a PR.

### Widening the sandbox

If you have a reason to expand `SAKTHAI_READ_ALLOW` defaults or add new shell-adjacent capabilities, open a PR describing the threat model change. Do not widen defaults silently.

### Adding or updating dependencies

- Add to `pyproject.toml`; lock with `uv lock`.
- Review the package's security history before adding; prefer packages with active maintenance and a small transitive footprint.
- Optional extras (`dashboard`, `cloud`) are not imported at module load time — keep it that way to limit the attack surface of the default install.

### Subprocess calls

All subprocess invocations must use `shell=False` with a list or `shlex.split`-parsed argument array. The Bandit subprocess skips (`B603`, `B606`, `B607`) exist because the existing calls are verified safe; do not add new `# nosec` annotations without a justification comment.

---

*This project is all rights reserved (© 2026 beer-sakthai); see the README for terms.*
