# SprintCycle Web End-to-End Stability Rule / SprintCycle Web 端到端稳定性规则

## Purpose / 目的
The web-triggered lifecycle is a stability contract for SprintCycle.

Current implementation context / 当前实现现状：
- The web path still depends on the existing `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` backbone.
- The HTTP protocol entry now lives in `sprintcycle/interfaces/http/`.
- Dashboard container and dashboard view concerns live in `sprintcycle/presentation/`.
- Stability rules should be read against the current end-to-end chain already present in the codebase.

- For any task initiated from the Web platform, the system must be able to complete the full lifecycle stably.
- This applies equally to self-evolution tasks and user project optimization tasks.
- The core chain should be understood as: request normalization / intent entry → plan and execution preparation → sprint orchestration and decomposition → SprintOrchestrator execution → execution observation and repair → result delivery and summary generation → deployment / runtime coordination → suggestion capture and governance → self-evolution and version evolution.
- `SprintCycle` is the public coordination layer and must remain thin.

## Trigger layers / 触发分层
### Tier 1 — Lifecycle trigger / 生命周期强触发
Apply this rule when changes touch:
- request entry, intent handling, or contract flow
- execution backbone stages such as release planning, sprint orchestration, execution, observation, repair, delivery, deployment/runtime, suggestion handling, or evolution
- state machines, lifecycle contracts, or stage handoffs

### Tier 2 — Continuity trigger / 连续性中触发
Apply this rule when changes touch:
- service/facade/hook/orchestrator logic that supports the lifecycle chain
- route handling, adapter behavior, or public coordination APIs
- configs, dependencies, or tests that may affect continuity across stages

### Tier 3 — Review trigger / 复核级弱触发
Apply a lightweight review when changes touch:
- docs, comments, examples, or naming around lifecycle behavior
- non-structural edits that may still affect the clarity of the end-to-end chain

## Web end-to-end stability guarantee / Web 端到端稳定性保障
- For any task initiated from the Web platform, the system must be able to complete the full lifecycle stably.
- This applies equally to self-evolution tasks and user project optimization tasks.
- Based on the current implementation, the core chain should be understood as: request normalization / intent entry → plan and execution preparation → sprint orchestration and decomposition → SprintOrchestrator execution → execution observation and repair → result delivery and summary generation → deployment / runtime coordination → suggestion capture and governance → self-evolution and version evolution.
- `SprintCycle` is the public coordination layer and must remain thin.
- The execution backbone centers on `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor`.
- LangGraph currently serves as the orchestration skeleton for `intent → plan → sprint decomposition → sprint execution → observe → repair`.
- `interfaces/http/` now owns HTTP public/internal route adaptation, while `presentation/` owns dashboard-specific views and container responsibilities.
- Suggestions, governance, observability, and evolution are coordinated capabilities around the execution backbone and must be integrated through existing services, facades, hooks, registries, and orchestrators.
- Any implementation change must preserve the continuity of this chain and must not weaken the ability to progress stably from one stage to the next.

## Implementation guidance / 实现指引
- Treat the web-triggered lifecycle as a stability contract, not as a loose aspiration.
- Do not remove or bypass any stage that is needed to keep the chain continuous.
- If a feature improves only one stage, ensure upstream and downstream handoffs still work.
- If a stage already exists in service or facade form, extend it rather than adding a parallel flow.
- Keep the lifecycle end-to-end complete: changes must preserve the chain from request entry through execution, repair, delivery, deployment/runtime, suggestion handling, and self-evolution.
- Any repository change that may affect lifecycle continuity, layer boundaries, routing, execution, or state flow should trigger this rule.
