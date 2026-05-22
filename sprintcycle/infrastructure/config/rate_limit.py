"""Rate limit support.

This module reserves the integration point for future quota and rate limiting
policies.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RateLimitState:
    allowed: bool = True
    limit: int = 0
    remaining: int = 0
    reset_after_seconds: int = 0


def check_rate_limit(*_args, **_kwargs) -> RateLimitState:
    return RateLimitState()
