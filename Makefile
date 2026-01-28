# Makefile - Sarvaja Platform DevOps
# Per TEST-006: DevOps Test Strategy
# Per WORKFLOW-SHELL-01-v1: Shell wrapper pattern

PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
VENV := .venv

# =============================================================================
# SETUP
# =============================================================================

.PHONY: setup
setup: ## Initial project setup
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pip install -r requirements-test.txt

# =============================================================================
# TEST TARGETS - Per TEST-006 DevOps Strategy
# =============================================================================

.PHONY: test
test: ## Run all unit tests (excluding e2e/integration)
	$(PYTEST) tests/ -v --ignore=tests/e2e --ignore=tests/integration

.PHONY: test-smoke
test-smoke: ## Smoke tests - fast sanity check (<30s)
	$(PYTEST) tests/unit/ -v -x --tb=short -m "smoke or not slow" --timeout=30

.PHONY: test-unit
test-unit: ## Unit tests only
	$(PYTEST) tests/unit/ -v --tb=short --junitxml=results/unit-tests.xml

.PHONY: test-fast
test-fast: ## Fast tests for pre-commit (<30s)
	$(PYTEST) tests/unit/ -v -q --tb=line --timeout=30 -x

.PHONY: test-functional
test-functional: ## Functional tests for PR merge (<5min)
	$(PYTEST) tests/ -v --ignore=tests/e2e --tb=short --timeout=300 \
		--junitxml=results/functional-tests.xml

.PHONY: test-full
test-full: ## Full test suite for release (<30min)
	$(PYTEST) tests/ -v --tb=short --timeout=1800 \
		--junitxml=results/full-tests.xml

.PHONY: test-e2e
test-e2e: ## E2E tests with Robot Framework
	./scripts/robot.sh -t smoke

.PHONY: test-e2e-api
test-e2e-api: ## API E2E tests only
	./scripts/robot.sh -t api

.PHONY: test-ui
test-ui: ## UI component tests
	$(PYTEST) tests/unit/ui/ -v --tb=short

.PHONY: test-governance
test-governance: ## Governance/TypeDB tests
	$(PYTEST) tests/test_governance*.py tests/test_typedb*.py -v --tb=short

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	$(PYTEST) tests/ --ignore=tests/e2e --cov=governance --cov=agent \
		--cov-report=html:results/coverage --cov-report=term-missing

# =============================================================================
# LINT & TYPE CHECK
# =============================================================================

.PHONY: lint
lint: ## Run linter (ruff)
	$(PYTHON) -m ruff check . --ignore E501,F401

.PHONY: lint-fix
lint-fix: ## Fix lint issues automatically
	$(PYTHON) -m ruff check . --fix --ignore E501,F401

.PHONY: typecheck
typecheck: ## Run type checker (pyright)
	$(PYTHON) -m pyright governance/ agent/

# =============================================================================
# CI SIMULATION
# =============================================================================

.PHONY: ci-precommit
ci-precommit: lint test-fast ## Pre-commit checks (lint + fast tests)
	@echo "Pre-commit checks passed!"

.PHONY: ci-pr
ci-pr: lint typecheck test-functional ## PR merge checks (lint + types + functional)
	@echo "PR checks passed!"

.PHONY: ci-release
ci-release: lint typecheck test-full test-coverage ## Release checks (full suite)
	@echo "Release checks passed!"

# =============================================================================
# DOCKER/PODMAN
# =============================================================================

.PHONY: up
up: ## Start all services
	podman compose --profile cpu up -d

.PHONY: down
down: ## Stop all services
	podman compose --profile cpu down

.PHONY: ps
ps: ## Show running containers
	podman compose --profile cpu ps

.PHONY: logs
logs: ## Show container logs
	podman compose --profile cpu logs -f

# =============================================================================
# DEVELOPMENT
# =============================================================================

.PHONY: dashboard
dashboard: ## Start dashboard (dev mode)
	$(PYTHON) -m governance.dashboard

.PHONY: mcp
mcp: ## Start MCP servers
	$(PYTHON) -m governance.mcp_server

.PHONY: clean
clean: ## Clean build artifacts
	rm -rf results/ .pytest_cache/ __pycache__/ *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Sarvaja Platform - DevOps Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
