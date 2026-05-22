# Phase 4 review (T018)

## Façade metrics

| Metric | Value |
|--------|-------|
| `api.py` lines | 595 (was 1085) |
| Public methods on `SprintCycle` | ~59 |
| New service modules | 6 |
| Access module | `infrastructure/evolution_registry_access.py` |

## Residual façade logic (acceptable)

- `console_overview`: aggregates closure scores from state store listing.
- `suggestion_lifecycle_from_event`: shapes suggestion + evolution_refs response.
- `evaluate_promotion`: thin wrapper adding runtime snapshot before delegation.
- `reload_runtime_config`: rewires execution and governance services after config reload.

## Import coupling fixes (validation unblockers)

During smoke/pytest collection, corrected broken imports unrelated to layering but blocking `from sprintcycle.application.http_factories import HTTPServices`:

- `execution/skill_store.py`, `execution/skills.py` — skill model paths
- `governance/runner.py` — HITL facade alias for `create_observability_facade`
- `governance/suggestion/__init__.py` — removed duplicate/broken `SuggestionBridge` import
- `governance/suggestion/{approval,reviewer}.py` — `SuggestionStore` from `.store`
- `governance/suggestion/bridge.py` — new bridge module (package/file name collision)
- `governance/suggestion_analyzer.py`, `governance/suggestion_service.py` — package imports
- `domain/verification/hooks.py` — execution module paths
- `execution/orchestrator.py` → `execution/execution_orchestrator.py` (package shadowing)
- `application/services/*` — `...hooks`, `...observability`, `...execution` relative paths
- `phase_workflow.py` — `build_lifecycle_state_machine` from `lifecycle_contracts`
- `presentation/__init__.py` — lazy `create_app` import
- `domain/platform/overview.py` — langgraph compiler imports
- `presentation/view_service.py` — dataclass `default_factory`
- `api.py` — `execution.core.engine.create_execution_engine`, evolution/memory imports

## Remaining platform import chain

Full `SprintCycle()` import still hits `execution.core` / `execution_core` gaps in some environments. Targeted service tests avoid the full chain:

```bash
.venv/bin/python -m pytest tests/test_api_layering_services.py -q
```

## Boundary leaks

None identified in new services beyond intentional callbacks for circular delivery/assembly wiring (resolved via post-init `lifecycle_contract` assignment on `LifecycleDeliveryService`).
