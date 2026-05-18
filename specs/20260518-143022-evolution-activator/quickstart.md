# Quickstart: EvolutionActivator（快速开始：自进化激活器）

1. Instantiate `EvolutionActivator` with a guard evaluator and loop starter.（使用守卫评估器和循环启动器实例化 `EvolutionActivator`。）
2. Call `activate()` and verify the returned `ActivationDecision`.（调用 `activate()` 并检查返回的 `ActivationDecision`。）
3. Confirm the activator enters `active` when guards pass.（确认在守卫通过时激活器进入 `active`。）
4. Simulate a transient loop failure and confirm the retry policy is used before degradation.（模拟瞬时循环失败并确认在降级前使用了重试策略。）
5. Force a persistent failure and confirm the activator transitions to `degraded`.（强制持续失败并确认激活器迁移到 `degraded`。）
6. Reset the dependencies to healthy and call `recover()` to return to `active`.（将依赖恢复为健康后调用 `recover()` 回到 `active`。）

## Minimal verification example（最小验证示例）
- Use mocked collaborators for guards, health checks, and retry policy.（使用 mock 的守卫、健康检查和重试策略协作者。）
- Verify the activator returns explicit reason codes for blocked, degraded, and recovered states.（验证激活器会为阻断、降级和恢复状态返回显式原因码。）
- Verify no duplicate session is started if `activate()` is called twice.（验证如果连续调用 `activate()`，不会启动重复 session。）
