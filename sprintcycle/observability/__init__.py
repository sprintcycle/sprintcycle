"""Canonical observability layer for SprintCycle V2.

This package now exposes the canonical event model and a thin facade only.
The legacy local replay/trace store implementations have been removed in V2.
"""

from __future__ import annotations

from .event_models import EventStoreSnapshot, ObservabilityEvent
from .facade import ObservabilityFacade

__all__ = [
    "ObservabilityFacade",
    "ObservabilityEvent",
    "EventStoreSnapshot",
]
