"""
Orchestration Factory - 统一管理编排器的依赖注入。

此模块负责创建和注入所有基础设施依赖，确保应用层不直接依赖基础设施层。
"""

from __future__ import annotations

import os
from typing import Any, Optional

from loguru import logger

from sprintcycle.domain.generic.ports.orchestration import (
    GraphCompilerPort,
    KnowledgeInjectionHookPort,
    KnowledgeRepositoryPort,
    OrchestrationDependencies,
    QualityConfigPort,
    RuntimeConfigPort,
    StateStorePort,
    TraceRuntimePort,
)


class GraphCompilerAdapter(GraphCompilerPort):
    """Adapter for LangGraph compiler."""

    def compile_intent_graph(self, **kwargs: Any) -> Any:
        from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import (
            compile_intent_graph as _compile,
        )
        return _compile(**kwargs)

    def compile_sprint_graph(self, **kwargs: Any) -> Any:
        from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import (
            compile_sprint_graph as _compile,
        )
        return _compile(**kwargs)


class KnowledgeRepositoryAdapter(KnowledgeRepositoryPort):
    """Adapter for knowledge repository."""

    def __init__(self, db_path: str):
        from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_repository import (
            KnowledgeCardRepository,
        )
        self._repo = KnowledgeCardRepository(db_path)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._repo, name)


class KnowledgeInjectionHookAdapter(KnowledgeInjectionHookPort):
    """Adapter for knowledge injection hook."""

    def __init__(self, project_root: str, config: Any):
        from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_hook import (
            KnowledgeInjectionHook,
        )
        self._hook = KnowledgeInjectionHook(project_root, config)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._hook, name)


class RuntimeConfigAdapter(RuntimeConfigPort):
    """Adapter for runtime configuration."""

    def __init__(self):
        from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
        self._config = RuntimeConfig()

    def to_dict(self) -> dict[str, Any]:
        return self._config.to_dict() if hasattr(self._config, "to_dict") else {}

    @property
    def dry_run(self) -> bool:
        return getattr(self._config, "dry_run", False)

    @property
    def max_verify_fix_rounds(self) -> int:
        return int(getattr(self._config, "max_verify_fix_rounds", 3))

    @property
    def governance_enabled(self) -> bool:
        return getattr(self._config, "governance_enabled", False)

    @property
    def governance_task_hooks_enabled(self) -> bool:
        return getattr(self._config, "governance_task_hooks_enabled", False)

    @property
    def hitl_enabled(self) -> bool:
        return getattr(self._config, "hitl_enabled", False)

    @property
    def verification_enabled(self) -> bool:
        return getattr(self._config, "verification_enabled", False)

    @property
    def coding_engine(self) -> str:
        return getattr(self._config, "coding_engine", "cursor")

    @property
    def quality_level(self) -> str:
        return getattr(self._config, "quality_level", "L2")

    @property
    def quality_profile(self) -> str:
        return getattr(self._config, "quality_profile", "")

    @property
    def checkpoint_store(self) -> Optional[Any]:
        return getattr(self._config, "checkpoint_store", None)


class TraceRuntimeAdapter(TraceRuntimePort):
    """Adapter for Phoenix trace runtime."""

    def __init__(self, project_name: str):
        from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.exporter import (
            PhoenixExporterSpec,
        )
        from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.trace_runtime import (
            PhoenixTraceRuntime,
        )
        self._runtime = PhoenixTraceRuntime(PhoenixExporterSpec(project_name=project_name))

    def emit_trace(self, events: list[dict]) -> None:
        self._runtime.emit_trace(events)


class StateStoreAdapter(StateStorePort):
    """Adapter for state storage."""

    def load(self, execution_id: str) -> Optional[Any]:
        from sprintcycle.infrastructure.adapters.core.execution.state_store import get_state_store
        store = get_state_store()
        return store.load(execution_id)

    def save(self, state: Any) -> None:
        from sprintcycle.infrastructure.adapters.core.execution.state_store import get_state_store
        store = get_state_store()
        store.save(state)


class QualityConfigAdapter(QualityConfigPort):
    """Adapter for quality configuration."""

    def resolve_effective_quality_level(self, profile: str, level: str) -> str:
        from sprintcycle.infrastructure.adapters.generic.config.quality import (
            resolve_effective_quality_level,
        )
        return resolve_effective_quality_level(profile, level)

    def runs_pytest(self, quality_level: str) -> bool:
        from sprintcycle.infrastructure.adapters.generic.config.quality import runs_pytest
        return runs_pytest(quality_level)


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