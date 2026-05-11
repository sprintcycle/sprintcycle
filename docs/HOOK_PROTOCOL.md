# SprintCycle 统一扩展点协议

本文档说明 SprintCycle 当前的统一 hook / domain event 协议，用于替代系统中分散的 hook-like call。

## 目标

- 将扩展点从隐式散点收敛为统一模型
- 明确谁能挂钩、何时挂钩、失败如何处理
- 让扩展点对主流程的影响可预测、可测试、可治理
- 避免 hook 变成散落在业务代码里的“兼容逻辑”

## 协议模型

### HookPhase

- `before`
- `after`
- `failed`

### HookPolicy

- `fail_open`
- `fail_closed`
- `compensate`

### HookContext

统一上下文对象，至少包含：

- `domain`
- `action`
- `subject_id`
- `execution_id`
- `project_path`
- `payload`
- `metadata`
- `trace_id`

### HookResult

统一钩子返回对象，至少包含：

- `ok`
- `blocked`
- `mutated_context`
- `message`
- `data`

### HookDefinition

统一 hook 定义对象，至少包含：

- `name`
- `domain`
- `action`
- `phase`
- `policy`
- `handler`
- `owner`

### HookRegistry

统一注册与触发入口：

- `register(...)`
- `register_event_handler(...)`
- `emit(...)`
- `emit_domain_event(...)`

## 谁能挂钩

允许通过 `HookRegistry` 显式注册的主体挂钩，通常包括：

- 内部业务服务
- composition root / 启动装配层
- 受控插件

不建议在业务代码中直接散落匿名 hook-like call。

## 挂钩时机

### `before_*`
主流程开始前。

用途：

- 参数检查
- 上下文补全
- 风险拦截
- 门禁校验

### `after_*`
主流程成功后。

用途：

- 记录审计
- 触发通知
- 派生事件
- 统计埋点

### `on_*_failed`
主流程失败后。

用途：

- 记录故障
- 生成告警
- 触发补偿
- 失败归因

### `emit_domain_event(...)`
领域事件发布。

用途：

- 将状态变化显式广播给订阅方
- 解耦副作用与主流程

## 失败语义

### `fail_closed`

失败即阻断主流程。

适用场景：

- 安全门禁
- 合规门禁
- 关键前置校验

### `fail_open`

钩子失败不阻断主流程，只记录或观察。

适用场景：

- 日志
- 观测
- 埋点
- 非关键通知

### `compensate`

钩子失败后由调用方或订阅者执行补偿。

适用场景：

- 半成功流程
- 外部依赖联动
- 需要回滚/修复的动作

## 是否影响主流程

默认规则：

- `before_*` 可能影响主流程
- `after_*` 默认不影响主流程
- `on_*_failed` 不改变主流程失败事实
- `emit_domain_event(...)` 默认不阻断主流程

只有 `before + fail_closed` 应作为默认可阻断路径。

## 返回值是否被消费

### `before_*`
会被主流程消费。

可以：

- 阻断主流程
- 传回修改后的上下文
- 附带校验结果

### `after_*`
通常不被主流程消费。

主要用于副作用与观测。

### `on_*_failed`
通常不被主流程消费。

主要用于故障处理与审计。

### `emit_domain_event(...)`
不依赖返回值驱动主流程。

由订阅者自行消费事件。

## 已接入的关键链路

当前统一协议已接入以下主链路：

- ExecutionLifecycleService
- SuggestionApplicationService
- GovernanceOrchestrationService

## 例子

### 执行启动

- `before_execution.start`
- `after_execution.start`
- `execution.started`
- `execution.start_failed`

### Suggestion 审批 / 推进

- `before_suggestion.approve`
- `after_suggestion.approve`
- `suggestion.approved`
- `suggestion.approve_failed`

### 治理检查

- `before_governance.check`
- `after_governance.check`
- `governance.checked`
- `governance.check_failed`

## 推荐使用方式

1. 在 composition root 创建 `HookRegistry`
2. 注册内部 hook 和事件订阅器
3. 将 registry 注入到关键 service
4. 仅在 service 边界触发统一协议
5. 不在 facade 内部散落新的 hook-like call

## 约束

- 不要绕过协议直接 monkey patch 主流程
- 不要在 `after_*` 里返回会影响主流程的隐式值
- 不要用普通 `try/except` 伪装 hook 机制
- 不要让事件订阅器修改主流程控制权

## 当前结论

统一扩展点协议的目的，不是增加回调数量，而是让扩展点的语义、失败策略和主流程关系都可预测。
