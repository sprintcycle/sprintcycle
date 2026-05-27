"""Event handlers and EventBus for domain events.

This module provides the event-driven communication infrastructure
between subdomains.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from .common import DomainEvent


# =============================================================================
# Event Handler Protocol
# =============================================================================


class EventHandler(ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle the given event."""
        raise NotImplementedError

    @property
    @abstractmethod
    def subscribed_event_types(self) -> List[str]:
        """Return list of event types this handler subscribes to."""
        raise NotImplementedError

    @property
    def handler_id(self) -> str:
        """Unique identifier for this handler."""
        return f"{self.__class__.__name__}_{id(self)}"


# =============================================================================
# Event Bus
# =============================================================================


class EventBus:
    """
    Domain event bus for publishing and subscribing to events.

    This is the central hub for cross-subdomain communication using
    the event-driven pattern.

    **Usage:**
    ```python
    # Subscribe
    handler = SprintCompleteToGovernanceHandler(governance_service)
    subscription = event_bus.subscribe(handler)

    # Publish
    await event_bus.publish(SprintCompleted(...))

    # Unsubscribe
    subscription.unsubscribe()
    ```
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._subscriptions: List[Subscription] = []
        self._event_history: List[DomainEvent] = []
        self._max_history: int = 1000

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed handlers.

        Errors in handlers are logged but do not stop other handlers.
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history :]

        event_type = event.event_type
        handlers = list(self._handlers.get(event_type, []))

        if not handlers:
            logger.debug("No handlers for event type: {}", event_type)
            return

        logger.debug(
            "Publishing event {} to {} handlers", event_type, len(handlers)
        )

        # Run all handlers concurrently
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._safe_handle(handler, event))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_handle(self, handler: EventHandler, event: DomainEvent) -> None:
        """Execute handler safely, catching any exceptions."""
        try:
            await handler.handle(event)
        except Exception as e:
            logger.exception(
                "Handler {} failed for event {}: {}",
                handler.handler_id,
                event.event_type,
                e,
            )

    def subscribe(self, handler: EventHandler) -> Subscription:
        """
        Subscribe a handler to its registered event types.

        Returns a Subscription that can be used to unsubscribe.
        """
        for event_type in handler.subscribed_event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                logger.debug(
                    "Handler {} subscribed to event type: {}",
                    handler.handler_id,
                    event_type,
                )

        subscription = Subscription(handler, self)
        self._subscriptions.append(subscription)
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe a handler from all its event types."""
        handler = subscription.handler
        for event_type in handler.subscribed_event_types:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h is not handler
                ]
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
                logger.debug(
                    "Handler {} unsubscribed from event type: {}",
                    handler.handler_id,
                    event_type,
                )

        self._subscriptions = [
            s for s in self._subscriptions if s is not subscription
        ]

    def get_handlers_for(self, event_type: str) -> List[EventHandler]:
        """Get all handlers subscribed to a specific event type."""
        return list(self._handlers.get(event_type, []))

    @property
    def subscribed_count(self) -> int:
        """Total number of subscriptions."""
        return len(self._subscriptions)

    @property
    def event_history(self) -> List[DomainEvent]:
        """Recent event history."""
        return list(self._event_history)

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history = []


@dataclass
class Subscription:
    """Represents a handler subscription to the event bus."""

    handler: EventHandler
    bus: EventBus

    def unsubscribe(self) -> None:
        """Unsubscribe this handler from the event bus."""
        self.bus.unsubscribe(self)


# =============================================================================
# Pre-built Event Handlers
# =============================================================================


class SprintCompleteToGovernanceHandler(EventHandler):
    """
    Handler: SprintCompleted → triggers Governance check.

    This handler listens for SprintCompleted or ReleasePlanCompleted
    events and initiates the Governance process.
    """

    def __init__(
        self,
        governance_starter: Callable[..., Any],
    ) -> None:
        """
        Args:
            governance_starter: Callable that starts governance.
                               Signature: async def(start_execution_id, gate, release_plan_id)
        """
        self._governance_starter = governance_starter

    @property
    def subscribed_event_types(self) -> List[str]:
        return ["SprintCompleted", "ReleasePlanCompleted"]

    async def handle(self, event: DomainEvent) -> None:
        from .common import ReleasePlanCompleted, SprintCompleted

        if isinstance(event, ReleasePlanCompleted):
            logger.info(
                "ReleasePlan {} completed, triggering governance",
                event.release_plan_id,
            )
            await self._governance_starter(
                execution_id=event.execution_id,
                gate="review",
                release_plan_id=event.release_plan_id,
            )
        elif isinstance(event, SprintCompleted):
            logger.debug(
                "Sprint {} completed with status {}",
                event.sprint_id,
                event.status,
            )


class GovernanceCompleteToEvolutionHandler(EventHandler):
    """
    Handler: GovernanceCompleted → triggers Evolution.

    This handler listens for GovernanceCompleted events and
    initiates the Evolution process if governance passed.
    """

    def __init__(
        self,
        evolution_starter: Callable[..., Any],
    ) -> None:
        """
        Args:
            evolution_starter: Callable that starts evolution.
                              Signature: async def(project_path, governance_session_id)
        """
        self._evolution_starter = evolution_starter

    @property
    def subscribed_event_types(self) -> List[str]:
        return ["GovernanceCompleted"]

    async def handle(self, event: DomainEvent) -> None:
        from .common import GovernanceCompleted

        if isinstance(event, GovernanceCompleted):
            if event.passed:
                logger.info(
                    "Governance {} passed, triggering evolution",
                    event.session_id,
                )
                # Get project_path from metadata
                project_path = event.metadata.get("project_path", "")
                if project_path:
                    await self._evolution_starter(
                        project_path=project_path,
                        governance_session_id=event.session_id,
                    )
            else:
                logger.warning(
                    "Governance {} failed, evolution not triggered",
                    event.session_id,
                )


class LifecycleStageTransitionHandler(EventHandler):
    """
    Handler: StageTransitioned → updates Lifecycle tracking.

    This handler listens for stage transitions and updates
    any external lifecycle tracking systems.
    """

    def __init__(
        self,
        lifecycle_tracker: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._lifecycle_tracker = lifecycle_tracker

    @property
    def subscribed_event_types(self) -> List[str]:
        return ["StageTransitioned", "RecoveryTriggered"]

    async def handle(self, event: DomainEvent) -> None:
        from .common import RecoveryTriggered, StageTransitioned

        if isinstance(event, StageTransitioned):
            logger.debug(
                "Lifecycle transition: {} → {} for execution {}",
                event.from_stage,
                event.to_stage,
                event.execution_id,
            )
        elif isinstance(event, RecoveryTriggered):
            logger.info(
                "Recovery triggered: {} → {} for execution {}",
                event.from_stage,
                event.target_stage,
                event.execution_id,
            )

        if self._lifecycle_tracker:
            await self._lifecycle_tracker(event)


class ExecutionMetricsHandler(EventHandler):
    """
    Handler: Aggregates execution metrics.

    This handler collects metrics from execution events
    for observability.
    """

    def __init__(self) -> None:
        self._metrics: Dict[str, Any] = {
            "sprints_completed": 0,
            "tasks_completed": 0,
            "failures": 0,
        }

    @property
    def subscribed_event_types(self) -> List[str]:
        return [
            "SprintCompleted",
            "TaskCompleted",
            "GovernanceCompleted",
            "EvolutionPromoted",
        ]

    async def handle(self, event: DomainEvent) -> None:
        from .common import (
            EvolutionPromoted,
            GovernanceCompleted,
            SprintCompleted,
            TaskCompleted,
        )

        if isinstance(event, TaskCompleted):
            self._metrics["tasks_completed"] += 1
            if event.status == "failed":
                self._metrics["failures"] += 1
        elif isinstance(event, SprintCompleted):
            self._metrics["sprints_completed"] += 1
        elif isinstance(event, GovernanceCompleted):
            self._metrics["governance_runs"] = (
                self._metrics.get("governance_runs", 0) + 1
            )
        elif isinstance(event, EvolutionPromoted):
            self._metrics["evolutions_promoted"] = (
                self._metrics.get("evolutions_promoted", 0) + 1
            )

    @property
    def metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)


# =============================================================================
# Event Bus Factory
# =============================================================================


_default_event_bus: Optional[EventBus] = None


def get_default_event_bus() -> EventBus:
    """Get or create the default event bus singleton."""
    global _default_event_bus
    if _default_event_bus is None:
        _default_event_bus = EventBus()
    return _default_event_bus


def reset_default_event_bus() -> None:
    """Reset the default event bus (mainly for testing)."""
    global _default_event_bus
    _default_event_bus = None


__all__ = [
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
