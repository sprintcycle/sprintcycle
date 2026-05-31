"""Sprint 生命周期钩子（编排与 SprintExecutor 之间的横切扩展点）。

**精简版**：移除了重复的 NoOp/Chained 类，使用统一的 HookFactory。
"""

from .governance_context import (
    CTX_GOVERNANCE_TASK_AFTER_FAILED,
    CTX_GOVERNANCE_TASK_AFTER_DETAIL,
)
from sprintcycle.domain.generic.interfaces.hooks import HookContext
from .quality_hooks import QualitySprintLifecycleHooks, QualityTaskLifecycleHooks, build_quality_lifecycle_report
from .skill_hooks import SkillLifecycleHook
from .sprint_hooks import (
    SprintLifecycleHooks,
    create_noop_sprint_hooks,
    create_chained_sprint_hooks,
)
from .task_hooks import (
    TaskLifecycleHooks,
    create_noop_task_hooks,
    create_chained_task_hooks,
)

__all__ = [
    "HookContext",
    "SprintLifecycleHooks",
    "create_noop_sprint_hooks",
    "create_chained_sprint_hooks",
    "TaskLifecycleHooks",
    "create_noop_task_hooks",
    "create_chained_task_hooks",
    "QualitySprintLifecycleHooks",
    "QualityTaskLifecycleHooks",
    "SkillLifecycleHook",
    "build_quality_lifecycle_report",
    "CTX_GOVERNANCE_TASK_AFTER_FAILED",
    "CTX_GOVERNANCE_TASK_AFTER_DETAIL",
]

