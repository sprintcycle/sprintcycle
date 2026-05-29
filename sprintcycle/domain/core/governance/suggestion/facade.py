"""Suggestion governance facade.

简化后的结构：SuggestionFacade 直接继承 SuggestionService，消除冗余层。
"""

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING

from .models import (
    Suggestion,
    SuggestionOverviewResult,
    SuggestionReviewContext,
    SuggestionSourceType,
    SuggestionStatus,
)
from .service import SuggestionService

if TYPE_CHECKING:
    from sprintcycle.domain.ports.suggestion import SuggestionStoreProtocol


class SuggestionFacade(SuggestionService):
    """简化的 Suggestion Facade - 直接继承 SuggestionService。
    
    消除了冗余的三层结构：
    - 之前：SuggestionFacadeService → SuggestionFacade → SuggestionService
    - 现在：SuggestionFacadeService → SuggestionFacade (继承自 SuggestionService)
    """

    def __init__(self, store: SuggestionStoreProtocol, *, evolution_facade: Any = None) -> None:
        super().__init__(store, evolution_facade=evolution_facade)


def create_suggestion_facade(project_path: str, config: Any, evolution_facade: Any = None) -> SuggestionFacade:
    from sprintcycle.domain.ports.suggestion import get_suggestion_store
    store_root = (
        getattr(getattr(config, "governance_suggestion", None), "root_dir", None)
        or ".sprintcycle/governance/suggestion"
    )
    return SuggestionFacade(get_suggestion_store(store_root), evolution_facade=evolution_facade)
