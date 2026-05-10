"""Replay projection for dashboard consumption."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ReplayProjection:
    run_id: str
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        steps = []
        for idx, event in enumerate(self.timeline):
            steps.append(
                {
                    "index": idx,
                    "kind": str(event.get("kind") or event.get("type") or event.get("event_type") or "event"),
                    "data": event,
                }
            )
        return {
            "run_id": self.run_id,
            "timeline": list(self.timeline),
            "steps": steps,
            "event_count": len(self.timeline),
        }
