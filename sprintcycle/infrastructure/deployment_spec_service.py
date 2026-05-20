"""Minimal Phase 3 deployment spec service.

This service represents the smallest self-built layer for AutoGPT-style
platform launch responsibilities: it turns a lifecycle contract into a
platform deployment specification and a start-ready launch plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class DeploymentSpecService:
    def build_spec(
        self, contract: Dict[str, Any], *, launch_mode: str = "auto", platform: str = "dashboard"
    ) -> Dict[str, Any]:
        contract = dict(contract or {})
        evaluation = dict(contract.get("evaluation") or contract.get("evaluation_refs") or {})
        score_card = dict(evaluation.get("score_card") or {})
        runtime = dict(contract.get("runtime") or {})
        promotion = dict(contract.get("promotion") or {})
        spec = {
            "platform": platform,
            "launch_mode": launch_mode,
            "execution_id": str(contract.get("execution_id") or ""),
            "stage": str(contract.get("lifecycle", {}).get("stage") or contract.get("stage") or "new"),
            "status": str(contract.get("lifecycle", {}).get("status") or contract.get("status") or "pending"),
            "contract_score": int(score_card.get("total") or contract.get("completion_score") or 0),
            "promotion_ready": bool(promotion.get("passed") or promotion.get("status") == "promotable"),
            "runtime_ready": bool(runtime.get("healthy") or runtime.get("deploy_ready")),
            "entrypoint": "sprintcycle.platform.launch",
            "args": {
                "execution_id": str(contract.get("execution_id") or ""),
                "project_path": str(
                    contract.get("normalized_request", {}).get("project_path") or contract.get("project_path") or ""
                ),
            },
        }
        spec["launch_ready"] = bool(spec["promotion_ready"] and spec["runtime_ready"] and spec["contract_score"] >= 70)
        return {"success": True, "data": spec}

    def launch_plan(
        self, contract: Dict[str, Any], *, launch_mode: str = "auto", platform: str = "dashboard"
    ) -> Dict[str, Any]:
        spec = self.build_spec(contract, launch_mode=launch_mode, platform=platform).get("data", {})
        plan = {
            "autogpt_responsibility": "deployment_spec_and_platform_launch",
            "phase": "phase_3",
            "steps": [
                "collect contract",
                "validate promotion readiness",
                "prepare runtime launch args",
                "start platform",
                "record launch audit",
            ],
            "spec": spec,
        }
        return {"success": True, "data": plan}
