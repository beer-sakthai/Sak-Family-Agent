.PHONY: help deploy-hermes doctor-hermes compose-personas test lint

help:
	@echo "SakThai Agent v2 - Monorepo Operations"
	@echo "======================================"
	@echo "Available commands:"
	@echo "  make deploy-hermes   - Deploy Hermes agent configs to live ~/.hermes/ environment"
	@echo "  make doctor-hermes   - Run diagnostics on the Hermes agent configurations"
	@echo "  make compose-personas- Rebuild full skill trees for all personas (shared + overlays)"
	@echo "  make test            - Run all pytest test suites"
	@echo "  make lint            - Run code linters (ruff, pylint)"

# Mitigate complexity by providing a shortcut from the root to the deployment scripts
deploy-hermes: compose-personas
	@echo "Deploying Hermes agent configs..."
	@cd infra/hermes-agents && ./deploy.py

doctor-hermes:
	@echo "Running Hermes configuration doctor..."
	@cd infra/hermes-agents && python3 doctor.py

# Prevent blast radius by composing and testing all personas
compose-personas:
	@echo "Composing persona skill trees..."
	@python3 scripts/compose_persona.py --all

test:
	@echo "Running tests..."
	@pytest tests/

lint:
	@echo "Running linters..."
	@ruff check .
