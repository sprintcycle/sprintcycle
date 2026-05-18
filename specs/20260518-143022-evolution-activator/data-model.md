# Data Model: EvolutionActivator（数据模型：自进化激活器）

## `ActivationState`（激活状态）
Represents the runtime lifecycle state of the activator.（表示激活器的运行时生命周期状态。）

**Values**（取值）:
- `inactive`：not yet activated or explicitly blocked（未激活或被显式阻断）
- `activating`：activation is in progress（激活进行中）
- `active`：evolution loop is running（自进化循环运行中）
- `degraded`：runtime is unhealthy and loop progression is paused（运行时不健康，循环推进暂停）
- `recovering`：recovery validation is in progress（恢复校验进行中）

## `ActivationReasonCode`（激活原因码）
Enumerates explicit outcome reasons returned by the activator.（枚举激活器返回的显式结果原因。）

- `ok`
- `blocked_guard`
- `blocked_already_active`
- `blocked_concurrent_session`
- `retrying_transient_failure`
- `retry_exhausted`
- `health_unhealthy`
- `degraded_by_failures`
- `recovered`

## `ActivationGuardResult`（激活守卫结果）
Represents whether activation may proceed and why it was blocked.（表示是否可继续激活，以及阻断原因。）

**Fields**（字段）:
- `allowed: bool`
- `reason: ActivationReasonCode`
- `details: dict[str, Any]`

## `RetryPolicyConfig`（重试策略配置）
Describes bounded retry behavior for transient failures.（描述瞬时失败的有界重试行为。）

**Fields**（字段）:
- `max_attempts`
- `backoff_seconds`
- `backoff_multiplier`
- `max_backoff_seconds`

## `RetryDecision`（重试决策）
Represents the policy result for a single activation attempt.（表示单次激活尝试的策略结果。）

**Fields**（字段）:
- `should_retry`
- `attempt`
- `reason`
- `delay_seconds`
- `details`

## `EvolutionHealthSnapshot`（运行时健康快照）
Represents the observed health state after a check.（表示一次健康检查后的观测快照。）

**Fields**（字段）:
- `healthy`
- `state`
- `reason`
- `details`

## `EvolutionHealthState`（运行时健康状态）
Tracks the current runtime condition and recovery context.（跟踪当前运行时状况与恢复上下文。）

**Fields**（字段）:
- `state`
- `last_snapshot`
- `consecutive_failures`
- `degraded`
- `active_session_id`
- `details`

## `ActivationDecision`（激活决策）
The explicit outcome returned from `activate()` and `recover()`.（`activate()` 和 `recover()` 返回的显式结果。）

**Fields**（字段）:
- `state`
- `reason`
- `message`
- `details`

## Relationships（关系）
- `EvolutionActivator` consumes `ActivationGuardResult`, `RetryPolicyConfig`, and `EvolutionHealthSnapshot`.（`EvolutionActivator` 消费 `ActivationGuardResult`、`RetryPolicyConfig` 和 `EvolutionHealthSnapshot`。）
- `EvolutionHealthState` is updated by health checks and activation outcomes.（`EvolutionHealthState` 由健康检查和激活结果更新。）
- Recovery is only allowed after guard and health checks pass again.（只有在守卫与健康检查重新通过后才允许恢复。）
