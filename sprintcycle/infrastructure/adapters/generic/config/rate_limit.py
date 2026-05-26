"""Rate limit support.

This module reserves the integration point for future quota and rate limiting
policies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RateLimitState:
    allowed: bool = True
    limit: int = 0
    remaining: int = 0
    reset_after_seconds: int = 0


class RateLimitAdapter:
    """Infrastructure adapter for rate limiting."""

    def check_rate_limit(
        self,
        route: str,
        context: Any,
        **kwargs,
    ) -> RateLimitState:
        """Check if a request should be rate limited."""
        return RateLimitState()


def check_rate_limit(*_args, **_kwargs) -> RateLimitState:
    """Legacy function for backward compatibility."""
    return RateLimitState()
