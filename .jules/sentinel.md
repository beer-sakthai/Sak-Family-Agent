## 2026-06-19 - [Insecure Dashboard Defaults]
**Vulnerability:** The dashboard server was binding to 0.0.0.0 by default and lacked basic security headers (CSP, X-Frame-Options).
**Learning:** Defaulting to all interfaces exposes internal data (like memory snapshots in data.json) to the local network.
**Prevention:** Always default dashboard/debug servers to 127.0.0.1 and include defensive security headers to prevent clickjacking and XSS.

## 2026-06-21 - [Sensitive Token Leakage in Tool Errors]
**Vulnerability:** The `send_telegram_message` tool leaked the raw `TELEGRAM_BOT_TOKEN` in its error message when the token failed format validation.
**Learning:** Incorporating raw environment-sourced secrets into error strings (e.g., via f-strings) for "better diagnostics" creates a high-severity data leak that models can see and potentially log.
**Prevention:** Redact or omit the actual secret value from all tool-level error messages. Rely on generic error descriptions for secret-related failures.
