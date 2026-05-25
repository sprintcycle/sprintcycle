"""状态存储端口 - Domain 层与状态持久化的接口

定义状态存储的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol

from sprintcycle.domain.generic.interfaces import ExecutionStatus


@dataclass
class ExecutionState:
    """执行状态数据类"""

    execution_id: str
    release_plan_name: str
    mode: str
    status: ExecutionStatus
    current_sprint: int = 0
    total_sprints: int = 0
    completed_tasks: int = 0
    total_tasks: int = 0
    created_at: str = ""
    updated_at: str = ""
    error: Optional[str] = None
    checkpoint: Optional[Dict[str, Any]] = None
    last_stable_state: Optional[Dict[str, Any]] = None
    event_cursor: Optional[int] = None
    replay_version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "release_plan_name": self.release_plan_name,
            "mode": self.mode,
            "status": self.status.value,
            "current_sprint": self.current_sprint,
            "total_sprints": self.total_sprints,
            "completed_tasks": self.completed_tasks,
            "total_tasks": self.total_tasks,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
            "checkpoint": self.checkpoint,
            "last_stable_state": self.last_stable_state,
            "event_cursor": self.event_cursor,
            "replay_version": self.replay_version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionState":
        data = data.copy()
        data["status"] = ExecutionStatus(data["status"])
        return cls(**data)


class StateStoreProtocol(Protocol):
    """状态存储协议接口"""

    def save(self, state: ExecutionState) -> None:
        """保存执行状态"""
        ...

    def load(self, execution_id: str) -> Optional[ExecutionState]:
        """加载执行状态"""
        ...

    def delete(self, execution_id: str) -> bool:
        """删除执行状态"""
        ...

    def list_executions(
        self, status: Optional[ExecutionStatus] = None, limit: int = 50
    ) -> List[ExecutionState]:
        """列出所有执行记录"""
        ...

    def can_resume(self, execution_id: str) -> bool:
        """是否可以恢复执行"""
        ...

    def get_resume_point(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取恢复点信息"""
        ...

    def update_status(
        self, execution_id: str, status: ExecutionStatus, error: Optional[str] = None
    ) -> bool:
        """更新执行状态"""
        ...

    def increment_progress(self, execution_id: str, completed_tasks: int = 1, completed_sprints: int = 0) -> bool:
        """更新执行进度"""
        ...


# 回滚相关类型协议
@dataclass
class VariantBranchLike:
    """变体分支记录协议"""
    variant_id: str
    branch_name: str
    base_commit: str
    committed: bool = False
    merged: bool = False
    created_at: str = ""


@dataclass
class RollbackConfigLike:
    """回滚配置协议"""
    git_branch_mode: bool = True
    repo_path: str = "."
    branch_prefix: str = "evo/variant-"
    backup_dir: str = ".sprintcycle/evo_backups"
    auto_cleanup: bool = True
    max_branches: int = 20


class RollbackErrorLike(Exception):
    """回滚错误异常协议"""
    pass


class GitRollbackMixinProtocol(Protocol):
    """Git 回滚 Mixin 协议"""
    pass


# 回滚实现注册
_git_rollback_mixin: Any = object
_rollback_config_cls: Any = RollbackConfigLike
_rollback_error_cls: Any = RollbackErrorLike
_variant_branch_cls: Any = VariantBranchLike
_is_git_repo_func: Optional[Callable[[str], bool]] = None
_run_git_func: Optional[Callable[..., Any]] = None
_has_git_rollback: bool = False


def register_rollback_implementations(
    GitRollbackMixin: Any = object,
    RollbackConfig: Any = None,
    RollbackError: Any = Exception,
    VariantBranch: Any = None,
    is_git_repo: Optional[Callable[[str], bool]] = None,
    run_git: Optional[Callable[..., Any]] = None,
) -> None:
    """注册回滚实现（由 Infrastructure 层调用）"""
    global _git_rollback_mixin, _rollback_config_cls, _rollback_error_cls, _variant_branch_cls
    global _is_git_repo_func, _run_git_func, _has_git_rollback

    _git_rollback_mixin = GitRollbackMixin
    _rollback_config_cls = RollbackConfig or RollbackConfigLike
    _rollback_error_cls = RollbackError or RollbackErrorLike
    _variant_branch_cls = VariantBranch or VariantBranchLike
    _is_git_repo_func = is_git_repo
    _run_git_func = run_git
    _has_git_rollback = all([
        _git_rollback_mixin is not object,
        _rollback_config_cls is not None,
        _variant_branch_cls is not None,
        _is_git_repo_func is not None,
        _run_git_func is not None,
    ])


def get_git_rollback_mixin() -> Any:
    """获取 Git 回滚 Mixin"""
    return _git_rollback_mixin


def get_rollback_config_cls() -> Any:
    """获取回滚配置类"""
    return _rollback_config_cls


def get_rollback_error_cls() -> Any:
    """获取回滚错误类"""
    return _rollback_error_cls


def get_variant_branch_cls() -> Any:
    """获取变体分支类"""
    return _variant_branch_cls


def get_is_git_repo_func() -> Optional[Callable[[str], bool]]:
    """获取 git 仓库判断函数"""
    return _is_git_repo_func


def get_run_git_func() -> Optional[Callable[..., Any]]:
    """获取 git 命令执行函数"""
    return _run_git_func


def has_git_rollback() -> bool:
    """检查是否有 git 回滚支持"""
    return _has_git_rollback


# 工厂函数注册
_state_store_factory: Optional[callable] = None


def register_state_store_factory(factory: callable) -> None:
    """注册状态存储工厂（由 Infrastructure 层调用）"""
    global _state_store_factory
    _state_store_factory = factory


def get_state_store(store_dir: Optional[str] = None) -> StateStoreProtocol:
    """获取状态存储实例"""
    if _state_store_factory is not None:
        return _state_store_factory(store_dir)
    raise RuntimeError(
        "State store factory not registered. "
        "Please call register_state_store_factory() from Infrastructure layer before using."
    )


__all__ = [
    "ExecutionState",
    "StateStoreProtocol",
    "VariantBranchLike",
    "RollbackConfigLike",
    "RollbackErrorLike",
    "GitRollbackMixinProtocol",
    "register_state_store_factory",
    "get_state_store",
    "register_rollback_implementations",
    "get_git_rollback_mixin",
    "get_rollback_config_cls",
    "get_rollback_error_cls",
    "get_variant_branch_cls",
    "get_is_git_repo_func",
    "get_run_git_func",
    "has_git_rollback",
]
