"""Public HTTP routes for external integrations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request

from sprintcycle.application.http_factories import HTTPServices
from sprintcycle.application.request_context import RequestContext
from sprintcycle.infrastructure.audit import record_audit_event
from sprintcycle.infrastructure.rate_limit import check_rate_limit


class _PublicRouteDeps:
    def __init__(self, services: HTTPServices, project_path: str):
        self.services = services
        self.project_path = project_path


def build_public_router(services: HTTPServices, project_path: str) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    deps = _PublicRouteDeps(services, project_path)

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
        from sprintcycle.application.sprint_orchestrator import SprintOrchestrator
        from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
        
        config = RuntimeConfig.from_project(deps.project_path)
        orchestrator = SprintOrchestrator(project_path=deps.project_path, config=config)
        
        result = orchestrator.plan(
            intent=payload.get("intent", ""),
            mode=payload.get("mode", "auto"),
            target=payload.get("target"),
            release_plan_yaml=payload.get("release_plan_yaml"),
            release_plan_path=payload.get("release_plan_path"),
            product=payload.get("product"),
            reference_paths=payload.get("reference_paths"),
            write_policy=payload.get("write_policy", "auto"),
        )
        
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="public.plan",
            resource="/api/v1/plan",
            outcome="success",
        )
        return result.to_dict() if hasattr(result, "to_dict") else dict(result)

    @router.post("/run")
    async def run(request: Request, payload: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/run", context=ctx)
        from sprintcycle.application.sprint_orchestrator import SprintOrchestrator
        from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
        
        config = RuntimeConfig.from_project(deps.project_path)
        orchestrator = SprintOrchestrator(project_path=deps.project_path, config=config)
        
        result = orchestrator.run(
            intent=payload.get("intent"),
            mode=payload.get("mode", "auto"),
            target=payload.get("target"),
            release_plan_yaml=payload.get("release_plan_yaml"),
            release_plan_path=payload.get("release_plan_path"),
            product=payload.get("product"),
            execution_id=payload.get("execution_id"),
            resume=payload.get("resume", False),
            reference_paths=payload.get("reference_paths"),
            write_policy=payload.get("write_policy", "auto"),
        )
        
        record_audit_event(
            request_id=ctx.request_id, actor=ctx.caller, action="public.run", resource="/api/v1/run", outcome="success"
        )
        return result.to_dict() if hasattr(result, "to_dict") else dict(result)

    @router.get("/diagnose")
    async def diagnose(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/v1/diagnose", context=ctx)
        result = deps.services.diagnose()
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
        result = deps.services.status(execution_id=payload.get("execution_id", ""))
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
        result = deps.services.rollback(execution_id=payload.get("execution_id", ""))
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
        result = deps.services.stop(execution_id=payload.get("execution_id", ""))
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="public.stop",
            resource="/api/v1/stop",
            outcome="success",
        )
        return result

    return router
