"""Runtime registry for deployed user projects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


@dataclass
class RuntimeRegistry:
    records: List[Dict[str, Any]] = field(default_factory=list)

    def register(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        verification = dict(payload.get("verification") or {})
        record = {
            "runtime_id": payload.get("runtime_id") or str(uuid4()),
            "project_name": payload.get("project_name") or payload.get("name") or "user-project",
            "status": payload.get("status") or "deployed",
            "ready": bool(payload.get("ready", True)),
            "verified": bool(verification.get("verified", payload.get("verified", False))),
            "healthy": bool(verification.get("healthy", payload.get("healthy", False))),
            "deploy_ready": bool(payload.get("deploy_ready", False)),
            "port": payload.get("port"),
            "url": payload.get("url"),
            "container_id": payload.get("container_id"),
            "suggestion_id": payload.get("suggestion_id"),
            "evolution_id": payload.get("evolution_id"),
            "verification": verification,
            "metadata": dict(payload.get("metadata") or {}),
            "created_at": now,
            "updated_at": now,
        }
        self.records.append(record)
        return {"success": True, "data": record}

    def update(self, runtime_id: str, **changes: Any) -> Dict[str, Any]:
        rid = str(runtime_id)
        for record in self.records:
            if str(record.get("runtime_id")) == rid:
                verification = dict(record.get("verification") or {})
                if "verification" in changes and isinstance(changes.get("verification"), dict):
                    verification.update(changes.pop("verification"))
                record.update(changes)
                if verification:
                    record["verification"] = verification
                    record["verified"] = bool(verification.get("verified", record.get("verified", False)))
                    record["healthy"] = bool(verification.get("healthy", record.get("healthy", False)))
                if "ready" in changes:
                    record["ready"] = bool(changes.get("ready"))
                if "deploy_ready" in changes:
                    record["deploy_ready"] = bool(changes.get("deploy_ready"))
                record["updated_at"] = datetime.now(timezone.utc).isoformat()
                return {"success": True, "data": record}
        return {"success": False, "error": f"runtime not found: {rid}"}

    def list(self) -> Dict[str, Any]:
        return {"success": True, "data": list(self.records), "total": len(self.records)}

    def latest(self) -> Dict[str, Any]:
        record = self.records[-1] if self.records else None
        return {"success": True, "data": record}
