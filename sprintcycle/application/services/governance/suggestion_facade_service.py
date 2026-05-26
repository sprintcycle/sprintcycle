"""Suggestion Facade 应用层服务 - 封装 domain 层的 SuggestionFacade。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sprintcycle.domain.core.governance.suggestion import SuggestionFacade, create_suggestion_facade
from sprintcycle.domain.generic.ports.config import RuntimeConfigProtocol


class SuggestionFacadeService:
    """Suggestion Facade 的应用层包装服务。"""

    def __init__(
        self,
        project_path: str,
        config: RuntimeConfigProtocol,
        evolution_facade: Optional[Any] = None,
    ):
        self._project_path = project_path
        self._config = config
        self._facade = create_suggestion_facade(
            project_path=project_path,
            config=config,
            evolution_facade=evolution_facade,
        )

    @property
    def facade(self) -> SuggestionFacade:
        """获取底层 SuggestionFacade 实例。"""
        return self._facade

    def approve(self, suggestion_id: str, approver: str, notes: Optional[str] = None) -> Any:
        """批准建议。"""
        return self._facade.approve(suggestion_id, approver, notes)

    def reject(self, suggestion_id: str, approver: str, notes: Optional[str] = None) -> Any:
        """拒绝建议。"""
        return self._facade.reject(suggestion_id, approver, notes)

    def review(self, suggestion_id: str, reviewer: str) -> Any:
        """审查建议。"""
        return self._facade.review(suggestion_id, reviewer)

    def archive(self, suggestion_id: str) -> Any:
        """归档建议。"""
        return self._facade.archive(suggestion_id)

    def overview(self) -> Any:
        """获取建议概览。"""
        return self._facade.overview()

    def board(self, execution_id: Optional[str] = None, limit: int = 20) -> Any:
        """获取建议看板。"""
        return self._facade.board(execution_id, limit=limit)

    def pending(self) -> Any:
        """获取待处理建议。"""
        return self._facade.pending()
