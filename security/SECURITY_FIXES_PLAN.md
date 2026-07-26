# Security Fixes Plan — 2026-07

> **High-Priority:** Credential rotation + Web API authentication

This plan tracks the two blocking security fixes identified in the 2026-07 audit.
Work top-to-bottom. Check off with date when done.

---

## 🚨 Overview

| Fix | Priority | Effort | Owner | Status |
|-----|----------|--------|-------|--------|
| **Rotate Stripe + Twilio credentials** | 🔴 HIGH | 5 min | Beer | [ ] |
| **Add Web API authentication** | 🔴 HIGH | 4-6 hrs | Claude | [ ] |

---

## Fix #1: Rotate Stripe + Twilio Credentials

**Impact:** SECURITY (credentials in git history)
**Effort:** 5 minutes
**Owner:** Beer (credential access)

### Context

The 2026-07 audit found that `.gitleaks.toml` previously allowlisted (by exact value):
1. A Stripe consumer key (`ck_…`)
2. A Twilio token (see audit report for exact value — do not commit actual token)

Both were scrubbed from the working tree but **remain in git history**. If the repository ever goes public (or is accessed by someone with history access), these credentials are compromised.

### Why This is Important

- ✅ `.gitleaks.toml` entries were already removed (so new commits won't introduce similar issues)
- ❌ **But:** The old values sit in git history and must be rotated
- Scrubbing a secret from the tree does **not** invalidate it

### What You Need To Do

**Step 1: Stripe Dashboard (2 min)**

1. Go to https://dashboard.stripe.com/apikeys
2. Locate the consumer key starting with `ck_…`
3. Click "Revoke" or "Delete"
4. Confirm revocation
5. Generate a new consumer key (if needed for integration)
6. Copy new key and update `ANTHROPIC_API_KEY` or relevant .env file

**Step 2: Twilio Console (2 min)**

1. Go to https://www.twilio.com/console/account/api-keys
2. Locate the compromised token (see audit report for exact value)
3. Click "Delete"
4. Confirm deletion
5. Generate a new API key (if needed)
6. Update your `.env` or Telegram bot config

**Step 3: Verify (1 min)**

```bash
# Confirm old credentials no longer work (should fail)
curl -H "Authorization: Bearer <OLD_TWILIO_TOKEN>" \
  https://api.twilio.com/2010-04-01/Accounts.json
# Expected: 401 Unauthorized

# Confirm new credentials work (update with new token)
curl -H "Authorization: Bearer <NEW_TOKEN>" \
  https://api.twilio.com/2010-04-01/Accounts.json
# Expected: 200 OK or 403 (if no access, but not 401)
```

### Definition of Done

- [ ] Stripe credential revoked in dashboard; new one generated
- [ ] Twilio token deleted in console; new one generated
- [ ] `.env` updated with new credentials
- [ ] Telegram bot / integrations re-tested with new keys
- [ ] Date recorded: **2026-07-__**

---

## Fix #2: Add Web API Authentication

**Impact:** SECURITY (unauthenticated memory access if public)
**Effort:** 4-6 hours
**Owner:** Claude Code (implementation)
**Status:** [ ] Not started

### Context

The web API (`personas/sakthai/sakthai/web/server.py`) currently has **no authentication**:

```python
@app.route('/api/stages')
def get_stages():
    return {"stage": store.get_current_stage()}  # Anyone can call this!
```

**Current safeguard:** The server defaults to loopback-only (`127.0.0.1`), so it's safe for local use. However, if `SAKTHAI_WEB_ALLOW_PUBLIC=1` is set to expose the API to a network, there's **zero authentication**.

### Why This is Important

- ✅ Personal/local use is fine (loopback only)
- ❌ **Production use:** If the API is exposed to a network, anyone can read memory, retrieve all facts, search observations
- ❌ **Data leak risk:** Memory contains personal notes, meeting summaries, leads, sensitive decision logs

### Design: Bearer Token Authentication

Implement a **bearer token** scheme:

1. **Token format:** Opaque string (e.g., 32 random hex chars)
2. **Storage:** In `memory.db` as a `config` fact (kind=`web_auth`, key=`bearer_token`)
3. **Enforcement:** All `/api/*` routes require `Authorization: Bearer <token>` header
4. **Generation:** Auto-generate on first server start if missing; expose via `sakthai web setup`

### Implementation Plan

#### Phase 1: Add Token Storage (1 hour)

**File:** `personas/sakthai/sakthai/web/server.py`

1. Add function `_get_or_create_bearer_token(store)`:
   ```python
   def _get_or_create_bearer_token(store: MemoryStore) -> str:
       """Get or create bearer token from memory store."""
       try:
           fact = store.search(kind='web_auth', key='bearer_token')[0]
           return fact.value
       except IndexError:
           # Generate new token
           import secrets
           token = secrets.token_hex(16)  # 32 hex chars
           store.add_fact(
               kind='web_auth',
               key='bearer_token',
               value=token,
               tags=['system', 'no-export']  # Exclude from memory exports
           )
           return token
   ```

2. Modify `serve()` function to load token on startup:
   ```python
   def serve(store: MemoryStore, host: str = '127.0.0.1', port: int = 8080) -> None:
       global BEARER_TOKEN
       BEARER_TOKEN = _get_or_create_bearer_token(store)
       # ... rest of server setup
   ```

**Tests to add:**
- `test_web_auth_token_created_on_first_run`
- `test_web_auth_token_persists_across_restarts`

#### Phase 2: Middleware + Enforcement (1.5 hours)

**File:** `personas/sakthai/sakthai/web/server.py`

1. Add decorator to protect routes:
   ```python
   def require_auth(f):
       """Require Bearer token in Authorization header."""
       @functools.wraps(f)
       def decorated_function(*args, **kwargs):
           auth = request.headers.get('Authorization', '')
           if not auth.startswith('Bearer '):
               return {'error': 'Unauthorized'}, 401
           token = auth[7:]  # Strip "Bearer "
           if token != BEARER_TOKEN:
               return {'error': 'Forbidden'}, 403
           return f(*args, **kwargs)
       return decorated_function
   ```

2. Apply to all `/api/*` routes:
   ```python
   @app.route('/api/stages')
   @require_auth
   def get_stages():
       return {"stage": store.get_current_stage()}
   ```

3. **Exception:** Keep health check unauth'd (optional):
   ```python
   @app.route('/health')
   def health():
       return {'status': 'ok'}, 200  # No auth needed; allows monitoring
   ```

**Tests to add:**
- `test_api_routes_require_bearer_token`
- `test_api_rejects_missing_auth_header`
- `test_api_rejects_invalid_token`
- `test_api_accepts_valid_token`
- `test_health_endpoint_unauth'd`

#### Phase 3: CLI Setup Command (1.5 hours)

**File:** `personas/sakthai/sakthai/cli/system.py` (new `web setup` command)

1. Add command:
   ```python
   @click.group()
   def web():
       """Web server commands."""
       pass

   @web.command()
   @click.pass_obj
   def setup(ctx):
       """Initialize web API authentication."""
       store = ctx['store']
       token = _get_or_create_bearer_token(store)
       click.echo(f"✅ Web API token configured")
       click.echo(f"Use: Authorization: Bearer {token}")
   ```

2. Display token securely (one-time, on creation):
   ```
   sakthai web setup
   # Output:
   # ✅ Web API token configured
   # Token: abc123def456...
   # Save this securely. You can regenerate anytime with `sakthai web regen-token`
   ```

3. Add regenerate command:
   ```python
   @web.command()
   @click.confirmation_option(
       prompt='Are you sure? All existing clients will stop working.'
   )
   def regen_token(ctx):
       """Regenerate web API bearer token."""
       store = ctx['store']
       import secrets
       new_token = secrets.token_hex(16)
       store.add_fact(
           kind='web_auth',
           key='bearer_token',
           value=new_token,
           tags=['system', 'no-export']
       )
       click.echo(f"✅ New token: {new_token}")
   ```

**Tests to add:**
- `test_web_setup_creates_token`
- `test_web_regen_token_requires_confirmation`
- `test_web_regen_token_invalidates_old_token`

#### Phase 4: Documentation (1 hour)

**Files to update:**

1. **`docs/runtimes.md`** — Add section:
   ```markdown
   ## Web Server Authentication

   The `/api/*` endpoints require a bearer token:

   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8080/api/stages
   ```

   **Setup:**
   ```bash
   sakthai web setup  # Initialize and display token
   sakthai web regen-token  # Regenerate (all clients must update)
   ```

   **Security note:** Tokens are stored in memory.db with `tags=['system', 'no-export']`
   so they never appear in snapshot exports. Keep tokens secret; rotate if compromised.
   ```

2. **`SECURITY.md`** — Add to "Enforced security gates":
   ```markdown
   | Web API auth | `require_auth` decorator | All `/api/*` protected (bearer token) | ✅ Enforced |
   ```

3. **`.env.example`** — Add (if needed):
   ```
   # Web server (optional)
   SAKTHAI_WEB_ALLOW_PUBLIC=0  # Set to 1 to expose to network (requires auth!)
   ```

4. **`README.md`** — Update security section if web API is documented there

**Tests to add:**
- `test_doc_includes_web_auth_setup`

#### Phase 5: Testing (1 hour)

**New test file:** `tests/test_web_auth.py`

```python
import pytest
from sakthai.web.server import app, require_auth, _get_or_create_bearer_token
from sakthai.memory.store import MemoryStore

@pytest.fixture
def client_and_store():
    store = MemoryStore(':memory:')
    app.config['TESTING'] = True
    app.config['STORE'] = store
    return app.test_client(), store

def test_api_requires_bearer_token(client_and_store):
    client, _ = client_and_store
    response = client.get('/api/stages')
    assert response.status_code == 401

def test_api_rejects_invalid_token(client_and_store):
    client, _ = client_and_store
    response = client.get(
        '/api/stages',
        headers={'Authorization': 'Bearer invalid_token'}
    )
    assert response.status_code == 403

def test_api_accepts_valid_token(client_and_store):
    client, store = client_and_store
    token = _get_or_create_bearer_token(store)
    response = client.get(
        '/api/stages',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200

def test_token_persists_across_calls(client_and_store):
    client, store = client_and_store
    token1 = _get_or_create_bearer_token(store)
    token2 = _get_or_create_bearer_token(store)
    assert token1 == token2

def test_health_endpoint_unauth'd(client_and_store):
    client, _ = client_and_store
    response = client.get('/health')
    assert response.status_code == 200
    assert 'Authorization' not in response.json or response.json.get('status') == 'ok'
```

**Run before committing:**
```bash
uv run pytest tests/test_web_auth.py -v --cov=sakthai.web
```

### Rollout Strategy

**Phase A: Code Changes (4-6 hrs)**
- [ ] Implement token storage (Phase 1)
- [ ] Add auth middleware (Phase 2)
- [ ] Add CLI commands (Phase 3)
- [ ] Update docs (Phase 4)
- [ ] Add tests (Phase 5)

**Phase B: Testing & Verification (1 hr)**
- [ ] All tests pass (`uv run pytest tests/test_web_auth.py`)
- [ ] Existing API tests still pass (no regressions)
- [ ] Coverage remains >97%
- [ ] Bandit + mypy + ruff all pass

**Phase C: Integration Testing (30 min)**
- [ ] Start server: `sakthai web setup`
- [ ] Verify token created: `echo "SELECT value FROM facts WHERE kind='web_auth'" | sqlite3 ~/.sakthai/memory.db`
- [ ] Test with token:
  ```bash
  TOKEN=<from setup>
  curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/stages
  # Should return: {"stage": "dream"} or similar
  ```
- [ ] Test without token:
  ```bash
  curl http://localhost:8080/api/stages
  # Should return: {"error": "Unauthorized"}, 401
  ```

**Phase D: Documentation Review (30 min)**
- [ ] Proofread `docs/runtimes.md`
- [ ] Verify `.env.example` is clear
- [ ] Test that `sakthai --help` includes new `web setup` command
- [ ] Check that SECURITY.md is up-to-date

### Definition of Done

- [ ] All code changes committed (Phase 1-5)
- [ ] All tests passing (including new `test_web_auth.py`)
- [ ] Coverage ≥97%
- [ ] CI passing (ruff, mypy, bandit, pytest)
- [ ] Documentation updated
- [ ] Integration tested locally
- [ ] PR created and merged
- [ ] Date recorded: **2026-07-__**

### Rollback Plan

If issues arise:

1. **Revert commits:** `git revert <commit-sha>`
2. **Clear tokens:** `sqlite3 ~/.sakthai/memory.db "DELETE FROM facts WHERE kind='web_auth'"`
3. **Restart:** `pkill -f 'sakthai mcp'` or restart service
4. **Communicate:** Update SECURITY.md with status

---

## Timeline & Dependencies

```
┌─ Fix #1: Rotate Credentials ─────────────────────────────┐
│  [/] Stripe dashboard (2 min)                             │
│  [/] Twilio console (2 min)                               │
│  [/] Verify old credentials revoked (1 min)               │
│  [/] Test new credentials (2 min)                         │
│  Duration: 5 minutes | Owner: Beer                        │
└───────────────────────────────────────────────────────────┘

  ↓ (independent)

┌─ Fix #2: Web API Auth ──────────────────────────────────┐
│  [/] Phase 1: Token storage (1 hr)                       │
│  [/] Phase 2: Auth middleware (1.5 hrs)                  │
│  [/] Phase 3: CLI commands (1.5 hrs)                     │
│  [/] Phase 4: Docs (1 hr)                                │
│  [/] Phase 5: Tests (1 hr)                               │
│  [/] Integration testing (30 min)                        │
│  [/] Final review (30 min)                               │
│  Duration: 4-6 hours | Owner: Claude Code                │
└───────────────────────────────────────────────────────────┘
```

**Parallel work:** Both fixes can proceed in parallel (no dependencies).

---

## Success Criteria

✅ **Fix #1 Complete When:**
- Old Stripe key revoked
- Old Twilio token deleted
- New credentials in `.env` or config
- Integrations re-tested and working

✅ **Fix #2 Complete When:**
- Bearer token auth enforced on all `/api/*` routes
- `/health` endpoint unauth'd (for monitoring)
- CLI commands working (`sakthai web setup`, `regen-token`)
- All tests passing (including new `test_web_auth.py`)
- Documentation updated
- PR merged

✅ **Overall Complete When:**
- Both fixes done + verified
- CI passing on `main`
- No regressions in other security features
- Update PLAN.md with completion dates

---

## Notes & References

- **Audit report:** `docs/SECURITY.md` + `docs/security-hardening.md`
- **Current server:** `personas/sakthai/sakthai/web/server.py`
- **Memory store:** `personas/sakthai/sakthai/memory/store.py` (add_fact, search)
- **CLI patterns:** `personas/sakthai/sakthai/cli/system.py` (see `setup` command)
- **Test patterns:** `tests/test_web_server.py` (existing web tests)
- **Environment:** `.env.example` (for reference)

---

## Approvals & Sign-Off

| Role | Status | Date | Notes |
|------|--------|------|-------|
| **Beer** (credential rotation) | [ ] | — | Approve when ready to rotate |
| **Claude Code** (web auth impl) | [ ] | — | Approve when ready to start |
| **Reviewer** (PR sign-off) | [ ] | — | Final code review before merge |

---

**Last updated:** 2026-07-26
**Created by:** Audit Report (Claude Code)
**Status:** Ready for approval
