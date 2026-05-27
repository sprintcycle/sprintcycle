"""
HTTP 层服务工厂 - 为 interfaces/http 提供基础设施工厂注册

遵循洋葱架构原则：application 层不直接依赖 infrastructure 层，所有基础设施依赖通过延迟导入。
"""

from __future__ import annotations

from typing import Any, Optional


class InfrastructureFactory:
    """基础设施工厂注册器 - 负责注册所有 Domain 层依赖的 Infrastructure 工厂函数"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self._register_infrastructure_factories()

    def _register_infrastructure_factories(self) -> None:
        """注册 Domain 层依赖的 Infrastructure 工厂函数（DDD 依赖倒置）"""
        from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
        from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_repository import KnowledgeCardRepository
        from sprintcycle.infrastructure.adapters.core.evolution.evolution_registry_access import create_evolution_registry

        register_event_backend_factory()

        from sprintcycle.infrastructure.adapters.core.evolution.rollback_store.rollback import (
            GitRollbackMixin,
            RollbackConfig,
            _is_git_repo,
            _run_git,
        )
        from sprintcycle.infrastructure.adapters.core.evolution.rollback_store.rollback_types import (
            RollbackError,
            VariantBranch,
        )
        from sprintcycle.domain.ports.state_store import register_rollback_implementations

        register_rollback_implementations(
            GitRollbackMixin=GitRollbackMixin,
            RollbackConfig=RollbackConfig,
            RollbackError=RollbackError,
            VariantBranch=VariantBranch,
            is_git_repo=_is_git_repo,
            run_git=_run_git,
        )

        from sprintcycle.domain.ports.state_store import register_state_store_factory

        def create_state_store(store_dir: Optional[str] = None):
            from sprintcycle.infrastructure.adapters.core.execution.state_store import get_state_store as _get
            return _get(store_dir)

        register_state_store_factory(create_state_store)

        from sprintcycle.domain.ports.cache import register_cache_backend_factory

        def create_cache_backend(runtime: Any = None, project_path: str = "."):
            from sprintcycle.infrastructure.adapters.generic.cache import build_cache_backend as _get
            effective_runtime = runtime or RuntimeConfig()
            return _get(effective_runtime, project_path)

        register_cache_backend_factory(create_cache_backend)

        from sprintcycle.domain.ports.config import register_runtime_config_factory

        def create_runtime_config(project_path: Optional[str] = None):
            if project_path:
                return RuntimeConfig.from_project(project_path)
            return RuntimeConfig()

        register_runtime_config_factory(create_runtime_config)

        from sprintcycle.domain.ports.registry import register_runtime_registry_factory

        def create_runtime_registry(config: Any):
            from sprintcycle.infrastructure.adapters.generic.config.runtime_registry import RuntimeRegistry
            return RuntimeRegistry(config)

        register_runtime_registry_factory(create_runtime_registry)

        from sprintcycle.domain.ports.deploy import register_platform_launch_factory

        def create_platform_launch_service():
            from sprintcycle.infrastructure.adapters.generic.deploy.platform_launch_service import PlatformLaunchService
            from sprintcycle.infrastructure.adapters.generic.deploy.deployment_spec_service import DeploymentSpecService
            return PlatformLaunchService(spec_service=DeploymentSpecService())

        register_platform_launch_factory(create_platform_launch_service)

        from sprintcycle.domain.ports.evolution import (
            register_evolution_registry_factory,
            register_version_manifest_factory,
        )

        register_evolution_registry_factory(create_evolution_registry)

        from sprintcycle.infrastructure.adapters.core.evolution.version_store.interface import get_version_manifest_summary

        register_version_manifest_factory(get_version_manifest_summary)

        from sprintcycle.domain.ports.governance import (
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

        from sprintcycle.infrastructure.adapters.core.governance.hitl_store import HitlSqliteStore
        from sprintcycle.domain.ports.hitl import register_hitl_store_factory

        def create_hitl_store(project_path: Optional[str] = None):
            from sprintcycle.infrastructure.adapters.core.governance.hitl_store import default_hitl_db_path
            return HitlSqliteStore(default_hitl_db_path(project_path))

        register_hitl_store_factory(create_hitl_store)

        from sprintcycle.infrastructure.adapters.core.governance.suggestion_store import SuggestionStore
        from sprintcycle.domain.ports.suggestion import register_suggestion_store_factory

        def create_suggestion_store(store_root: Optional[str] = None):
            root = store_root or ".sprintcycle/governance/suggestion"
            return SuggestionStore(root)

        register_suggestion_store_factory(create_suggestion_store)

        from sprintcycle.domain.ports.llm import register_engine_adapter_factory

        def create_engine_adapter(engine: str, config: Any):
            from sprintcycle.infrastructure.adapters.generic.llm.engine_adapters import resolve_engine_adapter as _resolve
            from sprintcycle.infrastructure.adapters.generic.llm.engine_adapters import EngineAdapterConfig as InfraConfig

            return _resolve(
                engine,
                InfraConfig(
                    timeout_seconds=config.timeout_seconds,
                    cwd=config.cwd,
                    max_output_chars=config.max_output_chars,
                ),
            )

        register_engine_adapter_factory(create_engine_adapter)

        from sprintcycle.domain.ports.observability import register_observability_facade_factory

        def create_observability_facade(project_path: Optional[str] = None, config: Any = None):
            from sprintcycle.infrastructure.adapters.generic.observability.facade import ObservabilityFacade
            return ObservabilityFacade()

        register_observability_facade_factory(create_observability_facade)

        from sprintcycle.domain.ports.knowledge import (
            register_knowledge_repository_factory,
            register_sprint_outcome_card_factory,
        )

        def create_knowledge_repository(db_path: Optional[str] = None):
            path = db_path or ".sprintcycle/knowledge.db"
            return KnowledgeCardRepository(path)

        register_knowledge_repository_factory(create_knowledge_repository)

        def create_sprint_outcome_card_persister():
            from sprintcycle.infrastructure.adapters.generic.knowledge.sprint_knowledge_card import persist_sprint_outcome_card
            from sprintcycle.domain.ports.knowledge import SprintOutcomeCardAdapter
            return SprintOutcomeCardAdapter(persist_sprint_outcome_card)

        register_sprint_outcome_card_factory(create_sprint_outcome_card_persister)

        from sprintcycle.domain.ports.integrations import (
            register_autogpt_compose_factory,
            register_autogpt_runtime_factory,
            register_langgraph_adapter_factory,
            register_compiled_graph_runtime_factory,
            register_compiled_sprint_graph_factory,
            register_plan_runtime_factory,
            register_phoenix_exporter_factory,
            register_phoenix_trace_factory,
        )
        from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import (
            compile_intent_graph,
            compile_sprint_graph,
        )
        from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.plan_runtime import PlanRuntime

        def create_autogpt_compose_spec(project_name: str):
            from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.compose import build_default_compose_spec
            return build_default_compose_spec(project_name)

        def create_autogpt_runtime_spec(project_name: str):
            from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.runtime import AutoGPTRuntimeSpec
            return AutoGPTRuntimeSpec(project_name=project_name)

        def create_langgraph_adapter(graph_name: str):
            from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.adapter import LangGraphExecutionAdapter
            return LangGraphExecutionAdapter(graph_name=graph_name)

        def create_phoenix_exporter_spec(project_name: str):
            from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.exporter import PhoenixExporterSpec
            return PhoenixExporterSpec(project_name=project_name)

        def create_phoenix_trace_runtime(exporter_spec: Any):
            from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.trace_runtime import PhoenixTraceRuntime
            return PhoenixTraceRuntime(exporter_spec)

        register_autogpt_compose_factory(create_autogpt_compose_spec)
        register_autogpt_runtime_factory(create_autogpt_runtime_spec)
        register_langgraph_adapter_factory(create_langgraph_adapter)
        register_compiled_graph_runtime_factory(compile_intent_graph)
        register_compiled_sprint_graph_factory(compile_sprint_graph)

        def create_plan_runtime(**kwargs):
            return PlanRuntime(**kwargs)

        register_plan_runtime_factory(create_plan_runtime)
        register_phoenix_exporter_factory(create_phoenix_exporter_spec)
        register_phoenix_trace_factory(create_phoenix_trace_runtime)

        from sprintcycle.domain.ports.rate_limit import register_rate_limit_adapter
        from sprintcycle.infrastructure.adapters.generic.config.rate_limit import RateLimitAdapter

        register_rate_limit_adapter(RateLimitAdapter())

        from sprintcycle.domain.ports.audit import register_audit_adapter
        from sprintcycle.infrastructure.adapters.generic.integrations.audit import AuditAdapter

        register_audit_adapter(AuditAdapter())

        from sprintcycle.domain.ports.diagnostics import register_diagnostic_adapter
        from sprintcycle.infrastructure.adapters.generic.observability.diagnostics.adapter import DiagnosticAdapter

        register_diagnostic_adapter(DiagnosticAdapter(self.project_path))


def register_event_backend_factory() -> None:
    """注册事件后端工厂（抽离为独立函数便于测试）"""
    from sprintcycle.infrastructure.adapters.core.execution.state_store import register_event_backend_factory as _register
    _register()


def initialize_http_infrastructure(project_path: str) -> InfrastructureFactory:
    """初始化 HTTP 层所需的基础设施工厂注册"""
    return InfrastructureFactory(project_path)
