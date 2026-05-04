"""将 KnowledgeInjector 挂到 Sprint 生命周期（on_before_sprint）。"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from ..config import RuntimeConfig
from ..prd.models import PRD, PRDSprint
from .knowledge_injector import KnowledgeInjector
from .sprint_hooks import SprintLifecycleHooks
from .sprint_types import SprintResult

logger = logging.getLogger(__name__)


def resolve_knowledge_db_path(project_path: str, config: RuntimeConfig) -> str:
    """知识卡片与 sqlite 执行库默认共用同一文件路径。"""
    from .state_store import resolve_sqlite_database_path

    return resolve_sqlite_database_path(project_path, config)


class KnowledgeInjectionHook(SprintLifecycleHooks):
    """每个 Sprint 开始前注入经验（写入 prd_overlay.yaml + context）。"""

    def __init__(self, project_path: str, config: RuntimeConfig):
        self._project_path = project_path
        self._config = config

    def _enabled(self) -> bool:
        return bool(getattr(self._config, "knowledge_injection_enabled", True))

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        if not self._enabled():
            return
        try:
            db_path = resolve_knowledge_db_path(self._project_path, self._config)
            inj = KnowledgeInjector(db_path)
            res = inj.inject_for_sprint(self._project_path, sprint, prd)
            context["prd_overlay_yaml"] = res.yaml_text
            context["knowledge_injection_diff"] = res.diff_text
            context["knowledge_card_ids"] = res.cards_used
        except Exception as e:
            logger.warning("Knowledge injection skipped: %s", e)

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        result: SprintResult,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        return None
