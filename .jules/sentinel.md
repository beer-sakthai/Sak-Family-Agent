## 2025-07-26 - Empty Host Loopback Binding Bypass
**Vulnerability:** Python's socket and HTTP/HTTPS servers treat an empty string `""` as `INADDR_ANY` (binding to all interfaces, equivalent to `0.0.0.0`). Classifying `""` as loopback-only allows unauthenticated servers to be exposed publicly to the network.
**Learning:** Checking host values against `_LOOPBACK_NAMES = frozenset({"localhost", ""})` created a security loophole where passing `""` allowed the unauthenticated server to bypass the loopback restriction check and listen publicly on all interfaces.
**Prevention:** Exclude `""` from loopback hostname whitelists. Always validate loopback-only requirements against concrete IP loopback structures or strict non-empty loopback names (like `"localhost"` or `"127.0.0.1"`).
