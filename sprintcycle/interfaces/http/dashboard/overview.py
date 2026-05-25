"""Overview dashboard routes.

HTTP endpoints for dashboard overview pages.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse

from sprintcycle.application.http_factories import HTTPServices
from sprintcycle.application.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_overview_router(services: HTTPServices, project_path: str) -> APIRouter:
    """Build overview dashboard router.

    Args:
        services: HTTP services instance.
        project_path: Project root path.

    Returns:
        APIRouter: Overview routes router.
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

    @router.get("/")
    async def dashboard_home(request: Request) -> Response:
        """Dashboard home page.

        Args:
            request: FastAPI request object.

        Returns:
            Response: HTML response.
        """
        html = """<!DOCTYPE html>
<html>
<head><title>SprintCycle Dashboard</title></head>
<body><h1>SprintCycle Dashboard</h1></body>
</html>"""
        return HTMLResponse(content=html, media_type="text/html")

    @router.get("/api/console/overview")
    async def console_overview(request: Request, limit: int = 20) -> dict:
        """Get console overview.

        Args:
            request: FastAPI request object.
            limit: Maximum number of items.

        Returns:
            dict: Console overview data.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/console/overview", context=ctx)
        result = services.console_overview(limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.console_overview",
            resource="/api/console/overview",
            outcome="success",
        )
        return result

    @router.get("/api/clients")
    async def api_clients(request: Request) -> Dict[str, Any]:
        """Get connected clients count.

        Args:
            request: FastAPI request object.

        Returns:
            Dict[str, Any]: Client count.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/clients", context=ctx)
        try:
            from sprintcycle.infrastructure.adapters.generic.observability.hooks import get_client_manager
            count = get_client_manager().get_client_count()
        except Exception:
            count = 0
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.clients",
            resource="/api/clients",
            outcome="success",
        )
        return {"success": True, "client_count": count}

    @router.get("/api/events/stream")
    async def api_events_stream(request: Request) -> StreamingResponse:
        """SSE event stream.

        Args:
            request: FastAPI request object.

        Returns:
            StreamingResponse: SSE stream.
        """
        async def event_generator():
            while True:
                yield f"data: {json.dumps({'event': 'keepalive'})}\n\n"
                from asyncio import sleep
                await sleep(15)
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.get("/api/events")
    async def api_events_legacy(request: Request) -> Dict[str, Any]:
        """Legacy events endpoint.

        Args:
            request: FastAPI request object.

        Returns:
            Dict[str, Any]: Empty events list.
        """
        return {"success": True, "events": []}

    @router.get("/api/events/legacy")
    async def api_events_legacy_path(request: Request) -> Dict[str, Any]:
        """Another legacy events endpoint.

        Args:
            request: FastAPI request object.

        Returns:
            Dict[str, Any]: Empty events list.
        """
        return {"success": True, "events": []}

    return router
