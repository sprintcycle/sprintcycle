"""
SprintCycle 依赖注入容器 - 基于 dependency-injector 的六边形架构 DI 容器

本模块统一管理所有依赖注入，提供：
1. 声明式依赖配置
2. 自动依赖图验证
3. 生命周期管理（Singleton/Factory）
4. 配置注入支持
5. 测试友好的 Override 机制

使用方式：
```python
from sprintcycle.application.composition.di_container import Container, container

# 获取子容器中的服务
cache = container.infrastructure.cache_backend()
governance = container.governance.archguard_adapter()

# 测试时覆盖
with container.infrastructure.cache_backend.override(MockCache()):
    service = MyService()
```
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from dependency_injector import containers, providers


# 工厂函数（不是类方法）
def _create_cache_backend(runtime: Any = None, project_path: str = ".") -> Any:
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
    from sprintcycle.infrastructure.adapters.generic.cache.factory import build_cache_backend
    effective_runtime = runtime or RuntimeConfig()
    return build_cache_backend(effective_runtime, project_path)


def _create_state_store(store_dir: Optional[str] = None) -> Any:
    from sprintcycle.infrastructure.adapters.core.execution.state_store import get_state_store
    return get_state_store(store_dir)


def _create_archguard_adapter() -> Any:
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import ArchonAdapter
    return ArchonAdapter()


def _create_grimp_adapter() -> Any:
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import GrimpAdapter
    return GrimpAdapter()


def _create_import_linter_adapter() -> Any:
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import ImportLinterAdapter
    return ImportLinterAdapter()


def _create_ruff_adapter() -> Any:
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import RuffAdapter
    return RuffAdapter()


def _create_typecheck_adapter() -> Any:
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import TypeCheckAdapter
    return TypeCheckAdapter()


def _compile_intent_graph(**kwargs) -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import compile_intent_graph
    return compile_intent_graph(**kwargs)


def _compile_sprint_graph(**kwargs) -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import compile_sprint_graph
    return compile_sprint_graph(**kwargs)


def _create_plan_runtime(**kwargs) -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.plan_runtime import PlanRuntime
    return PlanRuntime(**kwargs)


def _create_hitl_store(project_path: Optional[str] = None) -> Any:
    from sprintcycle.infrastructure.adapters.core.governance.hitl_store import (
        HitlSqliteStore,
        default_hitl_db_path,
    )
    return HitlSqliteStore(default_hitl_db_path(project_path))


def _create_suggestion_store(store_root: Optional[str] = None) -> Any:
    from sprintcycle.infrastructure.adapters.core.governance.suggestion_store import SuggestionStore
    root = store_root or ".sprintcycle/governance/suggestion"
    return SuggestionStore(root)


def _create_knowledge_repository(db_path: Optional[str] = None) -> Any:
    from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_repository import KnowledgeCardRepository
    path = db_path or ".sprintcycle/knowledge.db"
    return KnowledgeCardRepository(path)


def _create_sprint_outcome_card() -> Any:
    from sprintcycle.infrastructure.adapters.generic.knowledge.sprint_knowledge_card import persist_sprint_outcome_card
    from sprintcycle.domain.ports.knowledge import SprintOutcomeCardAdapter
    return SprintOutcomeCardAdapter(persist_sprint_outcome_card)


def _create_observability_facade() -> Any:
    from sprintcycle.infrastructure.adapters.generic.observability.facade import ObservabilityFacade
    return ObservabilityFacade()


def _create_phoenix_trace_runtime(exporter_spec: Any) -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.trace_runtime import PhoenixTraceRuntime
    return PhoenixTraceRuntime(exporter_spec)


def _create_diagnostic_adapter(project_path: str = ".") -> Any:
    from sprintcycle.infrastructure.adapters.generic.observability.diagnostics.adapter import DiagnosticAdapter
    return DiagnosticAdapter(project_path)


def _create_runtime_config(project_path: Optional[str] = None) -> Any:
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
    if project_path:
        return RuntimeConfig.from_project(project_path)
    return RuntimeConfig()


def _create_rate_limit_adapter() -> Any:
    from sprintcycle.infrastructure.adapters.generic.config.rate_limit import RateLimitAdapter
    return RateLimitAdapter()


def _create_audit_adapter() -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.audit import AuditAdapter
    return AuditAdapter()


def _create_runtime_registry(config: Any) -> Any:
    from sprintcycle.infrastructure.adapters.generic.config.runtime_registry import RuntimeRegistry
    return RuntimeRegistry(config)


def _create_evolution_registry(config: Any) -> Any:
    from sprintcycle.infrastructure.adapters.core.evolution.evolution_registry_access import create_evolution_registry
    return create_evolution_registry(config)


def _create_autogpt_compose_spec(project_name: str = "sprintcycle") -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.compose_spec import build_default_compose_spec
    return build_default_compose_spec(project_name)


def _create_autogpt_runtime_spec(project_name: str = "sprintcycle") -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.runtime_spec import create_autogpt_runtime_spec
    return create_autogpt_runtime_spec(project_name)


def _create_langgraph_adapter(graph_name: str) -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.adapter import create_langgraph_adapter
    return create_langgraph_adapter(graph_name)


def _create_phoenix_exporter_spec(project_name: str = "sprintcycle") -> Any:
    from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.exporter_spec import create_phoenix_exporter_spec
    return create_phoenix_exporter_spec(project_name)


def _create_platform_launch_service() -> Any:
    from sprintcycle.infrastructure.adapters.generic.deploy.platform_launch_service import PlatformLaunchService
    from sprintcycle.infrastructure.adapters.generic.deploy.deployment_spec_service import DeploymentSpecService
    return PlatformLaunchService(spec_service=DeploymentSpecService())


class CoreInfrastructureContainer(containers.DeclarativeContainer):
    """核心基础设施容器 - 提供底层技术依赖"""

    config = providers.Configuration()
    cache_backend = providers.Singleton(_create_cache_backend)
    state_store = providers.Singleton(_create_state_store)


class GovernanceAdaptersContainer(containers.DeclarativeContainer):
    """治理适配器容器 - 提供架构检查和质量门禁依赖"""

    archguard_adapter = providers.Singleton(_create_archguard_adapter)
    grimp_adapter = providers.Singleton(_create_grimp_adapter)
    import_linter_adapter = providers.Singleton(_create_import_linter_adapter)
    ruff_adapter = providers.Singleton(_create_ruff_adapter)
    typecheck_adapter = providers.Singleton(_create_typecheck_adapter)


class IntegrationAdaptersContainer(containers.DeclarativeContainer):
    """集成适配器容器 - 提供第三方服务集成依赖"""

    compiled_graph_runtime = providers.Callable(_compile_intent_graph)
    compiled_sprint_graph = providers.Callable(_compile_sprint_graph)
    plan_runtime = providers.Factory(_create_plan_runtime)
    autogpt_compose_spec = providers.Factory(_create_autogpt_compose_spec)
    autogpt_runtime_spec = providers.Factory(_create_autogpt_runtime_spec)
    langgraph_adapter = providers.Factory(_create_langgraph_adapter)
    phoenix_exporter_spec = providers.Factory(_create_phoenix_exporter_spec)
    platform_launch_service = providers.Singleton(_create_platform_launch_service)


class StorageAdaptersContainer(containers.DeclarativeContainer):
    """存储适配器容器 - 提供持久化依赖"""

    hitl_store = providers.Factory(_create_hitl_store)
    suggestion_store = providers.Singleton(_create_suggestion_store)
    knowledge_repository = providers.Singleton(_create_knowledge_repository)
    sprint_outcome_card = providers.Singleton(_create_sprint_outcome_card)


class ObservabilityAdaptersContainer(containers.DeclarativeContainer):
    """可观测性适配器容器 - 提供监控和追踪依赖"""

    observability_facade = providers.Singleton(_create_observability_facade)
    phoenix_trace_runtime = providers.Factory(_create_phoenix_trace_runtime)
    diagnostic_adapter = providers.Singleton(_create_diagnostic_adapter)


class RuntimeConfigContainer(containers.DeclarativeContainer):
    """运行时配置容器 - 提供配置依赖"""

    config = providers.Configuration()
    runtime_config = providers.Singleton(_create_runtime_config)
    rate_limit_adapter = providers.Singleton(_create_rate_limit_adapter)
    audit_adapter = providers.Singleton(_create_audit_adapter)
    runtime_registry = providers.Factory(_create_runtime_registry)
    evolution_registry = providers.Factory(_create_evolution_registry)


class Container(containers.DeclarativeContainer):
    """
    SprintCycle 主容器 - 统一管理所有依赖注入

    容器结构：
    - infrastructure: 核心基础设施（缓存、状态存储）
    - governance: 治理适配器
    - integrations: 第三方集成
    - storage: 持久化存储
    - observability: 可观测性
    - runtime_config: 运行时配置

    生命周期策略：
    - Singleton: 共享实例（配置、缓存、适配器）
    - Factory: 每次创建新实例（无状态服务）
    - Callable: 工具函数（编译、转换）
    """

    config = providers.Configuration()

    infrastructure = providers.Container(CoreInfrastructureContainer)

    governance = providers.Container(GovernanceAdaptersContainer)

    integrations = providers.Container(IntegrationAdaptersContainer)

    storage = providers.Container(StorageAdaptersContainer)

    observability = providers.Container(ObservabilityAdaptersContainer)

    runtime_config_container = providers.Container(RuntimeConfigContainer)


_container: Optional[Container] = None


def create_container(
    project_path: str = ".",
    state_store_dir: Optional[str] = None,
    runtime_config: Optional[Any] = None,
) -> Container:
    """
    创建并配置 SprintCycle 容器

    Args:
        project_path: 项目根目录路径
        state_store_dir: 状态存储目录
        runtime_config: 运行时配置对象

    Returns:
        Container: 配置好的依赖注入容器
    """
    container = Container()

    container.config.runtime.from_value(runtime_config)
    container.config.project_path.from_value(project_path)
    container.config.state_store_dir.from_value(state_store_dir)

    return container


def get_container() -> Container:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = create_container()
    return _container


container: Container = get_container()


__all__ = [
    "Container",
    "CoreInfrastructureContainer",
    "GovernanceAdaptersContainer",
    "IntegrationAdaptersContainer",
    "StorageAdaptersContainer",
    "ObservabilityAdaptersContainer",
    "RuntimeConfigContainer",
    "create_container",
    "get_container",
    "container",
]
