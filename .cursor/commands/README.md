# Cursor Commands Index / 命令索引

This directory contains the fixed command entry points for SprintCycle Cursor workflows.

## Governance references

Before using commands, read:
- `docs/AI_GOVERNANCE.md` for governance, routing, and conflict policy / 治理、路由和冲突策略
- `docs/CURSOR_TEAM_PLAYBOOK.md` for the minimum complete AI team and workflow order / 最小完整 AI 团队与工作流顺序

## Core command set / 核心命令集

These are the 7 primary commands for the minimal complete workflow:

- `/team-command`
- `/spec-command`
- `/architect-command`
- `/implement-command`
- `/qa-command`
- `/review-command`
- `/commit-message-command`

## Routing summary / 路由摘要

- `/team-command` is the intake and routing entry point.
- `/spec-command` turns a request into a routed task spec.
- `/architect-command` decomposes boundaries and dependencies.
- `/implement-command` applies the approved changes.
- `/qa-command` validates behavior and decides pass, change, or loop back.
- `/review-command` consolidates final judgment.
- `/commit-message-command` drafts the delivery summary and commit text.

- `/team-command` 是接单与路由入口。
- `/spec-command` 将需求转成带路由的任务规范。
- `/architect-command` 负责边界和依赖拆解。
- `/implement-command` 负责执行已批准的改动。
- `/qa-command` 负责验证并决定通过、修改或回流。
- `/review-command` 负责整合最终结论。
- `/commit-message-command` 负责交付摘要和提交信息。

## Command details / 命令说明

### `/team-command`
Use this first for new work, ambiguous requests, or multi-step changes.

Responsibilities:
- classify task complexity
- choose OpenSpec or Spec-Kit
- select the minimum required workflow
- decide whether Architect is required
- produce the routing decision and next step

Use for:
- new feature planning
- multi-step refactors
- cross-layer changes
- unclear requirements

### `/spec-command`
Use this when you want to turn a request into a task spec.

Responsibilities:
- define goal, non-goals, scope, constraints, and acceptance criteria
- choose OpenSpec for low complexity or Spec-Kit for medium/high complexity
- produce a spec handoff for Implementation or Architect

Use for:
- request clarification
- task scoping
- spec drafting
- complexity-based spec routing

### `/architect-command`
Use this when the task needs decomposition or boundary design.

Responsibilities:
- split work into safe sub-steps
- define dependencies and ownership boundaries
- identify parallelizable parts
- produce an implementation plan

Use for:
- multi-file changes
- boundary-sensitive work
- cross-module design
- refactor planning

### `/implement-command`
Use this when the spec and breakdown are ready and code changes should begin.

Responsibilities:
- implement only what the spec covers
- keep changes localized
- report files touched, deviations, and self-check notes

Use for:
- code changes
- refactors with approved scope
- feature delivery
- localized fixes

### `/qa-command`
Use this when implementation is ready for validation.

Responsibilities:
- verify behavior against the spec
- check regressions and edge cases
- identify missing tests or follow-up work
- decide whether the change passes or must loop back

Use for:
- validation
- regression review
- test gap discovery
- release readiness checks

### `/review-command`
Use this for final synthesis when multiple checks or judgments need consolidation.

Responsibilities:
- consolidate review results
- resolve cross-role conflicts
- produce the final verdict
- summarize rule updates or blockers

Use for:
- multi-review changes
- final verdict consolidation
- release-ready decision-making

### `/commit-message-command`
Use this to summarize the current change and draft a commit message.

Responsibilities:
- summarize the task outcome
- align commit text with repository style
- keep the message concise and accurate

Use for:
- preparing a commit summary
- aligning commit text with the repository's style

## Routing policy / 路由策略

### OpenSpec route / OpenSpec 路由
Use OpenSpec for low complexity, small scope, low risk tasks with no architecture or contract change.

Use for:
- single-file or tiny-surface edits
- localized fixes
- quick bug fixes

### Spec-Kit route / Spec-Kit 路由
Use Spec-Kit for anything medium or high complexity, boundary-sensitive, cross-module, or higher risk.

Use for:
- multi-file work
- boundary-sensitive changes
- refactors and migrations
- contract or state changes

### Default rule / 默认规则
If a task is not clearly low complexity, route it to Spec-Kit by default.

## Quality gates and return-to-owner / 质量门禁与回流归属

- `team-command` returns uncertainty to the smallest owner and confirms the route.
- `spec-command` returns incomplete scope or acceptance criteria to `team-command` or itself as needed.
- `architect-command` returns boundary or dependency ambiguity to `spec-command` or itself as needed.
- `implement-command` returns scope creep or overreach to `architect-command`.
- `qa-command` returns missing tests or unresolved risks to `implement-command`.
- `review-command` is the final gate and returns unresolved consolidation issues upstream.

## Delivery observability and retro / 交付可观测性与复盘

After meaningful tasks, capture lightweight metadata for later analysis:
- task summary / 任务摘要
- routing path / 路由路径
- complexity level / 复杂度等级
- gates triggered / 触发的门禁
- return-to-owner events / 回流归属事件
- final verdict / 最终结论
- key risks / 关键风险
- lessons learned / 复盘结论

Retro output template:

```text
Task summary
Routing path
Complexity level
Key risks
Gates triggered
Return-to-owner events
Blocking reasons
Final verdict
Lessons learned
Rule improvement candidates
```

## Maintenance / 维护

When adding a new command:
- document its purpose here / 在此记录用途
- link it to the correct role or workflow / 关联正确角色或流程
- keep terminology aligned with `docs/AI_GOVERNANCE.md` / 与治理总纲保持术语一致
- keep the index concise and role-oriented / 保持索引简洁且角色导向
