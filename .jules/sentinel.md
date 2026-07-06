# Sentinel Security Journal

## 2026-07-01 - [Redacting Secrets in Tool Error Handlers]

**Vulnerability:** Raw `TELEGRAM_BOT_TOKEN` was included in the exception string returned to the LLM when an `Unexpected Error` occurred during message sending.

**Learning:** Generic `except Exception as exc` handlers that return `str(exc)` can inadvertently leak sensitive configuration data (like API tokens in URLs or credentials in object representations) to the model.

**Prevention:** Always redact sensitive tokens or use specific, safe error messages in tool return strings. Use `re.sub` or structured error objects instead of raw exception stringification for external API calls.

## 2026-07-02 - [Global Secret Redaction Fail-safe]

**Vulnerability:** Multi-provider API keys and Telegram tokens could still leak via raw exception strings in tool handlers if not manually redacted in every single tool.

**Learning:** While individual tool hardening (like in the Telegram tool) is good, a global fail-safe in the agent's tool execution loop (`_execute_tool`) provides defense-in-depth against future tools or forgotten handlers.

**Prevention:** Implement a centralized `redact_secrets` utility that knows about all sensitive environment variables and apply it to all stringified exceptions returned from the tool layer to the LLM.

## 2026-07-03 - [Defense-in-Depth for Persistent Data and Logs]

**Vulnerability:** Session logs and the memory database were created with default system permissions (often 0644), potentially exposing sensitive interaction history or learned facts to other users on the same host. Additionally, session logs could contain unredacted secrets if tools were used directly or if the model echoed sensitive inputs.

**Learning:** Security must extend beyond the active tool loop to the persistent data layer. Centralizing redaction at the tool execution boundary and the log writing boundary, combined with strict POSIX file permissions (0600/0700), ensures that sensitive data remains protected both in transit (to the LLM) and at rest (on disk).

**Prevention:** Use `os.open` with explicit modes for file creation and `os.chmod` for existing sensitive directories/files. Always apply central redaction logic to any data being persisted to logs or returned from external tool executions.

## 2026-07-04 - [Centralized Path Validation for Tools]

**Vulnerability:** The `ingest_document` tool lacked the directory restriction checks (SAKTHAI_READ_ALLOW) present in `read_file`, allowing the agent to potentially read and learn facts from any file accessible by the process, including sensitive configuration or system files outside the intended sandbox.

**Learning:** When multiple tools share similar side-effect patterns (e.g., reading from the filesystem), security controls must be centralized. Implementing validation individually in each tool is error-prone and leads to security gaps as new tools are added or existing ones are refactored.

**Prevention:** Centralize sensitive validation logic (like path resolution and containment checks) into shared internal helpers (e.g., `_resolve_and_validate_path`). Mandate that any tool accessing the filesystem must use these helpers to ensure a consistent security posture across the entire toolset.

## 2026-07-04 - [Hardening Shell Command Guardrails]

**Vulnerability:** Shell command guardrails for `rm -rf` were too specific, only blocking the exact string `-rf` and standalone `/` or `~` arguments. This allowed bypasses using different flag combinations (e.g., `-r -f`, `-fr`, `--recursive`) or targeting absolute subdirectories (e.g., `/etc`).

**Learning:** String-matching based security checks on CLI commands are fragile. Effective guardrails must parse the command (e.g., using `shlex`) and evaluate the semantic intent (recursive deletion) and the reach of the target (absolute or home-relative paths) across all possible flag variations.

**Prevention:** Use robust flag detection that handles combined, individual, and long-form flags. Validate all positional arguments for sensitive path prefixes rather than matching exact strings.

## 2026-07-06 - [Robust Command Binary Detection in Guardrails]

**Vulnerability:** Destructive command guardrails (like the `rm` check) could be bypassed by using absolute paths to the binary (e.g., `/bin/rm` or `sudo /bin/rm`) because the detection logic only looked for exact string matches on the command name.

**Learning:** When building security guardrails that inspect shell commands, simply checking for a command name is insufficient. Command aliases, absolute paths, and wrappers (like `sudo`) must be considered to prevent trivial bypasses.

**Prevention:** Use matching logic that identifies a binary both by its base name and its path-prefixed forms (e.g., `part == "binary" or part.endswith("/binary")`). Ensure this check is applied even when commands are prefixed by administrative wrappers.

## 2026-07-05 - [Unified Security Enforcement for MCP Tools]

**Vulnerability:** Tool calls in the MCP server bypassed the `GuardrailPolicy` and `redact_secrets` mechanisms used by the main agent loop, leading to inconsistent security enforcement and potential secret leakage during remote tool execution.

**Learning:** Security controls must be enforced at every layer that executes tools. Implementing guardrails only in the primary agent loop leaves other interfaces (like MCP or API endpoints) vulnerable if they share the same tool registry but bypass the orchestration's security logic.

**Prevention:** Ensure all tool execution entry points consistently apply the full security pipeline: pre-execution policy checks, argument validation, exception redaction, and post-execution output filtering. Pass the active `GuardrailPolicy` through all transport layers to maintain a unified security posture.

## 2026-07-07 - [Comprehensive Secret Detection in Guardrails]

**Vulnerability:** The secret detection guardrail only matched underscore-prefixed tokens (`sk_`), allowing Anthropic and OpenAI keys that use hyphens (`sk-`) to bypass the filter and potentially leak in tool outputs.

**Learning:** Secret formats are provider-specific and can vary even within a single provider's ecosystem. A generic regular expression that assumes a single separator (like `_`) is insufficient for a multi-provider agent.

**Prevention:** Use robust, multi-pattern regular expressions that account for various separators (`-`, `_`) and known provider prefixes (e.g., `AIza` for Google, `ghp` for GitHub). Periodically update these patterns as new providers or token formats are integrated.

## 2026-07-05 - [Hardening Destructive Command Guardrails Against Bypass]

**Vulnerability:** Shell command guardrails for `rm -rf` were bypassed if the force flag (`-f`) was omitted, or if path traversal (`..`) was used to target files outside the current directory (e.g., `rm -rf ../../../etc/shadow`).

**Learning:** Destructive command detection must not rely on specific flag combinations (like `-rf`) as recursive deletion alone (`rm -r`) on sensitive targets is equally dangerous. Furthermore, target path validation must account for path traversal sequences (`..`) to prevent escaping the intended sandbox via relative paths.

**Prevention:** Enforce recursive deletion blocks on sensitive targets regardless of the presence of the force flag. Implement robust path inspection that denies any target containing path traversal characters (`..`) when evaluating destructive commands.

## 2026-07-05 - [Path Traversal in Hugging Face Downloads]

**Vulnerability:** The `hf_download` function in `sakthai/hf.py` constructed the local download directory by simply appending the user-provided `repo_id` to the base cache path. This allowed an attacker to use path traversal sequences (e.g., `../../.ssh`) to download files into arbitrary locations accessible by the agent.

**Learning:** Any tool that uses user-provided strings to construct filesystem paths must explicitly validate that the resulting path remains within the intended directory. Simply appending strings is never safe, even if the base path is trusted.

**Prevention:** Always resolve the final target path using `Path.resolve()` and verify that it is still a child of the intended root directory using `path.is_relative_to(root)`.
