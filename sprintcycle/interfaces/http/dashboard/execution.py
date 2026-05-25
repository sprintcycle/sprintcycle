"""Execution dashboard routes.

HTTP endpoints for execution-related dashboard pages.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from sprintcycle.application.http_factories import HTTPServices
from sprintcycle.application.request_context import RequestContext
from sprintcycle.infrastructure.adapters.generic.config.rate_limit import check_rate_limit
from sprintcycle.infrastructure.adapters.generic.integrations.audit import record_audit_event


def build_execution_router(services: HTTPServices, project_path: str) -> APIRouter:
    """Build execution dashboard router.

    Args:
        services: HTTP services instance.
        project_path: Project root path.

    Returns:
        APIRouter: Execution routes router.
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

    @router.get("/api/dashboard/trace")
    async def dashboard_trace(request: Request, execution_id: str) -> dict:
        """Get execution trace.

        Args:
            request: FastAPI request object.
            execution_id: Execution ID.

        Returns:
            dict: Trace data.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/trace", context=ctx)
        result = services.observability_trace(execution_id)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.observability_trace",
            resource="/api/dashboard/trace",
            outcome="success",
        )
        return result

    @router.get("/api/dashboard/lifecycle-contract")
    async def dashboard_lifecycle_contract(request: Request, execution_id: str, limit: int = 200) -> dict:
        """Get lifecycle contract for an execution.

        Args:
            request: FastAPI request object.
            execution_id: Execution ID.
            limit: Maximum number of items.

        Returns:
            dict: Lifecycle contract data.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/lifecycle-contract", context=ctx)
        result = services.lifecycle_contract(execution_id, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.lifecycle_contract",
            resource="/api/dashboard/lifecycle-contract",
            outcome="success",
        )
        return result

    @router.post("/api/dashboard/lifecycle-contract/{execution_id}/review")
    async def dashboard_lifecycle_contract_review(request: Request, execution_id: str, body: dict) -> dict:
        """Review a lifecycle contract.

        Args:
            request: FastAPI request object.
            execution_id: Execution ID.
            body: Review data.

        Returns:
            dict: Review result.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/dashboard/lifecycle-contract/{execution_id}/review", context=ctx)
        contract = services.lifecycle_contract(execution_id)
        payload = dict(body or {})
        payload.setdefault("contract", contract.get("data", {}))
        result = services.evaluate_sprint_contract(payload)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.lifecycle_contract_review",
            resource="/api/dashboard/lifecycle-contract/{execution_id}/review",
            outcome="success",
        )
        return result

    @router.get("/api/execution/{execution_id}/detail")
    async def execution_detail(request: Request, execution_id: str, limit: int = 200) -> dict:
        """Get execution details.

        Args:
            request: FastAPI request object.
            execution_id: Execution ID.
            limit: Maximum number of items.

        Returns:
            dict: Execution detail data.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/execution/{execution_id}/detail", context=ctx)
        result = services.execution_detail(execution_id, limit=limit)
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.execution_detail",
            resource="/api/execution/{execution_id}/detail",
            outcome="success",
        )
        return result

    @router.get("/api/diagnose")
    async def api_diagnose(request: Request) -> dict:
        """Diagnose project or execution.

        Args:
            request: FastAPI request object.

        Returns:
            dict: Diagnosis result.
        """
        ctx = _ctx(request)
        check_rate_limit(request, route="/api/diagnose", context=ctx)
        result = services.diagnose()
        record_audit_event(
            request_id=ctx.request_id,
            actor=ctx.caller,
            action="internal.diagnose",
            resource="/api/diagnose",
            outcome="success",
        )
        return result

    return router
