"""Small state machine for phase 1 execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


ExecutionState = str
"""Simple execution state identifier used by the core state machine."""


@dataclass
class ExecutionStateMachine:
    transitions: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "created": ["running"],
            "running": ["sandboxing", "failed"],
            "sandboxing": ["validating", "failed"],
            "validating": ["deploying", "failed"],
            "deploying": ["deployed", "failed"],
            "deployed": ["succeeded", "failed"],
            "succeeded": [],
            "failed": [],
        }
    )

    def can_transition(self, current: str, target: str) -> bool:
        return target in self.transitions.get(current, [])

    def next_state(self, current: str) -> str:
        options = self.transitions.get(current, [])
        return options[0] if options else current

    def to_dict(self) -> Dict[str, List[str]]:
        return dict(self.transitions)
