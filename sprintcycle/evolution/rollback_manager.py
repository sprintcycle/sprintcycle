"""
sprintcycle.evolution.rollback_manager - backward-compatible re-export.

Re-exports everything from ``sprintcycle.application.evolution.rollback_manager``
so that tests can patch ``sprintcycle.evolution.rollback_manager._is_git_repo``.
"""

from ..application.evolution.rollback_manager import (  # noqa: F401
    HAS_GIT_ROLLBACK,
    EvolutionRollbackManager,
    RollbackConfig,
    RollbackError,
    VariantBranch,
    _is_git_repo,
    _run_git,
)

__all__ = [
    "EvolutionRollbackManager",
    "HAS_GIT_ROLLBACK",
    "RollbackConfig",
    "RollbackError",
    "VariantBranch",
    "_is_git_repo",
    "_run_git",
]
