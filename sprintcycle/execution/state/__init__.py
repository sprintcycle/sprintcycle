"""执行状态持久化、SQLite 后端与断点检查点 Mixin。"""

from .checkpoint import CheckpointMixin
from .machine import (
    EXECUTION_TRANSITIONS,
    TASK_TRANSITIONS,
    StateTransition,
    allowed_transitions,
    can_transition,
    summarize_state_machine,
    validate_transition,
)
from .sqlite_state_store import SqliteExecutionStore
from .state_store import (
    ExecutionState,
    StateStore,
    configure_default_store,
    get_state_store,
    reset_default_state_store,
    resolve_sqlite_database_path,
)

__all__ = [
    "CheckpointMixin",
    "EXECUTION_TRANSITIONS",
    "TASK_TRANSITIONS",
    "StateTransition",
    "allowed_transitions",
    "can_transition",
    "summarize_state_machine",
    "validate_transition",
    "StateStore",
    "ExecutionState",
    "configure_default_store",
    "get_state_store",
    "reset_default_state_store",
    "resolve_sqlite_database_path",
    "SqliteExecutionStore",
]
