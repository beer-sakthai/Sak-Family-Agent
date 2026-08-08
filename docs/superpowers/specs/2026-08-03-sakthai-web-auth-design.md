# SakThai Web Auth — Design

**Status:** Draft (awaiting user review)
**Date:** 2026-08-03
**Owner:** Claude Code (with Beer input on credential rotation, parallel)

---

## Context

The 2026-07 security audit identified that the SakThai web server
(`personas/sakthai/sakthai/web/server.py`) exposes memory data without
authentication when bound to a non-loopback host. The full plan is in
`security/SECURITY_FIXES_PLAN.md`; this design covers the *technical* shape
of "Web API Authentication" (Fix #2) and the gaps that surfaced during a
re-read of the existing code on 2026-08-03.

### What's already in place (as of 2026-08-03)

A re-read of `web/server.py` shows that part of Fix #2 is already implemented:

- `_get_or_create_bearer_token()` (server.py:29) generates a 32-hex token,
  stores it as a `web_auth` fact in the unscoped `memory.db` with
  `tags=['system', 'no-export']`, and registers the secret via
  `config.register_secret`.
- The `/api/*` handler enforces `Authorization: Bearer <token>` using
  `secrets.compare_digest` (server.py:176-200).
- `serve()` refuses non-loopback binds unless `SAKTHAI_WEB_ALLOW_PUBLIC=1`
  is set (server.py:246).
- `cli/system.py` registers a `web` group with `web setup` (one-time token
  print) and `web regen-token` (rotates via confirmation).

### What's still missing or wrong

1. **Static dashboard is not gated.** Q5 of the brainstorming said yes; the
   current handler serves any path under `_STATIC_ROOT` without auth
   (server.py:219-239). Anyone who can reach the server gets `index.html`
   and any JS bundle it pulls.
2. **`web setup` prints the token in cleartext.** `web regen-token` does too.
   Q3 said "CLI never prints token"; this needs a fix that avoids leaking
   the token via terminal scrollback, shell history, or CI logs.
3. **No per-persona scoping.** Both `_get_or_create_bearer_token` and
   `web regen-token` open the unscoped `MemoryStore()`, ignoring
   `SAKTHAI_HOME`/`--persona`. With per-persona memory sharding now landed,
   each persona should have its own token so one persona's leaked token
   doesn't unlock another's memory.
4. **No `~/.sakthai/<persona>/web.token` file.** Q3 said the CLI shouldn't
   print tokens; the user's recovery path is `cat web.token`. That file
   doesn't exist yet — the only way to recover the token today is
   `sakthai web setup`, which contradicts Q3.
5. **`/health` endpoint isn't defined yet** but the design assumes it's
   public. Currently `/api/stages` and `/api/ecosystem` are the only
   endpoints; no health exists. (Adding a `/health` route is in scope.)

### Why this matters

Until the static dashboard is gated, "bearer token on `/api/*`" is a paper
gate: the dashboard HTML/JS bundle is served to anyone who reaches the
host, and the JS uses the token internally — but a network observer who
sees the initial HTML can read all the user-visible structure, and any
exposed debug endpoint would also be reachable.

The "no-cleartext-print" fix matters because terminal scrollback and shell
history routinely capture printed secrets for years; `web setup` should
not be the recovery path.

---

## Decisions (from brainstorming)

| # | Question | Answer |
|---|----------|--------|
| 1 | Where does the token live? | memory.db fact (canonical) |
| 2 | How is auth enforced? | Per-route `@require_auth` style (already done) |
| 3 | Rotation UX | File-based; CLI never prints token |
| 4 | Multi-persona | Per-persona token (default) |
| 5 | Static + health | Static also gated |
| 6 | Dashboard login UX | URL fragment + JS storage |

---

## Goal

Complete Fix #2 from the security plan so that:

1. Every request to `/api/*` requires a valid bearer token (already done).
2. Every request to `/static/*` and `/` (the dashboard entry) also requires
   a valid bearer token.
3. `/health` is public.
4. Tokens are per-persona, scoped via `config.persona_memory_db_path(persona)`.
5. The CLI never prints tokens in cleartext on stdout.
6. A user can recover their token by reading
   `~/.sakthai/<persona>/web.token` (mode 0600).
7. Coverage remains ≥97%; ruff/mypy/bandit/pytest all pass.

---

## Architecture

### Components

```
┌──────────────────────────────────────────────────────────────────┐
│ persona-aware config                                              │
│   config.persona_memory_db_path(persona)  ← already exists        │
│   config.persona_web_token_path(persona)  ← NEW                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ web/server.py                                                     │
│   _get_or_create_bearer_token(persona=None)                      │
│     • reads MemoryStore via config.persona_memory_db_path         │
│     • writes derived file to config.persona_web_token_path        │
│   _validate_bearer_header(headers, persona)                       │
│   _Handler.do_GET                                                 │
│     • /api/* and /* (except /health) → require valid token        │
│     • /health → always 200                                        │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ cli/system.py                                                     │
│   web setup [--persona NAME]                                      │
│     • ensures token exists                                        │
│     • tells user the file path; never prints the token            │
│   web regen-token [--persona NAME]                                │
│     • rotates token + writes new file (atomic)                    │
│     • never prints the token                                      │
│   web show-path [--persona NAME]                                  │
│     • prints ONLY the file path (cat-able by user)                │
└──────────────────────────────────────────────────────────────────┘
```

### Data flow on a request

```
client → GET /api/stages
              │
              ▼
  _Handler.do_GET
              │
              ├── path == /health → 200 (public)
              ├── path starts with /api/ OR / (static root)
              │     │
              │     ▼
              │   _validate_bearer_header(headers)
              │     • token from Authorization header (Bearer …)
              │     • compare against token in MemoryStore
              │     • missing  → 401 {"error":"Unauthorized"}
              │     • mismatch → 403 {"error":"Forbidden"}
              │     • match    → continue
              │
              └── serve response
```

The same gate covers `/api/stages`, `/api/ecosystem`, `/`, `/index.html`,
`/assets/*`, and any future path under the static root. Future-proof: any
new `/api/*` is gated because the check is at the top of `do_GET`, before
path dispatch.

### Data flow on token rotation

```
$ sakthai web regen-token --persona sakthai

web_setup_command(ctx)
  ├─ persona = ctx.persona or "sakthai"
  ├─ db_path = config.persona_memory_db_path(persona)
  ├─ file_path = config.persona_web_token_path(persona)
  ├─ new_token = secrets.token_hex(16)
  ├─ atomic write:
  │     write to db_path: replace web_auth.bearer_token
  │     write to file_path: new_token (0600, atomic rename)
  ├─ refresh in-process _BEARER_TOKEN cache (best-effort)
  ├─ echo: "Token rotated. New token written to <file_path>."
  └─ echo: "Read it with: cat <file_path>"
```

No print of `new_token`. Recovery = `cat ~/.sakthai/<persona>/web.token`.

### Token storage: two-tier

| Layer | Path | Mode | Owner |
|-------|------|------|-------|
| memory.db fact (canonical) | `~/.sakthai/<persona>/memory.db` table `facts`, `kind='web_auth'`, `key='bearer_token'`, `tags=['system','no-export']` | n/a (sqlite) | MemoryStore |
| Derived file | `~/.sakthai/<persona>/web.token` | 0600 | `config.register_secret` (so `redact_secrets` masks it in any future log/dump) |

The fact is the source of truth for the running server. The file exists
purely so the user can recover the token without it being printed. Both
must be written atomically; the file is rewritten on every successful
`setup`/`regen-token` call so it never goes stale.

Atomic write pattern (already standard in the codebase via `os.replace`):

```python
tmp = file_path.with_suffix(file_path.suffix + ".tmp")
tmp.write_text(token, encoding="utf-8")
os.chmod(tmp, 0o600)
os.replace(tmp, file_path)
```

### Per-persona scoping

`--persona` is the only way to choose which persona's token to act on.
Default is `sakthai` to match the existing CLI convention
(`sakthai.Persona` in config). The server reads the persona from
`SAKTHAI_HOME` if set, falling back to `sakthai`. If a `--persona` flag is
passed to `web setup`, it overrides.

For `serve()` (the long-running server), the persona is determined at
startup; there's no per-request switching — that would defeat the purpose
of having separate tokens.

---

## Components (precise)

### New helper: `config.persona_web_token_path(persona) -> Path`

```python
def persona_web_token_path(persona: str) -> Path:
    """Path to the derived token file for ``persona``.

    Same convention as persona_memory_db_path: ``~/.sakthai/<persona>/web.token``.
    Independent of the current process's own SAKTHAI_HOME.
    """
    return Path.home() / ".sakthai" / persona / "web.token"
```

Lives next to `persona_memory_db_path` (config.py:189). Same pattern,
same test coverage expectation.

### Refactor: `_get_or_create_bearer_token(persona=None)`

- Adds an optional `persona` parameter (default `"sakthai"`).
- Opens `MemoryStore(db_path=config.persona_memory_db_path(persona))`.
- On create/rotate, writes the derived file via
  `config.persona_web_token_path(persona)`.
- Backward-compatible: existing callers (the server) get the default
  persona; tests that don't pass a persona continue to work.

### Refactor: `_validate_bearer_header(headers, persona) -> tuple[int, dict] | None`

Pure function that returns `None` on success or `(code, body)` to send.
Replaces the inline auth check in `_Handler.do_GET`. Kept separate so the
static-path branch and the api-path branch share the same gate.

### Refactor: `_Handler.do_GET`

- Public exemption: `/health` (new endpoint, see below) returns 200.
- Auth check moves to the top of `do_GET`, applied uniformly to every
  other path. The current inline check at lines 180-200 is removed.
- Static fallback: the auth check happens *before* the path traversal
  check, so an attacker can't probe paths to test the traversal logic
  without a token.

### New: `GET /health`

Returns `{"status": "ok"}` with 200, always. Used by monitoring and
process supervisors; intentionally cheap and unauthenticated.

### Refactor: `cli/system.py`

- `web setup` no longer prints the token. New behavior:
  ```
  ── SakThai Web API Setup ──
  [+] Web API bearer token is configured.
  [i] Read your token: cat ~/.sakthai/<persona>/web.token
  [i] Use it as:  Authorization: Bearer <token>
  ```
- `web regen-token` no longer prints the token. Same output shape.
- New `web show-path` prints *only* the path:
  ```
  $ sakthai web show-path
  /home/beern/.sakthai/sakthai/web.token
  ```
- All three commands accept `--persona NAME`.

### Tests

- Extend `tests/test_web_server.py`:
  - Static root requires auth (current behavior: any path works; new
    behavior: needs token).
  - `/health` returns 200 without auth.
  - `_validate_bearer_header` returns 401 missing, 403 mismatch, None on
    match.
- New `tests/test_web_cli.py` (or extend `tests/test_cli_system.py`):
  - `web setup` no longer prints the token in stdout.
  - `web regen-token` rotates; old token rejected, new token accepted.
  - `web show-path` prints only the path.
  - `web setup --persona sakthai` writes to
    `~/.sakthai/sakthai/web.token`; `--persona saktan` writes to a
    different file.
- Existing tests should continue to pass (the API surface is
  unchanged for them).

---

## Data flow: server startup with auth enabled

```
$ SAKTHAI_WEB_ALLOW_PUBLIC=1 sakthai web setup --persona sakthai
   ↓
   persona = "sakthai"
   db_path = ~/.sakthai/sakthai/memory.db
   file_path = ~/.sakthai/sakthai/web.token
   ↓
   token = secrets.token_hex(16)
   ↓
   MemoryStore.open(db_path):
     add_fact(kind=web_auth, key=bearer_token, value=token, tags=[system, no-export])
     (or update existing)
   ↓
   atomic write of token to file_path (0600)
   ↓
   echo "Token configured. Read it with: cat ~/.sakthai/sakthai/web.token"

$ cat ~/.sakthai/sakthai/web.token
abcdef1234567890abcdef1234567890

$ SAKTHAI_WEB_ALLOW_PUBLIC=1 sakthai run --persona sakthai &
   ↓
   server starts; _get_or_create_bearer_token("sakthai") reads from db_path
   ↓
   _BEARER_TOKEN cache populated

$ curl http://localhost:3001/api/stages
   → 401 Unauthorized

$ curl -H "Authorization: Bearer abcdef..." http://localhost:3001/api/stages
   → 200 (JSON)

$ curl http://localhost:3001/
   → 401 (static gated)

$ curl http://localhost:3001/health
   → 200 {"status":"ok"}

$ curl "http://localhost:3001/#token=abcdef..."
   → 200 (static HTML; JS reads fragment, stores in memory, attaches header)
```

---

## Error handling

| Failure | Behavior |
|---------|----------|
| `MemoryStore.open` fails (file locked, perms) | `_get_or_create_bearer_token` falls back to in-memory ephemeral token (matches current behavior); warn loudly. |
| `web.token` write fails (perms, disk full) | CLI errors out with `click.ClickException`; doesn't leave the memory.db fact half-rotated. |
| `register_secret` fails | Logged, but not fatal — the token still works. |
| In-process `_BEARER_TOKEN` cache refresh after `regen-token` fails | Already best-effort (current code); server keeps old token until restart. Warning is sufficient. |
| Auth header missing on `/api/*` | 401 `{"error":"Unauthorized"}` (already the case). |
| Auth header missing on `/` or `/assets/*` | 401 same response shape, JSON, so the JS can detect and redirect. |
| Auth header malformed | 401 `{"error":"Unauthorized", "message":"Authorization header must be in 'Bearer <token>' format"}` (already the case). |
| Token mismatch | 403 `{"error":"Forbidden"}` (already the case). |

The atomic-write pattern (`tmp + os.replace`) prevents the
`memory.db fact written, web.token not written` half-state. Both writes
happen; if the file write fails, the fact write is also rolled back
(delete the new fact).

---

## Testing strategy

1. **Unit tests** for the new helpers:
   - `persona_web_token_path` returns the right path for each persona.
   - `_validate_bearer_header` returns the right tuple for each case.
   - Atomic-write helper rejects when the directory doesn't exist.

2. **Integration tests** (existing test server fixture):
   - Static requests now require auth.
   - `/health` is always 200.
   - Token rotation invalidates the old token in the next request.

3. **CLI tests**:
   - `web setup` stdout does **not** contain a 32-hex token.
   - `web regen-token` rotates; old token gets a 403.
   - `web show-path` output matches `config.persona_web_token_path()`.

4. **Manual verification checklist** (run after merge):
   - [ ] `sakthai web setup --persona sakthai` writes the file
   - [ ] `cat ~/.sakthai/sakthai/web.token` returns a 32-hex string
   - [ ] `chmod 600` is set on the file
   - [ ] `curl -H "Authorization: Bearer $(cat …)" /api/stages` → 200
   - [ ] `curl /api/stages` (no header) → 401
   - [ ] `curl /` (no header) → 401
   - [ ] `curl /health` (no header) → 200
   - [ ] `sakthai web regen-token` → old token gets 403, new token works
   - [ ] Two different personas have two different tokens

5. **CI gate**: full pytest must pass; coverage ≥97%; ruff/mypy/bandit
   all green. Matches the existing CI matrix (Python 3.11/3.12).

---

## Out of scope (deferred)

- **Fix #1: Stripe/Twilio credential rotation** — owner: Beer. Independent
  of this design.
- **HTML login form** — explicit user choice (Q6: URL fragment + JS storage).
- **Reverse-proxy auth** — explicit user choice (Q2: per-route).
- **OAuth / mTLS / API keys per client** — over-engineered for a
  personal-use dashboard.
- **Multi-user support** — this is a personal app.
- **Token TTL / auto-rotation on server start** — explicit user choice
  (Q3: token persists across restarts; rotation is manual).
- **Audit log of auth failures** — useful, but YAGNI for v1; can be
  added in a follow-up.
- **The `dashboard/dist` rebuild** — separate work; out of scope here.
- **The full plan's `run/cycle` integration** — `SECURITY_FIXES_PLAN.md`
  Phase 5 tests assume a running server on port 8080, but the SakThai
  server defaults to port 3001. Tests will use 3001 (the actual default)
  and document the port explicitly.

---

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| A user runs `web setup` once, never reads the file, then forgets the token | Medium | `doctor` and `status` print the path so the user can find it later; `web show-path` is a one-shot command. |
| A user accidentally `git add`s `~/.sakthai/<persona>/web.token` | Low | The file is outside the repo (in `$HOME`). `.gitleaks.toml` already covers pattern-based detection. |
| A user runs the server with `SAKTHAI_WEB_ALLOW_PUBLIC=1` but never runs `web setup` | Low | `_get_or_create_bearer_token` auto-generates on first request, so the server starts; the user just won't have a recoverable token until they run `web setup`. |
| Existing dashboard bundle expects un-authed `/` | Medium | The dashboard bundle needs an `index.html` that reads the URL fragment and attaches the bearer header. If the existing bundle doesn't do this, we serve a small `auth_gate.html` that does the work; redirect logic lives there. (Implementation detail, scoped to the plan, not this design.) |
| Test flakiness from real HTTPServer in pytest | Low | Existing tests already use this pattern with success; no new concerns. |
| Atomic write races between `setup` and `regen-token` | Negligible | Both go through the same helper; CLI is single-threaded. |

---

## Open questions

1. **What happens to a token if the persona's memory.db is deleted?**
   Answer: server regenerates on next request. Document this in
   `docs/runtimes.md` as part of the implementation, not this design.

2. **Should `web setup` overwrite an existing token by default, or
   only create one if missing?**
   Recommendation: create-if-missing by default; `--force` flag to
   overwrite. Final answer in the implementation plan, not this design.

3. **Should the static dashboard bundle be updated as part of this
   work, or shipped as a separate change?**
   Recommendation: separate change. This design only gates the path;
   the bundle update is a follow-up.

---

## Definition of done

- [ ] All five components implemented and reviewed.
- [ ] All tests in `tests/test_web_server.py` and `tests/test_cli_system.py`
      pass; new tests added; coverage ≥97%.
- [ ] `docs/runtimes.md`, `SECURITY.md`, `.env.example` updated.
- [ ] Manual verification checklist run end-to-end.
- [ ] `security/SECURITY_FIXES_PLAN.md` Fix #2 marked complete with date.
- [ ] `PLAN.md` updated to reflect completion.
- [ ] Fix #1 (credential rotation) explicitly noted as still pending
      (it's Beer's track).

---

## Approval

- [ ] Beer — scope and trade-offs
- [ ] Beer — UX for token recovery (file-based, no cleartext print)
- [ ] Reviewer — code review before merge
