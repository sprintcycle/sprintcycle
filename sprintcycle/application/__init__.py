"""
SprintCycle Application Layer
=============================

统一的应用服务层入口，导出所有核心服务。

Architecture:
    L6 (Application Services)
    ├── SprintOrchestrator      - Sprint 编排核心
    ├── HTTPServices            - HTTP 层服务工厂
    ├── Evolution Loop         - 意图演进循环
    └── Protocols              - 接口定义
"""

from sprintcycle.application.protocols import (
    EvolutionProtocol,
    FeedbackProtocol,
    LifecycleProtocol,
    OrchestrationProtocol,
)
from sprintcycle.application.http_factories import HTTPServices, create_http_services
from sprintcycle.application.request_context import RequestContext
from sprintcycle.application.sprint_orchestrator import SprintOrchestrator

__all__ = [
    # Core
    "SprintOrchestrator",
    # HTTP Services
    "HTTPServices",
    "create_http_services",
    # Context
    "RequestContext",
    # Protocols
    "OrchestrationProtocol",
    "LifecycleProtocol",
    "EvolutionProtocol",
    "FeedbackProtocol",
]
