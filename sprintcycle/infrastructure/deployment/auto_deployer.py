"""Minimal auto deployer for phase 1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4

from .runtime_registry import RuntimeRegistry


@dataclass
class AutoDeployer:
    runtime_registry: RuntimeRegistry = field(default_factory=RuntimeRegistry)

    def deploy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        runtime_payload = {
            "runtime_id": payload.get("runtime_id") or str(uuid4()),
            "project_name": payload.get("project_name") or "user-project",
            "status": "deployed",
            "port": payload.get("port") or 3000,
            "url": payload.get("url") or "http://localhost:3000",
            "container_id": payload.get("container_id") or f"container-{uuid4().hex[:8]}",
            "metadata": dict(payload.get("metadata") or {}),
        }
        return self.runtime_registry.register(runtime_payload)

    def to_payload(self) -> Dict[str, Any]:
        return self.runtime_registry.list()


def create_auto_deployer(runtime_registry: Optional[RuntimeRegistry] = None) -> AutoDeployer:
    return AutoDeployer(runtime_registry=runtime_registry or RuntimeRegistry())
