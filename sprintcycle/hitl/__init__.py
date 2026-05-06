"""Human-in-the-loop（HITL）编排卡点：SQLite 持久化 + 事件 + Dashboard/MCP/CLI。"""

from .coordinator import HitlCoordinator, create_hitl_coordinator
from .hooks import HitlSprintHooks, HitlTaskHooks
from .store_sqlite import HitlSqliteStore, default_hitl_db_path
from .types import HitlDecision, HitlGate, HitlRequestRecord

__all__ = [
    "HitlCoordinator",
    "HitlSqliteStore",
    "HitlSprintHooks",
    "HitlTaskHooks",
    "HitlDecision",
    "HitlGate",
    "HitlRequestRecord",
    "create_hitl_coordinator",
    "default_hitl_db_path",
]
