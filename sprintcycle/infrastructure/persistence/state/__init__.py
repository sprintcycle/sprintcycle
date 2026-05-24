"""
状态持久化模块 - 基础设施层

提供执行状态的持久化、回滚、断点管理功能。
"""

from .cache import ExecutionCache
from .checkpoint import CheckpointMixin
from .context import TaskExecutionContext
from .machine import ExecutionStateMachine
from .rollback import RollbackConfig, RollbackManager, get_rollback_manager
from .rollback_types import BackupRecord, RollbackError, RollbackResult, VariantBranch
from .sqlite_event_backend import SQLiteMQEventBackend as SqliteEventBackend
from .sqlite_state_store import SqliteExecutionStore as SqliteStateStore
from .state_store import StateStore, get_state_store

__all__ = [
    "BackupRecord",
    "ExecutionCache",
    "CheckpointMixin",
    "ExecutionStateMachine",
    "RollbackConfig",
    "RollbackError",
    "RollbackManager",
    "RollbackResult",
    "SqliteEventBackend",
    "SqliteStateStore",
    "StateStore",
    "TaskExecutionContext",
    "VariantBranch",
    "get_rollback_manager",
    "get_state_store",
]
