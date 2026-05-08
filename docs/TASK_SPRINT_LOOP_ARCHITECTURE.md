# SprintCycle 内层 Task Loop 与外层 Sprint Loop 架构设计

> 目标：把「单任务执行」与「Sprint 级编排」拆开，保留现有行为兼容，同时为后续治理、质量门禁、测量、回滚、重试、HITL 等能力预留清晰扩展点。

## 1. 设计目标

1. **边界清晰**：
   - 内层 `task loop` 只负责单个任务的执行、验证、修复与结果回收。
   - 外层 `sprint loop` 只负责多个 Sprint 的顺序编排、Sprint 级评估与反馈决策。
2. **扩展点稳定**：
   - 新的 agent、新的 task 后处理、新的 Sprint 后评估、新的重试策略都应该以“增加组件”为主，而不是修改核心流程。
3. **默认行为不变**：
   - 现有 CLI/API/Dashboard 的调用方式保持兼容。
   - 现有 task hooks / sprint hooks / feedback loop 仍可工作。
4. **职责单一**：
   - `SprintExecutor` 专注执行。
   - `SprintOrchestrator` 专注编排。
   - agent 专注产出内容。

## 2. 双层循环模型

### 2.1 内层 task loop

**职责**：把一个 `SprintBacklogItem` 做完。

推荐生命周期：

1. 组装 task context
2. 选择 executor / agent
3. 执行 task
4. 如失败则按策略进入验证-修复重试
5. 触发 task hooks
6. 产出 `TaskResult`

**典型可变点**：

- task 执行器类型（coder / tester / architect / regression_tester / future custom agent）
- 重试策略（重试次数、重试条件、是否保留上下文）
- task 后 hook（治理、统计、审计、埋点）

**不应承担的职责**：

- Sprint 之间的反馈决策
- Sprint 后测量 / 知识卡片沉淀
- ReleasePlan 级别的编排决策

### 2.2 外层 sprint loop

**职责**：把多个 Sprint 依次执行，并决定是否继续、重试、跳过或中止。

推荐生命周期：

1. 进入 Sprint 前 hook
2. 执行当前 Sprint 的 task loop
3. 收集 Sprint 结果
4. 做 Sprint 级反馈 / 评估 / 测量
5. 触发 Sprint 后 hook
6. 进入下一个 Sprint 或终止

**典型可变点**：

- Sprint 前检查（规划、依赖、治理、HITL）
- Sprint 后测量（质量测量、知识沉淀、事件发射）
- Sprint 失败策略（重试 / 中止 / 继续）
- Sprint 结束后的通知、报告、持久化

**不应承担的职责**：

- 单个 task 的执行细节
- 单个 agent 的 prompt 构造细节
- coder 内部验证-修复循环

### 2.3 Release finalization loop

**职责**：当所有 Sprint 执行结束后，对整个 Release 做最终测试、最终评估、必要修正与发布判定。

推荐生命周期：

1. 收集所有 Sprint 的最终结果
2. 运行 Release 级全量测试 / 集成测试 / 回归测试
3. 运行 Release 级质量评估与门禁判定
4. 如发现问题，生成收尾修复任务或回流到补丁 Sprint
5. 产出最终发布结论（ready / blocked / needs another iteration）

**典型可变点**：

- 全量测试策略（pytest / e2e / smoke / compose healthcheck）
- 最终质量门禁（coverage、静态分析、架构约束、治理规则）
- 修正策略（补丁任务、收尾 Sprint、人工确认）
- 发布判定与交付报告

**不应承担的职责**：

- 重复执行已经完成的 Sprint
- 重新定义每个 Sprint 的局部目标
- 再次拆分 backlog

### 2.4 三层关系总结

- `task loop` 解决“一个任务怎么做完”
- `sprint loop` 解决“一个 Sprint 怎么做完并决定下一步”
- `release finalization loop` 解决“整个 Release 怎么验收并能否交付”

## 3. 现有代码边界映射

### 3.1 `sprintcycle/execution/sprint_executor.py`

建议保留：

- `execute_sprint(...)`
- `execute_sprints(...)`
- `execute_sprint_parallel(...)`
- `_execute_task(...)`
- `_execute_coder_task(...)`
- task hooks 调用
- task 结果聚合

建议抽出：

- 任务内重试策略
- Sprint 失败后的重试策略

### 3.2 `sprintcycle/orchestration/sprint_orchestrator.py`

建议保留：

- `execute_release_plan(...)`
- `resume_from_sprint(...)`
- Sprint hooks 组合
- Sprint 后测量与知识卡片
- Sprint 级失败策略

建议不要放入：

- task 执行细节
- coder agent 的重试逻辑
- 任务级 context 拼接规则

## 4. 推荐抽象

### 4.1 Task 层抽象

建议新增：

- `TaskExecutionPolicy`
- `TaskRetryPolicy`
- `TaskExecutionCoordinator`

它们负责：

- 决定是否重试
- 决定重试上下文如何构造
- 决定失败后是否把错误提升给 Sprint 层

### 4.2 Sprint 层抽象

建议新增：

- `SprintRetryPolicy`
- `SprintEvaluationPolicy`
- `SprintFeedbackPolicy`

它们负责：

- 是否根据反馈重试当前 Sprint
- 是否中止后续 Sprint
- 是否生成额外的评估上下文

## 5. 已落地的扩展点

当前代码已经具备以下扩展点：

- `TaskLifecycleHooks`
- `SprintLifecycleHooks`
- `FeedbackLoop`
- `EventBus`
- `GovernanceTaskLifecycleHooks`
- `KnowledgeInjectionHook`
- `GovernanceSprintHooks`

本次重构的方向是：

- 不推翻这些钩子
- 让它们落在更清晰的层级上
- 把策略逻辑从执行流程里抽出来

## 6. 推荐重构顺序

### 第 1 步：抽策略，不改行为

- 把 task verify-fix 抽成独立 policy
- 把 sprint retry 抽成独立 policy
- 让 `SprintExecutor` 只调用 policy

### 第 2 步：收窄执行器职责

- `SprintExecutor` 只保留 task loop
- Sprint 后决策和评估尽量归到 orchestrator

### 第 3 步：统一上下文

- 统一 task / sprint context 的字段来源
- 减少 executor / orchestrator 对同一字段的重复拼装

## 7. 验收标准

- task loop 的所有行为可以在单个组件内讲清楚
- sprint loop 的所有行为可以在单个组件内讲清楚
- release finalization loop 的所有行为可以在单个组件内讲清楚
- task 级重试和 sprint 级重试互不混淆
- finalization 只做 Release 级终检，不重复执行已完成的 Sprint
- 新增一个 agent、一个 Sprint 级检查或一个 Release 终检，不需要改核心循环结构
- 现有测试通过或仅做兼容性调整
