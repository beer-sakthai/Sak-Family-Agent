.PHONY: help compose-personas export-agent-repos export-agent-repo test lint mutation

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
