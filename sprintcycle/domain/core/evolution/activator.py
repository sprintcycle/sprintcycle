"""Evolution activator - 使用接口协议"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from sprintcycle.domain.core.evolution.runtime_state import (
    ActivationGuardResult,
    EvolutionHealthState,
    RetryPolicyConfig,
)
from sprintcycle.domain.generic.interfaces import (
    HealthCheckAdapterProtocol,
    RetryPolicyAdapterProtocol,
)

LoopStarter = Callable[[str], None]
GuardEvaluator = Callable[[], ActivationGuardResult]


@dataclass(slots=True)
class EvolutionActivator:
    """演化激活器 - 使用协议接口"""

    guard_evaluator: GuardEvaluator
    loop_starter: LoopStarter
    health_check: HealthCheckAdapterProtocol = field(default_factory=lambda: DefaultHealthCheckAdapter())
    retry_policy: RetryPolicyAdapterProtocol = field(default_factory=lambda: DefaultRetryPolicyAdapter())
    retry_config: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)
    health_state: EvolutionHealthState = field(default_factory=EvolutionHealthState)
    session_id: Optional[str] = None


# 默认实现（从 Infrastructure 层导入）
class DefaultHealthCheckAdapter:
    """默认健康检查适配器"""

    def check(self) -> bool:
        return True


class DefaultRetryPolicyAdapter:
    """默认重试策略适配器"""

    def execute_with_retry(self, func: Callable, max_retries: int = 3) -> Any:
        last_error = None
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue
        if last_error:
            raise last_error


__all__ = ["EvolutionActivator"]
