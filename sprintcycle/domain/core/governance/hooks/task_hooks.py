"""
治理任务钩子。

**已精简**：本模块保留用于向后兼容，实际函数已合并到 governance_hooks.py。
"""

from .governance_hooks import GovernanceTaskLifecycleHooks

__all__ = ["GovernanceTaskLifecycleHooks"]
