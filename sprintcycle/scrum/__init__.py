"""
Scrum 对齐的类型别名（零运行时开销）

与 ``release_plan.models`` 中为**同一类型**，便于新代码用 Scrum 词汇阅读与导入。
详见 ``docs/DESIGN_SCRUM_NAMING_MIGRATION.md``。
"""

from __future__ import annotations

from ..release_plan.models import (
    PRD,
    PRDProject,
    PRDEvolutionParams,
    PRDSprint,
    PRDTask,
    ExecutionMode,
)

# --- Scrum 对等名（类型别名）---

ReleasePlan = PRD
"""多 Sprint 可执行交付计划（非完整 Product Backlog）。"""

ProductAnchor = PRDProject
"""产品侧元数据：名称、路径、版本；与 Product Goal 叙述常一起出现在计划中。"""

SprintDefinition = PRDSprint
"""单次 Sprint：Sprint Goal（goals）+ Sprint Backlog（tasks）。"""

SprintBacklogItem = PRDTask
"""Sprint Backlog 上的一条可执行工作项；主字段 ``description``。"""

__all__ = [
    "ReleasePlan",
    "ProductAnchor",
    "SprintDefinition",
    "SprintBacklogItem",
    "PRD",
    "PRDProject",
    "PRDSprint",
    "PRDTask",
    "PRDEvolutionParams",
    "ExecutionMode",
]
