"""
Composition Root 包 - 负责应用程序的依赖注入和组合。

根据洋葱架构原则，组合根是应用程序的最外层，负责：
1. 创建所有基础设施依赖
2. 将它们注入到应用层服务
3. 建立依赖关系

应用层（application）不应直接依赖基础设施层（infrastructure），
所有依赖都应通过组合根注入。
"""

from __future__ import annotations

__all__ = [
    "initialize_http_infrastructure",
    "InfrastructureFactory",
    "create_default_evolution_facade",
    "create_orchestration_dependencies",
]

from sprintcycle.composition.http_factory import (
    InfrastructureFactory,
    initialize_http_infrastructure,
)
from sprintcycle.composition.evolution_factory import create_default_evolution_facade
from sprintcycle.composition.orchestration_factory import create_orchestration_dependencies
