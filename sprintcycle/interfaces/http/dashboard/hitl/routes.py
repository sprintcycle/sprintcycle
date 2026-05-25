"""HITL (Human-in-the-Loop) domain routes.

HTTP endpoints for human intervention operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.application.factories.http import HTTPServices
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_hitl_router(services: HTTPServices, project_path: str) -> APIRouter:
    router = APIRouter()

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/hitl/pending")
    async def hitl_pending(request: Request, execution_id: str = "") -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/hitl/pending", context=ctx)
        result = services.hitl_pending(execution_id if execution_id else None)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.hitl_pending",
            resource="/api/hitl/pending",
            outcome="success",
        )
        return result

    @router.get("/api/hitl/history")
    async def hitl_history(request: Request, execution_id: str = "", limit: int = 50) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/hitl/history", context=ctx)
        result = services.hitl_history(execution_id if execution_id else None, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.hitl_history",
            resource="/api/hitl/history",
            outcome="success",
        )
        return result

    @router.post("/api/hitl/{request_id}/decision")
    async def hitl_decision(request: Request, request_id: str, body: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/hitl/{request_id}/decision", context=ctx)
        result = services.hitl_submit(
            request_id,
            body.get("decision", ""),
            body.get("note"),
        )
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.hitl_decision",
            resource="/api/hitl/{request_id}/decision",
            outcome="success",
        )
        return result

    @router.get("/api/hitl/{request_id}")
    async def hitl_show(request: Request, request_id: str) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/hitl/{request_id}", context=ctx)
        result = services.hitl_show(request_id)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.hitl_show",
            resource="/api/hitl/{request_id}",
            outcome="success",
        )
        return result

    return router