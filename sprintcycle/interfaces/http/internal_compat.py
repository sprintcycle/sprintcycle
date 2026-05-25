"""Internal HTTP routes for Dashboard control surfaces (backward compatibility)."""

from __future__ import annotations

from fastapi import APIRouter

from sprintcycle.application.http_factories import HTTPServices
from .dashboard import (
    build_governance_router,
    build_execution_router,
    build_platform_router,
    build_config_router,
    build_overview_router,
)


def build_internal_router(services: HTTPServices, project_path: str) -> APIRouter:
    """Build internal router (backward compatibility).

    Args:
        services: HTTP services instance.
        project_path: Project root path.

    Returns:
        APIRouter: Combined internal router.
    """
    router = APIRouter()
    router.include_router(build_governance_router(services, project_path))
    router.include_router(build_execution_router(services, project_path))
    router.include_router(build_platform_router(services, project_path))
    router.include_router(build_config_router(services, project_path))
    router.include_router(build_overview_router(services, project_path))
    return router
