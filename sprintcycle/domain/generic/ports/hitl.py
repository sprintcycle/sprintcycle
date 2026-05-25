"""HITL 端口 - Domain 层与 HITL 存储的接口

定义 HITL 存储的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class HitlRequestRecordLike:
    """HITL 请求记录协议"""
    request_id: str
    execution_id: str
    gate: str
    status: str
    title: str
    summary: str
    context: Dict[str, Any]
    decision: Optional[str] = None
    created_at: str = ""
    timeout_seconds: int = 300
    risk_level: str = "medium"


class HitlStoreProtocol(ABC):
    """HITL 存储协议"""

    @abstractmethod
    async def insert_open(self, row: HitlRequestRecordLike) -> None:
        """插入开放的 HITL 请求"""
        ...

    @abstractmethod
    async def update_decision(
        self,
        request_id: str,
        *,
        decision: str,
        note: Optional[str] = None,
        decision_kind: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """更新决策"""
        ...

    @abstractmethod
    async def get(self, request_id: str) -> Optional[HitlRequestRecordLike]:
        """获取请求记录"""
        ...

    @abstractmethod
    async def list_open(self, execution_id: Optional[str] = None) -> List[HitlRequestRecordLike]:
        """列出开放的请求"""
        ...

    @abstractmethod
    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> List[HitlRequestRecordLike]:
        """列出历史请求"""
        ...

    @abstractmethod
    async def insert_correction(self, request_id: str, correction: Any) -> None:
        """插入修正"""
        ...

    @abstractmethod
    async def insert_replay(self, request_id: str, replay: Any) -> None:
        """插入重放指令"""
        ...


# 工厂函数注册
_hitl_store_factory: Optional[callable] = None


def register_hitl_store_factory(factory: callable) -> None:
    """注册 HITL store 工厂（由 Infrastructure 层调用）"""
    global _hitl_store_factory
    _hitl_store_factory = factory


def get_hitl_store(project_path: Optional[str] = None) -> HitlStoreProtocol:
    """获取 HITL store 实例"""
    if _hitl_store_factory is not None:
        return _hitl_store_factory(project_path)
    from sprintcycle.infrastructure.adapters.core.governance.hitl_store import HitlSqliteStore, default_hitl_db_path
    return HitlSqliteStore(default_hitl_db_path(project_path))


__all__ = [
    "HitlRequestRecordLike",
    "HitlStoreProtocol",
    "register_hitl_store_factory",
    "get_hitl_store",
]
