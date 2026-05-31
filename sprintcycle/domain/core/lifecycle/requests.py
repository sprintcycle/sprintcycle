"""Request data classes for lifecycle operations.

These data classes group related parameters to reduce parameter explosion
in service methods. They follow the builder pattern for flexible construction.

**Design Principles:**
- Group related parameters logically
- Use builder pattern for optional parameters
- Immutable data classes for safety
- Type hints for better IDE support
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .state_machine import LifecycleSubstage
from .values import CorrelationContext, FailureInfo, GovernanceRef, EvolutionRef, RuntimeRef


# =============================================================================
# Build Lifecycle Request
# =============================================================================

@dataclass(frozen=True)
class BuildLifecycleRequest:
    """Request data for building a lifecycle.
    
    Groups all parameters needed to create a new lifecycle.
    Replaces the previous 28+ parameter method signature.
    """
    
    # Required identity
    execution_id: str
    task_id: str
    project_path: str
    
    # Optional task metadata
    task_type: str = "project_optimization"
    intent: str = ""
    
    # Optional state override
    initial_stage: LifecycleSubstage = field(default_factory=lambda: LifecycleSubstage.NEW)
    
    # Optional references
    governance_ref: Optional[GovernanceRef] = None
    evolution_ref: Optional[EvolutionRef] = None
    runtime_ref: Optional[RuntimeRef] = None
    
    # Optional context
    correlation: Optional[CorrelationContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def builder(cls):
        """Create a builder for BuildLifecycleRequest."""
        return BuildLifecycleRequestBuilder()


class BuildLifecycleRequestBuilder:
    """Builder for BuildLifecycleRequest."""
    
    def __init__(self):
        self.execution_id: str = ""
        self.task_id: str = ""
        self.project_path: str = ""
        self.task_type: str = "project_optimization"
        self.intent: str = ""
        self.initial_stage: LifecycleSubstage = LifecycleSubstage.NEW
        self.governance_ref: Optional[GovernanceRef] = None
        self.evolution_ref: Optional[EvolutionRef] = None
        self.runtime_ref: Optional[RuntimeRef] = None
        self.correlation: Optional[CorrelationContext] = None
        self.metadata: Dict[str, Any] = {}
    
    def with_execution_id(self, execution_id: str) -> "BuildLifecycleRequestBuilder":
        self.execution_id = execution_id
        return self
    
    def with_task_id(self, task_id: str) -> "BuildLifecycleRequestBuilder":
        self.task_id = task_id
        return self
    
    def with_project_path(self, project_path: str) -> "BuildLifecycleRequestBuilder":
        self.project_path = project_path
        return self
    
    def with_task_type(self, task_type: str) -> "BuildLifecycleRequestBuilder":
        self.task_type = task_type
        return self
    
    def with_intent(self, intent: str) -> "BuildLifecycleRequestBuilder":
        self.intent = intent
        return self
    
    def with_initial_stage(self, stage: LifecycleSubstage) -> "BuildLifecycleRequestBuilder":
        self.initial_stage = stage
        return self
    
    def with_governance_ref(self, ref: GovernanceRef) -> "BuildLifecycleRequestBuilder":
        self.governance_ref = ref
        return self
    
    def with_evolution_ref(self, ref: EvolutionRef) -> "BuildLifecycleRequestBuilder":
        self.evolution_ref = ref
        return self
    
    def with_runtime_ref(self, ref: RuntimeRef) -> "BuildLifecycleRequestBuilder":
        self.runtime_ref = ref
        return self
    
    def with_correlation(self, correlation: CorrelationContext) -> "BuildLifecycleRequestBuilder":
        self.correlation = correlation
        return self
    
    def with_metadata(self, **kwargs: Any) -> "BuildLifecycleRequestBuilder":
        self.metadata.update(kwargs)
        return self
    
    def build(self) -> BuildLifecycleRequest:
        if not self.execution_id:
            raise ValueError("execution_id is required")
        if not self.task_id:
            raise ValueError("task_id is required")
        if not self.project_path:
            raise ValueError("project_path is required")
        
        return BuildLifecycleRequest(
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            task_type=self.task_type,
            intent=self.intent,
            initial_stage=self.initial_stage,
            governance_ref=self.governance_ref,
            evolution_ref=self.evolution_ref,
            runtime_ref=self.runtime_ref,
            correlation=self.correlation,
            metadata=dict(self.metadata),
        )


# =============================================================================
# Transition Request
# =============================================================================

@dataclass(frozen=True)
class TransitionRequest:
    """Request data for stage transition.
    
    Groups all parameters needed to transition a lifecycle to a new stage.
    """
    
    execution_id: str
    task_id: str
    target_stage: LifecycleSubstage
    reason: str = ""
    
    # Optional failure info for recovery transitions
    failure_info: Optional[FailureInfo] = None
    
    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def builder(cls):
        """Create a builder for TransitionRequest."""
        return TransitionRequestBuilder()


class TransitionRequestBuilder:
    """Builder for TransitionRequest."""
    
    def __init__(self):
        self.execution_id: str = ""
        self.task_id: str = ""
        self.target_stage: LifecycleSubstage = LifecycleSubstage.NEW
        self.reason: str = ""
        self.failure_info: Optional[FailureInfo] = None
        self.metadata: Dict[str, Any] = {}
    
    def with_execution_id(self, execution_id: str) -> "TransitionRequestBuilder":
        self.execution_id = execution_id
        return self
    
    def with_task_id(self, task_id: str) -> "TransitionRequestBuilder":
        self.task_id = task_id
        return self
    
    def with_target_stage(self, stage: LifecycleSubstage) -> "TransitionRequestBuilder":
        self.target_stage = stage
        return self
    
    def with_reason(self, reason: str) -> "TransitionRequestBuilder":
        self.reason = reason
        return self
    
    def with_failure_info(self, failure_info: FailureInfo) -> "TransitionRequestBuilder":
        self.failure_info = failure_info
        return self
    
    def with_metadata(self, **kwargs: Any) -> "TransitionRequestBuilder":
        self.metadata.update(kwargs)
        return self
    
    def build(self) -> TransitionRequest:
        if not self.execution_id:
            raise ValueError("execution_id is required")
        if not self.task_id:
            raise ValueError("task_id is required")
        
        return TransitionRequest(
            execution_id=self.execution_id,
            task_id=self.task_id,
            target_stage=self.target_stage,
            reason=self.reason,
            failure_info=self.failure_info,
            metadata=dict(self.metadata),
        )


# =============================================================================
# Web Request
# =============================================================================

@dataclass(frozen=True)
class WebLifecycleRequest:
    """Request data for web lifecycle orchestration.
    
    Groups all parameters needed for web-based lifecycle operations.
    """
    
    # Core identity
    execution_id: str
    task_id: str
    project_path: str
    
    # Request metadata
    request_id: str = ""
    source: str = "web"
    intent: str = ""
    
    # Optional references
    governance_session_id: str = ""
    evolution_request_id: str = ""
    runtime_id: str = ""
    
    # Optional data
    evidence: Dict[str, Any] = field(default_factory=dict)
    correlation_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def builder(cls):
        """Create a builder for WebLifecycleRequest."""
        return WebLifecycleRequestBuilder()


class WebLifecycleRequestBuilder:
    """Builder for WebLifecycleRequest."""
    
    def __init__(self):
        self.execution_id: str = ""
        self.task_id: str = ""
        self.project_path: str = ""
        self.request_id: str = ""
        self.source: str = "web"
        self.intent: str = ""
        self.governance_session_id: str = ""
        self.evolution_request_id: str = ""
        self.runtime_id: str = ""
        self.evidence: Dict[str, Any] = {}
        self.correlation_data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
    
    def with_execution_id(self, execution_id: str) -> "WebLifecycleRequestBuilder":
        self.execution_id = execution_id
        return self
    
    def with_task_id(self, task_id: str) -> "WebLifecycleRequestBuilder":
        self.task_id = task_id
        return self
    
    def with_project_path(self, project_path: str) -> "WebLifecycleRequestBuilder":
        self.project_path = project_path
        return self
    
    def with_request_id(self, request_id: str) -> "WebLifecycleRequestBuilder":
        self.request_id = request_id
        return self
    
    def with_source(self, source: str) -> "WebLifecycleRequestBuilder":
        self.source = source
        return self
    
    def with_intent(self, intent: str) -> "WebLifecycleRequestBuilder":
        self.intent = intent
        return self
    
    def with_governance_session_id(self, session_id: str) -> "WebLifecycleRequestBuilder":
        self.governance_session_id = session_id
        return self
    
    def with_evolution_request_id(self, request_id: str) -> "WebLifecycleRequestBuilder":
        self.evolution_request_id = request_id
        return self
    
    def with_runtime_id(self, runtime_id: str) -> "WebLifecycleRequestBuilder":
        self.runtime_id = runtime_id
        return self
    
    def with_evidence(self, **kwargs: Any) -> "WebLifecycleRequestBuilder":
        self.evidence.update(kwargs)
        return self
    
    def with_correlation_data(self, **kwargs: Any) -> "WebLifecycleRequestBuilder":
        self.correlation_data.update(kwargs)
        return self
    
    def with_metadata(self, **kwargs: Any) -> "WebLifecycleRequestBuilder":
        self.metadata.update(kwargs)
        return self
    
    def build(self) -> WebLifecycleRequest:
        if not self.execution_id:
            raise ValueError("execution_id is required")
        if not self.task_id:
            raise ValueError("task_id is required")
        if not self.project_path:
            raise ValueError("project_path is required")
        
        return WebLifecycleRequest(
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            request_id=self.request_id,
            source=self.source,
            intent=self.intent,
            governance_session_id=self.governance_session_id,
            evolution_request_id=self.evolution_request_id,
            runtime_id=self.runtime_id,
            evidence=dict(self.evidence),
            correlation_data=dict(self.correlation_data),
            metadata=dict(self.metadata),
        )


# =============================================================================
# Recovery Request
# =============================================================================

@dataclass(frozen=True)
class RecoveryRequest:
    """Request data for recovery operations."""
    
    execution_id: str
    task_id: str
    failure_kind: str = ""
    failure_reason: str = ""
    failure_code: str = ""
    
    @classmethod
    def builder(cls):
        """Create a builder for RecoveryRequest."""
        return RecoveryRequestBuilder()


class RecoveryRequestBuilder:
    """Builder for RecoveryRequest."""
    
    def __init__(self):
        self.execution_id: str = ""
        self.task_id: str = ""
        self.failure_kind: str = ""
        self.failure_reason: str = ""
        self.failure_code: str = ""
    
    def with_execution_id(self, execution_id: str) -> "RecoveryRequestBuilder":
        self.execution_id = execution_id
        return self
    
    def with_task_id(self, task_id: str) -> "RecoveryRequestBuilder":
        self.task_id = task_id
        return self
    
    def with_failure_kind(self, kind: str) -> "RecoveryRequestBuilder":
        self.failure_kind = kind
        return self
    
    def with_failure_reason(self, reason: str) -> "RecoveryRequestBuilder":
        self.failure_reason = reason
        return self
    
    def with_failure_code(self, code: str) -> "RecoveryRequestBuilder":
        self.failure_code = code
        return self
    
    def build(self) -> RecoveryRequest:
        if not self.execution_id:
            raise ValueError("execution_id is required")
        if not self.task_id:
            raise ValueError("task_id is required")
        
        return RecoveryRequest(
            execution_id=self.execution_id,
            task_id=self.task_id,
            failure_kind=self.failure_kind,
            failure_reason=self.failure_reason,
            failure_code=self.failure_code,
        )


__all__ = [
    "BuildLifecycleRequest",
    "BuildLifecycleRequestBuilder",
    "TransitionRequest",
    "TransitionRequestBuilder",
    "WebLifecycleRequest",
    "WebLifecycleRequestBuilder",
    "RecoveryRequest",
    "RecoveryRequestBuilder",
]