# Data Model: API Layering Refactor

## Module ownership

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Façade | `sprintcycle/api.py` | `SprintCycle` public entrypoints, wiring, thin delegation |
| Service | `application/services/evolution_version_service.py` | Evolution version query and overview |
| Service | `application/services/management_overview_service.py` | Management/suggestion overview aggregation |
| Service | `application/services/web_lifecycle_orchestration_service.py` | Normalize, coerce, web phase orchestration |
| Service | `application/services/lifecycle_contract_assembly_service.py` | Full lifecycle contract assembly |
| Service | `application/services/lifecycle_delivery_service.py` | Runtime/governance/deploy/recovery delivery |
| Service | `application/services/evolution_promotion_service.py` | Versioned promotion + registry persistence |
| Access | `infrastructure/evolution_registry_access.py` | Evolution registry factory |

## Method → owner map (public `SprintCycle`)

| Method cluster | Owner |
|----------------|-------|
| `get_evolution_version`, `list_evolution_versions`, `export_evolution_index`, `evolution_overview*` | `EvolutionVersionService` |
| `suggestion_overview*`, `promotion_readiness`, `management_overview*` | `ManagementOverviewService` |
| `normalize_lifecycle_request`, `orchestrate_web_request`, `run_phase_workflow`, `plan_task`, `prepare_task`, `decompose_task` | `WebLifecycleOrchestrationService` |
| `lifecycle_contract` | `LifecycleContractAssemblyService` |
| `runtime_lifecycle`, `governance_lifecycle`, `deliver_*`, `deploy_lifecycle`, `diagnose_repair_observe`, `lifecycle_recovery_and_promotion` | `LifecycleDeliveryService` |
| `promote_versioned_evolution` | `EvolutionPromotionService` |
| `start_execution_run`, `execution_*`, `runtime_latest`, `runtime_update` | `ExecutionLifecycleService` |
| `observability_*` (trace/replay/events) | `ObservabilityService` |
| `observability_pending/submit/history/summary/show` | `GovernanceOrchestrationService` |
| `review_suggestion`, `approve_suggestion`, … | `SuggestionApplicationService` |
| `platform_overview`, `platform_spec`, `fitness_view`, `deploy_view`, `console_overview` | `PlatformSummaryService` |

## Façade initialization rules

- Construct registries, facades, and stores once in `__init__`.
- Wire services with explicit dependencies; break cycles via post-init assignment (`lifecycle_contract` on delivery).
- Public methods delegate in one line where possible; no workflow branching in `api.py`.

## Compatibility shims

- All public method names and signatures preserved on `SprintCycle`.
- `run_phase_workflow` remains an alias for `orchestrate_web_request`.
- `evaluate_sprint_contract` still returns `EvaluatorAgent` result shape.

## Phase 4 validation

| Check | Result |
|-------|--------|
| `tests/test_api_layering_services.py` | 3 passed |
| `api.py` line count | 595 |
| Full `SprintCycle` smoke | Blocked by pre-existing import chain gaps (`execution.core`, etc.) — see `review-phase4.md` |

Post-init wiring: `LifecycleDeliveryService.lifecycle_contract` assigned to `LifecycleContractAssemblyService.assemble` after both are constructed.
