"""Execution domain routes.

HTTP endpoints for execution-related operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.application.factories.http import HTTPServices
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_execution_router(services: HTTPServices, project_path: str) -> APIRouter:
    router = APIRouter()

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/execution/trace")
    async def execution_trace(request: Request, execution_id: str) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/execution/trace", context=ctx)
        result = services.observability_trace(execution_id)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.execution_trace",
            resource="/api/execution/trace",
            outcome="success",
        )
        return result

    @router.get("/api/execution/{execution_id}/detail")
    async def execution_detail(request: Request, execution_id: str, limit: int = 200) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/execution/{execution_id}/detail", context=ctx)
        result = services.execution_detail(execution_id, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.execution_detail",
            resource="/api/execution/{execution_id}/detail",
            outcome="success",
        )
        return result

    @router.get("/api/execution/{execution_id}/replay")
    async def execution_replay(request: Request, execution_id: str, limit: int = 500) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/execution/{execution_id}/replay", context=ctx)
        result = services.replay_execution(execution_id, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.execution_replay",
            resource="/api/execution/{execution_id}/replay",
            outcome="success",
        )
        return result

    @router.get("/api/execution/diagnose")
    async def execution_diagnose(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/execution/diagnose", context=ctx)
        result = services.diagnose()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.execution_diagnose",
            resource="/api/execution/diagnose",
            outcome="success",
        )
        return result

    @router.get("/api/platform/overview")
    async def platform_overview(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/platform/overview", context=ctx)
        result = services.platform_overview()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.platform_overview",
            resource="/api/platform/overview",
            outcome="success",
        )
        return result

    @router.get("/api/platform/fitness")
    async def platform_fitness(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/platform/fitness", context=ctx)
        result = services.fitness_view()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.platform_fitness",
            resource="/api/platform/fitness",
            outcome="success",
        )
        return result

    @router.get("/api/platform/deploy")
    async def platform_deploy(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/platform/deploy", context=ctx)
        result = services.deploy_view()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.platform_deploy",
            resource="/api/platform/deploy",
            outcome="success",
        )
        return result

    return router