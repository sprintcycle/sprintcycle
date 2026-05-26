"""
SprintCycle Application Layer
=============================

统一的应用服务层入口，导出所有核心服务。

Architecture:
    L6 (Application Services)
    ├── SprintOrchestrator      - Sprint 编排核心
    └── Protocols              - 接口定义

注意：组合根已迁移到 composition/ 层，application 层不再负责依赖注入。
"""

from sprintcycle.domain.generic.interfaces.protocols import (
    EvolutionProtocol,
    FeedbackProtocol,
    LifecycleProtocol,
    OrchestrationProtocol,
)
from sprintcycle.application.orchestration.sprint_orchestrator import SprintOrchestrator

__all__ = [
    # Core
    "SprintOrchestrator",
    # Protocols
    "OrchestrationProtocol",
    "LifecycleProtocol",
    "EvolutionProtocol",
    "FeedbackProtocol",
]
