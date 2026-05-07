# SprintCycle — common local workflows (see also docs/QUICKSTART.md)

.PHONY: install install-frontend build-frontend build test lint-frontend lint export-openapi e2e dev

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
