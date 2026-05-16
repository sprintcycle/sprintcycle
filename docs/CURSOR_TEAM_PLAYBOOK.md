# SprintCycle Cursor Team Playbook / SprintCycle Cursor 团队手册

This document defines the operating model for AI-assisted development work in SprintCycle. It describes the minimum complete team, command entry points, task routing policy, and the relationship between this playbook and the governance document.

本文档定义 SprintCycle 中 AI 辅助开发工作的运行模型，包括最小完整团队、命令入口、任务路由策略，以及本手册与治理文档的关系。

## Document hierarchy / 文档关系

- `AGENTS.md` — repository-level baseline / 仓库级底线
- `docs/AI_GOVERNANCE.md` — governance charter / 治理总纲
- `docs/CURSOR_TEAM_PLAYBOOK.md` — execution manual / 执行手册
- `.cursor/rules/` — routing and priority / 路由与优先级
- `.cursor/commands/` — command entry points / 命令入口

## 1. Relationship to AI governance / 与 AI 治理的关系

This playbook is the execution manual.
`docs/AI_GOVERNANCE.md` is the governance source of truth.

本手册是执行手册。
`docs/AI_GOVERNANCE.md` 是治理真相源。

- Governance defines the rules
- This playbook defines how the team executes those rules
- Task specs define what a specific task must accomplish
- See the governance overview diagram in `docs/AI_GOVERNANCE.md` for the full layer map

- 治理定义规则
- 本手册定义团队如何执行这些规则
- 任务规范定义单次任务要完成什么
- 请参考 `docs/AI_GOVERNANCE.md` 中的治理总览图查看完整层级

## 2. Team model / 团队模型

SprintCycle’s minimum complete AI development team is intentionally small and explicit:

- `Coordinator` — intake, classification, routing, and work breakdown
- `Spec` — task specification, scope definition, and acceptance criteria
- `Architect` — boundaries, dependencies, and task decomposition
- `Implementation` — code changes and implementation execution
- `QA/Review` — regression checks, spec compliance, and validation

SprintCycle 的最小完整 AI 研发团队刻意保持精简且职责明确：

- `Coordinator` — 接单、分类、路由与工作拆解
- `Spec` — 任务规范、范围定义与验收标准
- `Architect` — 边界、依赖与任务拆分
- `Implementation` — 代码修改与实现执行
- `QA/Review` — 回归检查、规范符合性与验证

This is the smallest team that can still complete the full loop from intake to validated delivery.

这是能够从接单到验证交付完整闭环的最小团队。

## 3. Role responsibilities / 角色职责

### 3.1 Coordinator / 协调者
Use first when the request is broad, multi-step, or ambiguous.

当需求范围广、步骤多或含糊时，优先使用 Coordinator。

Responsibilities:
- classify task complexity
- choose OpenSpec or Spec-Kit
- select the minimum required workflow
- assign the next role
- decide whether a task needs Architect involvement
- collect final results and trigger review loops if necessary

职责：
- 判断任务复杂度
- 选择 OpenSpec 或 Spec-Kit
- 选择最小必要工作流
- 指派下一角色
- 判断是否需要 Architect 参与
- 汇总结果并在必要时触发回流

### 3.2 Spec / 规范编写
Responsibilities:
- transform the request into an explicit task spec
- define scope, non-goals, constraints, and acceptance criteria
- choose OpenSpec for low complexity tasks
- choose Spec-Kit for medium/high complexity tasks

职责：
- 将需求转成明确任务规范
- 定义范围、非目标、约束与验收标准
- 低复杂度使用 OpenSpec
- 中高复杂度使用 Spec-Kit

### 3.3 Architect / 架构拆分
Responsibilities:
- split the task into safe sub-steps
- define dependencies and boundaries
- identify parallelizable parts
- keep the implementation surface small

职责：
- 将任务拆成安全的子步骤
- 定义依赖与边界
- 找出可并行部分
- 保持实现面最小

### 3.4 Implementation / 实现
Responsibilities:
- implement only what is covered by the spec
- avoid unrelated refactors
- keep changes localized to the owning layer

职责：
- 只实现规范覆盖的内容
- 避免无关重构
- 保持改动局部化到所属层

### 3.5 QA/Review / 验证与审查
Responsibilities:
- verify the change against the spec
- check for regressions and edge cases
- block completion when acceptance criteria are not met
- recommend concrete follow-up fixes

职责：
- 按规范验证变更
- 检查回归与边界场景
- 当验收标准未满足时阻止完成
- 给出具体后续修复建议

## 4. Command entry points / 命令入口

Use commands when you want a fixed entry that maps to a specific role.

当你希望使用一个固定入口映射到某个角色时，使用命令。

- `/team-command` → `team-agent`
- `/spec-command` → `spec-agent`
- `/architect-command` → `architect-agent`
- `/implement-command` → `implement-agent`
- `/qa-command` → `qa-agent`
- `/review-command` → `review-agent`
- `/commit-message-command` → `commit-message-agent`

If the repository later introduces commands for spec routing, document them here.

如果仓库后续引入规范路由命令，也请在这里补充。

## 5. Routing policy / 路由策略

### 5.1 OpenSpec route / OpenSpec 路由
Use OpenSpec for:
- low complexity
- small scope
- low risk
- no architecture change
- no contract change

低复杂度任务使用 OpenSpec：
- 范围小
- 风险低
- 无架构变化
- 无 contract 变化

Recommended flow:
- Coordinator
- OpenSpec
- Implementation
- QA/Review
- Complete

推荐流程：
- Coordinator
- OpenSpec
- Implementation
- QA/Review
- 完成

### 5.2 Spec-Kit route / Spec-Kit 路由
Use Spec-Kit for:
- medium complexity
- high complexity
- boundary-sensitive changes
- cross-module work
- higher regression risk

中高复杂度任务使用 Spec-Kit：
- 中等复杂度
- 高复杂度
- 边界敏感改动
- 跨模块工作
- 更高回归风险

Recommended flow:
- Coordinator
- Spec-Kit
- Architect
- Implementation
- QA/Review
- Complete

推荐流程：
- Coordinator
- Spec-Kit
- Architect
- Implementation
- QA/Review
- 完成

### 5.3 Skipping Architect / 跳过 Architect
Architect can be skipped only when:
- the task is low complexity
- the change is localized
- the boundaries are already obvious

仅在以下情况下可跳过 Architect：
- 任务低复杂度
- 改动局部化
- 边界已经很明确

### 5.4 Mandatory review / 强制审查
QA/Review is mandatory for:
- contract changes
- refactors
- cross-layer changes
- anything that may regress behavior

以下情况必须经过 QA/Review：
- contract 变更
- 重构
- 跨层变更
- 任何可能引发回归的改动

## 6. Complexity decision guide / 复杂度判断指南

### Low complexity / 低复杂度
Typical signals:
- one file
- limited surface area
- low risk
- simple acceptance criteria

典型特征：
- 单文件
- 影响面小
- 风险低
- 验收标准简单

Use OpenSpec.

使用 OpenSpec。

### Medium complexity / 中复杂度
Typical signals:
- multiple files
- some dependencies
- moderate risk
- explicit validation needed

典型特征：
- 多文件
- 存在一些依赖
- 中等风险
- 需要明确验证

Use Spec-Kit.

使用 Spec-Kit。

### High complexity / 高复杂度
Typical signals:
- architecture change
- runtime or governance change
- cross-layer coupling
- migration or refactor work
- high regression risk

典型特征：
- 架构变化
- 运行时或治理变化
- 跨层耦合
- 迁移或重构
- 高回归风险

Use Spec-Kit and require Architect plus QA/Review.

使用 Spec-Kit，并要求 Architect 与 QA/Review 参与。

## 7. Conflict avoidance rules / 冲突规避规则

- Do not maintain duplicate global constraints in both spec systems
- Do not let a task spec override governance rules
- Do not treat OpenSpec as a second governance system
- Do not rewrite the same rule in multiple places
- If a rule changes, update the governance layer first

- 不要在两个规范系统里维护重复的全局约束
- 不要让任务规范覆盖治理规则
- 不要把 OpenSpec 当成第二套治理系统
- 不要在多个地方重复写同一条规则
- 规则变化时先更新治理层

## 8. Recommended work patterns / 推荐工作模式

### A. Small bug fix / 小 bug 修复
1. Coordinator
2. OpenSpec
3. Implementation
4. QA/Review
5. Complete

1. Coordinator
2. OpenSpec
3. Implementation
4. QA/Review
5. 完成

### B. Standard feature / 标准功能
1. Coordinator
2. Spec-Kit
3. Architect
4. Implementation
5. QA/Review
6. Complete

1. Coordinator
2. Spec-Kit
3. Architect
4. Implementation
5. QA/Review
6. 完成

### C. Large refactor / 大重构
1. Coordinator
2. Spec-Kit
3. Architect
4. Implementation
5. QA/Review
6. Loop back if needed
7. Complete

1. Coordinator
2. Spec-Kit
3. Architect
4. Implementation
5. QA/Review
6. 必要时回流
7. 完成

## 9. Workflow protocol / 工作流协议

SprintCycle uses a mixed-mode execution protocol so the same five roles can handle both small iterations and larger refactors without changing the team model.

SprintCycle 使用混合模式执行协议，让同一组五角色既能处理小迭代，也能处理较大重构，而无需改变团队模型。

### 9.1 Lightweight flow / 轻量流
Use the lightweight flow when the task is small, localized, and low risk.

当任务小、局部且低风险时使用轻量流。

```text
Coordinator → Spec → Implementation → QA/Review → Done
```

### 9.2 Strict flow / 严格流
Use the strict flow when the task is multi-file, boundary-sensitive, or higher risk.

当任务涉及多文件、边界敏感或风险更高时使用严格流。

```text
Coordinator → Spec → Architect → Implementation → QA/Review → Done
```

### 9.3 Handoff rules / 交接规则
Every role must pass a compact handoff package to the next role.

每个角色都必须向下一角色传递简洁的交接包。

- Coordinator → Spec: task summary, complexity, route, risks
- Spec → Architect / Implementation: goals, non-goals, scope, constraints, acceptance criteria
- Architect → Implementation: breakdown, dependencies, boundaries, implementation order
- Implementation → QA/Review: changed files, deviations, self-check summary, validation focus
- QA/Review → Coordinator: verdict, missing checks, risk level, required follow-up

- Coordinator → Spec：任务摘要、复杂度、路由、风险
- Spec → Architect / Implementation：目标、非目标、范围、约束、验收标准
- Architect → Implementation：拆解、依赖、边界、实现顺序
- Implementation → QA/Review：修改文件、偏差、自检摘要、验证重点
- QA/Review → Coordinator：结论、缺失检查、风险等级、后续动作

### 9.4 Escalation rules / 升级规则
- If the Spec discovers scope expansion, escalate to the strict flow.
- If Implementation finds hidden dependencies, escalate to the strict flow.
- If QA/Review finds high regression risk, block completion and route back through Coordinator.

- 如果 Spec 发现范围扩张，升级为严格流。
- 如果 Implementation 发现隐藏依赖，升级为严格流。
- 如果 QA/Review 发现高回归风险，阻止完成并通过 Coordinator 回流。

### 9.5 Output templates / 输出模板
Each role should keep its output short and structured.

每个角色的输出都应保持简短且结构化。

- Coordinator: classification, routing, workflow mode, risks, next step
- Spec: goal, non-goals, scope, constraints, acceptance criteria, recommended route
- Architect: breakdown, dependencies, boundaries, implementation order, risks
- Implementation: changes made, files touched, notes, self-check summary
- QA/Review: validation summary, missing checks, high-risk scenarios, verdict, follow-up

- Coordinator：分类、路由、工作流模式、风险、下一步
- Spec：目标、非目标、范围、约束、验收标准、推荐路径
- Architect：拆解、依赖、边界、实现顺序、风险
- Implementation：已做修改、涉及文件、备注、自检摘要
- QA/Review：验证摘要、缺失检查、高风险场景、结论、后续跟进

## 10. AI team quick card / AI 团队速查卡

### 10.1 Minimum complete team / 最小完整团队
- Coordinator
- Spec
- Architect
- Implementation
- QA/Review

- Coordinator
- Spec
- Architect
- Implementation
- QA/Review

### 10.2 Default full flow / 默认完整流程
```text
Coordinator → Spec → Architect → Implementation → QA/Review → Done
```

### 10.3 Lightweight flow / 轻量流程
```text
Coordinator → Spec → Implementation → QA/Review → Done
```

### 10.4 Routing rule / 路由规则
- Low complexity → OpenSpec + lightweight flow
- Medium complexity → Spec-Kit + strict flow
- High complexity → Spec-Kit + strict flow + stronger review

- 低复杂度 → OpenSpec + 轻量流
- 中复杂度 → Spec-Kit + 严格流
- 高复杂度 → Spec-Kit + 严格流 + 更强审查

### 10.5 One-line rule of thumb / 一句话规则
- `Coordinator` decides the route
- `Spec` writes the task contract
- `Architect` breaks down the work
- `Implementation` changes the code
- `QA/Review` decides pass or loop back

- `Coordinator` 决定路由
- `Spec` 编写任务 contract
- `Architect` 拆解工作
- `Implementation` 修改代码
- `QA/Review` 决定通过或回流

## 11. Quality gates and return-to-owner / 质量门禁与回流归属

SprintCycle treats quality gates as part of the delivery system, not as an afterthought.

SprintCycle 将质量门禁视为交付系统的一部分，而不是事后补救措施。

### 11.1 Gate outcomes / 门禁结果
Every role must be able to produce one of three outcomes:
- `approve` — the output is complete enough to continue
- `request changes` — the current owner must revise the output
- `loop back` — the issue must return to a specific upstream role

每个角色都必须能给出三种结果之一：
- `approve` — 输出足够完整，可以继续推进
- `request changes` — 当前责任人需要修改输出
- `loop back` — 问题必须回到明确的上游角色

### 11.2 Return-to-owner matrix / 回流归属表
- Requirement ambiguity / 需求不清楚 -> `team-agent`
- Spec incompleteness / 规范不完整 -> `spec-agent`
- Boundary or dependency ambiguity / 边界或依赖不清晰 -> `architect-agent`
- Scope creep or implementation overreach / 范围扩大或实现越界 -> `implement-agent`
- Missing tests or high regression risk / 缺失测试或高回归风险 -> `qa-agent`
- Conflicting cross-role conclusions / 跨角色结论冲突 -> `review-agent`

- 需求不清楚 -> `team-agent`
- 规范不完整 -> `spec-agent`
- 边界或依赖不清晰 -> `architect-agent`
- 范围扩大或实现越界 -> `implement-agent`
- 缺失测试或高回归风险 -> `qa-agent`
- 跨角色结论冲突 -> `review-agent`

### 11.3 Blocking criteria / 阻断条件
A gate must block progression when the change:
- breaks the `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` chain
- bypasses governance, observability, suggestion, or evolution flows
- violates architecture boundaries or introduces parallel orchestration paths
- leaves critical regression risk unresolved

当改动出现以下情况时，门禁必须阻断推进：
- 破坏 `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` 主链路
- 绕过 governance、observability、suggestion 或 evolution 流程
- 违反架构边界或引入平行编排路径
- 关键回归风险未解决

### 11.4 Review authority / Review 权限
`review-agent` is the final gate for consolidated decisions.
`qa-agent` is the quality gate for implementation readiness.

`review-agent` 是综合决策的最终门禁。
`qa-agent` 是实现就绪的质量门禁。

### 11.5 QA and Review decision discipline / QA 与 Review 决策纪律
- `qa-agent` must output an explicit readiness verdict: `approve`, `request changes`, or `loop back`.
- `qa-agent` must name the return-to-owner role when changes are required.
- `qa-agent` must call out missing tests, high-risk scenarios, and any gap in the `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` chain.
- `review-agent` must output a consolidated final verdict: `approve`, `approve with warnings`, or `request changes`.
- `review-agent` must identify blocking reasons explicitly when the change cannot proceed.
- `review-agent` must prioritize the most conservative risk assessment when specialist conclusions conflict.

- `qa-agent` 必须输出明确的就绪结论：`approve`、`request changes` 或 `loop back`。
- `qa-agent` 在需要修改时必须指明回流的责任角色。
- `qa-agent` 必须指出缺失测试、高风险场景，以及 `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` 链路中的任何缺口。
- `review-agent` 必须输出综合后的最终结论：`approve`、`approve with warnings` 或 `request changes`。
- `review-agent` 在无法继续推进时必须显式说明阻断原因。
- 当专项结论冲突时，`review-agent` 必须优先采用最保守的风险判断。

## 12. Delivery observability and retro / 交付可观测性与复盘

SprintCycle should record lightweight delivery metadata for every meaningful task so the team can improve route selection, gate behavior, and agent discipline over time.

SprintCycle 应为每个有意义的任务记录轻量级交付元数据，以便团队长期优化路由选择、门禁行为和 Agent 纪律。

### 12.1 Recorded metadata / 记录的元数据
- task summary / 任务摘要
- routing path / 路由路径
- complexity level / 复杂度等级
- gates triggered / 触发的门禁
- return-to-owner events / 回流归属事件
- final verdict / 最终结论
- key risks / 关键风险
- lessons learned / 复盘结论

### 12.2 Retro output template / 复盘输出模板
```text
Task summary
Routing path
Key risks
Gates triggered
Return-to-owner events
Final verdict
Lessons learned
Rule improvement candidates
```

### 12.3 Retro questions / 复盘问题
- Which route was chosen and why? / 为什么选择这条路由？
- Where did the task return, and why? / 问题回到了哪里、为什么？
- Which gate blocked progress? / 哪个门禁阻断了推进？
- Which agent most often needed correction? / 哪个 Agent 最常需要纠正？
- Which rule or template should be strengthened? / 哪条规则或模板应该加强？

### 12.4 Feedback loop / 反馈闭环
Retro findings should be used to improve:
- agent behavior constraints / Agent 行为约束
- command routing / 命令路由
- playbook gate rules / 执行手册中的门禁规则
- quality thresholds / 质量阈值

## 13. Delivery observability and retro / 交付可观测性与复盘

SprintCycle should record lightweight delivery metadata for every meaningful task so the team can improve route selection, gate behavior, and agent discipline over time.

SprintCycle 应为每个有意义的任务记录轻量级交付元数据，以便团队长期优化路由选择、门禁行为和 Agent 纪律。

### 13.1 Recorded metadata / 记录的元数据
- task summary / 任务摘要
- routing path / 路由路径
- complexity level / 复杂度等级
- gates triggered / 触发的门禁
- return-to-owner events / 回流归属事件
- final verdict / 最终结论
- key risks / 关键风险
- lessons learned / 复盘结论

### 13.2 Task record template / 任务记录模板
Each meaningful task should be recorded with the following fields:

每个有意义的任务都应使用以下字段记录：

- `task_id`
- `task_summary`
- `task_type`
- `complexity_level`
- `routing_path`
- `workflow_mode`
- `final_verdict`
- `return_to_owner`
- `blocking_reasons`
- `risk_types`
- `critical_chain_hit`
- `critical_component_hit`
- `missing_tests`
- `lessons_learned`
- `rule_updates_needed`

### 13.3 Retro output template / 复盘输出模板
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

### 13.4 Retro questions / 复盘问题
- Which route was chosen and why? / 为什么选择这条路由？
- Where did the task return, and why? / 问题回到了哪里、为什么？
- Which gate blocked progress? / 哪个门禁阻断了推进？
- Which agent most often needed correction? / 哪个 Agent 最常需要纠正？
- Which rule or template should be strengthened? / 哪条规则或模板应该加强？

### 13.5 Feedback loop / 反馈闭环
Retro findings should be used to improve:
- agent behavior constraints / Agent 行为约束
- command routing / 命令路由
- playbook gate rules / 执行手册中的门禁规则
- quality thresholds / 质量阈值
- task record template / 任务记录模板

### 13.6 Review retro summary / Review 复盘摘要
`review-agent` should produce a concise retro summary for each completed task so the record can be archived consistently.

`review-agent` 应为每个完成的任务产出简洁的复盘摘要，以便统一归档记录。

Recommended fields:
- task summary / 任务摘要
- routing path / 路由路径
- gates triggered / 触发的门禁
- return-to-owner events / 回流归属事件
- blocking reasons / 阻断原因
- final verdict / 最终结论
- lessons learned / 复盘结论
- rule updates needed / 需要更新的规则

推荐字段：
- 任务摘要
- 路由路径
- 触发的门禁
- 回流归属事件
- 阻断原因
- 最终结论
- 复盘结论
- 需要更新的规则

### 13.7 Structured task record template / 结构化任务记录模板
Every meaningful task should produce a structured record that can be archived, queried, and used for retrospection.

每个有意义的任务都应产出一份结构化记录，便于归档、查询和复盘。

```text
Task ID
Task summary
Task type
Complexity level
Routing path
Workflow mode
Critical chain hit
Critical component hit
Gates triggered
Return-to-owner events
Blocking reasons
Missing tests
Final verdict
Lessons learned
Rule updates needed
```

## 14. Recordable output alignment / 可记录输出对齐

Every agent output should be structured so it can be copied into the task record template with minimal interpretation.

每个 Agent 的输出都应结构化到可以几乎不经解释地填入任务记录模板。

### 14.1 `team-agent`
- Supports: `task_type`, `complexity_level`, `routing_path`, `workflow_mode`, `risk_types`
- Required emphasis: route reason, chosen workflow, return-to-owner hints

- 支持字段：`task_type`、`complexity_level`、`routing_path`、`workflow_mode`、`risk_types`
- 必须强调：路由理由、选择的工作流、回流提示

### 14.2 `spec-agent`
- Supports: `task_summary`, `task_type`, `critical_chain_hit`, `critical_component_hit`, `return_to_owner`
- Required emphasis: scope clarity, constraints, acceptance criteria, route justification

- 支持字段：`task_summary`、`task_type`、`critical_chain_hit`、`critical_component_hit`、`return_to_owner`
- 必须强调：范围清晰度、约束、验收标准、路由依据

### 14.3 `architect-agent`
- Supports: `risk_types`, `critical_chain_hit`, `critical_component_hit`, `blocking_reasons`
- Required emphasis: boundaries, dependencies, implementation order, orchestration safety

- 支持字段：`risk_types`、`critical_chain_hit`、`critical_component_hit`、`blocking_reasons`
- 必须强调：边界、依赖、实现顺序、编排安全性

### 14.4 `implement-agent`
- Supports: `blocking_reasons`, `risk_types`, `critical_chain_hit`, `critical_component_hit`, `lessons_learned`
- Required emphasis: files touched, deviations, self-check summary, main-chain integrity

- 支持字段：`blocking_reasons`、`risk_types`、`critical_chain_hit`、`critical_component_hit`、`lessons_learned`
- 必须强调：修改文件、偏差、自检摘要、主链路完整性

### 14.5 `qa-agent`
- Supports: `missing_tests`, `blocking_reasons`, `critical_chain_hit`, `critical_component_hit`, `final_verdict`, `return_to_owner`
- Required emphasis: test gaps, edge cases, return decision, gate outcome

- 支持字段：`missing_tests`、`blocking_reasons`、`critical_chain_hit`、`critical_component_hit`、`final_verdict`、`return_to_owner`
- 必须强调：测试缺口、边界场景、回流决定、门禁结果

### 14.6 `review-agent`
- Supports: `final_verdict`, `blocking_reasons`, `lessons_learned`, `rule_updates_needed`, `critical_chain_hit`, `critical_component_hit`
- Required emphasis: consolidated judgment, blockers, retrospective value, rule changes

- 支持字段：`final_verdict`、`blocking_reasons`、`lessons_learned`、`rule_updates_needed`、`critical_chain_hit`、`critical_component_hit`
- 必须强调：综合裁决、阻断项、复盘价值、规则变更

### 14.7 `commit-message-agent`
- Supports: `task_summary`, `final_verdict`, `lessons_learned`, `rule_updates_needed`
- Required emphasis: change purpose, main-chain impact, governance meaning

- 支持字段：`task_summary`、`final_verdict`、`lessons_learned`、`rule_updates_needed`
- 必须强调：变更目的、主链路影响、治理意义

## 15. Agent behavior constraints / Agent 行为约束

### 11.1 `team-agent` / 协调总指挥
- Only负责接单、分类和路由，不直接输出实现细节。
- Must先判断是否触及 `ReleasePlan`、`SprintOrchestrator`、`SprintExecutor`、`Governance`、`Observability`、`Suggestion`、`Evolution`。
- 遇到不清晰任务时，先问最少必要问题。
- 输出必须包括：classification / routing / execution plan / risks / next step。

### 11.2 `spec-agent` / 规范编写
- 只负责把需求转成规范，不替代架构拆分。
- 必须显式写出 goal / non-goals / scope / constraints / acceptance criteria。
- 必须判断 OpenSpec 或 Spec-Kit。
- 如果任务涉及主链路，要明确是否触及 `ReleasePlan`、`SprintOrchestrator`、`SprintExecutor`、生命周期状态或治理接入点。

### 11.3 `architect-agent` / 架构拆分
- 只负责拆分、边界和依赖，不写具体实现。
- 必须保护 `ReleasePlan → SprintOrchestrator.execute_release_plan → SprintExecutor` 主链路不被破坏。
- 必须判断是否存在跨层耦合、编排越权或平行流程。
- 对任何 graph / orchestration 修改，只能做编排，不得承担领域职责。

### 11.4 `implement-agent` / 实现
- 只实现已批准的 spec 和 architect 结果，不重定义任务。
- 改动必须最小化，避免无关重构。
- 不能绕过 service / facade / hook / registry / orchestrator。
- 必须保持治理、可观测性、建议和自进化接入方式不变。

### 11.5 `qa-agent` / QA 验证
- 只做验证，不替代 Implementation 修代码。
- 必须明确 pass / fail / loop back。
- 必须检查主链路是否仍然完整，尤其是 `ReleasePlan`、`SprintOrchestrator`、`SprintExecutor`、治理、可观测性、建议和自进化链路。
- 发现回归风险时，必须明确回流到哪个角色。

### 11.6 `review-agent` / 最终审查
- 只做最终汇总，不重复 QA 细节。
- 必须整合架构、编排、QA、生命周期、运行时和交付可用性。
- 冲突时优先保守判断。
- 对关键链路风险必须优先保留阻断级问题。

### 11.7 `commit-message-agent` / 提交信息
- 只负责摘要和提交信息，不做技术审查。
- 必须总结当前变更目的，而不是只列文件。
- 如果变更影响主链路或关键组件，提交信息必须体现这一点。
- 输出必须简短、准确、可直接提交。

## 12. Maintenance / 维护

When adding a new agent, command, or routing rule:
- add it here
- define its trigger conditions
- keep the name aligned with the existing team vocabulary
- update `docs/AI_GOVERNANCE.md` if it affects governance

当新增 Agent、命令或路由规则时：
- 在此补充
- 定义触发条件
- 保持名称与现有团队词汇一致
- 如果影响治理层，则更新 `docs/AI_GOVERNANCE.md`

## 13. Final recommended minimal set / 最终推荐最小集合

### 13.1 Core docs / 核心文档（3 份）
- `AGENTS.md`
- `docs/AI_GOVERNANCE.md`
- `docs/CURSOR_TEAM_PLAYBOOK.md`

### 13.2 Entry docs / 入口说明（2 份）
- `.cursor/README.md`
- `.cursor/commands/README.md`

### 13.3 Core rules / 主规则（2 份）
- `sprintcycle-architecture-orchestration.mdc`
- `team-routing.mdc`

### 13.4 Core commands / 主命令（7 个）
- `/team-command`
- `/spec-command`
- `/architect-command`
- `/implement-command`
- `/qa-command`
- `/review-command`
- `/commit-message-command`
