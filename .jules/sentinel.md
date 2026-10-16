## 2026-10-16 - Prevent XSS in Dashboard and Index Error Messages
**Vulnerability:** Cross-Site Scripting (XSS) via `e.message` injection into DOM using `.innerHTML`.
**Learning:** Even internal API error messages can contain reflected user input if the backend echoes bad input in the error response. Directly inserting these into the DOM using `.innerHTML` creates an XSS vulnerability.
**Prevention:** Always wrap dynamically generated error strings with an HTML escaper (like the local `escapeHtml` function) before injecting them into `.innerHTML`.
