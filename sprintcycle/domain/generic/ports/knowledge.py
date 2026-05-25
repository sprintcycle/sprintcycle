"""Knowledge 端口 - Domain 层与知识持久化的接口

定义知识卡片存储的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence


class KnowledgeCardLike:
    """知识卡片协议"""
    id: str
    sprint_id: Optional[str]
    domain: str
    outcome: str
    body: str
    lessons: Dict[str, Any]
    related_files: List[str]
    tags: List[str]
    scores: Dict[str, Any]


class KnowledgeRepositoryProtocol(ABC):
    """知识仓库协议"""

    @abstractmethod
    def add(
        self,
        *,
        domain: str = "",
        outcome: str = "",
        body: str = "",
        sprint_id: Optional[str] = None,
        lessons: Optional[Dict[str, Any]] = None,
        related_files: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
        scores: Optional[Dict[str, Any]] = None,
        card_id: Optional[str] = None,
    ) -> KnowledgeCardLike:
        """添加知识卡片"""
        ...

    @abstractmethod
    def get(self, card_id: str) -> Optional[KnowledgeCardLike]:
        """获取知识卡片"""
        ...

    @abstractmethod
    def search(
        self,
        query: str = "",
        tags: Optional[Sequence[str]] = None,
        limit: int = 50,
    ) -> List[KnowledgeCardLike]:
        """搜索知识卡片"""
        ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> List[KnowledgeCardLike]:
        """列出最近的知识卡片"""
        ...

    @abstractmethod
    def delete(self, card_id: str) -> bool:
        """删除知识卡片"""
        ...


# Sprint outcome card 持久化协议
class SprintOutcomeCardProtocol(ABC):
    """Sprint 结果卡片持久化协议"""

    @abstractmethod
    def persist(
        self,
        project_path: str,
        config: Any,
        release_plan: Any,
        sprint_index: int,
        sprint: Any,
        sprint_result: Any,
        measurement: Any,
    ) -> None:
        """持久化 Sprint 结果卡片"""
        ...


# 工厂函数注册
_knowledge_repository_factory: Optional[callable] = None
_sprint_outcome_card_factory: Optional[callable] = None


def register_knowledge_repository_factory(factory: callable) -> None:
    """注册知识仓库工厂（由 Infrastructure 层调用）"""
    global _knowledge_repository_factory
    _knowledge_repository_factory = factory


def register_sprint_outcome_card_factory(factory: callable) -> None:
    """注册 Sprint outcome card 工厂（由 Infrastructure 层调用）"""
    global _sprint_outcome_card_factory
    _sprint_outcome_card_factory = factory


def get_knowledge_repository(db_path: Optional[str] = None) -> KnowledgeRepositoryProtocol:
    """获取知识仓库实例"""
    if _knowledge_repository_factory is not None:
        return _knowledge_repository_factory(db_path)
    from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_repository import KnowledgeCardRepository
    path = db_path or ".sprintcycle/knowledge.db"
    return KnowledgeCardRepository(path)


def get_sprint_outcome_card_persister() -> SprintOutcomeCardProtocol:
    """获取 Sprint outcome card 持久化实例"""
    if _sprint_outcome_card_factory is not None:
        return _sprint_outcome_card_factory()
    from sprintcycle.infrastructure.adapters.generic.knowledge.sprint_knowledge_card import persist_sprint_outcome_card
    return SprintOutcomeCardAdapter(persist_sprint_outcome_card)


class SprintOutcomeCardAdapter(SprintOutcomeCardProtocol):
    """Sprint outcome card 适配器"""

    def __init__(self, impl: callable) -> None:
        self._impl = impl

    def persist(
        self,
        project_path: str,
        config: Any,
        release_plan: Any,
        sprint_index: int,
        sprint: Any,
        sprint_result: Any,
        measurement: Any,
    ) -> None:
        self._impl(
            project_path=project_path,
            config=config,
            release_plan=release_plan,
            sprint_index=sprint_index,
            sprint=sprint,
            sprint_result=sprint_result,
            measurement=measurement,
        )


__all__ = [
    "KnowledgeCardLike",
    "KnowledgeRepositoryProtocol",
    "SprintOutcomeCardProtocol",
    "register_knowledge_repository_factory",
    "register_sprint_outcome_card_factory",
    "get_knowledge_repository",
    "get_sprint_outcome_card_persister",
    "SprintOutcomeCardAdapter",
]
