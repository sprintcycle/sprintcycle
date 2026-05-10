"""Platform dashboard views for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PlatformSpecView:
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return dict(self.payload)


@dataclass
class PlatformComposeView:
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return dict(self.payload)


__all__ = ["PlatformSpecView", "PlatformComposeView"]
