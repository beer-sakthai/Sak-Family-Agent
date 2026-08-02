# Sentinel Security Findings Journal

## 2025-07-26 - Empty Host Loopback Binding Bypass
**Vulnerability:** Python's socket and HTTP/HTTPS servers treat an empty string `""` as `INADDR_ANY` (binding to all interfaces, equivalent to `0.0.0.0`). Classifying `""` as loopback-only allows unauthenticated servers to be exposed publicly to the network.
**Learning:** Checking host values against `_LOOPBACK_NAMES = frozenset({"localhost", ""})` created a security loophole where passing `""` allowed the unauthenticated server to bypass the loopback restriction check and listen publicly on all interfaces.
**Prevention:** Exclude `""` from loopback hostname whitelists. Always validate loopback-only requirements against concrete IP loopback structures or strict non-empty loopback names (like `"localhost"` or `"127.0.0.1"`).

## 2026-07-26 - [CRITICAL] Web API Exposing Personal Memory Under Public Binding
**Vulnerability:** SAKTHAI_WEB_ALLOW_PUBLIC=1 permitted binding the unauthenticated Web API server to non-loopback network interfaces, exposing personal memory, recent facts, and observations to the network with zero authentication.
**Learning:** Defaulting to local loopback binds prevents accidental exposure, but lacks defense-in-depth once public binding is enabled. Standardizing token authentication on the HTTP request handler level protects the API under any binding configuration.
**Prevention:** Always implement Bearer Token authentication on standard library HTTP request handlers, and store security tokens inside the MemoryStore facts table under `kind='web_auth'` and `key='bearer_token'` for secure rotation and retrieval.

## 2026-08-01 - Hostname Wildcard Loopback Bypass and Unauthenticated Standalone Server Binding
**Vulnerability:** The unauthenticated API in `server.py` could be bound to any interface (publicly exposing sensitive personal memory/data) via an empty string host (`""`) bypass because `""` was incorrectly included in `_LOOPBACK_NAMES`. In addition, the standalone `scripts/serve_api.py` server lacked hostname validation entirely, permitting arbitrary non-loopback bindings.
**Learning:** In Python's `socket` library, passing an empty string `""` as the hostname binds the listener to `INADDR_ANY` (all interfaces, equivalent to `0.0.0.0`), allowing any client on the network to access it. If an application incorrectly classifies empty string hosts as local/loopback-only, attackers can bypass security checks meant to protect unauthenticated endpoints. Standalone scripts that mirror core API behavior are easily overlooked during security hardening and must be explicitly audited and validated.
**Prevention:** Always exclude the empty host string `""` from loopback hostname allowlists. Ensure that any standalone scripts or testing servers are subjected to the same rigorous hostname validation and network exposure policies as the primary application. Always write regression tests verifying empty string host blocks and non-loopback restrictions.

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

## 2026-08-02 - Server-Side Request Forgery, DNS Rebinding, and Option Smuggling in Verification Utilities
**Vulnerability:** The asset verification script `verify_hf_upload.py` executed `curl` with arbitrary user-supplied command-line URL parameters without schema restrictions, hostname validation, or option validation. This could lead to: (1) option smuggling / parameter injection into curl subprocesses, (2) Server-Side Request Forgery (SSRF) targeting loopback or private network infrastructure, and (3) DNS rebinding to bypass IP blocklists.
**Learning:** Utilities running within automated CI/CD pipelines (such as GitHub Actions) often bypass standard input sanitization layers, making them prime targets for credential extraction, SSRF, or local resource exposure. Subprocesses running command-line requests must treat all external parameters defensively, resolving and validating hostnames to ensure requests do not access non-public, local, or multicast IP addresses.
**Prevention:** Always restrict schemes strictly to `http` or `https` and block leading hyphens (`-`) to neutralize option smuggling. Perform DNS resolution via `socket.getaddrinfo` and parse results via `ipaddress.ip_address` to reject multicast and non-global IPs before making requests. Securely pin host resolution using curl's `--resolve` parameter to prevent DNS rebinding attacks between DNS lookup and curl execution.
