"""
Orchestration Factory - 统一管理编排器的依赖注入。

此模块负责创建和注入所有基础设施依赖，确保应用层不直接依赖基础设施层。
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger

from sprintcycle.domain.ports.orchestration import OrchestrationDependencies


def create_orchestration_dependencies(
    project_root: str,
    db_path: Optional[str] = None,
) -> OrchestrationDependencies:
    """
    创建编排器依赖容器。

    此工厂函数负责：
    1. 创建所有基础设施适配器
    2. 将它们封装到 OrchestrationDependencies 容器中
    3. 返回给调用者进行依赖注入

    Args:
        project_root: 项目根目录路径
        db_path: 知识库数据库路径（可选）

    Returns:
        OrchestrationDependencies: 包含所有依赖的容器
    """
    from sprintcycle.infrastructure.adapters.core.orchestration import (
        GraphCompilerAdapter,
        KnowledgeInjectionHookAdapter,
        KnowledgeRepositoryAdapter,
        QualityConfigAdapter,
        RuntimeConfigAdapter,
        StateStoreAdapter,
        TraceRuntimeAdapter,
    )

    runtime_config = RuntimeConfigAdapter()
    graph_compiler = GraphCompilerAdapter()

    knowledge_repo = KnowledgeRepositoryAdapter(db_path or ".sprintcycle/knowledge.db")
    knowledge_injection_hook = KnowledgeInjectionHookAdapter(project_root, runtime_config)

    trace_runtime: Optional[TraceRuntimeAdapter] = None
    if os.environ.get("PHOENIX_ENABLED"):
        try:
            trace_runtime = TraceRuntimeAdapter(project_name=project_root)
        except ImportError:
            logger.debug("Phoenix not available")

    state_store = StateStoreAdapter()
    quality_config = QualityConfigAdapter()

    return OrchestrationDependencies(
        runtime_config=runtime_config,
        graph_compiler=graph_compiler,
        trace_runtime=trace_runtime,
        knowledge_repository=knowledge_repo,
        knowledge_injection_hook=knowledge_injection_hook,
        state_store=state_store,
        quality_config=quality_config,
    )
