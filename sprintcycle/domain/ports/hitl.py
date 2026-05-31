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


__all__ = [
    "HitlRequestRecordLike",
    "HitlStoreProtocol",
]
