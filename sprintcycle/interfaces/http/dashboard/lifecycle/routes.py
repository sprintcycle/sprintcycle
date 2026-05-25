"""Lifecycle domain routes.

HTTP endpoints for lifecycle contract operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.application.factories.http import HTTPServices
from sprintcycle.interfaces.http.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_lifecycle_router(services: HTTPServices, project_path: str) -> APIRouter:
    router = APIRouter()

    def _ctx(request: Request) -> RequestContext:
        return RequestContext(
            request_id=request.headers.get("x-request-id", ""),
            trace_id=request.headers.get("x-trace-id", ""),
            caller=request.client.host if request.client else "",
            project_path=project_path,
            client_type=request.headers.get("x-client-type", "dashboard"),
        )

    @router.get("/api/lifecycle/contract")
    async def lifecycle_contract(request: Request, execution_id: str, limit: int = 200) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/lifecycle/contract", context=ctx)
        result = services.lifecycle_contract(execution_id, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.lifecycle_contract",
            resource="/api/lifecycle/contract",
            outcome="success",
        )
        return result

    @router.post("/api/lifecycle/contract/{execution_id}/review")
    async def lifecycle_contract_review(request: Request, execution_id: str, body: dict) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/lifecycle/contract/{execution_id}/review", context=ctx)
        contract = services.lifecycle_contract(execution_id)
        payload = dict(body or {})
        payload.setdefault("contract", contract.get("data", {}))
        result = services.evaluate_sprint_contract(payload)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.lifecycle_contract_review",
            resource="/api/lifecycle/contract/{execution_id}/review",
            outcome="success",
        )
        return result

    @router.get("/api/lifecycle/delivery")
    async def lifecycle_delivery(request: Request) -> dict:
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/lifecycle/delivery", context=ctx)
        result = await services.deploy_lifecycle()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.lifecycle_delivery",
            resource="/api/lifecycle/delivery",
            outcome="success",
        )
        return result

    return router
