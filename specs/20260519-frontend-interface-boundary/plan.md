# Implementation Plan: Frontend / Interface Boundary Separation

**Branch**: `20260519-frontend-interface-boundary` | **Date**: 2026-05-19 | **Spec**: `specs/20260519-frontend-interface-boundary/spec.md`

**Input**: Feature specification from `specs/20260519-frontend-interface-boundary/spec.md`

## Summary

Restructure the repository so the dashboard UI lives in the dedicated `frontend` application, `interfaces/http` owns all HTTP protocol concerns, and backend `application` / `domain` / `infrastructure` layers remain unchanged. The migration should preserve API behavior while removing presentation responsibilities from backend modules.

## Technical Context

**Language/Version**: Python 3.11+ backend, existing frontend stack already in repository

**Primary Dependencies**: Existing SprintCycle application services, current FastAPI HTTP routes, current frontend application, audit/rate-limit infrastructure, and existing presentation modules being migrated

**Storage**: No new persistence layer; existing backend storage, config, and audit mechanisms remain in infrastructure

**Testing**: pytest for backend, frontend build/test workflows as already configured, plus focused route and UI integration checks

**Target Platform**: Local development and existing backend/frontend deployment workflows

**Project Type**: Full-stack repository with separated frontend and backend responsibilities

**Performance Goals**: Reduce architectural coupling, improve boundary clarity, and preserve observable API behavior during migration

**Constraints**: Do not move business rules into frontend; do not put route handling or request parsing into frontend; keep `interfaces/http` as the backend API boundary; preserve current public/internal endpoint behavior where practical; use compatibility shims only as a transition aid

**Scale/Scope**: Moderate refactor spanning frontend extraction, HTTP boundary cleanup, and removal or isolation of backend presentation code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Frontend owns visual output, routing, state, interactions, and API consumption.
- Interfaces own HTTP protocol handling, DTOs, auth, rate limiting, and audit.
- Application/domain/infrastructure responsibilities stay where they are.
- Temporary compatibility shims are allowed only during migration and must not become a new architectural layer.

## Project Structure

### Documentation (this feature)

```text
specs/20260519-frontend-interface-boundary/
├── spec.md
├── plan.md
├── data-model.md
├── quickstart.md
└── contracts/
```

### Source Code (repository root)

```text
frontend/
├── src/
├── public/
├── router/
├── stores/
└── views/

sprintcycle/
├── interfaces/
│   └── http/
├── application/
├── domain/
└── infrastructure/

sprintcycle/presentation/
└── (temporary compatibility only, then removed)
```

**Structure Decision**: Move dashboard rendering and UI orchestration into `frontend`, keep API handlers and protocol adaptation in `sprintcycle/interfaces/http`, and leave backend core layers unchanged. Any backend `presentation` code becomes either a temporary shim or is deleted after migration.

## Phase 0 - Research

1. Catalog all current backend `presentation` modules and classify them as UI rendering, view model assembly, SSE/live-update support, or protocol-adjacent code.
2. Identify the current frontend entrypoints, route structure, stores, and API client usage that can absorb the migrated UI responsibilities.
3. Identify which backend routes in `interfaces/http` already expose dashboard data and which ones need DTO or adapter cleanup only.
4. Determine the minimal compatibility shims needed so existing imports or startup flows continue to work during migration.

## Phase 1 - Design

1. Design the target `frontend` organization so routing, stores, and views own all user-facing UI flows.
2. Design the HTTP boundary shape so FastAPI handlers, DTOs, auth, rate limiting, and audit remain in `interfaces/http`.
3. Design the migration path for presentation modules, including which files move to frontend, which files are deleted, and which files remain as short-lived shims.
4. Design compatibility rules for endpoint behavior, frontend API calls, and startup entrypoints.
5. Design the test matrix for backend route behavior, frontend build/runtime validation, and boundary regression checks.

## Phase 1 Output Artifacts

- `data-model.md`: Directory ownership map, file classification, and boundary responsibilities.
- `quickstart.md`: Minimal steps to validate the separated frontend and HTTP layers.
- `contracts/`: Explicit boundary contracts for frontend API consumption and HTTP interface responsibilities.

## Phase 1 Constitution Re-check

After design, re-validate that UI concerns live only in `frontend`, protocol concerns live only in `interfaces/http`, and backend core layers remain unchanged.

## Complexity Tracking

This refactor is moderate because it spans both frontend and backend boundaries, but the scope is bounded by a strict responsibility split and by preserving existing application logic.