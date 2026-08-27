.PHONY: help compose-personas export-agent-repos export-agent-repo test lint mutation \
	dashboard-dev dashboard-test contract-types

help:
	@echo "SakThai Agent v2 - Workspace Operations"
	@echo "======================================"
	@echo "Available commands:"
	@echo "  make compose-personas - Rebuild full skill trees for all personas (shared + overlays)"
	@echo "  make export-agent-repos - Materialize standalone repo snapshots for all six personas"
	@echo "  make export-agent-repo PERSONA=sakjules - Export one standalone persona repo"
	@echo "  make test            - Run all pytest test suites"
	@echo "  make lint            - Run code linters (ruff, pylint)"
	@echo "  make mutation        - Run mutmut on the core seam modules (slow, local-only)"
	@echo "  make contract-types  - Regenerate the dashboard TypeScript types from web/contracts.py"
	@echo "  make dashboard-test  - Lint, build, typecheck and test apps/sak_agent_dashboard"
	@echo "  make dashboard-dev   - Run the web API (:3001) and the dashboard (:3000) together"

# Prevent blast radius by composing and testing all personas
compose-personas:
	@echo "Composing persona skill trees..."
	@mkdir -p build/personas
	@python3 scripts/compose_persona.py sakthai --out build/personas/sakthai
	@python3 scripts/compose_persona.py sakking --out build/personas/sakking
	@python3 scripts/compose_persona.py saksee --out build/personas/saksee
	@python3 scripts/compose_persona.py saksit --out build/personas/saksit
	@python3 scripts/compose_persona.py saktan --out build/personas/saktan
	@python3 scripts/compose_persona.py sakjules --out build/personas/sakjules

export-agent-repo:
	@if [ -z "$$PERSONA" ]; then echo "Usage: make export-agent-repo PERSONA=<sakking|sakthai|saksee|saksit|saktan|sakjules>"; exit 1; fi
	@python3 scripts/export_agent_repo.py "$$PERSONA" --out "build/agent-repos/$$PERSONA"

export-agent-repos:
	@echo "Exporting standalone repo snapshots..."
	@mkdir -p build/agent-repos
	@python3 scripts/export_agent_repo.py sakking --out build/agent-repos/sakking
	@python3 scripts/export_agent_repo.py sakthai --out build/agent-repos/sakthai
	@python3 scripts/export_agent_repo.py saksee --out build/agent-repos/saksee
	@python3 scripts/export_agent_repo.py saksit --out build/agent-repos/saksit
	@python3 scripts/export_agent_repo.py saktan --out build/agent-repos/saktan
	@python3 scripts/export_agent_repo.py sakjules --out build/agent-repos/sakjules

test:
	@echo "Running tests..."
	@if command -v uv >/dev/null 2>&1; then uv run pytest tests/; else pytest tests/; fi

lint:
	@echo "Running linters..."
	@if command -v uv >/dev/null 2>&1; then uv run ruff check .; else ruff check .; fi

# Mutation testing on the core seam modules (see [tool.mutmut] in pyproject.toml).
# A full run is slow and is intentionally NOT part of CI; use it locally to find
# covered-but-unasserted code, then strengthen the responsible test.
#   make mutation        # run, then `uv run mutmut results` to list survivors
mutation:
	@echo "Running mutation testing (mutmut) on core seam modules..."
	@uv run --extra dev --extra mutation mutmut run || true
	@uv run --extra mutation mutmut results

# -- dashboard ---------------------------------------------------------------

DASHBOARD_DIR := apps/sak_agent_dashboard

# web/contracts.py is the single definition of every API payload; the
# dashboard's TypeScript types are generated from it and CI fails if the
# committed file is stale.
contract-types:
	@python3 scripts/gen_dashboard_types.py

# The same sequence .github/workflows/apps.yml runs. Build precedes typecheck
# because next-env.d.ts imports ./.next/types/*.d.ts, which only exists after
# a build.
dashboard-test:
	@cd $(DASHBOARD_DIR) && npm ci && npm run lint && npm run build && npx tsc --noEmit && npm test

# End-to-end locally: the Python API on :3001 and the Next.js app on :3000
# talking to it. Without SAKTHAI_API_URL the dashboard reads ~/.sakthai
# directly instead, which is the default for local development.
#
# Get a token first with `sakthai web setup`.
dashboard-dev:
	@command -v sakthai >/dev/null 2>&1 || { echo "sakthai not on PATH; run 'uv sync --all-extras' first"; exit 1; }
	@echo "Starting the SakThai web API on http://127.0.0.1:3001 ..."
	@SAKTHAI_WEB_CORS_ORIGIN=http://localhost:3000 sakthai web serve --port 3001 & echo $$! > /tmp/sakthai-web.pid
	@sleep 1
	@echo "Starting the dashboard on http://localhost:3000 ..."
	@cd $(DASHBOARD_DIR) && \
		SAKTHAI_API_URL=http://127.0.0.1:3001 \
		SAKTHAI_API_TOKEN="$$(sakthai web setup | awk '/^  Token:/ {print $$2}')" \
		npm run dev; \
		kill "$$(cat /tmp/sakthai-web.pid)" 2>/dev/null || true
