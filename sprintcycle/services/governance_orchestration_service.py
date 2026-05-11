"""Governance orchestration service.

Keeps governance check and HITL read/write coordination out of the facade.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from ..governance.facade import GovernanceFacade
from ..hooks import HookContext, HookPhase, HookRegistry


@dataclass
class GovernanceOrchestrationService:
    project_path: str
    config: Any
    governance: Optional[GovernanceFacade] = None
    hooks: HookRegistry | None = None

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        from ..governance.arch_guard.config import ArchGuardConfig
        from ..governance.arch_guard.engine import ArchGuardEngine
        from ..governance.arch_guard.reporter import GovernanceReportAdapter

        start = time.time()
        hook_ctx = HookContext(
            domain="governance",
            action="check",
            subject_id=gate,
            project_path=self.project_path,
            payload=dict(kwargs),
            metadata=dict(kwargs.get("context") or {}),
        )
        if self.hooks is not None:
            for result in self.hooks.emit(domain="governance", action="check", phase=HookPhase.BEFORE, context=hook_ctx):
                if result.blocked or not result.ok:
                    return {"success": False, "error": result.message or "blocked by before_governance_check", "hook": result.to_dict()}
        try:
            cfg = ArchGuardConfig.from_runtime_config(self.config, self.project_path)
            engine = ArchGuardEngine(cfg)
            context: Dict[str, Any] = dict(kwargs.get("context") or {})
            if gate == "planning":
                release_plan = kwargs.get("release_plan")
                if release_plan is None:
                    return {"success": False, "error": "planning gate requires release_plan"}
                report = asyncio.run(engine.run_planning_gate(self.project_path, release_plan=release_plan, context=context))
            else:
                report = asyncio.run(engine.run_review_gate(self.project_path, context=context))
            gov = GovernanceReportAdapter.to_governance_report(report)
            payload = {"success": True, "gate": gate, "data": gov.to_dict(), "duration": time.time() - start}
            if self.hooks is not None:
                self.hooks.emit(domain="governance", action="check", phase=HookPhase.AFTER, context=hook_ctx)
                self.hooks.emit_domain_event("governance.checked", {"gate": gate, "report": payload["data"], "project_path": self.project_path})
            return payload
        except Exception as e:
            logger.exception("governance_check failed")
            if self.hooks is not None:
                self.hooks.emit(domain="governance", action="check", phase=HookPhase.FAILED, context=hook_ctx)
                self.hooks.emit_domain_event("governance.check_failed", {"gate": gate, "project_path": self.project_path, "error": str(e)})
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
