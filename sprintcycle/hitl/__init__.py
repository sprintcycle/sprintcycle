"""Human-in-the-loop（HITL）编排卡点：SQLite 持久化 + 事件 + Dashboard/MCP/CLI。"""

from .coordinator import HitlCoordinator, create_hitl_coordinator
from .decision_normalize import normalize_hitl_decision, validate_hitl_decision_for_submit
from .hooks import HitlSprintHooks, HitlTaskHooks
from .store_sqlite import HitlSqliteStore, default_hitl_db_path
from .types import HitlDecision, HitlGate, HitlRequestRecord

__all__ = [
    "normalize_hitl_decision",
    "validate_hitl_decision_for_submit",
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
