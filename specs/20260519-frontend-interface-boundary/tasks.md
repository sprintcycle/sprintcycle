# Tasks: Frontend / Interface Boundary Separation

## 1. Frontend extraction
- [ ] Move dashboard UI rendering and page composition out of `sprintcycle/presentation` into `frontend`.
- [ ] Relocate view components, layouts, and page-level state management into the frontend app structure.
- [ ] Ensure frontend routes own user navigation and interaction flow.
- [ ] Update frontend API consumption to call backend HTTP endpoints only.

## 2. HTTP interface cleanup
- [ ] Keep all REST handlers in `sprintcycle/interfaces/http`.
- [ ] Verify request/response DTO handling remains in the HTTP boundary.
- [ ] Confirm auth, rate limiting, and audit logic stay in HTTP interface modules.
- [ ] Remove any UI rendering or presentation assembly from HTTP handlers.

## 3. Backend presentation deconstruction
- [ ] Classify each `sprintcycle/presentation` file as frontend-movable, HTTP-adjacent, or temporary shim.
- [ ] Move frontend-owned files into `frontend`.
- [ ] Retain only temporary compatibility shims where required for startup/import stability.
- [ ] Delete obsolete backend presentation modules once no longer referenced.

## 4. Compatibility and validation
- [ ] Keep public and internal API behavior stable throughout migration.
- [ ] Update imports and startup paths so the backend and frontend continue to launch cleanly.
- [ ] Add or update tests covering backend endpoint behavior and frontend integration.
- [ ] Run lint, type, and build validation for both frontend and backend surfaces.
