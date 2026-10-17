## 2024-10-18 - XSS in RAG Search Results
**Vulnerability:** The RAG search results in `docs/index.html` and `scripts/saksee/dashboard.html` rendered user-controlled properties (`r.agent`, `r.source`, `r.text`) directly into the DOM using `.innerHTML` without escaping.
**Learning:** Even data coming from internal APIs (like RAG results) can contain untrusted data that leads to Cross-Site Scripting (XSS) if not properly escaped before insertion into the DOM using `.innerHTML`.
**Prevention:** Always wrap variables containing potentially untrusted strings with an HTML escaping function (like `escapeHtml()`) before concatenating them into strings destined for `.innerHTML`, or assign directly to `.textContent`.
## 2026-10-18 - XSS in RAG Search Results
**Vulnerability:** The RAG search results in `docs/index.html` and `scripts/saksee/dashboard.html` rendered user-controlled properties (`r.agent`, `r.source`, `r.text`) directly into the DOM using `.innerHTML` without escaping.
**Learning:** Even data coming from internal APIs (like RAG results) can contain untrusted data that leads to Cross-Site Scripting (XSS) if not properly escaped before insertion into the DOM using `.innerHTML`.
**Prevention:** Always wrap variables containing potentially untrusted strings with an HTML escaping function (like `escapeHtml()`) before concatenating them into strings destined for `.innerHTML`, or assign directly to `.textContent`.

## 2026-10-18 - XSS in RAG Search Results
**Vulnerability:** The RAG search results in `docs/index.html` and `scripts/saksee/dashboard.html` rendered user-controlled properties (`r.agent`, `r.source`, `r.text`) directly into the DOM using `.innerHTML` without escaping.
**Learning:** Even data coming from internal APIs (like RAG results) can contain untrusted data that leads to Cross-Site Scripting (XSS) if not properly escaped before insertion into the DOM using `.innerHTML`.
**Prevention:** Always wrap variables containing potentially untrusted strings with an HTML escaping function (like `escapeHtml()`) before concatenating them into strings destined for `.innerHTML`, or assign directly to `.textContent`.
