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
## 2024-10-18 - Hardcoded Cache Path for HuggingFace Token
**Vulnerability:** A hardcoded, user-specific absolute path (`/opt/data/profiles/sakthai/home/.cache/huggingface/token`) was used to load the Hugging Face token in `services/inference-endpoint/poll_endpoint.py`.
**Learning:** Hardcoding absolute paths, especially those tied to a specific user profile or environment (`sakthai`), leads to brittle code and potential security risks if secrets are improperly exposed or shared. It also breaks execution in different environments.
**Prevention:** Prioritize retrieving credentials from established environment variables (like `HF_TOKEN`). As a fallback, dynamically construct paths relative to the current user's home directory (e.g., using `Path.home() / ".cache/huggingface/token"`).
## 2026-10-18 - SSRF via Multiple Encoding
**Vulnerability:** The API dashboard `fetchJson` used single validation but allowed recursively decoded URLs, exposing the system to Server-Side Request Forgery via double-encoding (e.g. `%252F%252F`).
**Learning:** Defending against SSRF requires deep, bounded unquoting in `try/catch` blocks to catch encoding tricks without blocking legitimate queries containing raw `%` symbols.
**Prevention:** Apply a robust bounding unquote mechanism that defaults safely when decoding fails.
## 2026-10-18 - DoS via Unhandled TypeError in compare_digest
**Vulnerability:** The API server in `scripts/serve_api.py` called `secrets.compare_digest(val, expected_token)` directly. Since `compare_digest` only supports ASCII string operands, feeding it a string with a non-ASCII character (e.g., in an `Authorization` header or `?token=` parameter) raised a `TypeError`, crashing the connection handler.
**Learning:** Security functions like `compare_digest` often have strict input constraints. Exposing them directly to unvalidated network input (like headers) can inadvertently create Denial of Service (DoS) vectors.
**Prevention:** Always encode user-provided strings to bytes (e.g., `.encode("utf-8")`) before using them with `secrets.compare_digest` to ensure type safety and prevent unhandled exceptions.
