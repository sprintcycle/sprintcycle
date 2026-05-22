"""Minimal platform launch service for Phase 3.

The launch service uses a deployment spec to produce a platform start result.
It does not automate external infrastructure; it only self-hosts the smallest
launchable workflow and returns auditable state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from sprintcycle.infrastructure.deployment.deployment_spec_service import DeploymentSpecService


@dataclass
class PlatformLaunchService:
    spec_service: DeploymentSpecService

    def launch(
        self, contract: Dict[str, Any], *, launch_mode: str = "auto", platform: str = "dashboard"
    ) -> Dict[str, Any]:
        spec_result = self.spec_service.build_spec(contract, launch_mode=launch_mode, platform=platform)
        spec = dict(spec_result.get("data") or {})
        launch_ready = bool(spec.get("launch_ready"))
        return {
            "success": launch_ready,
            "data": {
                "spec": spec,
                "status": "running" if launch_ready else "blocked",
                "launch_mode": launch_mode,
                "platform": platform,
                "reason": "launch ready" if launch_ready else "contract or runtime not ready",
                "autogpt_responsibility": "deployment_spec_and_platform_launch",
            },
        }
