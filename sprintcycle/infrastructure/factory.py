"""
Infrastructure 工厂层 — DDD 依赖注入的组装点

本模块负责：
1. 实例化所有 Infrastructure 实现
2. 注册到 Domain/Application 层的工厂回调
3. 组装完整的依赖关系图

所有 Infrastructure 实例的创建都集中在这里，确保分层清晰。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from pathlib import Path

from loguru import logger


def register_all_infrastructure(project_path: str, config: Any) -> None:
    """统一注册所有 Infrastructure 层实现到 Domain/Application 层"""
    # 状态持久化相关
    from sprintcycle.infrastructure.persistence.state import (
        register_event_backend_factory,
        register_rollback_implementations,
    )
    
    register_event_backend_factory()
    register_rollback_implementations()
    logger.debug("[Infrastructure] Registered persistence factories")


__all__ = [
    "register_all_infrastructure",
]
