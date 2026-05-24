"""Promotion policy gate.

This module re-exports from domain layer to maintain imports for existing code.
"""

from sprintcycle.domain.core.governance.promotion_policy import PromotionPolicy

__all__ = ["PromotionPolicy"]
