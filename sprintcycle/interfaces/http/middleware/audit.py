"""Audit logging middleware for FastAPI."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response

from sprintcycle.domain.ports.audit import get_audit_adapter


async def audit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Middleware that records audit events for incoming requests.
    
    This middleware automatically logs audit events for all HTTP requests,
    capturing request details and outcome.
    """
    adapter = get_audit_adapter()
    
    request_id = request.headers.get("x-request-id", "")
    caller = request.client.host if request.client else ""
    action = f"{request.method.lower()}.{request.url.path.lstrip('/').replace('/', '.')}"
    resource = str(request.url.path)
    
    try:
        response = await call_next(request)
        outcome = "success"
    except Exception:
        outcome = "failure"
        raise
    finally:
        adapter.record_audit_event(
            request_id=request_id,
            actor=caller,
            action=action,
            resource=resource,
            outcome=outcome,
            method=request.method,
            status_code=response.status_code if 'response' in locals() else 500,
        )
    
    return response
