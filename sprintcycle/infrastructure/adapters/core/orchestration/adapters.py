"""
Orchestration adapters - infrastructure implementations of domain ports.

These adapters bridge domain-level abstractions with concrete infrastructure implementations.
"""

from __future__ import annotations

from typing import Any, Optional

from sprintcycle.domain.generic.ports.orchestration import (
    GraphCompilerPort,
    KnowledgeInjectionHookPort,
    KnowledgeRepositoryPort,
    QualityConfigPort,
    RuntimeConfigPort,
    StateStorePort,
    TraceRuntimePort,
)


class GraphCompilerAdapter(GraphCompilerPort):
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
    def __init__(self, db_path: str):
        from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_repository import (
            KnowledgeCardRepository,
        )
        self._repo = KnowledgeCardRepository(db_path)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._repo, name)


class KnowledgeInjectionHookAdapter(KnowledgeInjectionHookPort):
    def __init__(self, project_root: str, config: Any):
        from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_hook import (
            KnowledgeInjectionHook,
        )
        self._hook = KnowledgeInjectionHook(project_root, config)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._hook, name)


class RuntimeConfigAdapter(RuntimeConfigPort):
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
    def load(self, execution_id: str) -> Optional[Any]:
        from sprintcycle.infrastructure.adapters.core.execution.state_store import get_state_store
        store = get_state_store()
        return store.load(execution_id)

    def save(self, state: Any) -> None:
        from sprintcycle.infrastructure.adapters.core.execution.state_store import get_state_store
        store = get_state_store()
        store.save(state)


class QualityConfigAdapter(QualityConfigPort):
    def resolve_effective_quality_level(self, profile: str, level: str) -> str:
        from sprintcycle.infrastructure.adapters.generic.config.quality import (
            resolve_effective_quality_level,
        )
        return resolve_effective_quality_level(profile, level)

    def runs_pytest(self, quality_level: str) -> bool:
        from sprintcycle.infrastructure.adapters.generic.config.quality import runs_pytest
        return runs_pytest(quality_level)
