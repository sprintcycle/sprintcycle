"""
Infrastructure 工厂层 - 现在使用 DI Container

所有 Infrastructure 实例的创建现在由 DI Container 统一管理。
保持向后兼容性。
"""

from __future__ import annotations

from typing import Any


def register_all_infrastructure(project_path: str, config: Any) -> None:
    """统一注册所有 Infrastructure 层实现（保持向后兼容）"""
    # 不再需要手动注册工厂，DI Container 已处理所有依赖
    from sprintcycle.application.composition.di_container import create_container
    create_container(project_path=project_path)
