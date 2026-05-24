"""Application Lifecycle Services - 生命周期服务模块。

包含 Sprint 生命周期相关的所有服务，按职责分组：
- contracts: 契约管理
- execution: 执行生命周期
- delivery: 交付生命周期
- evolution: 进化生命周期
- state_machine: 状态机
- web_orchestration: Web 编排
"""

from .lifecycle_contracts import (
    LifecycleContract,
)
from .lifecycle_contract_assembly_service import LifecycleContractAssemblyService
from .lifecycle_delivery_service import LifecycleDeliveryService
from .lifecycle_evolution_service import LifecycleEvolutionService
from .execution_lifecycle_service import ExecutionLifecycleService
from .lifecycle_state_machine import LifecycleStateMachine
from .web_lifecycle_orchestration_service import WebLifecycleOrchestrationService

__all__ = [
    # Contracts
    "LifecycleContract",
    "LifecycleContractAssemblyService",
    # Lifecycle Services
    "LifecycleDeliveryService",
    "LifecycleEvolutionService",
    "ExecutionLifecycleService",
    # State Machine
    "LifecycleStateMachine",
    # Web Orchestration
    "WebLifecycleOrchestrationService",
]
