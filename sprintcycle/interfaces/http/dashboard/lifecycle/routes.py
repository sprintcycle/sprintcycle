"""Lifecycle domain routes.

HTTP endpoints for lifecycle contract operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.interfaces.http.handlers.lifecycle import LifecycleHandler
from sprintcycle.interfaces.http.request_context import RequestContext


def build_lifecycle_router(handler: LifecycleHandler, project_path: str) -> APIRouter:
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
        _ctx(request)
        result = handler.lifecycle_contract(execution_id, limit=limit)
        return result

    @router.post("/api/lifecycle/contract/{execution_id}/review")
    async def lifecycle_contract_review(request: Request, execution_id: str, body: dict) -> dict:
        _ctx(request)
        contract = handler.lifecycle_contract(execution_id)
        payload = dict(body or {})
        payload.setdefault("contract", contract.get("data", {}))
        result = handler.evaluate_sprint_contract(payload)
        return result

    @router.get("/api/lifecycle/delivery")
    async def lifecycle_delivery(request: Request) -> dict:
        _ctx(request)
        result = await handler.deploy_lifecycle()
        return result

    return router
