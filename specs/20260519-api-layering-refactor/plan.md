# Implementation Plan: API Layering Refactor for `api.py`

**Branch**: `20260519-api-layering-refactor` | **Date**: 2026-05-19 | **Spec**: `specs/20260519-api-layering-refactor/spec.md`

**Input**: Feature specification from `specs/20260519-api-layering-refactor/spec.md`

## Summary

Refactor `sprintcycle/api.py` from a monolithic coordination module into a thin public façade backed by smaller internal service and access layers. The work preserves existing public behavior as much as possible while moving orchestration-heavy logic into narrower modules that match the current architecture boundaries.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing SprintCycle application services, facades, registries, stores, orchestrators, and supporting modules already used by `api.py`

**Storage**: Existing runtime-backed persistence abstractions already used by the project; no new persistence technology is required for this refactor

**Testing**: pytest, targeted unit tests for public `SprintCycle` methods, and focused integration tests for module boundaries and preserved payload shapes

**Target Platform**: Backend Python runtime and local developer workflows

**Project Type**: Python backend refactor inside SprintCycle

**Performance Goals**: Reduce cognitive complexity and import coupling in `api.py` while preserving existing runtime characteristics and call behavior

**Constraints**: Preserve the current public interface where practical; keep `SprintCycle` thin; do not move domain rules into the façade; reuse existing services/facades before introducing new abstractions; do not change user-facing behavior unnecessarily

**Scale/Scope**: Focused refactor of one large module plus the smallest set of supporting service/access modules required to restore clear ownership boundaries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- The public API remains a thin coordination layer and does not absorb workflow logic.
- Execution, governance, observability, suggestion, deployment/runtime, and evolution stay separated behind existing or narrower service boundaries.
- The refactor reuses current architecture rather than introducing a competing pipeline.
- Any new helper modules land in the correct layer and do not bypass existing facades or workflows.

## Project Structure

### Documentation (this feature)

```text
specs/20260519-api-layering-refactor/
├── spec.md
├── plan.md
└── (future implementation artifacts if needed)
```

### Source Code (repository root)

```text
sprintcycle/
├── api.py                         # Public façade to thin out
├── application/services/          # Service-layer extractions and workflow helpers
├── infrastructure/                # Access/registry/repository integration boundaries (包含 observability)
├── governance/                    # Governance façade and orchestration boundaries
└── tests/                         # Focused tests for preserved behavior and boundaries
```

**Structure Decision**: Keep `sprintcycle/api.py` as the entry façade, move high-complexity methods into existing or newly added service modules that already match responsibility boundaries, and keep storage/registry access behind access-oriented modules so the façade only normalizes, delegates, and assembles responses.

## Phase 0 - Research

1. Catalog the public `SprintCycle` methods in `api.py` and group them by responsibility so each cluster can be extracted without changing call sites.
2. Identify which responsibilities already have dedicated service/facade modules that can absorb logic with minimal change.
3. Determine which methods are pure delegation versus which ones still contain orchestration, response assembly, or persistence access.
4. Confirm the minimal set of access-layer boundaries needed so `api.py` stops talking directly to storage/registry details.

## Phase 1 - Design

1. Design the thin façade shape for `SprintCycle`, including what initialization and boundary normalization should remain in `api.py`.
2. Design the service split for the largest responsibility clusters, prioritizing modules that already exist or clearly align with current domains.
3. Design the access boundary split for registries, repositories, and stores so persistence details are isolated from the façade.
4. Design compatibility shims for public methods whose internal implementation moves but whose signature and output must remain stable.
5. Design the test matrix that proves the façade remains thin and the public contract remains stable.

## Phase 1 Output Artifacts

- `data-model.md`: Module ownership map, method-to-service mapping, and boundary responsibilities.
- `quickstart.md`: Minimal verification steps for exercising the refactored `SprintCycle` façade.
- `contracts/`: Any explicit boundary contracts needed to keep the refactor testable.

## Phase 1 Constitution Re-check

After design, re-validate that the public API is still thin, that no domain logic migrated upward, and that all new internal helpers respect the existing layered architecture.

## Complexity Tracking

This refactor is moderate in size because `api.py` currently spans many responsibilities, but the scope remains bounded by preserving behavior and moving logic into already-established architectural layers.
