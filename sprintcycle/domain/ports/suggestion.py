"""Suggestion 端口 - Domain 层与 Suggestion 存储的接口

定义 Suggestion 存储的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class SuggestionLike:
    """Suggestion 数据类协议"""
    suggestion_id: str
    source_type: str
    source_id: Optional[str]
    title: str
    summary: str
    details: str
    impact_scope: List[str]
    severity: str
    status: str
    created_at: str
    updated_at: str
    reviewed_at: Optional[str]
    approved_at: Optional[str]
    reviewer: Optional[str]
    review_notes: Optional[str]
    linked_evolution_id: Optional[str]
    linked_version_id: Optional[str]
    metadata: Dict[str, Any]


class SuggestionStoreProtocol(ABC):
    """Suggestion 存储协议"""

    @abstractmethod
    async def save(self, suggestion: SuggestionLike) -> SuggestionLike:
        """保存 Suggestion"""
        ...

    @abstractmethod
    async def get(self, suggestion_id: str) -> Optional[SuggestionLike]:
        """获取 Suggestion"""
        ...

    @abstractmethod
    async def list(
        self,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SuggestionLike]:
        """列出 Suggestions"""
        ...

    @abstractmethod
    async def update_status(self, suggestion_id: str, status: str) -> SuggestionLike:
        """更新状态"""
        ...

    @abstractmethod
    async def update_evolution_link(self, suggestion_id: str, evolution_id: str) -> SuggestionLike:
        """更新进化链接"""
        ...

    @abstractmethod
    async def append_review(self, record: Any) -> None:
        """追加审核记录"""
        ...

    @abstractmethod
    async def append_approval(self, record: Any) -> None:
        """追加审批记录"""
        ...


__all__ = [
    "SuggestionLike",
    "SuggestionStoreProtocol",
]
