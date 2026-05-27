"""Execution domain routes.

HTTP endpoints for execution-related operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.interfaces.http.handlers.execution import ExecutionHandler
from sprintcycle.interfaces.http.request_context import RequestContext


def build_execution_router(handler: ExecutionHandler, project_path: str) -> APIRouter:
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
        _ctx(request)
        result = handler.observability_trace(execution_id)
        return result

    @router.get("/api/execution/{execution_id}/detail")
    async def execution_detail(request: Request, execution_id: str, limit: int = 200) -> dict:
        _ctx(request)
        result = handler.execution_detail(execution_id, limit=limit)
        return result

    @router.get("/api/execution/{execution_id}/replay")
    async def execution_replay(request: Request, execution_id: str, limit: int = 500) -> dict:
        _ctx(request)
        result = handler.replay_execution(execution_id, limit=limit)
        return result

    @router.get("/api/execution/diagnose")
    async def execution_diagnose(request: Request) -> dict:
        _ctx(request)
        result = handler.diagnose()
        return result

    @router.get("/api/platform/overview")
    async def platform_overview(request: Request) -> dict:
        _ctx(request)
        result = handler.platform_overview()
        return result

    @router.get("/api/platform/fitness")
    async def platform_fitness(request: Request) -> dict:
        _ctx(request)
        result = handler.fitness_view()
        return result

    @router.get("/api/platform/deploy")
    async def platform_deploy(request: Request) -> dict:
        _ctx(request)
        result = handler.deploy_view()
        return result

    return router
