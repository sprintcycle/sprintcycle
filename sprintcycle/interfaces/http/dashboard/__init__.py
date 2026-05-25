"""Dashboard HTTP routes.

All internal routes for the SprintCycle web dashboard.
"""

from .governance import build_governance_router
from .execution import build_execution_router
from .platform import build_platform_router
from .config import build_config_router
from .overview import build_overview_router

__all__ = [
    "build_governance_router",
    "build_execution_router",
    "build_platform_router",
    "build_config_router",
    "build_overview_router",
]
