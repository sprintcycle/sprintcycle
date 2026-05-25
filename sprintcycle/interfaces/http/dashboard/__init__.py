"""Dashboard HTTP routes.

All internal routes for the SprintCycle web dashboard, organized by domain.
"""

from .execution import build_execution_router
from .governance import build_governance_router
from .lifecycle import build_lifecycle_router
from .hitl import build_hitl_router
from .suggestions import build_suggestions_router

__all__ = [
    "build_execution_router",
    "build_governance_router",
    "build_lifecycle_router",
    "build_hitl_router",
    "build_suggestions_router",
]