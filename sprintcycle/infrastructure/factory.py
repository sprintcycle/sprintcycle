"""
Infrastructure 工厂层 — DDD 依赖注入的组装点

本模块负责：
1. 实例化所有 Infrastructure 实现
2. 注册到 Domain/Application 层的工厂回调（通过 ports 端口层）
3. 组装完整的依赖关系图

所有 Infrastructure 实例的创建都集中在这里，确保分层清晰。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from pathlib import Path

from loguru import logger


def register_all_infrastructure(project_path: str, config: Any) -> None:
    """统一注册所有 Infrastructure 层实现到 Domain/Application 层的端口"""
    
    # 状态持久化相关
    from sprintcycle.infrastructure.adapters.core.execution.state_store import (
        register_event_backend_factory,
        register_rollback_implementations,
    )
    
    register_event_backend_factory()
    register_rollback_implementations()
    logger.debug("[Infrastructure] Registered persistence factories")
    
    # 注册状态存储工厂到端口
    from sprintcycle.domain.generic.ports.state_store import register_state_store_factory
    from sprintcycle.infrastructure.adapters.core.execution.state_store import get_state_store
    
    register_state_store_factory(get_state_store)
    logger.debug("[Infrastructure] Registered state_store factory to ports")
    
    # 注册缓存工厂到端口
    from sprintcycle.domain.generic.ports.cache import register_cache_backend_factory
    from sprintcycle.infrastructure.adapters.generic.cache import build_cache_backend
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
    
    def _cache_factory(runtime: Optional[Any] = None, project_path: str = ".") -> Any:
        effective_runtime = runtime or RuntimeConfig()
        return build_cache_backend(effective_runtime, project_path)
    
    register_cache_backend_factory(_cache_factory)
    logger.debug("[Infrastructure] Registered cache factory to ports")
    
    # 注册治理适配器工厂到端口
    from sprintcycle.domain.generic.ports.governance import (
        register_archguard_adapter_factory,
        register_grimp_adapter_factory,
        register_import_linter_adapter_factory,
        register_ruff_adapter_factory,
        register_typecheck_adapter_factory,
    )
    from sprintcycle.infrastructure.adapters.core.governance.arch_guard import (
        ArchonAdapter,
        GrimpAdapter,
        ImportLinterAdapter,
        RuffAdapter,
        TypeCheckAdapter,
    )
    
    register_archguard_adapter_factory(lambda: ArchonAdapter())
    register_grimp_adapter_factory(lambda: GrimpAdapter())
    register_import_linter_adapter_factory(lambda: ImportLinterAdapter())
    register_ruff_adapter_factory(lambda: RuffAdapter())
    register_typecheck_adapter_factory(lambda: TypeCheckAdapter())
    logger.debug("[Infrastructure] Registered governance adapters to ports")
    
    # 注册配置工厂到端口
    from sprintcycle.domain.generic.ports.config import register_runtime_config_factory
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
    
    def _config_factory(project_path: Optional[str] = None) -> RuntimeConfig:
        if project_path:
            return RuntimeConfig.from_project(project_path)
        return RuntimeConfig()
    
    register_runtime_config_factory(_config_factory)
    logger.debug("[Infrastructure] Registered config factory to ports")
    
    # 注册 LLM 引擎适配器工厂到端口
    from sprintcycle.domain.generic.ports.llm import register_engine_adapter_factory
    from sprintcycle.infrastructure.adapters.generic.llm.engine_adapters import (
        resolve_engine_adapter,
        EngineAdapterConfig,
    )
    
    def _engine_factory(engine: str, config: Any) -> Any:
        return resolve_engine_adapter(
            engine,
            EngineAdapterConfig(
                timeout_seconds=config.timeout_seconds,
                cwd=config.cwd,
                max_output_chars=config.max_output_chars,
            ),
        )
    
    register_engine_adapter_factory(_engine_factory)
    logger.debug("[Infrastructure] Registered LLM engine factory to ports")
    
    # 注册集成适配器工厂到端口
    from sprintcycle.domain.generic.ports.integrations import (
        register_autogpt_compose_factory,
        register_autogpt_runtime_factory,
        register_langgraph_adapter_factory,
        register_phoenix_exporter_factory,
        register_phoenix_trace_factory,
    )
    from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.compose import (
        build_default_compose_spec,
    )
    from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.runtime import (
        AutoGPTRuntimeSpec,
    )
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.adapter import (
        LangGraphExecutionAdapter,
    )
    from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.exporter import (
        PhoenixExporterSpec,
    )
    from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.trace_runtime import (
        PhoenixTraceRuntime,
    )
    
    register_autogpt_compose_factory(build_default_compose_spec)
    register_autogpt_runtime_factory(lambda name: AutoGPTRuntimeSpec(project_name=name))
    register_langgraph_adapter_factory(lambda name: LangGraphExecutionAdapter(graph_name=name))
    register_phoenix_exporter_factory(lambda name: PhoenixExporterSpec(project_name=name))
    register_phoenix_trace_factory(lambda spec: PhoenixTraceRuntime(spec))
    logger.debug("[Infrastructure] Registered integration adapters to ports")


__all__ = [
    "register_all_infrastructure",
]
