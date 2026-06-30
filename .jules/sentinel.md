## 2026-06-19 - [Insecure Dashboard Defaults]
**Vulnerability:** The dashboard server was binding to 0.0.0.0 by default and lacked basic security headers (CSP, X-Frame-Options).
**Learning:** Defaulting to all interfaces exposes internal data (like memory snapshots in data.json) to the local network.
**Prevention:** Always default dashboard/debug servers to 127.0.0.1 and include defensive security headers to prevent clickjacking and XSS.
## 2025-05-23 - [Dashboard Denial of Service via days parameter]
**Vulnerability:** The dashboard data collection endpoint allowed arbitrary integer values for the `days` parameter, which was used to allocate multiple lists (labels, bins, series).
**Learning:** External parameters used in list allocations or loop ranges must be clamped to prevent memory exhaustion attacks.
**Prevention:** Always validate and clamp numeric inputs that control resource allocation.
