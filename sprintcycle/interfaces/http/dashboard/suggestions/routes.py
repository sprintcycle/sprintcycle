"""Suggestions domain routes.

HTTP endpoints for suggestion management operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.interfaces.http.handlers.suggestions import SuggestionsHandler
from sprintcycle.interfaces.http.request_context import RequestContext


def build_suggestions_router(handler: SuggestionsHandler, project_path: str) -> APIRouter:
    router = APIRouter()

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.post("/api/suggestions/{suggestion_id}/approve")
    async def suggestion_approve(request: Request, suggestion_id: str, body: dict) -> dict:
        _ctx(request)
        result = handler.approve_suggestion(
            suggestion_id,
            body.get("approver", "dashboard"),
            body.get("notes"),
        )
        return result

    @router.post("/api/suggestions/{suggestion_id}/reject")
    async def suggestion_reject(request: Request, suggestion_id: str, body: dict) -> dict:
        _ctx(request)
        result = handler.reject_suggestion(
            suggestion_id,
            body.get("approver", "dashboard"),
            body.get("notes"),
        )
        return result

    @router.post("/api/suggestions/{suggestion_id}/review")
    async def suggestion_review(request: Request, suggestion_id: str) -> dict:
        _ctx(request)
        result = handler.review_suggestion(suggestion_id, suggestion_id)
        return result

    @router.post("/api/suggestions/{suggestion_id}/archive")
    async def suggestion_archive(request: Request, suggestion_id: str) -> dict:
        _ctx(request)
        result = handler.suggestion_archive(suggestion_id)
        return result

    @router.get("/api/suggestions/overview")
    async def suggestions_overview(request: Request) -> dict:
        _ctx(request)
        result = await handler.suggestion_overview()
        return result

    @router.get("/api/suggestions/board")
    async def suggestions_board(request: Request, execution_id: str = "", limit: int = 20) -> dict:
        _ctx(request)
        result = handler.suggestion_board(execution_id if execution_id else None, limit=limit)
        return result

    return router
