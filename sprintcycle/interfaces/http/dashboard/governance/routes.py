"""Governance domain routes.

HTTP endpoints for governance-related operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request

from sprintcycle.interfaces.http.handlers.governance import GovernanceHandler
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_governance_router(handler: GovernanceHandler, project_path: str) -> APIRouter:
    router = APIRouter()

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/governance/latest")
    async def governance_latest(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/latest", context=ctx)
        cfg = RuntimeConfig.from_project(project_path)
        root = Path(project_path).expanduser().resolve()
        rel = (cfg.governance_report_dir or ".sprintcycle").strip() or ".sprintcycle"
        out_dir = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        last = out_dir / "governance_last.json"
        planning = out_dir / "governance_planning_last.json"
        if not last.is_file() and not planning.is_file():
            raise FileNotFoundError("未找到治理报告")
        payload: Dict[str, Any] = {}
        if planning.is_file():
            payload["planning"] = planning.read_text(encoding="utf-8")
        if last.is_file():
            payload["review"] = last.read_text(encoding="utf-8")
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_reports",
            resource="/api/governance/latest",
            outcome="success",
        )
        return payload

    @router.get("/api/governance/history")
    async def governance_history(request: Request, limit: int = 50) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/history", context=ctx)
        result = await handler.governance_history(limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_history",
            resource="/api/governance/history",
            outcome="success",
        )
        return result

    @router.post("/api/governance/check")
    async def governance_check(request: Request, body: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/check", context=ctx)
        result = await handler.governance_check(gate=body.get("gate", "review"))
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_check",
            resource="/api/governance/check",
            outcome="success",
        )
        return result

    @router.get("/api/governance/lifecycle")
    async def governance_lifecycle(request: Request, execution_id: str = "") -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/lifecycle", context=ctx)
        result = await handler.governance_lifecycle(execution_id=execution_id)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.governance_lifecycle",
            resource="/api/governance/lifecycle",
            outcome="success",
        )
        return result

    return router
