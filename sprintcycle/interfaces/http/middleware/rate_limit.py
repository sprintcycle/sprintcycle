"""Rate limiting middleware for FastAPI."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response

from sprintcycle.domain.generic.ports.rate_limit import get_rate_limit_adapter


async def rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Middleware that applies rate limiting to incoming requests.
    
    This middleware checks if the request should be rate limited before
    passing it to the next handler.
    """
    adapter = get_rate_limit_adapter()
    route = request.url.path
    
    context = {
        "request_id": request.headers.get("x-request-id", ""),
        "caller": request.client.host if request.client else "",
    }
    
    state = adapter.check_rate_limit(route=route, context=context)
    
    if not state.allowed:
        return Response(
            status_code=429,
            content=f"Rate limit exceeded. Try again in {state.reset_after_seconds} seconds.",
        )
    
    response = await call_next(request)
    
    if state.limit > 0:
        response.headers["X-RateLimit-Limit"] = str(state.limit)
        response.headers["X-RateLimit-Remaining"] = str(state.remaining)
        response.headers["X-RateLimit-Reset"] = str(state.reset_after_seconds)
    
    return response
