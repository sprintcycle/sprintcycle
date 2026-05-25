"""Config dashboard routes.

HTTP endpoints for configuration management dashboard pages.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel

from sprintcycle.application.http_factories import HTTPServices
from sprintcycle.application.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    updates: Dict[str, Any] = {}


class ConfigImportRequest(BaseModel):
    """Request model for configuration imports."""
    config: Dict[str, Any] = {}


class ReloadRequest(BaseModel):
    """Request model for configuration reloads."""
    pass


def build_config_router(services: HTTPServices, project_path: str) -> APIRouter:
    """Build config dashboard router.

    Args:
        services: HTTP services instance.
        project_path: Project root path.

    Returns:
        APIRouter: Config routes router.
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

    @router.get("/api/config")
    async def get_config(request: Request) -> Dict[str, Any]:
        """Get current configuration.

        Args:
            request: FastAPI request object.

        Returns:
            Dict[str, Any]: Configuration data.
        """
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
        """Update configuration.

        Args:
            request: FastAPI request object.
            body: Configuration updates.

        Returns:
            Dict[str, Any]: Updated configuration.
        """
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
        """Get configuration schema.

        Args:
            request: FastAPI request object.

        Returns:
            Dict[str, Any]: Configuration schema.
        """
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
        """Get configuration history.

        Args:
            request: FastAPI request object.

        Returns:
            Dict[str, Any]: Configuration change history.
        """
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
        """Reload configuration.

        Args:
            request: FastAPI request object.
            _body: Reload request (unused).

        Returns:
            Dict[str, Any]: Reloaded configuration.
        """
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
        """Import configuration.

        Args:
            request: FastAPI request object.
            body: Configuration to import.

        Returns:
            Dict[str, Any]: Imported configuration.
        """
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
