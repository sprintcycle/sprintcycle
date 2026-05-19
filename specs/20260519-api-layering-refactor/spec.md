# Spec: API Layering Refactor for `api.py`

## Summary

`api.py` is currently acting as a large coordination hub that mixes interface concerns, orchestration, business workflows, runtime lifecycle handling, observability, governance, and platform summary assembly. This spec defines a refactor that preserves the public API surface as much as possible while splitting responsibilities into smaller internal modules with clear boundaries.

## Problem Statement

The current `sprintcycle/api.py` file is too large and difficult to reason about. It contains many unrelated methods and directly wires together a broad set of services, which makes maintenance, testing, and future changes risky.

## Goals

- Reduce `api.py` to a thin façade focused on public entrypoints and delegation.
- Separate responsibilities into smaller modules with well-defined interfaces.
- Preserve existing external behavior and public method names as much as practical.
- Improve maintainability and make future changes easier to test and reason about.

## Non-Goals

- Redesigning the public API contract.
- Renaming existing public methods unless required for internal consistency.
- Changing product behavior unrelated to module boundaries.
- Introducing new product capabilities.

## Scope

This work focuses on internal refactoring of the API layer around `api.py`.

Primary split direction:

- Keep `api.py` as the public façade.
- Move orchestration and lifecycle workflow methods into dedicated service modules.
- Move observability, governance, suggestion, evolution, deployment, and platform summary related logic behind narrower interfaces where possible.
- Keep the current outward-facing behavior stable for dashboard, REST API, and SDK consumers.

## Clarifications

### Session 2026-05-19

- Q: What is the primary target architecture? → A: Split `api.py` into `api.py` plus `service` plus `data/access` layers.
- Q: What is the priority of this refactor? → A: Focus on responsibility separation while keeping the external interface stable.

## Proposed Design

### 1. Public façade layer

`api.py` should remain the top-level coordination entrypoint and retain the `SprintCycle` class as the main interface. Its job should be limited to:

- constructing or holding references to internal services
- validating and normalizing request inputs at the boundary
- delegating to lower-level services
- assembling response objects from service outputs

It should not contain large workflow implementations or domain-specific branching logic.

### 2. Service layer

Extract clusters of related behavior into narrower service modules. The exact split should follow existing responsibilities in the current file, for example:

- execution lifecycle operations
- governance orchestration
- suggestion application and review
- observability operations
- lifecycle evolution and promotion logic
- platform summary / dashboard payload assembly
- deployment / launch orchestration
- phase workflow helpers

Each service should have a single responsibility and expose a small, purpose-specific API.

### 3. Data / access layer

Move direct access to storage, registries, repositories, and persistence-related concerns behind dedicated access abstractions where helpful. This includes components such as version registries, knowledge repositories, and state stores.

The API layer should not know storage details beyond the minimal objects needed to call those abstractions.

## Interface Boundaries

- `api.py` owns public entry methods and response shape assembly.
- Services own workflow logic and cross-component orchestration.
- Repositories / registries / stores own persistence access.
- Lower layers should not depend on the public façade.

## Compatibility Rules

- Existing public methods should remain callable with the same or equivalent parameters.
- Return shapes should remain stable unless an internal dependency requires a small compatibility shim.
- Consumers should not need to change imports or call sites for this refactor.

## Acceptance Criteria

- `api.py` is noticeably smaller and contains only façade-level coordination logic.
- Large workflow blocks are moved into dedicated modules.
- The public `SprintCycle` interface continues to work for existing consumers.
- Internal dependencies are organized so responsibilities are easier to test in isolation.
- The refactor does not introduce regressions in existing behavior.

## Validation Strategy

- Run targeted tests for the public `SprintCycle` methods most affected by the refactor.
- Verify that representative entrypoints still return expected payload structures.
- Check that module imports and initialization still work from the dashboard, REST API, and SDK entry paths.

## Risks and Mitigations

- Risk: Over-splitting too early could make the code harder to follow. Mitigation: only create modules that correspond to clear responsibility boundaries already present in the file.
- Risk: Hidden behavior changes in response assembly. Mitigation: preserve current public method signatures and payload shapes.
- Risk: Initialization complexity moves around without improving clarity. Mitigation: keep façade construction straightforward and push logic into services.

## Out of Scope for This Iteration

- Complete redesign of the architecture.
- New domain models or API versions.
- Deep cleanup of unrelated modules.
