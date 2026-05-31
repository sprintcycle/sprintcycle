"""
任务级生命周期钩子。

**已精简**：本模块保留用于向后兼容，实际函数已合并到 lifecycle_hooks.py。
"""

from .lifecycle_hooks import (
    TaskLifecycleHooks,
    create_chained_task_hooks,
    create_noop_task_hooks,
)

__all__ = [
    "TaskLifecycleHooks",
    "create_noop_task_hooks",
    "create_chained_task_hooks",
]
