"""
sprintcycle.evolution - 兼容层导出

为了向后兼容，保留从顶层包访问 Evolution 模块的能力。
实际实现已移动到 sprintcycle.domain.evolution。
"""

from sprintcycle.domain.evolution import (
    EvolutionRollbackManager,
    RollbackConfig,
)

__all__ = ["EvolutionRollbackManager", "RollbackConfig"]
