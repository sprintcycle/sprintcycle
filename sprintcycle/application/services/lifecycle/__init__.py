"""Application Lifecycle Services - 生命周期服务模块。

职责拆分（DDD+六边形架构）：
- LifecycleRootService: 聚合根服务
- WebLifecycleOrchestrationService: Web 请求编排
- DeliveryService: 交付生命周期 - 合并了运行时/治理/发布
- RecoveryLifecycleService: 恢复流程编排
- ExecutionLifecycleService: 执行启动与追踪
- LifecycleEvolutionService: 演化版本管理
"""

from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleSubstage,
    LifecycleStatus,
    create_lifecycle,
    LifecycleStateMachine,
)

from .lifecycle_evolution_service import LifecycleEvolutionService
from .execution_lifecycle_service import ExecutionLifecycleService
from .web_lifecycle_orchestration_service import WebLifecycleOrchestrationService
from .lifecycle_root_services import LifecycleRootService
from .recovery_lifecycle_service import RecoveryLifecycleService
from .delivery_service import DeliveryService

__all__ = [
    "LifecycleRoot",
    "LifecycleSubstage",
    "LifecycleStatus",
    "create_lifecycle",
    "LifecycleStateMachine",
    "LifecycleRootService",
    "LifecycleEvolutionService",
    "ExecutionLifecycleService",
    "WebLifecycleOrchestrationService",
    "RecoveryLifecycleService",
    "DeliveryService",
]
