"""FastAPI application factory for SprintCycle HTTP serving."""

from __future__ import annotations

import json
from typing import Any, Dict

import os

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from sprintcycle.application.composition import initialize_http_infrastructure
from sprintcycle.interfaces.http.handlers import (
    ServiceAggregator,
    ExecutionHandler,
    GovernanceHandler,
    LifecycleHandler,
    HitlHandler,
    SuggestionsHandler,
    ConfigHandler,
)
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.interfaces.http.middleware import rate_limit_middleware, audit_middleware
from sprintcycle.domain.ports.observability import get_observability_facade
from pydantic import BaseModel

_DASHBOARD_DEV = os.environ.get("SPRINTCYCLE_ENV", "production") == "development"


class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any] = {}


class ConfigImportRequest(BaseModel):
    config: Dict[str, Any] = {}


class ReloadRequest(BaseModel):
    pass


def build_config_router(config_handler: ConfigHandler, project_path: str) -> APIRouter:
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
        _ctx(request)
        result = {"success": True, "data": config_handler.load_config()}
        return result

    @router.put("/api/config")
    async def put_config(request: Request, body: ConfigUpdateRequest) -> Dict[str, Any]:
        _ctx(request)
        cfg = config_handler.load_config()
        cfg.update(body.updates)
        config_handler.save_config(cfg)
        config_handler.add_config_history(body.updates, source="api_put")
        return {"success": True, "data": cfg}

    @router.get("/api/config/schema")
    async def get_config_schema(request: Request) -> Dict[str, Any]:
        _ctx(request)
        result = {
            "success": True,
            "data": config_handler.get_config_schema(),
        }
        return result

    @router.get("/api/config/history")
    async def get_config_history(request: Request) -> Dict[str, Any]:
        _ctx(request)
        result = {"success": True, "data": config_handler.get_config_history()}
        return result

    @router.post("/api/config/reload")
    async def reload_config(request: Request, _body: ReloadRequest) -> Dict[str, Any]:
        _ctx(request)
        result = {"success": True, "data": config_handler.load_config()}
        return result

    @router.post("/api/config/import")
    async def import_config(request: Request, body: ConfigImportRequest) -> Dict[str, Any]:
        _ctx(request)
        cfg = config_handler.load_config()
        cfg.update(body.config)
        config_handler.save_config(cfg)
        config_handler.add_config_history(body.config, source="api_import")
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
            facade = get_observability_facade()
            count = facade.get_client_count() if hasattr(facade, "get_client_count") else 0
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

    return router


def create_app(project_path: str = ".") -> FastAPI:
    initialize_http_infrastructure(project_path)
    services = ServiceAggregator(project_path)
    
    execution_handler = ExecutionHandler(services)
    governance_handler = GovernanceHandler(services)
    lifecycle_handler = LifecycleHandler(services)
    hitl_handler = HitlHandler(services)
    suggestions_handler = SuggestionsHandler(services)
    config_handler = ConfigHandler(services)

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

    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(audit_middleware)

    from .dashboard.execution import build_execution_router
    from .dashboard.governance import build_governance_router
    from .dashboard.lifecycle import build_lifecycle_router
    from .dashboard.hitl import build_hitl_router
    from .dashboard.suggestions import build_suggestions_router
    from .public.execution import build_public_execution_router
    from .public.health import build_health_router

    app.include_router(build_health_router())
    app.include_router(build_public_execution_router(execution_handler, project_path))

    app.include_router(build_execution_router(execution_handler, project_path))
    app.include_router(build_governance_router(governance_handler, project_path))
    app.include_router(build_lifecycle_router(lifecycle_handler, project_path))
    app.include_router(build_hitl_router(hitl_handler, project_path))
    app.include_router(build_suggestions_router(suggestions_handler, project_path))
    app.include_router(build_config_router(config_handler, project_path))
    app.include_router(build_overview_router())

    return app
