"""Trace projection for dashboard consumption."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TraceProjection:
    run_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        nodes = []
        for idx, event in enumerate(self.events):
            kind = str(event.get("kind") or event.get("type") or event.get("event_type") or "event")
            nodes.append(
                {
                    "id": f"{self.run_id}:{idx}",
                    "label": kind,
                    "event": event,
                }
            )
        return {
            "run_id": self.run_id,
            "events": list(self.events),
            "nodes": nodes,
            "event_count": len(self.events),
        }
