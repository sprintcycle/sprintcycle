"""Governance orchestration service.

Coordinates governance checks plus pending, history, summary, and request
lookup access while emitting hook callbacks and domain events around the
check flow.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from ...governance.core.facade import GovernanceFacade
from ...domain.hooks import (
    GOVERNANCE_CHECK,
    GOVERNANCE_CHECK_FAILED_EVENT,
    GOVERNANCE_CHECKED_EVENT,
    HookContext,
    HookRegistry,
    HookRunner,
)


@dataclass
class GovernanceOrchestrationService:
    project_path: str
    config: Any
    governance: Optional[GovernanceFacade] = None
    hooks: HookRegistry | None = None

    async def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        from ...governance.arch_guard.config import ArchGuardConfig
        from ...governance.arch_guard.engine import ArchGuardEngine
        from ...governance.arch_guard.reporter import GovernanceReportAdapter

        start = time.time()
        hook_ctx = HookContext(
            domain=GOVERNANCE_CHECK[0],
            action=GOVERNANCE_CHECK[1],
            subject_id=gate,
            project_path=self.project_path,
            payload=dict(kwargs),
            metadata=dict(kwargs.get("context") or {}),
        )
        runner = HookRunner(self.hooks)
        before = runner.before(GOVERNANCE_CHECK[0], GOVERNANCE_CHECK[1], hook_ctx)
        if any(r.blocked or not r.ok for r in before):
            result = next((r for r in before if r.blocked or not r.ok), None)
            return {
                "success": False,
                "error": result.message if result and result.message else "blocked by before_governance_check",
                "hook": [r.to_dict() for r in before],
            }
        try:
            cfg = ArchGuardConfig.from_runtime_config(self.config, self.project_path)
            engine = ArchGuardEngine(cfg)
            context: Dict[str, Any] = dict(kwargs.get("context") or {})
            if gate == "planning":
                release_plan = kwargs.get("release_plan")
                if release_plan is None:
                    return {"success": False, "error": "planning gate requires release_plan"}
                report = await engine.run_planning_gate(self.project_path, release_plan=release_plan, context=context)
            else:
                report = await engine.run_review_gate(self.project_path, context=context)
            gov = GovernanceReportAdapter.to_governance_report(report)
            payload = {"success": True, "gate": gate, "data": gov.to_dict(), "duration": time.time() - start}
            runner.after(GOVERNANCE_CHECK[0], GOVERNANCE_CHECK[1], hook_ctx)
            runner.event(
                "governance",
                "check",
                GOVERNANCE_CHECKED_EVENT,
                {"gate": gate, "report": payload["data"], "project_path": self.project_path},
            )
            return payload
        except Exception as e:
            logger.exception("governance_check failed")
            runner.failed(GOVERNANCE_CHECK[0], GOVERNANCE_CHECK[1], hook_ctx)
            runner.event(
                "governance",
                "check",
                GOVERNANCE_CHECK_FAILED_EVENT,
                {"gate": gate, "project_path": self.project_path, "error": str(e)},
            )
            return {"success": False, "error": str(e), "duration": time.time() - start}

    async def pending(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": True, "data": []}
        return {"success": True, "data": await self.governance.list_pending(execution_id)}

    async def history(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": True, "data": []}
        return {"success": True, "data": await self.governance.list_history(execution_id, limit)}

    async def summary(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": True, "data": {"has_service": False, "pending_count": 0, "history_count": 0}}
        return {"success": True, "data": await self.governance.summary(execution_id, limit)}

    async def show(self, request_id: str) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        rid = (request_id or "").strip()
        if not rid:
            return {"success": False, "error": "request_id required"}
        rec = await self.governance.get_request(rid)
        if rec is None:
            return {"success": False, "error": "Request not found"}
        return {"success": True, "data": rec}


__all__ = ["GovernanceOrchestrationService"]
