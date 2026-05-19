# Tasks: API Layering Refactor for `api.py`

**Input**: Design documents from `/specs/20260519-api-layering-refactor/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification, so test tasks are omitted unless needed for validation during implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the refactor workspace and document the intended module boundaries.

- [x] T001 Review `sprintcycle/api.py` public methods and record the responsibility clusters in `specs/20260519-api-layering-refactor/data-model.md`
- [x] T002 [P] Create `specs/20260519-api-layering-refactor/contracts/` and add boundary contract notes for façade, service, and access layers
- [x] T003 [P] Add a concise verification checklist to `specs/20260519-api-layering-refactor/quickstart.md` for exercising the refactored `SprintCycle` façade

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared boundary map and extraction targets that all refactor work depends on.

- [x] T004 Extract the full `SprintCycle` method inventory and map each method to façade, service, or access ownership in `specs/20260519-api-layering-refactor/data-model.md`
- [x] T005 Define the thin façade initialization and delegation rules for `SprintCycle` in `specs/20260519-api-layering-refactor/data-model.md`
- [x] T006 Define the access-layer boundary responsibilities for registries, repositories, and stores in `specs/20260519-api-layering-refactor/data-model.md`
- [x] T007 Identify the compatibility shims required to preserve existing public method signatures and payload shapes in `specs/20260519-api-layering-refactor/data-model.md`

**Checkpoint**: Boundary map is ready, and implementation can proceed without guessing ownership.

---

## Phase 3: User Story 1 - Thin `SprintCycle` façade with layered delegation (Priority: P1) 🎯 MVP

**Goal**: Refactor `sprintcycle/api.py` into a thin public façade that delegates workflow logic to service modules and isolates persistence access behind narrower boundaries while keeping the public interface stable.

**Independent Test**: Instantiate `SprintCycle` and exercise representative public methods from the refactored façade; confirm the same call sites still work and the returned payload shapes remain stable.

### Implementation for User Story 1

- [x] T008 [P] [US1] Extract orchestration-heavy lifecycle logic from `sprintcycle/api.py` into `sprintcycle/application/services/`
- [x] T009 [P] [US1] Extract governance, observability, suggestion, deployment/runtime, and evolution workflows from `sprintcycle/api.py` into purpose-specific service modules under `sprintcycle/application/services/`
- [x] T010 [P] [US1] Move direct storage, registry, repository, and store access behind access-oriented modules under `sprintcycle/infrastructure/`
- [x] T011 [US1] Reduce `sprintcycle/api.py` to boundary normalization, service wiring, and response assembly only
- [x] T012 [US1] Wire the new service and access modules into `SprintCycle` initialization and method delegation in `sprintcycle/api.py`
- [x] T013 [US1] Preserve compatibility shims for any public methods whose internal implementation moved but whose signature or return shape must stay stable in `sprintcycle/api.py`
- [x] T014 [US1] Update imports and module references so the new layer boundaries are the only path used by `sprintcycle/api.py`

**Checkpoint**: `SprintCycle` remains callable from existing consumers, but the workflow logic now lives behind clearer service and access boundaries.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation alignment, and validation of the refactor boundaries.

- [x] T015 [P] Update `specs/20260519-api-layering-refactor/quickstart.md` with final verification steps for the refactored `SprintCycle` façade
- [x] T016 [P] Update `specs/20260519-api-layering-refactor/data-model.md` and `specs/20260519-api-layering-refactor/contracts/` to reflect the final module ownership map
- [x] T017 Run the targeted pytest subset covering `sprintcycle/api.py` entrypoints and any refactored service boundaries
- [x] T018 Review `sprintcycle/api.py` and the new service/access modules for residual orchestration logic, import coupling, or boundary leaks

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user story work.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **Polish (Phase 4)**: Depends on User Story 1 completion.

### User Story Dependencies

- **User Story 1 (P1)**: The refactor’s core delivery; no dependency on other stories.

### Within the User Story

- Boundary mapping and compatibility requirements must be defined before extraction work lands.
- Service extraction should happen before façade slimming and final delegation wiring.
- Access-layer extraction should be in place before removing direct storage or registry access from `api.py`.
- Compatibility shims must be preserved while implementation moves underneath them.

### Parallel Opportunities

- Setup tasks `T002` and `T003` can run in parallel.
- User Story 1 extraction tasks `T008`, `T009`, and `T010` can run in parallel because they target different modules and boundaries.
- Polish tasks `T015` and `T016` can run in parallel.

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup.
2. Complete Phase 2 boundary mapping.
3. Deliver Phase 3 User Story 1.
4. Verify the façade still works for existing consumers.

### Incremental Delivery

1. Establish the boundary map and ownership rules.
2. Extract the largest workflow clusters into services.
3. Move persistence access into infrastructure boundaries.
4. Thin `sprintcycle/api.py` down to delegation and response assembly.
5. Validate the refactor with targeted pytest coverage and final cleanup.
