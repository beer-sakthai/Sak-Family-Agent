## 2026-06-19 - [Insecure Dashboard Defaults]
**Vulnerability:** The dashboard server was binding to 0.0.0.0 by default and lacked basic security headers (CSP, X-Frame-Options).
**Learning:** Defaulting to all interfaces exposes internal data (like memory snapshots in data.json) to the local network.
**Prevention:** Always default dashboard/debug servers to 127.0.0.1 and include defensive security headers to prevent clickjacking and XSS.
