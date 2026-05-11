# SprintCycle 扩展点 / 服务职责地图

本文档给出 SprintCycle 当前的统一扩展点、服务职责边界，以及 `SprintCycle` facade 应保留与下沉的责任划分。

目标：

- 让扩展点从“代码里到处是 hook-like call”收敛为统一协议
- 让服务职责清晰、可替换、可测试
- 让 `SprintCycle` 继续回归真正的 facade：只做入口组合与薄转发

---

## 1. 总体原则

### 1.1 `SprintCycle` 应只做

- 统一入口聚合
- 参数归一化
- 跨服务薄转发
- 结果汇总与兼容适配
- 少量边界错误处理

### 1.2 `SprintCycle` 不应承担

- 具体业务流编排
- dashboard / console payload 细节组装
- 执行状态推进细节
- suggestion / governance / observability 的内部规则实现
- 通过大量 `try/except` 充当隐式兼容层

---

## 2. 统一扩展点协议

当前系统使用统一 hook / domain event 协议，定义在：`sprintcycle/hooks.py`

### 2.1 协议语义

- `before_*`：主流程前置钩子，可校验、补全、阻断
- `after_*`：主流程成功后钩子，主要做副作用
- `on_*_failed`：主流程失败后钩子，主要做审计、告警、补偿
- `emit_domain_event(...)`：领域事件统一出口

### 2.2 标准模型

- `HookContext`
- `HookResult`
- `HookDefinition`
- `HookRegistry`
- `HookPhase`
- `HookPolicy`

### 2.3 失败策略

- `fail_open`：失败不阻断主流程
- `fail_closed`：失败阻断主流程
- `compensate`：失败后由调用方或订阅方补偿

### 2.4 主流程消费规则

- `before_*` 的返回值会被主流程消费
- `after_*` / `on_*_failed` 通常不被主流程消费
- `emit_domain_event(...)` 由订阅者消费，不直接驱动主流程

---

## 3. 扩展点注册与挂钩边界

### 3.1 谁能挂钩

允许通过 `HookRegistry` 显式注册的主体：

- 内部业务服务
- composition root / 启动装配层
- 受控插件

### 3.2 不建议的做法

- 在业务代码中随手添加匿名 hook-like call
- 用普通 `try/except` 伪装钩子机制
- 直接 monkey patch 主流程对象
- 让事件订阅器修改主流程控制权

---

## 4. 服务职责地图

### 4.1 `ExecutionLifecycleService`

路径：`sprintcycle/services/execution_lifecycle_service.py`

#### 职责

- 执行启动编排
- pre-run gate
- execution event 记录
- runtime registry 更新
- execution detail / replay / events 查询

#### 主要方法

- `start_execution_run(...)`
- `execution_events(...)`
- `replay_execution(...)`
- `execution_detail(...)`
- `runtime_latest()`
- `runtime_update(...)`

#### 扩展点

- `before_execution.start`
- `after_execution.start`
- `on_execution.start_failed`
- `emit_domain_event("execution.started")`
- `emit_domain_event("execution.start_failed")`

---

### 4.2 `SuggestionApplicationService`

路径：`sprintcycle/services/suggestion_application_service.py`

#### 职责

- suggestion 生命周期
- review / approve / reject / archive
- suggestion promotion 到 HITL
- 从 execution event 生成 suggestion

#### 主要方法

- `suggestion_review(...)`
- `review_suggestion(...)`
- `approve_suggestion(...)`
- `reject_suggestion(...)`
- `promote_suggestion_to_hitl(...)`
- `attach_suggestion_replay(...)`
- `suggestion_approve(...)`
- `suggestion_reject(...)`
- `suggestion_archive(...)`
- `create_suggestion_from_execution_event(...)`

#### 扩展点

- `before_suggestion.review`
- `after_suggestion.review`
- `before_suggestion.approve`
- `after_suggestion.approve`
- `before_suggestion.reject`
- `after_suggestion.reject`
- `before_suggestion.promote_to_hitl`
- `after_suggestion.promote_to_hitl`
- `emit_domain_event("suggestion.*")`

---

### 4.3 `GovernanceOrchestrationService`

路径：`sprintcycle/services/governance_orchestration_service.py`

#### 职责

- governance check 编排
- planning / review gate 调用
- HITL pending / history / summary / show 查询
- governance 报告转换

#### 主要方法

- `governance_check(...)`
- `pending(...)`
- `history(...)`
- `summary(...)`
- `show(...)`

#### 扩展点

- `before_governance.check`
- `after_governance.check`
- `on_governance.check_failed`
- `emit_domain_event("governance.checked")`
- `emit_domain_event("governance.check_failed")`

---

### 4.4 `ObservabilityService`

路径：`sprintcycle/services/observability_service.py`

#### 职责

- 事件记录
- trace / replay 构造
- 观测数据查询
- 作为 execution / governance / dashboard 的观测读侧支撑

#### 主要方法

- `record_event(...)`
- `list_events()`
- `trace(...)`
- `replay(...)`
- `pending(...)`
- `pending_async(...)`
- `execution_detail(...)`

#### 说明

该服务以读侧和事件记录为主，不承载业务裁决。

---

### 4.5 `PlatformSummaryService`

路径：`sprintcycle/services/platform_summary_service.py`

#### 职责

- platform overview
- console overview
- dashboard / workspace 聚合
- fitness / deploy / governance / fix 视图组织

#### 主要方法

- `platform_overview()`
- `platform_spec()`
- `fitness_payload(...)`
- `fitness_view(...)`
- `deploy_view(...)`
- `governance_view(...)`
- `fix_view(...)`
- `console_overview(...)`
- `execution_detail(...)`
- `platform_workspace(...)`
- `execution_workspace(...)`

#### 说明

该服务负责“聚合与呈现”，不负责领域规则。

---

## 5. `SprintCycle` 当前建议保留的职责

### 5.1 适合保留

- facade 初始化与依赖装配
- 对外统一入口方法
- 少量参数清洗
- 兼容老接口的薄转发
- 汇总多个 service 的结果

### 5.2 建议继续下沉或保持薄转发

- `start_execution_run(...)` → `ExecutionLifecycleService`
- `execution_detail(...)` → `ExecutionLifecycleService` / `PlatformSummaryService`
- `console_overview(...)` → `PlatformSummaryService`
- `platform_overview(...)` → `PlatformSummaryService`
- `governance_check(...)` → `GovernanceOrchestrationService`
- `observability_*` → `ObservabilityService` / `GovernanceOrchestrationService`
- `suggestion_*` → `SuggestionApplicationService`

---

## 6. 组件间关系

### 6.1 Facade 层

- `SprintCycle`
- `GovernanceFacade`
- `SuggestionFacade`
- `ObservabilityFacade`

作用：统一入口、薄协调、最小暴露。

### 6.2 应用服务层

- `ExecutionLifecycleService`
- `SuggestionApplicationService`
- `GovernanceOrchestrationService`
- `ObservabilityService`
- `PlatformSummaryService`

作用：编排具体能力，但不将业务规则散落到 facade。

### 6.3 领域 / 基础设施层

- `ExecutionEngine`
- `RuntimeRegistry`
- `state_store`
- `event_bus`
- `ArchGuard`
- `SuggestionStore`
- `GovernanceRunner`

作用：提供具体领域能力与持久化实现。

---

## 7. 建议的扩展点命名规范

### 7.1 命名形式

- `before_<domain>.<action>`
- `after_<domain>.<action>`
- `on_<domain>.<action>_failed`
- `emit_domain_event("<domain>.<event>")`

### 7.2 示例

- `before_execution.start`
- `after_execution.start`
- `execution.started`
- `on_execution.start_failed`

- `before_suggestion.approve`
- `after_suggestion.approve`
- `suggestion.approved`
- `on_suggestion.approve_failed`

- `before_governance.check`
- `after_governance.check`
- `governance.checked`
- `on_governance.check_failed`

---

## 8. 使用建议

### 8.1 新增扩展点时

优先遵循：

1. 能否用 `before/after/failed` 表达清楚
2. 是否需要领域事件
3. 是否应放入某个 service，而不是 `SprintCycle`
4. 是否需要 `fail_closed` 语义

### 8.2 新增逻辑时

- 优先放进对应 service
- facade 只保留薄转发
- 如果是跨域流程，明确是哪一个 application service 负责编排

---

## 9. 迁移判断标准

如果某段代码满足以下任一条件，通常就应该从 `SprintCycle` 下沉：

- 需要 2 个以上下游能力协同
- 有明显的成功 / 失败 / 后置分支
- 需要对外暴露 dashboard / console payload
- 需要统一 hook / event 行为
- 需要显式的失败政策

---

## 10. 当前结论

SprintCycle 的职责边界已经比之前清晰很多。后续工作的重点不是继续往 `SprintCycle` 里加能力，而是持续：

- 收紧 facade
- 统一扩展点协议
- 让 service 承载编排
- 让领域层承载规则
- 让 event / hook 机制保持显式、可测试、可治理
