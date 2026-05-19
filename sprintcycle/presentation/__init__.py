"""
SprintCycle Dashboard — Web 可视化界面

FastAPI + SSE 实时推送，调用 SprintCycle API。
"""

from .projections import (
    DashboardProjectionBundle,
    HitlRequestViewModel,
    SuggestionBoardViewModel,
    SuggestionCardViewModel,
)
from .service import DashboardQueryService
from .workbench import DashboardWorkbenchService


def __getattr__(name: str):
    if name == "create_app":
        from .server import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "create_app",
    "DashboardProjectionBundle",
    "DashboardQueryService",
    "DashboardWorkbenchService",
    "HitlRequestViewModel",
    "SuggestionBoardViewModel",
    "SuggestionCardViewModel",
]
