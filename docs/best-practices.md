# Engineering Best Practices & Architecture Standards

> **House of Sak · Operational Excellence Guidelines**  
> Canonical guide for developing agents, tools, pipelines, and web interfaces across the `Sak-Family-Agent` ecosystem.

---

## 1. Core Principles

1. **One Source of Truth**: Never duplicate configuration, schemas, or documentation. Reference canonical definitions in `config.py`, `SOUL.md`, or master plans.
2. **Local-First & Cost Conscious**: Favor local models (`sakthai`), hermetic environments, and cached data over recurring cloud/API spend.
3. **Plan First, Verify Always**: Never execute substantial changes without an in-progress marker in `PLAN.md` and automated test verification.
4. **Defense-in-Depth**: Treat every input (agent prompt, CLI flag, HTTP query, git URL, MCP payload) as untrusted.

---

## 2. Agent Engineering Standards

### A. Persona Isolation & Boundaries
- Each persona (`personas/<name>/`) maintains its own distinct domain, tone, and operational focus.
- Every automated agent reply or PR must begin with the persona header (e.g., `**SakJules · Master of Automation & CI/CD.**`).
- Persona memory operations must store facts with structured tags (e.g., `[persona, system, no-export]`).

### B. Deterministic Tool Execution
- Tool signatures must use Python type hints and descriptive docstrings; schemas are derived directly from AST/signatures without ad-hoc JSON declarations.
- Tool handlers must be pure or state-isolated functions with complete error trapping.
- Avoid network access inside unit tests; pass `--no-mcp` or mock external endpoints.

---

## 3. Security & Guardrails

### A. Path Traversal & File Protection
- All path validations must use `os.path.realpath` canonicalization and verify directory containment:
  ```python
  root = os.path.realpath(str(ALLOWED_ROOT))
  candidate = os.path.realpath(os.path.join(root, user_path))
  if not candidate.startswith(root + os.sep) and candidate != root:
      raise PermissionError("Access denied: path traversal detected")
  ```
- Block sensitive paths (`.ssh/`, `.aws/`, `.gnupg/`, `.env*`, `memory.db*`, critical system roots).

### B. Secret Handling & Redaction
- All bearer tokens, API keys, and sensitive tokens must be registered via `config.register_secret(token)` immediately upon instantiation.
- JSON endpoints and CLI outputs must run payloads through `config.redact_secrets()`.
- HTTP Set-Cookie headers must echo only the server-known token, never unvalidated user input.

---

## 4. CI/CD & Automation Standards

### A. Preflight Quality Gates
Every contribution must pass the five standard gates locally before opening a PR:
```bash
# 1. Lint & Format
uv run ruff check . && uv run ruff format --check .

# 2. Strict Typecheck
uv run mypy personas/sakthai/sakthai

# 3. Security Analysis
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai

# 4. Test Suite & Coverage Floor
uv run pytest tests/ --cov=personas/sakthai/sakthai --cov-fail-under=97

# 5. Frontend Checks (when touching web/dashboard)
pnpm --prefix apps/sak_agent_dashboard typecheck
pnpm --prefix apps/sak_agent_dashboard test
```

### B. Zero-Duplicate PR Policy
- Always run `git fetch origin` and `gh pr list` before creating branches or submitting changes.
- If an overlapping open PR exists, extend that branch rather than creating a duplicate.

---

## 5. Web & Routing Architecture

### A. Dynamic Route Handlers
- Dynamic Next.js documentation routes (`/docs/:page`) must implement static pre-rendering via `generateStaticParams` and provide fallback handling for non-existent slugs.
- Web API endpoints must enforce Bearer token authentication and loopback binding defaults (`127.0.0.1`).
