"""
Domain Interfaces - 领域接口层

定义所有领域相关的协议/接口，由外层（Infrastructure、Execution、Governance）实现。
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

from .lifecycle_hooks import (
    SprintLifecycleHookProtocol,
    TaskLifecycleHookProtocol,
    ExecutionEventProtocol,
)

from .governance import (
    GovernanceCheckResult,
    GovernanceCheckProtocol,
    ArchitectureCheckProtocol,
    QualityGateProtocol,
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
    # Lifecycle Hooks
    "SprintLifecycleHookProtocol",
    "TaskLifecycleHookProtocol",
    "ExecutionEventProtocol",
    # Governance
    "GovernanceCheckResult",
    "GovernanceCheckProtocol",
    "ArchitectureCheckProtocol",
    "QualityGateProtocol",
]
