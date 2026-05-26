"""Application layer EventBus integration.

This module provides the application-level event-driven orchestration
that connects all domain subdomains.

**Event Flow Configuration:**
```
Execution → Governance → Evolution
    ↓            ↓            ↓
SprintCompleted → GovernanceCompleted → EvolutionPromoted
```

**Usage:**
```python
from sprintcycle.application.events import get_orchestration_bus

# Get the orchestration event bus
bus = get_orchestration_bus()

# Publish an event
await bus.publish(SprintCompleted(...))
```
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional

from sprintcycle.domain.core.events import (
    EventBus,
    get_default_event_bus,
    SprintCompleted,
    ReleasePlanCompleted,
    GovernanceCompleted,
    EvolutionPromoted,
    StageTransitioned,
    RecoveryTriggered,
)

from sprintcycle.domain.core.governance.aggregates import (
    create_governance_session,
    DEFAULT_REVIEW_RULESET,
)

from sprintcycle.domain.core.evolution.aggregates import (
    create_evolution_request,
)

from sprintcycle.domain.core.lifecycle import (
    create_lifecycle,
    LifecycleStage,
)


# =============================================================================
# Orchestration Handlers
# =============================================================================


class SprintCompleteHandler:
    """
    Handler: SprintCompleted → triggers Governance check.
    
    When a sprint completes, automatically start governance review.
    """
    
    def __init__(self, governance_starter: Optional[Callable] = None):
        self._governance_starter = governance_starter or self._default_governance_starter
    
    async def _default_governance_starter(
        self,
        execution_id: str,
        gate: str,
        release_plan_id: str,
    ) -> None:
        """Default governance starter implementation."""
        session = create_governance_session(
            gate=gate,
            execution_id=execution_id,
            project_path="/path/to/project",
            release_plan_id=release_plan_id,
        )
        session = session.start()
        # Apply default rules
        for rule in DEFAULT_REVIEW_RULESET.get_rules_for_gate(gate):
            session = session.add_rule_evaluation(...)
        session = session.complete()
        print(f"Governance session {session.session_id} completed: {session.status}")
    
    async def handle(self, event: SprintCompleted) -> None:
        """Handle SprintCompleted event."""
        print(f"Handling SprintCompleted: {event.sprint_id}")
        await self._governance_starter(
            execution_id=event.execution_id if hasattr(event, 'execution_id') else "",
            gate="review",
            release_plan_id=event.release_plan_id,
        )


class ReleasePlanCompleteHandler:
    """
    Handler: ReleasePlanCompleted → triggers Governance.
    
    When all sprints in a release plan complete, start governance check.
    """
    
    def __init__(self, governance_starter: Optional[Callable] = None):
        self._governance_starter = governance_starter or self._default_governance_starter
    
    async def _default_governance_starter(
        self,
        execution_id: str,
        gate: str,
        release_plan_id: str,
    ) -> None:
        """Default governance starter."""
        session = create_governance_session(
            gate=gate,
            execution_id=execution_id,
            project_path="/path/to/project",
            release_plan_id=release_plan_id,
        )
        session = session.start()
        session = session.complete()
        print(f"ReleasePlan governance {session.session_id} completed: {session.status}")
    
    async def handle(self, event: ReleasePlanCompleted) -> None:
        """Handle ReleasePlanCompleted event."""
        print(f"Handling ReleasePlanCompleted: {event.release_plan_id}")
        if event.governance_required:
            await self._governance_starter(
                execution_id=event.execution_id,
                gate="review",
                release_plan_id=event.release_plan_id,
            )


class GovernanceCompleteHandler:
    """
    Handler: GovernanceCompleted → triggers Evolution.
    
    When governance passes, start evolution process.
    """
    
    def __init__(self, evolution_starter: Optional[Callable] = None):
        self._evolution_starter = evolution_starter or self._default_evolution_starter
    
    async def _default_evolution_starter(
        self,
        project_path: str,
        governance_session_id: str,
    ) -> None:
        """Default evolution starter."""
        evo = create_evolution_request(
            project_path=project_path,
            target="code",
            mode="single_sprint",
        )
        evo = evo.attach_governance(governance_session_id, approved=True)
        evo = evo.create_sandbox(f"sandbox-{governance_session_id}")
        print(f"Evolution request {evo.request_id} created")
    
    async def handle(self, event: GovernanceCompleted) -> None:
        """Handle GovernanceCompleted event."""
        print(f"Handling GovernanceCompleted: {event.session_id}")
        if event.passed:
            project_path = event.metadata.get("project_path", "/path/to/project")
            await self._evolution_starter(
                project_path=project_path,
                governance_session_id=event.session_id,
            )
        else:
            print(f"Governance failed, skipping evolution")


class LifecycleTransitionHandler:
    """
    Handler: StageTransitioned → updates lifecycle tracking.
    
    Track lifecycle stage transitions for observability.
    """
    
    async def handle(self, event: StageTransitioned) -> None:
        """Handle StageTransitioned event."""
        print(f"Lifecycle transition: {event.from_stage} → {event.to_stage}")


# =============================================================================
# Orchestration Bus
# =============================================================================


class OrchestrationEventBus:
    """
    Application-level event bus for domain orchestration.
    
    This bus connects all domain subdomains through event handlers.
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self._bus = event_bus or get_default_event_bus()
        self._subscriptions = []
    
    async def start(self) -> None:
        """Start the orchestration bus and register handlers."""
        # Register execution handlers
        sprint_handler = SprintCompleteHandler()
        release_handler = ReleasePlanCompleteHandler()
        
        # Register governance handlers
        governance_handler = GovernanceCompleteHandler()
        
        # Register lifecycle handlers
        lifecycle_handler = LifecycleTransitionHandler()
        
        # Subscribe to events
        self._bus.subscribe(self._create_subscription(sprint_handler, SprintCompleted))
        self._bus.subscribe(self._create_subscription(release_handler, ReleasePlanCompleted))
        self._bus.subscribe(self._create_subscription(governance_handler, GovernanceCompleted))
        self._bus.subscribe(self._create_subscription(lifecycle_handler, StageTransitioned))
        
        print("Orchestration event bus started")
    
    def _create_subscription(
        self,
        handler,
        event_type,
    ):
        """Create a subscription wrapper."""
        import uuid
        
        class HandlerWrapper:
            handler_id = f"wrapper-{uuid.uuid4().hex[:8]}"
            
            @property
            def subscribed_event_types(self):
                return [event_type.__name__]
            
            async def handle(self, event):
                if isinstance(event, event_type):
                    await handler.handle(event)
        
        return HandlerWrapper()
    
    async def publish(self, event) -> None:
        """Publish an event to the bus."""
        await self._bus.publish(event)
    
    async def stop(self) -> None:
        """Stop the orchestration bus."""
        for sub in self._subscriptions:
            sub.unsubscribe()
        self._subscriptions.clear()
        print("Orchestration event bus stopped")


# =============================================================================
# Singleton and Factory
# =============================================================================


_orchestration_bus: Optional[OrchestrationEventBus] = None


def get_orchestration_bus() -> OrchestrationEventBus:
    """Get the singleton orchestration event bus."""
    global _orchestration_bus
    if _orchestration_bus is None:
        _orchestration_bus = OrchestrationEventBus()
    return _orchestration_bus


async def start_orchestration() -> OrchestrationEventBus:
    """Start the orchestration bus."""
    bus = get_orchestration_bus()
    await bus.start()
    return bus


async def stop_orchestration() -> None:
    """Stop the orchestration bus."""
    global _orchestration_bus
    if _orchestration_bus:
        await _orchestration_bus.stop()
        _orchestration_bus = None


# =============================================================================
# Workflow Orchestrators
# =============================================================================


class LifecycleOrchestrator:
    """
    Orchestrator for lifecycle workflows.
    
    Coordinates the complete lifecycle from execution to promotion.
    """
    
    def __init__(self, event_bus: Optional[OrchestrationEventBus] = None):
        self._bus = event_bus or get_orchestration_bus()
    
    async def execute_lifecycle(
        self,
        execution_id: str,
        task_id: str,
        project_path: str,
    ) -> None:
        """Execute the complete lifecycle workflow."""
        # Create lifecycle
        lifecycle = create_lifecycle(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path,
        )
        
        # Transition through stages
        lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
        await self._bus.publish(StageTransitioned(
            execution_id=execution_id,
            task_id=task_id,
            from_stage="new",
            to_stage="normalized",
        ))
        
        lifecycle = lifecycle.transition_to(LifecycleStage.PLANNED)
        await self._bus.publish(StageTransitioned(
            execution_id=execution_id,
            task_id=task_id,
            from_stage="normalized",
            to_stage="planned",
        ))
        
        # Continue with more stages...
        print(f"Lifecycle {lifecycle.contract_id} workflow initiated")


class ExecutionOrchestrator:
    """
    Orchestrator for execution workflows.
    
    Coordinates sprint execution and release plan completion.
    """
    
    def __init__(self, event_bus: Optional[OrchestrationEventBus] = None):
        self._bus = event_bus or get_orchestration_bus()
    
    async def execute_sprint(
        self,
        sprint_id: str,
        release_plan_id: str,
        execution_id: str = "",
    ) -> None:
        """Execute a sprint and publish completion event."""
        # Simulate sprint execution
        await asyncio.sleep(0.1)
        
        # Publish completion event
        event = SprintCompleted(
            sprint_id=sprint_id,
            release_plan_id=release_plan_id,
            status="success",
            success_rate=1.0,
            metadata={"execution_id": execution_id},
        )
        await self._bus.publish(event)
    
    async def complete_release_plan(
        self,
        release_plan_id: str,
        execution_id: str,
        overall_success_rate: float,
    ) -> None:
        """Complete a release plan and publish event."""
        event = ReleasePlanCompleted(
            release_plan_id=release_plan_id,
            execution_id=execution_id,
            overall_success_rate=overall_success_rate,
            governance_required=True,
        )
        await self._bus.publish(event)


__all__ = [
    # Handlers
    "SprintCompleteHandler",
    "ReleasePlanCompleteHandler",
    "GovernanceCompleteHandler",
    "LifecycleTransitionHandler",
    # Orchestration Bus
    "OrchestrationEventBus",
    "get_orchestration_bus",
    "start_orchestration",
    "stop_orchestration",
    # Orchestrators
    "LifecycleOrchestrator",
    "ExecutionOrchestrator",
]
