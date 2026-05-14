"""Runtime helpers for a Phoenix-style observability backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .exporter import PhoenixExporterSpec


@dataclass
class PhoenixRuntimeSpec:
    project_name: str = "sprintcycle"
    export_mode: str = "trace"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "export_mode": self.export_mode,
            "config": dict(self.config),
        }


@dataclass
class PhoenixRuntimeAdapter:
    spec: PhoenixRuntimeSpec = field(default_factory=PhoenixRuntimeSpec)
    exporters: List[str] = field(default_factory=lambda: ["trace", "replay", "eval"])
    exporter: PhoenixExporterSpec = field(default_factory=PhoenixExporterSpec)

    def build_exporter(self) -> Dict[str, Any]:
        try:
            import phoenix  # type: ignore  # noqa: F401
        except Exception as exc:
            raise RuntimeError("Phoenix runtime is required for V2 observability") from exc

        return {
            "spec": self.spec.to_dict(),
            "exporters": list(self.exporters),
            "exporter": self.exporter.to_dict(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec": self.spec.to_dict(),
            "exporters": list(self.exporters),
            "exporter": self.exporter.to_dict(),
        }


__all__ = ["PhoenixRuntimeSpec", "PhoenixRuntimeAdapter"]
