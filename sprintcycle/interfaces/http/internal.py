"""Internal HTTP routes for Dashboard control surfaces."""

from __future__ import annotations

import asyncio
from fastapi import APIRouter, Request

from sprintcycle.application.internal_api_service import InternalAPIService
from sprintcycle.application.request_context import RequestContext
from sprintcycle.infrastructure.audit import record_audit_event
from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
from sprintcycle.infrastructure.rate_limit import check_rate_limit
from sprintcycle.governance.runner import run_governance_check_and_persist


class _InternalRouteDeps:
    def __init__(self, service: InternalAPIService, project_path: str):
        self.service = service
        self.project_path = project_path


def build_internal_router(service: InternalAPIService, project_path: str) -> APIRouter:
    router = APIRouter()
    deps = _InternalRouteDeps(service, project_path)

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=deps.project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/governance/latest")
    async def governance_latest(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/latest", context=ctx)
        result = deps.service.read_governance_reports(context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.governance_reports", resource="/api/governance/latest", outcome="success")
        return result

    @router.get("/api/governance/history")
    async def governance_history(request: Request, limit: int = 50) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/history", context=ctx)
        result = deps.service.governance_history(limit=limit, context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.governance_history", resource="/api/governance/history", outcome="success")
        return result

    @router.post("/api/governance/check")
    async def governance_check(request: Request, body: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/governance/check", context=ctx)
        cfg = RuntimeConfig.from_project(deps.service.project_path())
        planning_report, review_report, fail = await asyncio.to_thread(
            run_governance_check_and_persist,
            deps.service.project_path(),
            cfg,
            body.get("gate", "review"),
        )
        out = {"should_fail_ci": fail, "gate": body.get("gate", "review")}
        if planning_report is not None:
            out["planning"] = planning_report.to_dict()
        if review_report is not None:
            out["review"] = review_report.to_dict()
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.governance_check", resource="/api/governance/check", outcome="success")
        return out

    @router.get("/api/dashboard/governance")
    async def dashboard_governance(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/governance", context=ctx)
        result = deps.service.governance_view(context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.governance_view", resource="/api/dashboard/governance", outcome="success")
        return result

    @router.get("/api/dashboard/platform")
    async def dashboard_platform(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/platform", context=ctx)
        result = deps.service.dashboard_platform_workspace(context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.dashboard_platform_workspace", resource="/api/dashboard/platform", outcome="success")
        return result

    @router.get("/api/platform/overview")
    async def platform_overview(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/platform/overview", context=ctx)
        result = deps.service.platform_overview(context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.platform_overview", resource="/api/platform/overview", outcome="success")
        return result

    @router.get("/api/dashboard/trace")
    async def dashboard_trace(request: Request, execution_id: str) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/trace", context=ctx)
        result = deps.service.observability_trace(execution_id, context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.observability_trace", resource="/api/dashboard/trace", outcome="success")
        return result

    @router.get("/api/console/overview")
    async def console_overview(request: Request, limit: int = 20) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/console/overview", context=ctx)
        result = deps.service.console_overview(limit=limit, context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.console_overview", resource="/api/console/overview", outcome="success")
        return result

    @router.get("/api/execution/{execution_id}/detail")
    async def execution_detail(request: Request, execution_id: str, limit: int = 200) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/execution/{execution_id}/detail", context=ctx)
        result = deps.service.execution_detail(execution_id, limit=limit, context=ctx)
        record_audit_event(request_id=ctx.request_id, actor=ctx.caller, action="internal.execution_detail", resource="/api/execution/{execution_id}/detail", outcome="success")
        return result

    return router
