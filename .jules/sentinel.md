## 2026-08-02 - Web API Authentication & DB Order Quirks
**Vulnerability:** Unauthenticated endpoints `/api/stages` and `/api/ecosystem` exposing personal memory facts and system configuration.
**Learning:**
1. Registering secrets (via `register_secret`) *before* executing `store.add_fact(...)` causes the stored token itself to be masked to `'[REDACTED]'` in the database, breaking persistence.
2. Multiple imports of a module (e.g., `sakthai.web.server` vs `personas.sakthai.sakthai.web.server`) can result in duplicate global caches (`_BEARER_TOKEN`). Updating sys.modules dynamically resolves cache invalidation.
3. Querying SQLite database records ordered by `updated_at DESC` does not guarantee returning the newest row when both old and new records are inserted in the same second. Expressly deleting the old fact via `delete_facts_by_key` guarantees correct state.
**Prevention:**
- Secure all exposed HTTP endpoints with Bearer Token Authentication.
- Call database writes prior to registering secrets for redaction.
- Delete or replace existing key facts rather than appending duplicates with identical timestamps.
# Sentinel Security Findings Journal

## 2026-08-01 - Hostname Wildcard Loopback Bypass and Unauthenticated Standalone Server Binding
**Vulnerability:** The unauthenticated API in `server.py` could be bound to any interface (publicly exposing sensitive personal memory/data) via an empty string host (`""`) bypass because `""` was incorrectly included in `_LOOPBACK_NAMES`. In addition, the standalone `scripts/serve_api.py` server lacked hostname validation entirely, permitting arbitrary non-loopback bindings.
**Learning:** In Python's `socket` library, passing an empty string `""` as the hostname binds the listener to `INADDR_ANY` (all interfaces, equivalent to `0.0.0.0`), allowing any client on the network to access it. If an application incorrectly classifies empty string hosts as local/loopback-only, attackers can bypass security checks meant to protect unauthenticated endpoints. Standalone scripts that mirror core API behavior are easily overlooked during security hardening and must be explicitly audited and validated.
**Prevention:** Always exclude the empty host string `""` from loopback hostname allowlists. Ensure that any standalone scripts or testing servers are subjected to the same rigorous hostname validation and network exposure policies as the primary application. Always write regression tests verifying empty string host blocks and non-loopback restrictions.
