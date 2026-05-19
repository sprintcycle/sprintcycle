# Feature Specification: Frontend / Interface Boundary Separation

**Feature Branch**: `20260519-frontend-interface-boundary`  
**Created**: 2026-05-19  
**Status**: Draft  
**Input**: User description: "真正的前后端分离，把职责重新切成三层。frontend 负责视觉输出、页面组件、路由、状态管理、交互逻辑、调用后端 API；interfaces 负责 HTTP / API 协议边界、internal/public REST API、request/response DTO、auth / rate limit / audit、对 application 层的适配；application / domain / infrastructure 保持原有分层不变。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Frontend owns visual experience (Priority: P1)

As a user of SprintCycle, I can use a dedicated `frontend` application for dashboard rendering, routing, state management, and interaction logic without depending on backend presentation modules.

**Why this priority**: Removing presentation responsibilities from the backend is the primary architectural goal and the clearest user-facing boundary.

**Independent Test**: The dashboard can be started and exercised from the `frontend` app while backend API modules provide only data and protocol handling.

**Acceptance Scenarios**:

1. **Given** dashboard UI functionality currently living in backend presentation code, **When** the migration is complete, **Then** the same visual flows are served from `frontend`.
2. **Given** a user refreshes or navigates within the dashboard, **When** routing/state updates occur, **Then** the behavior is handled by `frontend` rather than backend presentation logic.

---

### User Story 2 - Interfaces own HTTP and protocol concerns (Priority: P1)

As a client of SprintCycle APIs, I can call public and internal REST endpoints through `interfaces/http` and receive stable request/response behavior, including rate limiting and audit handling.

**Why this priority**: The HTTP boundary is the stable contract that must remain intact while presentation logic is moved out.

**Independent Test**: Existing API endpoints continue to respond through `interfaces/http` while dashboard rendering code is removed from those handlers.

**Acceptance Scenarios**:

1. **Given** an API request to a public endpoint, **When** it is processed, **Then** the handler lives in `interfaces/http` and delegates to application services.
2. **Given** an internal dashboard data request, **When** it is processed, **Then** auth/rate-limit/audit and DTO mapping are handled in `interfaces/http`.

---

### User Story 3 - Backend layering stays stable (Priority: P2)

As a maintainer, I can keep `application`, `domain`, and `infrastructure` responsibilities unchanged while the UI and protocol boundaries are separated.

**Why this priority**: The migration should reduce coupling without forcing a redesign of the core backend layers.

**Independent Test**: Core services continue to run with the same business behavior after the presentation code is moved.

**Acceptance Scenarios**:

1. **Given** an existing application service, **When** the frontend or HTTP interfaces call it, **Then** the service contract remains unchanged.
2. **Given** persistence, audit, or config helpers, **When** the refactor is complete, **Then** they remain in infrastructure and are not moved into frontend or HTTP adapters.

---

## Edge Cases

- What happens when a dashboard route still points to backend presentation code during migration?
- How does the system preserve compatibility for existing API consumers while frontend is being extracted?
- What happens if SSE or live-update behavior currently spans both presentation and HTTP boundaries?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a dedicated `frontend` application for dashboard/UI rendering, routing, local state, interactions, and API consumption.
- **FR-002**: The system MUST keep HTTP protocol handling in `interfaces/http`.
- **FR-003**: The system MUST keep request/response DTO mapping, auth, rate limiting, and audit behavior in `interfaces/http`.
- **FR-004**: The system MUST preserve `application`, `domain`, and `infrastructure` responsibilities without moving backend business rules upward.
- **FR-005**: The migration MUST remove dashboard presentation concerns from backend `presentation` modules.
- **FR-006**: The system MUST preserve existing public and internal API behavior while presentation code is being migrated.
- **FR-007**: The system MUST route frontend API calls through the existing HTTP interface layer instead of direct backend implementation imports.
- **FR-008**: Any compatibility shims that remain during migration MUST be temporary and clearly isolated.

### Key Entities *(include if feature involves data)*

- **Frontend App**: The user-facing dashboard application responsible for rendering, routing, and interactive state.
- **HTTP Interface**: The backend boundary that exposes REST endpoints and adapts external requests into application calls.
- **Presentation Module**: Legacy backend UI/view orchestration code slated for migration or removal.
- **Application Service**: Business-use-case service consumed by HTTP interfaces and, indirectly, by frontend through APIs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All dashboard UI rendering code is moved out of backend `presentation` and into `frontend`.
- **SC-002**: All REST endpoint handlers remain available through `interfaces/http` with unchanged observable API behavior.
- **SC-003**: Backend `presentation` no longer owns route handling, request parsing, or UI rendering responsibilities.
- **SC-004**: Core backend services continue to pass existing tests after the migration.
- **SC-005**: A new contributor can identify frontend vs HTTP vs backend responsibilities from the directory structure without reading implementation files.

## Assumptions

- The repository already contains an established `frontend` project that can absorb the dashboard UI concerns.
- Existing HTTP API contracts should remain stable during this migration.
- The migration can use temporary shims where needed to preserve compatibility while files move.
- No redesign of business logic, persistence models, or domain rules is required for this feature.
