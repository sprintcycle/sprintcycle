"""
DI Bridge - 向后兼容层（已废弃，请直接使用 di_container）

这个模块将在未来版本中移除。请直接使用：
from sprintcycle.application.composition.di_container import container

所有函数现在都直接委托给 container。
"""

from __future__ import annotations

from typing import Any, Optional

from sprintcycle.application.composition.di_container import container


def get_cache_backend(runtime: Optional[Any] = None, project_path: str = ".") -> Any:
    """获取缓存后端（已废弃，请使用 container.infrastructure.cache_backend()）"""
    return container.infrastructure.cache_backend(runtime=runtime, project_path=project_path)


def get_state_store(store_dir: Optional[str] = None) -> Any:
    """获取状态存储（已废弃，请使用 container.infrastructure.state_store()）"""
    return container.infrastructure.state_store(store_dir=store_dir)


def get_runtime_config(project_path: Optional[str] = None) -> Any:
    """获取运行时配置（已废弃，请使用 container.runtime_config_container.runtime_config()）"""
    return container.runtime_config_container.runtime_config(project_path=project_path)


def get_observability_facade() -> Any:
    """获取可观测性门面（已废弃，请使用 container.observability.observability_facade()）"""
    return container.observability.observability_facade()


def get_archguard_adapter() -> Any:
    """获取 ArchGuard 适配器（已废弃，请使用 container.governance.archguard_adapter()）"""
    return container.governance.archguard_adapter()


__all__ = [
    "get_cache_backend",
    "get_state_store",
    "get_runtime_config",
    "get_observability_facade",
    "get_archguard_adapter",
]
