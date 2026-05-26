"""Domain events module.

This module provides the event-driven communication infrastructure
for cross-subdomain communication in SprintCycle.

**Event Flow:**
```
Execution → Governance → Evolution
    ↓            ↓            ↓
SprintCompleted → GovernanceCompleted → EvolutionPromoted
```

**Usage:**
```python
from sprintcycle.domain.core.events import (
    EventBus,
    get_default_event_bus,
    SprintCompleted,
    GovernanceStarted,
)

# Get the event bus
bus = get_default_event_bus()

# Subscribe a handler
async def on_sprint_complete(event: SprintCompleted):
    print(f"Sprint {event.sprint_id} completed")

bus.subscribe(on_sprint_complete)

# Publish an event
await bus.publish(SprintCompleted(...))
```
"""

from .common import (
    # Base
    DomainEvent,
    ALL_EVENTS,
    get_event_by_type,
    # Execution Events
    ExecutionStarted,
    SprintStarted,
    TaskStarted,
    TaskCompleted,
    SprintCompleted,
    ReleasePlanCompleted,
    # Lifecycle Events
    StageTransitioned,
    RecoveryTriggered,
    # Governance Events
    GovernanceStarted,
    RuleEvaluated,
    GovernanceCompleted,
    HitlDecisionRequested,
    HitlDecisionMade,
    # Evolution Events
    EvolutionRequested,
    SandboxCreated,
    VersionCreated,
    ValidationCompleted,
    EvolutionPromoted,
    RollbackPerformed,
)

from .handlers import (
    EventHandler,
    EventBus,
    Subscription,
    SprintCompleteToGovernanceHandler,
    GovernanceCompleteToEvolutionHandler,
    LifecycleStageTransitionHandler,
    ExecutionMetricsHandler,
    get_default_event_bus,
    reset_default_event_bus,
)

__all__ = [
    # Base
    "DomainEvent",
    "ALL_EVENTS",
    "get_event_by_type",
    # Execution Events
    "ExecutionStarted",
    "SprintStarted",
    "TaskStarted",
    "TaskCompleted",
    "SprintCompleted",
    "ReleasePlanCompleted",
    # Lifecycle Events
    "StageTransitioned",
    "RecoveryTriggered",
    # Governance Events
    "GovernanceStarted",
    "RuleEvaluated",
    "GovernanceCompleted",
    "HitlDecisionRequested",
    "HitlDecisionMade",
    # Evolution Events
    "EvolutionRequested",
    "SandboxCreated",
    "VersionCreated",
    "ValidationCompleted",
    "EvolutionPromoted",
    "RollbackPerformed",
    # Handlers
    "EventHandler",
    "EventBus",
    "Subscription",
    "SprintCompleteToGovernanceHandler",
    "GovernanceCompleteToEvolutionHandler",
    "LifecycleStageTransitionHandler",
    "ExecutionMetricsHandler",
    "get_default_event_bus",
    "reset_default_event_bus",
]
