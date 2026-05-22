"""
Domain Interfaces - 领域接口层

定义所有领域相关的协议/接口，由外层（Infrastructure、Execution、Governance）实现。

使用方式：
    from sprintcycle.domain.interfaces import VersionRegistryProtocol
    
    class EvolutionController:
        def __init__(self, registry: VersionRegistryProtocol):
            self._registry = registry
"""

from .version_registry import (
    VersionRegistryProtocol,
    RollbackManagerProtocol,
)

from .release_plan_generator import (
    ReleasePlanGeneratorProtocol,
    ReleasePlanParserProtocol,
    ReleasePlanValidatorProtocol,
    ValidationResult,
)

from .event_bus import (
    EventType,
    Event,
    EventSubscriber,
    EventBusProtocol,
    ExecutionEventBackendProtocol,
)

from .execution import (
    ExecutionPlannerProtocol,
    TaskExecutorProtocol,
    TaskResult,
)

from .sandbox import (
    SandboxManagerProtocol,
    HealthCheckAdapterProtocol,
    RetryPolicyAdapterProtocol,
)

__all__ = [
    # Version Registry
    "VersionRegistryProtocol",
    "RollbackManagerProtocol",
    # Release Plan
    "ReleasePlanGeneratorProtocol",
    "ReleasePlanParserProtocol",
    "ReleasePlanValidatorProtocol",
    "ValidationResult",
    # Event Bus
    "EventType",
    "Event",
    "EventSubscriber",
    "EventBusProtocol",
    "ExecutionEventBackendProtocol",
    # Execution
    "ExecutionPlannerProtocol",
    "TaskExecutorProtocol",
    "TaskResult",
    # Sandbox
    "SandboxManagerProtocol",
    "HealthCheckAdapterProtocol",
    "RetryPolicyAdapterProtocol",
]
