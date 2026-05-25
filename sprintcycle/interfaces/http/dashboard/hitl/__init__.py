"""HITL (Human-in-the-Loop) domain routes.

HTTP endpoints for human intervention operations.
"""

from .routes import build_hitl_router

__all__ = ["build_hitl_router"]