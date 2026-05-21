"""
sprintcycle.evolution - package for backward-compatible re-exports.

Tests and some internal callers reference ``sprintcycle.evolution.rollback_manager``
which lives at ``sprintcycle.application.evolution.rollback_manager``.
"""

from ..application.evolution.rollback_manager import EvolutionRollbackManager

__all__ = ["EvolutionRollbackManager"]
