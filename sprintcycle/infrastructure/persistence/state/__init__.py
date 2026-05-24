"""
状态持久化模块 - 基础设施层

提供执行状态的持久化、回滚、断点管理功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .cache import ExecutionCache
from .checkpoint import CheckpointMixin
from .context import TaskExecutionContext
from .machine import ExecutionStateMachine, summarize_state_machine
from .rollback import RollbackConfig, RollbackManager, get_rollback_manager
from .rollback_types import BackupRecord, RollbackError, RollbackResult, VariantBranch
from .sqlite_event_backend import SQLiteMQEventBackend as SqliteEventBackend, execution_events_sqlite_path
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


def create_sqlite_event_backend(project_path: str, config: Any = None) -> "SqliteEventBackend":
    """
    创建 SQLite 事件后端的工厂函数。

    用于注册到 Domain 层的事件后端工厂。

    Args:
        project_path: 项目路径
        config: 可选配置对象

    Returns:
        SqliteEventBackend 实例
    """
    from pathlib import Path

    root = str(Path(project_path).expanduser().resolve())
    db_path = execution_events_sqlite_path(root)
    return SqliteEventBackend(db_path)


def register_event_backend_factory() -> None:
    """注册 SQLite 事件后端工厂到 Domain 层。"""
    from sprintcycle.domain.execution.core.events import register_event_backend_factory as _register

    _register(create_sqlite_event_backend)


def register_rollback_implementations() -> None:
    """注册回滚实现到 Domain 层。"""
    from sprintcycle.infrastructure.persistence.state.rollback import (
        GitRollbackMixin,
        RollbackConfig,
        _is_git_repo,
        _run_git,
    )
    from sprintcycle.infrastructure.persistence.state.rollback_types import (
        RollbackError,
        VariantBranch,
    )
    from sprintcycle.domain.evolution.rollback_manager import register_rollback_implementations as _register

    _register({
        "GitRollbackMixin": GitRollbackMixin,
        "RollbackConfig": RollbackConfig,
        "RollbackError": RollbackError,
        "VariantBranch": VariantBranch,
        "_is_git_repo": _is_git_repo,
        "_run_git": _run_git,
    })
