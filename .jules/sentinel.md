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
## 2026-07-04 - Restricting File System Access in Document Ingestion
**Vulnerability:** The `ingest_document` tool lacked path validation, allowing it to read and ingest any file on the host that the process had permissions for (e.g., `/etc/hostname`), bypassing the intended directory restrictions enforced by `_allowed_read_roots`.
**Learning:** Security controls must be applied consistently across all tools that perform similar operations (like file I/O). Hardening one tool (`read_file`) but leaving another (`ingest_document`) open creates a gap that can be exploited for path traversal or unauthorized data exposure.
**Prevention:** Centralize security validation logic into reusable helper functions and ensure all relevant entry points use them. In this case, extracting the path resolution and root-containment check into `_resolve_and_validate_path` ensures consistent enforcement.
