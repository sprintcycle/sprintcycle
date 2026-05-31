"""Rate limiting port definition.

This port defines the interface for rate limiting functionality
that should be implemented by infrastructure adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True)
class RateLimitState:
    allowed: bool = True
    limit: int = 0
    remaining: int = 0
    reset_after_seconds: int = 0


@runtime_checkable
class RateLimitPort(Protocol):
    """Interface for rate limiting operations."""

    def check_rate_limit(
        self,
        route: str,
        context: Any,
        **kwargs,
    ) -> RateLimitState:
        """
        Check if a request should be rate limited.

        Args:
            route: The route/path being accessed
            context: Request context containing caller info
            **kwargs: Additional parameters

        Returns:
            RateLimitState indicating if the request is allowed
        """
        ...


__all__ = [
    "RateLimitState",
    "RateLimitPort",
]
