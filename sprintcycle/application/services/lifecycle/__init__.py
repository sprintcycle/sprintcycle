"""Application Lifecycle Services - 生命周期服务模块。

包含 Sprint 生命周期相关的所有服务，按职责分组：
- root_services: 新架构服务（推荐使用）
- web_orchestration: Web 编排
- delivery: 交付生命周期
- evolution: 进化生命周期
- execution: 执行生命周期

已完全迁移到新架构：LifecycleRoot + LifecycleStateMachineService
"""

# 新架构核心导出
from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
    LifecycleStateMachineService,
)

# 应用层服务
from .lifecycle_contract_assembly_service import LifecycleContractAssemblyService
from .lifecycle_delivery_service import LifecycleDeliveryService
from .lifecycle_evolution_service import LifecycleEvolutionService
from .execution_lifecycle_service import ExecutionLifecycleService
from .web_lifecycle_orchestration_service import WebLifecycleOrchestrationService
from .lifecycle_root_services import LifecycleRootService, WebLifecycleRootOrchestrationService

__all__ = [
    # 新架构核心
    "LifecycleRoot",
    "LifecycleStage",
    "LifecycleStatus",
    "create_lifecycle",
    "LifecycleStateMachineService",
    # 新架构服务（推荐使用）
    "LifecycleRootService",
    "WebLifecycleRootOrchestrationService",
    # 应用层服务（内部已使用新架构）
    "LifecycleContractAssemblyService",
    "LifecycleDeliveryService",
    "LifecycleEvolutionService",
    "ExecutionLifecycleService",
    "WebLifecycleOrchestrationService",
]
