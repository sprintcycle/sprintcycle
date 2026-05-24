"""
Sprint 执行类型 — 与 Scrum **Sprint / Sprint Backlog Item 结果 / Increment 证据** 对齐

v0.9.2: 类型已迁移到 domain.interfaces.types，本模块保留作为向后兼容的 re-export。

**已迁移类型：**
- ``ExecutionStatus`` → ``sprintcycle.domain.interfaces``
- ``TaskResult`` → ``sprintcycle.domain.interfaces``
- ``SprintResult`` → ``sprintcycle.domain.interfaces``
"""

# 向后兼容：从 Domain 层重新导出
from sprintcycle.domain.generic.interfaces import ExecutionStatus, TaskResult, SprintResult

__all__ = [
    "ExecutionStatus",
    "TaskResult",
    "SprintResult",
]
