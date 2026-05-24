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
)

from .types import (
    ExecutionStatus,
    TaskResult,
    SprintResult,
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

from sprintcycle.domain.governance.interfaces.governance import (
    GovernanceCheckResult,
    GovernanceCheckProtocol,
    ArchitectureCheckProtocol,
    QualityGateProtocol,
)

from .validators import (
    ValidatorProtocol,
    create_validator,
    get_validator,
)

from .quality import (
    QualityLevel,
    QualityProfile,
    normalize_quality_level,
    normalize_quality_profile,
    runs_pytest,
    runs_static_gate,
    runs_coverage_gate,
    runs_architecture_guard,
)

from .config import (
    ConfigProtocol,
    load_project_config,
)

from .evaluation import (
    EvaluatorAgentProtocol,
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
    "ExecutionStatus",
    "TaskResult",
    "SprintResult",
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
    # Validators
    "ValidatorProtocol",
    "create_validator",
    "get_validator",
    # Quality
    "QualityLevel",
    "QualityProfile",
    "normalize_quality_level",
    "normalize_quality_profile",
    "runs_pytest",
    "runs_static_gate",
    "runs_coverage_gate",
    "runs_architecture_guard",
    # Config
    "ConfigProtocol",
    "load_project_config",
    # Evaluation
    "EvaluatorAgentProtocol",
]
