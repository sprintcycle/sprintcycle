# SprintCycle Package Layout

This document records the current top-level package layout and the intended responsibility boundaries.

## 1. Top-level layout

- `sprintcycle/` — Python package for the core product
- `frontend/` — Web dashboard frontend
- `tests/` — Automated tests
- `docs/` — Architecture and product documentation
- `examples/` — Example configurations and plugins
- `scripts/` — Small utility scripts
- `tools/` — Developer workflows and local environment tooling
- `.github/` — CI and repository automation

## 2. Core Python package responsibilities

### `sprintcycle/governance/`
Governance domain entry point.

Responsibilities:

- governance facade
- HITL policy, gate, decision, correction, replay flows
- suggestion review and approval flows
- architecture and rule guards
- governance reporting and checks

Key subpackages:

- `hitl/` — governance-side human-in-the-loop implementation
- `suggestion/` — suggestion review and approval
- `arch_guard/` — architecture and rule enforcement

### `sprintcycle/runtime_observability/`
Runtime observability and replay views.

Responsibilities:

- execution facts recording
- runtime trace projections
- replay projections
- read-only observability views for execution-time events

This package does not own governance decisions or HITL gating.

### `sprintcycle/execution/`
Execution engine and runtime orchestration.

Responsibilities:

- planners and plan expansion
- orchestrator and execution state
- execution hooks and agents
- knowledge injection and checkpoints
- rollback and error handling

### `sprintcycle/evolution/`
Evolution and iteration workflow.

Responsibilities:

- evolution loops
- rollback orchestration
- measurement and decision support

### `sprintcycle/support/`
Support libraries used by multiple domains.

Responsibilities:

- intent parsing and runner support
- quality spec and verification helpers
- versioning and persistence adapters
- diagnostic utilities

### `sprintcycle/infrastructure/`
Infrastructure adapters.

Responsibilities:

- configuration
- logging
- cache
- message queue
- sandbox
- persistence
- LLM provider integration

### `sprintcycle/dashboard/`
Dashboard backend and runtime APIs.

### `sprintcycle/entrypoints/`
CLI and MCP entrypoints.

## 3. Current naming rules

- Use `governance` for governance domain APIs and policy logic.
- Use `hitl` for governance-side human-in-the-loop flows.
- Use `runtime_observability` for runtime execution facts, trace, and replay.
- Do not reintroduce governance-specific observability code under the runtime observability package.
- Keep package names aligned with their responsibility boundaries.

## 4. Public API guidance

Prefer the following top-level entrypoints:

- `sprintcycle.GovernanceFacade`
- `sprintcycle.governance.create_governance_facade`
- `sprintcycle.governance.create_hitl_facade`
- `sprintcycle.runtime_observability.RuntimeObservabilityFacade`

For lower-level work, import from the specific domain package rather than from the top-level package when possible.
