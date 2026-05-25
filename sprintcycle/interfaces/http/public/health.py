"""Public health API routes.

HTTP endpoints for health checks.
"""

from __future__ import annotations

from fastapi import APIRouter


def build_health_router() -> APIRouter:
    """Build health check router.

    Returns:
        APIRouter: Health routes router.
    """
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict:
        """Health check endpoint.

        Returns:
            dict: Health status.
        """
        return {"status": "ok"}

    return router
