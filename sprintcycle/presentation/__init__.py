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
from .server import create_app
from .workbench import DashboardWorkbenchService

__all__ = [
    "create_app",
    "DashboardProjectionBundle",
    "DashboardQueryService",
    "DashboardWorkbenchService",
    "HitlRequestViewModel",
    "SuggestionBoardViewModel",
    "SuggestionCardViewModel",
]
