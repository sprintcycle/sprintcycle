"""Public HTTP routes for external integrations."""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.application.public_api_service import PublicAPIService
from sprintcycle.application.request_context import RequestContext
from sprintcycle.infrastructure.audit import record_audit_event
from sprintcycle.infrastructure.rate_limit import check_rate_limit


class _PublicRouteDeps:
    def __init__(self, service: PublicAPIService, project_path: str):
        self.service = service
        self.project_path = project_path


def build_public_router(service: PublicAPIService, project_path: str) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    deps = _PublicRouteDeps(service, project_path)

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=deps.project_path,
            client_type=request.headers.get("x-client-type", "public"),
        )

    @router.post("/plan")
    async def plan(request: Request, payload: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/plan", context=ctx)
        result = deps.service.plan(context=ctx, **payload)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="public.plan",
            resource="/api/v1/plan",
            outcome="success",
        )
        return result

    @router.post("/run")
    async def run(request: Request, payload: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/run", context=ctx)
        result = deps.service.run(context=ctx, **payload)
        record_audit_event(
            request_id=ctx.request_id, actor=ctx.caller, action="public.run", resource="/api/v1/run", outcome="success"
        )
        return result

    @router.get("/diagnose")
    async def diagnose(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/diagnose", context=ctx)
        result = deps.service.diagnose(context=ctx)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="public.diagnose",
            resource="/api/v1/diagnose",
            outcome="success",
        )
        return result

    @router.post("/status")
    async def status(request: Request, payload: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/status", context=ctx)
        result = deps.service.status(execution_id=payload.get("execution_id"), context=ctx)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="public.status",
            resource="/api/v1/status",
            outcome="success",
        )
        return result

    @router.post("/rollback")
    async def rollback(request: Request, payload: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/rollback", context=ctx)
        result = deps.service.rollback(execution_id=payload["execution_id"], context=ctx)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="public.rollback",
            resource="/api/v1/rollback",
            outcome="success",
        )
        return result

    @router.post("/stop")
    async def stop(request: Request, payload: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/stop", context=ctx)
        result = deps.service.stop(execution_id=payload["execution_id"], context=ctx)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="public.stop",
            resource="/api/v1/stop",
            outcome="success",
        )
        return result

    return router
