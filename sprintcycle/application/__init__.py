"""
SprintCycle Application Layer
=============================

统一的应用服务层入口，导出所有核心服务。

Architecture:
    L6 (Application Services)
    ├── SprintOrchestrator      - Sprint 编排核心
    ├── HTTPServices            - HTTP 层服务工厂
    ├── Evolution Loop         - 意图演进循环
    ├── Evolution Factories     - Evolution 工厂函数
    └── Protocols              - 接口定义
"""

from sprintcycle.domain.generic.interfaces.protocols import (
    EvolutionProtocol,
    FeedbackProtocol,
    LifecycleProtocol,
    OrchestrationProtocol,
)
from sprintcycle.application.factories.http import HTTPServices, create_http_services
from sprintcycle.application.orchestration.sprint_orchestrator import SprintOrchestrator
from sprintcycle.application.factories.evolution import create_default_evolution_facade

__all__ = [
    # Core
    "SprintOrchestrator",
    # HTTP Services
    "HTTPServices",
    "create_http_services",
    # Evolution Factories
    "create_default_evolution_facade",
    # Protocols
    "OrchestrationProtocol",
    "LifecycleProtocol",
    "EvolutionProtocol",
    "FeedbackProtocol",
]
