"""Suggestions domain routes.

HTTP endpoints for suggestion management operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.application.factories.http import HTTPServices
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_suggestions_router(services: HTTPServices, project_path: str) -> APIRouter:
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
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/suggestions/{suggestion_id}/approve", context=ctx)
        result = services.approve_suggestion(
            suggestion_id,
            body.get("approver", "dashboard"),
            body.get("notes"),
        )
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.suggestion_approve",
            resource="/api/suggestions/{suggestion_id}/approve",
            outcome="success",
        )
        return result

    @router.post("/api/suggestions/{suggestion_id}/reject")
    async def suggestion_reject(request: Request, suggestion_id: str, body: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/suggestions/{suggestion_id}/reject", context=ctx)
        result = services.reject_suggestion(
            suggestion_id,
            body.get("approver", "dashboard"),
            body.get("notes"),
        )
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.suggestion_reject",
            resource="/api/suggestions/{suggestion_id}/reject",
            outcome="success",
        )
        return result

    @router.post("/api/suggestions/{suggestion_id}/review")
    async def suggestion_review(request: Request, suggestion_id: str) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/suggestions/{suggestion_id}/review", context=ctx)
        result = services.review_suggestion(suggestion_id, suggestion_id)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.suggestion_review",
            resource="/api/suggestions/{suggestion_id}/review",
            outcome="success",
        )
        return result

    @router.post("/api/suggestions/{suggestion_id}/archive")
    async def suggestion_archive(request: Request, suggestion_id: str) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/suggestions/{suggestion_id}/archive", context=ctx)
        result = services.suggestion_archive(suggestion_id)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.suggestion_archive",
            resource="/api/suggestions/{suggestion_id}/archive",
            outcome="success",
        )
        return result

    @router.get("/api/suggestions/overview")
    async def suggestions_overview(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/suggestions/overview", context=ctx)
        result = await services.suggestion_overview()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.suggestions_overview",
            resource="/api/suggestions/overview",
            outcome="success",
        )
        return result

    @router.get("/api/suggestions/board")
    async def suggestions_board(request: Request, execution_id: str = "", limit: int = 20) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/suggestions/board", context=ctx)
        result = services.suggestion_board(execution_id if execution_id else None, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.suggestions_board",
            resource="/api/suggestions/board",
            outcome="success",
        )
        return result

    return router