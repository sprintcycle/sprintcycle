"""FastAPI application factory for SprintCycle HTTP serving."""

from __future__ import annotations

import json
from typing import Any, Dict

import os

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from sprintcycle.application.factories.http import create_http_services

from .dashboard.execution import build_execution_router
from .dashboard.governance import build_governance_router
from .dashboard.lifecycle import build_lifecycle_router
from .dashboard.hitl import build_hitl_router
from .dashboard.suggestions import build_suggestions_router
from .public.execution import build_public_execution_router
from .public.health import build_health_router
from sprintcycle.application.factories.http import HTTPServices
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event
from pydantic import BaseModel

_DASHBOARD_DEV = os.environ.get("SPRINTCYCLE_ENV", "production") == "development"


class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any] = {}


class ConfigImportRequest(BaseModel):
    config: Dict[str, Any] = {}


class ReloadRequest(BaseModel):
    pass


def build_config_router(services: HTTPServices, project_path: str) -> APIRouter:
    router = APIRouter()

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/config")
    async def get_config(request: Request) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config", context=ctx)
        result = {"success": True, "data": services.load_config()}
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.get_config",
            resource="/api/config",
            outcome="success",
        )
        return result

    @router.put("/api/config")
    async def put_config(request: Request, body: ConfigUpdateRequest) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config", context=ctx)
        cfg = services.load_config()
        cfg.update(body.updates)
        services.save_config(cfg)
        services.add_config_history(body.updates, source="api_put")
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.put_config",
            resource="/api/config",
            outcome="success",
        )
        return {"success": True, "data": cfg}

    @router.get("/api/config/schema")
    async def get_config_schema(request: Request) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/schema", context=ctx)
        result = {
            "success": True,
            "data": services.get_config_schema(),
        }
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.get_config_schema",
            resource="/api/config/schema",
            outcome="success",
        )
        return result

    @router.get("/api/config/history")
    async def get_config_history(request: Request) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/history", context=ctx)
        result = {"success": True, "data": services.get_config_history()}
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.get_config_history",
            resource="/api/config/history",
            outcome="success",
        )
        return result

    @router.post("/api/config/reload")
    async def reload_config(request: Request, _body: ReloadRequest) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/reload", context=ctx)
        result = {"success": True, "data": services.load_config()}
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.reload_config",
            resource="/api/config/reload",
            outcome="success",
        )
        return result

    @router.post("/api/config/import")
    async def import_config(request: Request, body: ConfigImportRequest) -> Dict[str, Any]:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/config/import", context=ctx)
        cfg = services.load_config()
        cfg.update(body.config)
        services.save_config(cfg)
        services.add_config_history(body.config, source="api_import")
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.import_config",
            resource="/api/config/import",
            outcome="success",
        )
        return {"success": True, "data": cfg}

    return router


def build_overview_router() -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def dashboard_home(request: Request) -> Response:
        html = """<!DOCTYPE html>
<html>
<head><title>SprintCycle Dashboard</title></head>
<body><h1>SprintCycle Dashboard</h1></body>
</html>"""
        return HTMLResponse(content=html, media_type="text/html")

    @router.get("/api/clients")
    async def api_clients(request: Request) -> Dict[str, Any]:
        try:
            from sprintcycle.infrastructure.adapters.generic.observability.hooks import get_client_manager
            count = get_client_manager().get_client_count()
        except Exception:
            count = 0
        return {"success": True, "client_count": count}

    @router.get("/api/events/stream")
    async def api_events_stream(request: Request) -> StreamingResponse:
        async def event_generator():
            while True:
                yield f"data: {json.dumps({'event': 'keepalive'})}\n\n"
                from asyncio import sleep
                await sleep(15)
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.get("/api/events")
    async def api_events_legacy(request: Request) -> Dict[str, Any]:
        return {"success": True, "events": []}

    @router.get("/api/events/legacy")
    async def api_events_legacy_path(request: Request) -> Dict[str, Any]:
        return {"success": True, "events": []}

    return router


def create_app(project_path: str = ".") -> FastAPI:
    http_services = create_http_services(project_path)
    app = FastAPI(title="SprintCycle Console", version="0.9.2")

    if _DASHBOARD_DEV:
        _p = 5173
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[f"http://127.0.0.1:{_p}", f"http://localhost:{_p}"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(build_health_router())
    app.include_router(build_public_execution_router(http_services, project_path))

    app.include_router(build_execution_router(http_services, project_path))
    app.include_router(build_governance_router(http_services, project_path))
    app.include_router(build_lifecycle_router(http_services, project_path))
    app.include_router(build_hitl_router(http_services, project_path))
    app.include_router(build_suggestions_router(http_services, project_path))
    app.include_router(build_config_router(http_services, project_path))
    app.include_router(build_overview_router())

    return app
