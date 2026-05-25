"""Public HTTP routes for external integrations (backward compatibility)."""

from __future__ import annotations

from fastapi import APIRouter

from sprintcycle.application.http_factories import HTTPServices
from .public.execution import build_public_execution_router
from .public.health import build_health_router


def build_public_router(services: HTTPServices, project_path: str) -> APIRouter:
    """Build public router (backward compatibility).

    Args:
        services: HTTP services instance.
        project_path: Project root path.

    Returns:
        APIRouter: Combined public router.
    """
    router = APIRouter()
    router.include_router(build_health_router())
    router.include_router(build_public_execution_router(services, project_path))
    return router
