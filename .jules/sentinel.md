# Sentinel Security Journal

## 2026-07-01 - Redacting Secrets in Tool Error Handlers
**Vulnerability:** Raw `TELEGRAM_BOT_TOKEN` was included in the exception string returned to the LLM when an `Unexpected Error` occurred during message sending.
**Learning:** Generic `except Exception as exc` handlers that return `str(exc)` can inadvertently leak sensitive configuration data (like API tokens in URLs or credentials in object representations) to the model.
**Prevention:** Always redact sensitive tokens or use specific, safe error messages in tool return strings. Use `re.sub` or structured error objects instead of raw exception stringification for external API calls.

## 2026-07-02 - Global Secret Redaction Fail-safe
**Vulnerability:** Multi-provider API keys and Telegram tokens could still leak via raw exception strings in tool handlers if not manually redacted in every single tool.
**Learning:** While individual tool hardening (like in the Telegram tool) is good, a global fail-safe in the agent's tool execution loop (`_execute_tool`) provides defense-in-depth against future tools or forgotten handlers.
**Prevention:** Implement a centralized `redact_secrets` utility that knows about all sensitive environment variables and apply it to all stringified exceptions returned from the tool layer to the LLM.
