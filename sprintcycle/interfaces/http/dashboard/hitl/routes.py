"""HITL (Human-in-the-Loop) domain routes.

HTTP endpoints for human intervention operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.interfaces.http.handlers.hitl import HitlHandler
from sprintcycle.interfaces.http.request_context import RequestContext


def build_hitl_router(handler: HitlHandler, project_path: str) -> APIRouter:
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
        result = handler.hitl_pending(execution_id if execution_id else None)
        return result

    @router.get("/api/hitl/history")
    async def hitl_history(request: Request, execution_id: str = "", limit: int = 50) -> dict:
        ctx = _ctx(request)
        result = handler.hitl_history(execution_id if execution_id else None, limit=limit)
        return result

    @router.post("/api/hitl/{request_id}/decision")
    async def hitl_decision(request: Request, request_id: str, body: dict) -> dict:
        ctx = _ctx(request)
        result = handler.hitl_submit(
            request_id,
            body.get("decision", ""),
            body.get("note"),
        )
        return result

    @router.get("/api/hitl/{request_id}")
    async def hitl_show(request: Request, request_id: str) -> dict:
        ctx = _ctx(request)
        result = handler.hitl_show(request_id)
        return result

    return router
