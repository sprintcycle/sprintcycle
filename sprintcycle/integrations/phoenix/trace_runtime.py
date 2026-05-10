"""Concrete Phoenix trace/runtime wiring for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .exporter import PhoenixExporterSpec


@dataclass
class PhoenixTraceRuntime:
    exporter_spec: PhoenixExporterSpec = field(default_factory=PhoenixExporterSpec)

    def build(self) -> Dict[str, Any]:
        try:
            import phoenix  # type: ignore  # noqa: F401
        except Exception as exc:
            raise RuntimeError("Phoenix runtime is required for SprintCycle V2") from exc

        return {
            "exporter_spec": self.exporter_spec.to_dict(),
            "trace_runtime": {
                "project_name": self.exporter_spec.project_name,
                "endpoint": self.exporter_spec.endpoint,
            },
        }

    def emit_trace(self, events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a Phoenix-ready trace payload from SprintCycle events."""
        normalized: List[Dict[str, Any]] = []
        for event in events:
            normalized.append(
                {
                    "event_id": event.get("event_id") or event.get("id") or "",
                    "kind": event.get("kind") or event.get("type") or "event",
                    "execution_id": event.get("execution_id") or event.get("run_id") or "",
                    "timestamp": event.get("timestamp"),
                    "payload": dict(event.get("payload") or event.get("data") or {}),
                    "metadata": dict(event.get("metadata") or {}),
                }
            )
        return {
            "exporter_spec": self.exporter_spec.to_dict(),
            "events": normalized,
            "count": len(normalized),
        }


__all__ = ["PhoenixTraceRuntime"]
