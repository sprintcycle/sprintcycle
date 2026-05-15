"""In-memory runtime registry used by dashboard deployment views.

The registry keeps a minimal record of runtime linkage so the Dashboard can
show deployment state and the lifecycle layer can inspect runtime readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class RuntimeRecord:
    runtime_id: str
    project_name: str = ""
    status: str = "unknown"
    url: str = ""
    suggestion_id: str = ""
    evolution_id: str = ""
    deploy_ready: bool = False
    healthy: bool = False
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "project_name": self.project_name,
            "status": self.status,
            "url": self.url,
            "suggestion_id": self.suggestion_id,
            "evolution_id": self.evolution_id,
            "deploy_ready": self.deploy_ready,
            "healthy": self.healthy,
            "verified": self.verified,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


class RuntimeRegistry:
    def __init__(self) -> None:
        self._records: Dict[str, RuntimeRecord] = {}

    @property
    def records(self) -> List[Dict[str, Any]]:
        return [record.to_dict() for record in self._records.values()]

    def register(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        runtime_id = str(payload.get("runtime_id") or payload.get("id") or payload.get("execution_id") or payload.get("project_name") or f"runtime-{len(self._records) + 1}")
        record = RuntimeRecord(
            runtime_id=runtime_id,
            project_name=str(payload.get("project_name") or payload.get("project_path") or ""),
            status=str(payload.get("status") or payload.get("state") or "registered"),
            url=str(payload.get("url") or payload.get("endpoint") or ""),
            suggestion_id=str(payload.get("suggestion_id") or ""),
            evolution_id=str(payload.get("evolution_id") or ""),
            deploy_ready=bool(payload.get("deploy_ready", False)),
            healthy=bool(payload.get("healthy", False)),
            verified=bool(payload.get("verified", False)),
            metadata=dict(payload.get("metadata") or {}),
        )
        self._records[runtime_id] = record
        return {"success": True, "data": record.to_dict()}

    def list(self) -> Dict[str, Any]:
        return {"success": True, "data": self.records}

    def get(self, runtime_id: str) -> Dict[str, Any]:
        record = self._records.get(runtime_id)
        return record.to_dict() if record else {"runtime_id": runtime_id, "status": "missing", "success": False}
