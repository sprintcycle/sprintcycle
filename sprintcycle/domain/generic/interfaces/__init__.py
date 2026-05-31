"""通用接口定义子域 (Generic Interfaces)

**职责边界:**
- 定义领域层内部使用的通用协议和抽象
- 子域间共享的接口定义（非外部依赖）
- 领域服务之间的协作契约

**与 domain/ports 的区别:**
- `domain/ports/`: 六边形架构的外部端口，定义与外部系统的交互协议
- `domain/generic/interfaces/`: 领域层内部的通用接口，定义子域间的协作契约

**接口分类:**
- 执行层接口: ExecutionPlannerProtocol, TaskExecutorProtocol
- 生命周期钩子: SprintLifecycleHookProtocol, TaskLifecycleHookProtocol
- 验证接口: ValidatorProtocol
- 生成器接口: ReleasePlanGeneratorProtocol
- 事件总线: EventBusProtocol
- 质量评估: QualityLevel, QualityProfile
- 沙箱管理: SandboxManagerProtocol
"""

from .types import ExecutionStatus, TaskResult, SprintResult
from .execution import ExecutionPlannerProtocol, TaskExecutorProtocol
from .lifecycle_hooks import ExecutionEventProtocol
from .hook_factory import HookFactory, ChainedHooks
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
    # 执行接口（子域内协作）
    "ExecutionPlannerProtocol",
    "TaskExecutorProtocol",
    # 生命周期钩子（子域内协作）
    "SprintLifecycleHookProtocol",
    "TaskLifecycleHookProtocol",
    "ExecutionEventProtocol",
    # 验证接口（子域内协作）
    "ValidatorProtocol",
    "create_validator",
    "get_validator",
    # 生成器接口（子域内协作）
    "ReleasePlanGeneratorProtocol",
    "ReleasePlanParserProtocol",
    "ReleasePlanValidatorProtocol",
    "ValidationResult",
    # 版本注册接口（子域内协作）
    "VersionRegistryProtocol",
    "RollbackManagerProtocol",
    # 配置接口（子域内协作）
    "ConfigProtocol",
    # 评估接口（子域内协作）
    "EvaluatorAgentProtocol",
    # 事件总线接口（子域内协作）
    "EventType",
    "Event",
    "EventSubscriber",
    "EventBusProtocol",
    "ExecutionEventBackendProtocol",
    # 质量相关（子域内协作）
    "QualityLevel",
    "QualityProfile",
    "normalize_quality_level",
    "normalize_quality_profile",
    "runs_pytest",
    "runs_static_gate",
    "runs_coverage_gate",
    "runs_architecture_guard",
    # 沙箱管理接口（子域内协作）
    "SandboxManagerProtocol",
    "HealthCheckAdapterProtocol",
    "RetryPolicyAdapterProtocol",
]
