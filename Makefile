# SprintCycle — common local workflows (see also docs/QUICKSTART.md)

.PHONY: install install-frontend build-frontend build test lint-frontend lint export-openapi e2e dev \
	ci-local ci-local-quick ci-smoke arch-gate ci-fix-loop-start ci-fix-loop-stop

install:
	python -m pip install -e ".[dev,dashboard]"
	$(MAKE) install-frontend

install-frontend:
	cd frontend && npm ci

build-frontend:
	cd frontend && npm ci && npm run openapi:sync && npm run build

build: build-frontend
	@echo "Frontend built into sprintcycle/dashboard/static/"

test:
	python -m pytest tests/ -q --tb=short

lint-frontend:
	cd frontend && npm ci && npm run lint

export-openapi:
	python scripts/export_dashboard_openapi.py

e2e: build-frontend
	cd frontend && npx playwright install chromium && npm run test:e2e

dev:
	@echo "Run from your project directory, e.g.: SPRINTCYCLE_ENV=development sprintcycle dashboard --dev"

# --- CI mirror (see docs/CURSOR_PRODUCTION_FIX_WORKFLOW.md) ---
arch-gate:
	@CI_LOCAL_PHASE=arch bash scripts/ci-local.sh

ci-smoke:
	@bash scripts/import-smoke.sh

ci-local-quick:
	@CI_LOCAL_SKIP_E2E=1 bash scripts/ci-local.sh

ci-local:
	@bash scripts/ci-local.sh

ci-fix-loop-start:
	@mkdir -p .cursor && touch .cursor/.ci-fix-loop-active && rm -f .cursor/.ci-fix-loop-iterations && echo "ci-fix-loop enabled (Hooks will auto-continue on stop)"

ci-fix-loop-stop:
	@rm -f .cursor/.ci-fix-loop-active .cursor/.ci-fix-loop-iterations && echo "ci-fix-loop disabled"
