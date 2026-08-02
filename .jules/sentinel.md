## 2026-07-24 - [CRITICAL/HIGH] Missing Sensitive History and Post-Quantum SSH Key Protections
**Vulnerability:** Core guardrails sets did not include `.git-credentials`, various database/interactive REPL shell histories (`.node_repl_history`, `.mysql_history`, `.psql_history`, `.sqlite_history`), or the post-quantum SSH XMSS private keys (`id_xmss`).
**Learning:** General/classic SSH keys (like RSA, DSA, ED25519) were covered, but newer/post-quantum variants and specific utility-level histories were missed, leaving potential exfiltration vectors open.
**Prevention:** Ensure baseline lists are periodically reviewed against modern development and SSH credential standards. Keep all persona guardrail modules in strict sync.
