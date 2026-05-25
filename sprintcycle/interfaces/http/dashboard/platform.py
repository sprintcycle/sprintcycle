"""Platform dashboard routes.

HTTP endpoints for platform-related dashboard pages.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.application.http_factories import HTTPServices
from sprintcycle.application.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_platform_router(services: HTTPServices, project_path: str) -> APIRouter:
    """Build platform dashboard router.

    Args:
        services: HTTP services instance.
        project_path: Project root path.

    Returns:
        APIRouter: Platform routes router.
    """
    router = APIRouter()

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/dashboard/platform")
    async def dashboard_platform(request: Request) -> dict:
        """Get platform workspace view.

        Args:
            request: FastAPI request object.

        Returns:
            dict: Platform workspace data.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/platform", context=ctx)
        result = services.dashboard_platform_workspace()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.dashboard_platform_workspace",
            resource="/api/dashboard/platform",
            outcome="success",
        )
        return result

    @router.get("/api/platform/overview")
    async def platform_overview(request: Request) -> dict:
        """Get platform overview.

        Args:
            request: FastAPI request object.

        Returns:
            dict: Platform overview data.
        """
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

    @router.get("/api/dashboard/fitness")
    async def dashboard_fitness(request: Request) -> dict:
        """Get fitness view.

        Args:
            request: FastAPI request object.

        Returns:
            dict: Fitness view data.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/fitness", context=ctx)
        result = services.fitness_view()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.fitness_view",
            resource="/api/dashboard/fitness",
            outcome="success",
        )
        return result

    @router.get("/api/dashboard/deploy")
    async def dashboard_deploy(request: Request) -> dict:
        """Get deploy view.

        Args:
            request: FastAPI request object.

        Returns:
            dict: Deploy view data.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/deploy", context=ctx)
        result = services.deploy_view()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.deploy_view",
            resource="/api/dashboard/deploy",
            outcome="success",
        )
        return result

    return router
