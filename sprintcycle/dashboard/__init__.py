"""
Dashboard - 仪表盘服务

提供平台状态、视图和工作台服务。
"""

from .view_service import DashboardViewService
from .workbench import DashboardWorkbenchService

__all__ = [
    "DashboardViewService",
    "DashboardWorkbenchService",
]
