# Fitness 多维度整合

## Task summary
- Request source: `/team-command "Fitness多维度整合" | 当前Fitness分散，需统一评分入口 | 在 domain/fitness/ 创建`
- Owner / requester: SprintCycle IT 研发流程
- Date: 2026-05-16
- Complexity class: Medium/High
- Route decision: Spec-Kit

## Goal
Create a unified fitness aggregation entry in `sprintcycle/domain/fitness/` so multiple fitness dimensions can be scored through one explainable interface.

## Non-goals
- Do not change the broader lifecycle governance model.
- Do not redesign the frontend UI.
- Do not rewrite unrelated orchestration logic.
- Do not introduce tool execution responsibilities into the aggregator.

## Scope
Included:
- `sprintcycle/domain/fitness/`
- unified aggregation model
- evaluator compatibility path
- minimal test coverage for aggregation behavior

Excluded:
- external service execution
- dashboard presentation changes
- governance rule changes

## Constraints
- Keep the implementation within the fitness domain.
- Preserve existing compatibility with current fitness payloads where possible.
- The aggregator must remain explainable.
- Each dimension result must support `weight`, `reason`, and layered `metadata`.
- `metadata` must use a fixed `core` section and a free-form `extra` section.

## Implementation approach
1. Define normalized fitness dimension and aggregate result structures.
2. Add a unified fitness aggregator that computes weighted total score and per-dimension contributions.
3. Update the fitness evaluator to use the unified aggregator as the main entry.
4. Preserve compatibility with legacy payload shapes by deriving dimensions when needed.
5. Add focused tests for aggregation behavior and evaluator compatibility.

## Acceptance criteria
- A single fitness aggregation entry exists under `domain/fitness/`.
- The aggregator accepts multiple dimensions.
- The aggregator preserves `weight`, `reason`, and layered `metadata`.
- The evaluator can consume both direct `dimensions` input and legacy payload input.
- Tests cover the new aggregation behavior.
- Lint passes for changed files.

## Validation plan
- Run targeted tests for the new fitness aggregator.
- Run lint checks on modified fitness files and new tests.
- Confirm the new API shape is consistent across `aggregator`, `evaluator`, and exports.

## Risks
- Legacy payload compatibility may be incomplete if future callers rely on implicit scoring details.
- Overly flexible metadata could drift if new callers bypass the layered format.
- Weight choices may need tuning once more fitness dimensions are added.

## Loop-back conditions
Return to Coordinator if:
- the aggregator needs additional dimensions beyond the current compatibility set
- a caller requires a contract change outside `domain/fitness/`
- tests reveal score semantics that need governance or architecture changes
