"""
SprintCycle 监控模块

提供执行监控能力：
- 指标收集器 (MetricsCollector)
- Web 仪表盘 (Dashboard)
"""

from ..execution.sprint_types import ExecutionStatus
from .metrics import (
    MetricType,
    ExecutionRecord,
    MetricPoint,
    MetricsCollector,
    get_metrics_collector,
    set_metrics_collector,
)
from .dashboard import (
    create_dashboard_app,
    get_dashboard_html,
    run_dashboard,
)

__all__ = [
    # 统一执行状态
    "ExecutionStatus",
    # 指标收集
    "MetricType",
    "ExecutionRecord",
    "MetricPoint",
    "MetricsCollector",
    "get_metrics_collector",
    "set_metrics_collector",
    # 仪表盘
    "create_dashboard_app",
    "get_dashboard_html",
    "run_dashboard",
]
