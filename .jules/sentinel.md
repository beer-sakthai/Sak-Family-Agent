# Sentinel Security Journal

## 2026-07-01 - Redacting Secrets in Tool Error Handlers
**Vulnerability:** Raw `TELEGRAM_BOT_TOKEN` was included in the exception string returned to the LLM when an `Unexpected Error` occurred during message sending.
**Learning:** Generic `except Exception as exc` handlers that return `str(exc)` can inadvertently leak sensitive configuration data (like API tokens in URLs or credentials in object representations) to the model.
**Prevention:** Always redact sensitive tokens or use specific, safe error messages in tool return strings. Use `re.sub` or structured error objects instead of raw exception stringification for external API calls.
