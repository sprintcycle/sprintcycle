"""
sprintcycle.evolution.rollback_manager - 兼容重导出

测试文件使用 'sprintcycle.evolution.rollback_manager._is_git_repo' 进行 patch。
本模块提供这个路径的兼容实现。
"""

from sprintcycle.domain.evolution.rollback_manager import (
    EvolutionRollbackManager,
    HAS_GIT_ROLLBACK,
    RollbackConfig,
    RollbackError,
    _is_git_repo,
    _run_git,
)

# noqa: F401 - 为了被测试 patch
__all__ = [
    "EvolutionRollbackManager",
    "HAS_GIT_ROLLBACK",
    "RollbackConfig",
    "RollbackError",
    "_is_git_repo",
    "_run_git",
]
