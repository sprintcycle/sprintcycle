"""
Orchestration ports - domain-level abstractions for infrastructure dependencies.

These protocols define the contract that infrastructure adapters must implement,
allowing the application layer to depend on abstractions rather than concrete implementations.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class RuntimeConfigPort(Protocol):
    """Port for runtime configuration access."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        ...

    @property
    def dry_run(self) -> bool:
        ...

    @property
    def max_verify_fix_rounds(self) -> int:
        ...

    @property
    def governance_enabled(self) -> bool:
        ...

    @property
    def governance_task_hooks_enabled(self) -> bool:
        ...

    @property
    def hitl_enabled(self) -> bool:
        ...

    @property
    def verification_enabled(self) -> bool:
        ...

    @property
    def coding_engine(self) -> str:
        ...

    @property
    def quality_level(self) -> str:
        ...

    @property
    def quality_profile(self) -> str:
        ...

    @property
    def checkpoint_store(self) -> Optional[Any]:
        ...


@runtime_checkable
class TraceRuntimePort(Protocol):
    """Port for trace runtime operations."""

    def emit_trace(self, events: list[dict]) -> None:
        """Emit trace events."""
        ...


@runtime_checkable
class KnowledgeRepositoryPort(Protocol):
    """Port for knowledge repository operations."""

    ...


@runtime_checkable
class KnowledgeInjectionHookPort(Protocol):
    """Port for knowledge injection hook."""

    ...


@runtime_checkable
class GraphCompilerPort(Protocol):
    """Port for graph compilation."""

    def compile_intent_graph(self, **kwargs: Any) -> Any:
        """Compile intent graph."""
        ...

    def compile_sprint_graph(self, **kwargs: Any) -> Any:
        """Compile sprint graph."""
        ...


@runtime_checkable
class StateStorePort(Protocol):
    """Port for state storage operations."""

    def load(self, execution_id: str) -> Optional[Any]:
        """Load state by execution ID."""
        ...

    def save(self, state: Any) -> None:
        """Save state."""
        ...


@runtime_checkable
class QualityConfigPort(Protocol):
    """Port for quality configuration operations."""

    def resolve_effective_quality_level(self, profile: str, level: str) -> str:
        """Resolve effective quality level."""
        ...

    def runs_pytest(self, quality_level: str) -> bool:
        """Check if pytest should run for given quality level."""
        ...


class OrchestrationDependencies:
    """
    Container for orchestration dependencies.
    
    This class aggregates all infrastructure dependencies needed by the orchestrator,
    allowing them to be injected as a unit.
    """

    def __init__(
        self,
        runtime_config: RuntimeConfigPort,
        graph_compiler: Optional[GraphCompilerPort] = None,
        trace_runtime: Optional[TraceRuntimePort] = None,
        knowledge_repository: Optional[KnowledgeRepositoryPort] = None,
        knowledge_injection_hook: Optional[KnowledgeInjectionHookPort] = None,
        state_store: Optional[StateStorePort] = None,
        quality_config: Optional[QualityConfigPort] = None,
    ):
        self.runtime_config = runtime_config
        self.graph_compiler = graph_compiler
        self.trace_runtime = trace_runtime
        self.knowledge_repository = knowledge_repository
        self.knowledge_injection_hook = knowledge_injection_hook
        self.state_store = state_store
        self.quality_config = quality_config