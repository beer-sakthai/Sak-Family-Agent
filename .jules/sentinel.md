# Sentinel's Journal

## 2026-07-26 - [CRITICAL] Web API Exposing Personal Memory Under Public Binding
**Vulnerability:** SAKTHAI_WEB_ALLOW_PUBLIC=1 permitted binding the unauthenticated Web API server to non-loopback network interfaces, exposing personal memory, recent facts, and observations to the network with zero authentication.
**Learning:** Defaulting to local loopback binds prevents accidental exposure, but lacks defense-in-depth once public binding is enabled. Standardizing token authentication on the HTTP request handler level protects the API under any binding configuration.
**Prevention:** Always implement Bearer Token authentication on standard library HTTP request handlers, and store security tokens inside the MemoryStore facts table under `kind='web_auth'` and `key='bearer_token'` for secure rotation and retrieval.
