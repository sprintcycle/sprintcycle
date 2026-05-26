"""Evolution subdomain aggregates.

This module provides DDD aggregates for the Evolution subdomain.

**Usage:**
```python
from sprintcycle.domain.core.evolution.aggregates import (
    EvolutionRequest,
    SandboxSession,
    VersionArtifact,
    create_evolution_request,
    create_sandbox_session,
)
```
"""

from .evolution_aggregates import (
    # Enums
    EvolutionTarget,
    EvolutionMode,
    EvolutionStage,
    SandboxBackend,
    SandboxStatus,
    # Value Objects
    VersionArtifact,
    ValidationCheck,
    SandboxSpec,
    GovernanceRef,
    SandboxRef,
    VersionRef,
    # Aggregates
    SandboxSession,
    EvolutionRequest,
    # Factory Functions
    create_evolution_request,
    create_sandbox_session,
)

__all__ = [
    # Enums
    "EvolutionTarget",
    "EvolutionMode",
    "EvolutionStage",
    "SandboxBackend",
    "SandboxStatus",
    # Value Objects
    "VersionArtifact",
    "ValidationCheck",
    "SandboxSpec",
    "GovernanceRef",
    "SandboxRef",
    "VersionRef",
    # Aggregates
    "SandboxSession",
    "EvolutionRequest",
    # Factory Functions
    "create_evolution_request",
    "create_sandbox_session",
]
