# Cursor Commands Index / 命令索引

This directory contains the fixed command entry points for SprintCycle Cursor workflows.

## Governance references

Before using commands, read:
- `docs/AI_GOVERNANCE.md` for governance, routing, and conflict policy / 治理、路由和冲突策略
- `docs/CURSOR_TEAM_PLAYBOOK.md` for the minimum complete AI team and workflow order / 最小完整 AI 团队与工作流顺序

## Core command set / 核心命令集

These are the 7 primary commands recommended for the minimal complete workflow:

- `/it-it-team-command`
- `/it-it-spec-command`
- `/it-it-it-architect-command`
- `/it-it-it-implement-command`
- `/it-it-it-qa-command`
- `/it-it-review-command`
- `/it-it-commit-message-command`

## Command groups / 命令分组

### 1. Intake and routing / 接单与路由

#### `/it-team-command`
Use this as the first entry point for new work.

Responsibilities:
- classify task complexity / 任务复杂度分类
- choose OpenSpec or Spec-Kit / 选择 OpenSpec 或 Spec-Kit
- route to the right workflow mode / 路由到正确的工作流模式
- identify whether Architect is needed / 判断是否需要 Architect
- produce the minimal execution path / 给出最小执行路径

Use for:
- new feature planning / 新功能规划
- multi-step refactors / 多步骤重构
- cross-layer changes / 跨层改动
- unclear requirements / 需求不明确

### 2. Spec and implementation flow / 规范与实现流程

#### `/it-spec-command`
Use this when you want to turn a request into a task spec.

Responsibilities:
- define goal, non-goals, scope, constraints, and acceptance criteria / 定义目标、非目标、范围、约束和验收标准
- choose OpenSpec for low complexity or Spec-Kit for medium/high complexity / 低复杂度选 OpenSpec，中高复杂度选 Spec-Kit
- produce the spec handoff for Implementation or Architect / 为实现或架构拆分生成交接包

Use for:
- request clarification / 需求澄清
- task scoping / 任务范围界定
- spec drafting / 规范草拟
- complexity-based spec routing / 按复杂度选择规范路径

#### `/it-architect-command`
Use this when you need task decomposition and boundary design.

Responsibilities:
- split work into safe sub-steps / 拆分安全子步骤
- define dependencies and ownership boundaries / 定义依赖与职责边界
- identify parallelizable parts / 找出可并行部分
- produce an implementation plan / 产出实现计划

Use for:
- multi-file changes / 多文件改动
- boundary-sensitive work / 边界敏感工作
- cross-module design / 跨模块设计
- refactor planning / 重构规划

#### `/it-implement-command`
Use this when the spec and breakdown are ready and code changes should begin.

Responsibilities:
- implement only what the spec covers / 只实现规范覆盖的内容
- keep changes localized / 保持改动局部化
- report files touched, deviations, and self-check notes / 汇报修改文件、偏差和自检说明

Use for:
- code changes / 代码修改
- refactors with approved scope / 已批准范围内的重构
- feature delivery / 功能交付
- localized fixes / 局部修复

#### `/it-qa-command`
Use this when implementation is ready for validation.

Responsibilities:
- verify behavior against the spec / 按规范验证行为
- check regressions and edge cases / 检查回归与边界场景
- identify missing tests or follow-up work / 找出缺失测试或后续工作
- decide whether the change passes or must loop back / 判断通过或回流

Use for:
- validation / 验证
- regression review / 回归审查
- test gap discovery / 测试缺口发现
- release readiness checks / 发布就绪检查

### 3. Review and synthesis / 审查与汇总

#### `/it-review-command`
Runs final synthesis through the review commander path.

Use for:
- multi-review changes / 多个审查结论汇总
- final verdict consolidation / 最终结论整合
- release-ready decision-making / 发布前决策

### 4. Delivery support / 交付支持

#### `/it-commit-message-command`
Summarizes the current change and drafts a commit message.

Use for:
- preparing a commit summary / 准备提交摘要
- aligning commit text with the repository's style / 对齐仓库提交风格

## Quality gates and return-to-owner / 质量门禁与回流归属

- `team-command` should route uncertainty back to the smallest owner / `team-command` 应将不确定性回流到最小责任人
- `spec-command` should return incomplete scope or acceptance criteria to `team-command` or itself as needed / `spec-command` 应将不完整范围或验收标准回流给 `team-command` 或自身
- `architect-command` should return boundary or dependency ambiguity to `spec-command` or itself as needed / `architect-command` 应将边界或依赖不清回流给 `spec-command` 或自身
- `implement-command` should return scope creep or overreach to `architect-command` / `implement-command` 应将范围扩大或越界回流给 `architect-command`
- `qa-command` should return missing tests or unresolved risks to `implement-command` / `qa-command` 应将缺失测试或未解决风险回流给 `implement-command`
- `review-command` is the final gate and returns unresolved consolidation issues upstream / `review-command` 是最终门禁，并将未解决的汇总问题向上回流

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

## Recommended command flow / 推荐命令流

### Low complexity / 低复杂度
`/team-command` → `/spec-command` → `/implement-command` → `/qa-command` → `/review-command`

### Medium complexity / 中复杂度
`/team-command` → `/spec-command` → `/architect-command` → `/implement-command` → `/qa-command` → `/review-command`

### High complexity / 高复杂度
`/team-command` → `/spec-command` → `/architect-command` → `/implement-command` → `/qa-command` → `/review-command`

## Maintenance / 维护

When adding a new command:
- document its purpose here / 在此记录用途
- link it to the correct role or workflow / 关联正确角色或流程
- keep terminology aligned with `docs/AI_GOVERNANCE.md` / 与治理总纲保持术语一致
- keep the index concise and role-oriented / 保持索引简洁且角色导向
