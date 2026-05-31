"""Lifecycle domain services.

This module provides domain-level validation utilities for lifecycle operations.

**Design Principles:**
- Services are stateless and follow DDD domain service patterns
- All business logic is encapsulated in LifecycleStateMachine
- Helper functions provide convenient access to common validations
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class StateTransition:
    """State transition record."""
    entity: str
    entity_id: str
    from_status: str
    to_status: str
    reason: str = ""
    metadata: Dict[str, object] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, object]:
        return {
            "entity": self.entity,
            "entity_id": self.entity_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "StateTransition",
]
