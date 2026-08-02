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
