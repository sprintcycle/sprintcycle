"""通用接口定义子域"""

from .types import ExecutionStatus, TaskResult, SprintResult
from .execution import ExecutionPlannerProtocol, TaskExecutorProtocol
from .lifecycle_hooks import SprintLifecycleHookProtocol, TaskLifecycleHookProtocol, ExecutionEventProtocol
from .validators import ValidatorProtocol, create_validator, get_validator
from .release_plan_generator import (
    ReleasePlanGeneratorProtocol,
    ReleasePlanParserProtocol,
    ReleasePlanValidatorProtocol,
    ValidationResult,
)
from .version_registry import VersionRegistryProtocol, RollbackManagerProtocol
from .config import ConfigProtocol
from .evaluation import EvaluatorAgentProtocol
from .event_bus import EventType, Event, EventSubscriber, EventBusProtocol, ExecutionEventBackendProtocol
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
from .sandbox import SandboxManagerProtocol, HealthCheckAdapterProtocol, RetryPolicyAdapterProtocol

__all__ = [
    # 核心类型
    "ExecutionStatus",
    "TaskResult",
    "SprintResult",
    # 执行接口
    "ExecutionPlannerProtocol",
    "TaskExecutorProtocol",
    # 生命周期钩子
    "SprintLifecycleHookProtocol",
    "TaskLifecycleHookProtocol",
    "ExecutionEventProtocol",
    # 验证接口
    "ValidatorProtocol",
    "create_validator",
    "get_validator",
    # 生成器接口
    "ReleasePlanGeneratorProtocol",
    "ReleasePlanParserProtocol",
    "ReleasePlanValidatorProtocol",
    "ValidationResult",
    # 版本注册接口
    "VersionRegistryProtocol",
    "RollbackManagerProtocol",
    # 配置接口
    "ConfigProtocol",
    # 评估接口
    "EvaluatorAgentProtocol",
    # 事件总线接口
    "EventType",
    "Event",
    "EventSubscriber",
    "EventBusProtocol",
    "ExecutionEventBackendProtocol",
    # 质量相关
    "QualityLevel",
    "QualityProfile",
    "normalize_quality_level",
    "normalize_quality_profile",
    "runs_pytest",
    "runs_static_gate",
    "runs_coverage_gate",
    "runs_architecture_guard",
    # 沙箱管理接口
    "SandboxManagerProtocol",
    "HealthCheckAdapterProtocol",
    "RetryPolicyAdapterProtocol",
]
