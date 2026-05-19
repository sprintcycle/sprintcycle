# Service boundary contracts

## WebLifecycleOrchestrationService

- Owns: `normalize_lifecycle_request`, `coerce_execution_contract`, `orchestrate_web_request`, `plan_task`, `prepare_task`, `decompose_task`.
- Must not: start executions without injected `start_execution_run` callback.
- Returns: dict payloads with `lifecycle_contract` and phase artifacts.

## LifecycleContractAssemblyService

- Owns: `assemble(execution_id)` full contract aggregation.
- Must not: mutate governance or suggestion stores directly.
- Delegates: runtime/governance/delivery via injected callables.

## LifecycleDeliveryService

- Owns: `runtime_lifecycle`, `governance_lifecycle`, `deliver_runtime_governance_promotion`, `deploy_lifecycle`, recovery bundles.
- Must not: build lifecycle contracts without `lifecycle_contract` injection.

## EvolutionVersionService / EvolutionPromotionService

- Owns: version registry reads and versioned promotion persistence.
- Access: `infrastructure/evolution_registry_access.create_evolution_registry` only.

## SprintCycle façade

- One-line delegation to services for all extracted clusters.
- Allowed local logic: `console_overview` closure aggregation, `reload_runtime_config` rewiring, `suggestion_lifecycle_from_event` response shaping (< 20 lines each).
