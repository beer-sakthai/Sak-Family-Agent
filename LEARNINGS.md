# Learnings from OpenAI Provider Refactor

- Refactoring large functions like `call_openai_compat` into smaller helpers (`_prepare_payload`, `_get_request_executor`, `_parse_response`) significantly improves readability.
- When refactoring stream processing in Python, avoid bare `try/except: continue` blocks as they trigger Bandit's B112 security check. Instead, explicitly set the failed variable to `None` and check its type before continuing.
- Using `uv sync --extra dev` is necessary to ensure dev tools like `bandit` and `ruff` are available in the environment.
