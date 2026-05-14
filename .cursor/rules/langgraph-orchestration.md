# SprintCycle LangGraph Orchestration Rule / SprintCycle LangGraph 编排规则

## Purpose / 目的
LangGraph is the orchestration skeleton for SprintCycle planning and sprint-level execution coordination.

Current implementation context / 当前实现现状：
- LangGraph is currently used for plan-level outer decomposition and organization.
- LangGraph also coordinates sprint-level inner execution and repair orchestration.
- In practice, this means the graph spans both outer planning structure and inner sprint control, but still remains an orchestration layer rather than a domain logic layer.

- Current LangGraph scope is `intent → plan → sprint decomposition → sprint execution → observe → repair`.
- LangGraph should structure plan decomposition into sprints and coordinate internal scheduling within each sprint.
- Keep LangGraph focused on orchestration flow, state transitions, and routing between stages.
- Do not put domain business rules directly inside graph nodes when the logic belongs to application services, facades, hooks, or orchestrators.

## Trigger layers / 触发分层
### Tier 1 — Graph trigger / 图编排强触发
Apply this rule when changes touch:
- graph nodes, edges, guards, or transitions
- `plan`, `run`, `observe`, or `repair` stage behavior
- plan decomposition, sprint creation, sprint ordering, retry routing, or intra-sprint dispatch
- graph state models or state mutation paths

### Tier 2 — Orchestration trigger / 编排级中触发
Apply this rule when changes touch:
- service/facade/hook behavior that the graph delegates to
- execution lifecycle or repair loops that the graph coordinates
- routing or scheduling logic that can affect the graph backbone
- configs, dependencies, or tests that influence graph behavior

### Tier 3 — Review trigger / 复核级弱触发
Apply a lightweight review when changes touch:
- docs, comments, examples, or naming around graph behavior
- non-structural edits that may still affect orchestration clarity

## LangGraph orchestration rule / LangGraph 编排规则
- LangGraph is the core orchestration skeleton for planning and sprint-level scheduling.
- Current LangGraph scope is `plan / run / observe / repair`.
- Use LangGraph to structure plan decomposition into sprints and to manage internal scheduling within each sprint.
- Keep LangGraph focused on orchestration flow, state transitions, and routing between stages.
- Do not put domain business rules directly inside graph nodes when the logic belongs to application services, facades, hooks, or orchestrators.
- Do not use LangGraph as a shortcut to bypass existing architecture boundaries.
- Plan splitting, sprint creation, sprint sequencing, retry/fix routing, and intra-sprint dispatch must remain aligned with the layered architecture.
- Prefer reusing existing extension points, hook phases, registries, and service methods rather than introducing parallel graph-specific business logic.
- Preserve the clean separation between orchestration and domain responsibility.
- Any LangGraph change must keep the end-to-end lifecycle intact and must not weaken governance, observability, suggestion handling, or evolution flows.

## Implementation guidance / 实现指引
- Treat graph nodes as orchestration units, not as domain service replacements.
- Keep graph transitions explicit and minimal.
- If a node needs business behavior, move that behavior into the owning service/facade/hook and let the graph call it.
- Avoid hardcoding workflow policy inside graph construction when the policy already exists in the domain layer.
- Keep graph-based changes aligned with the end-to-end lifecycle and the current execution backbone.
- Treat any graph, routing, execution, or lifecycle change as a trigger to re-check LangGraph boundaries and the surrounding layered architecture.
- If a change touches plan/run/observe/repair behavior, verify that upstream and downstream contract flows still remain intact.
