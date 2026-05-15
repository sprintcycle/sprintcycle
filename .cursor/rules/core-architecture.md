# SprintCycle Core Architecture Rule / SprintCycle 核心架构规则

## Purpose / 目的
You are working on SprintCycle, a layered orchestration system with a stable core architecture.

Current implementation context / 当前实现现状：
- The repository is centered on the `sprintcycle` core package.
- The HTTP protocol layer now lives under `sprintcycle/interfaces/http/`.
- The dashboard/container and view/projection concerns live under `sprintcycle/presentation/`.
- Architecture rules should be read against this current split, not against an older `entrypoints/`-centric assumption.

- Preserve the current architecture and core skeleton.
- Keep the public API thin: it may normalize, route, delegate, and aggregate, but it must not own workflow logic.
- Keep execution, governance, observability, suggestion handling, deployment/runtime, and evolution strictly separated.
- Prefer existing services, facades, hooks, registries, adapters, and event backends over introducing parallel paths.
- Any new feature must land in the correct layer and use the smallest possible change.

## Trigger layers / 触发分层
### Tier 1 — Architecture trigger / 架构级强触发
Apply this rule when changes touch:
- public API shape, layer boundaries, or ownership boundaries
- service/facade/hook/registry/adapter responsibilities
- request normalization, routing, delegation, or result aggregation
- workflows, orchestration, or lifecycle transitions
- `presentation/` and `interfaces/http/` responsibilities

### Tier 2 — Boundary trigger / 边界级中触发
Apply this rule when changes touch:
- implementation details inside a layer that may shift responsibility
- code that coordinates more than one subsystem
- shared utilities used across orchestration, governance, observability, or evolution paths
- config or dependency changes that can alter ownership or call chains

### Tier 3 — Review trigger / 复核级弱触发
Apply a lightweight review when changes touch:
- comments, naming, docs, examples, or formatting
- local refactors that should still be checked for architecture drift

## System constitution / 系统总则
- Preserve the current architecture and core skeleton.
- Keep the public API thin: it may normalize, route, delegate, and aggregate, but it must not own workflow logic.
- Keep execution, governance, observability, suggestion handling, deployment/runtime, and evolution strictly separated.
- Prefer existing services, facades, hooks, registries, adapters, and event backends over introducing parallel paths.
- Any new feature must land in the correct layer and use the smallest possible change.

## Key component ownership / 关键组件职责限定
- AutoGPT is responsible for deployment specifications and platformized startup.
- LangGraph is responsible for execution graph adaptation.
- Phoenix is responsible for trace / replay observability adaptation.
- SprintCycle Core must continue to own business orchestration and the repair/fix closed loop.
- Do not move these responsibilities across layers unless the architecture is explicitly being redefined.

## Non-negotiable boundaries / 不可破坏的边界
- Do not move domain rules into the public API or presentation layer.
- Do not bypass hooks when lifecycle interception, compensation, or policy control is needed.
- Do not bypass facades when domain coordination already exists.
- Do not duplicate observability, governance, or suggestion logic inside execution code.
- Do not mutate suggestion or governance state outside their designated workflows.
- Do not introduce competing pipelines that weaken the current skeleton.
- Do not reintroduce CLI/MCP as formal product entry paths.

## Layer ownership / 分层职责
- `interfaces/http/`: request normalization, thin routing, protocol adaptation, and result aggregation for HTTP public/internal APIs.
- `presentation/`: dashboard container, views, projections, and view models.
- Service layer: workflow logic and orchestration of domain behavior.
- Facade layer: stable domain-facing coordination and compatibility.
- Hook layer: lifecycle interception, before/after/failed behavior, policy gating, and annotations.
- Orchestration/execution layer: runtime execution mechanics, scheduling, and execution lifecycle.
- Governance layer: checks, review, approval, and policy decisions.
- Observability layer: trace, replay, event capture, inspection, and read models.
- Suggestion layer: review, approval, rejection, archival, promotion, and replay linkage.
- Evolution layer: version growth, memory, knowledge capture, and iterative self-improvement.
- Registry/adapter layer: plugin lookup and environment-specific integration.

## Interaction rules / 交互规则
- For every request, first identify the owning subsystem.
- Determine whether the change is additive, behavioral, or structural.
- Reuse the nearest existing extension point before introducing new abstractions.
- Keep changes localized to the smallest responsible layer.
- If a request touches multiple subsystems, keep boundaries explicit and coordinate through services rather than direct coupling.
- Prefer explicit lifecycle steps over implicit side effects.

## Change strategy / 修改策略
1. Identify the owning subsystem.
2. Check whether an existing service, facade, hook, registry, or adapter can express the change.
3. Implement the smallest possible change in the correct layer.
4. Keep the public API thin.
5. Keep orchestration clean and domain logic localized.
6. Verify that the web-triggered end-to-end lifecycle still remains intact.
7. Verify that governance, observability, suggestion, and evolution flows remain consistent.

## Default decision policy / 默认决策原则
- When in doubt, preserve the current architecture.
- Prefer extension over replacement.
- Prefer composition over coupling.
- Prefer service-level changes over API-level complexity.
- Prefer explicit flow over hidden behavior.
- Avoid speculative abstractions and avoid duplicating logic across layers.
- If behavior belongs to a hook, facade, service, registry, or orchestration stage, implement it there rather than inline.
