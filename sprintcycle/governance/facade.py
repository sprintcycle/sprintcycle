"""Governance domain facade.

Routes governance check, HITL, and suggestion-related entry points to the
underlying services and domain facades.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .hitl.facade import HitlFacade, create_hitl_facade
from .runner import GovernanceRunner
from .suggestion import SuggestionFacade, create_suggestion_facade
from .suggestion_service import SuggestionService


class GovernanceFacade:
    """治理域统一入口。

    负责对外统一路由到 hitl / runner / suggestion 等子能力。
    """

    def __init__(
        self,
        *,
        project_path: str,
        config: Any,
        hitl: Optional[HitlFacade] = None,
        runner: Optional[GovernanceRunner] = None,
        suggestion: Optional[SuggestionService] = None,
    ) -> None:
        self._project_path = project_path
        self._config = config
        self._hitl = hitl
        self._runner = runner
        self._suggestion = suggestion

    @property
    def hitl(self) -> HitlFacade:
        if self._hitl is None:
            self._hitl = create_hitl_facade(self._project_path, self._config)
        return self._hitl

    @property
    def runner(self) -> GovernanceRunner:
        if self._runner is None:
            self._runner = GovernanceRunner(self._config)
        return self._runner

    @property
    def suggestion(self) -> SuggestionService:
        if self._suggestion is None:
            self._suggestion = SuggestionService(create_suggestion_facade())
        return self._suggestion

    async def observe(self, **kwargs: Any) -> None:
        await self.hitl.observe(**kwargs)

    async def request_human_decision(self, **kwargs: Any):
        return await self.hitl.request_human_decision(**kwargs)

    async def summary(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return await self.hitl.summary(execution_id, limit)

    async def list_pending(self, execution_id: Optional[str] = None):
        return await self.hitl.list_pending(execution_id)

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50):
        return await self.hitl.list_history(execution_id, limit)

    async def get_request(self, request_id: str):
        return await self.hitl.get_request(request_id)

    async def apply_context_patch(self, **kwargs: Any):
        return await self.hitl.apply_context_patch(**kwargs)

    async def submit_decision(self, *args: Any, **kwargs: Any):
        return await self.hitl.submit_decision(*args, **kwargs)

    async def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = ""):
        return self.suggestion.mark_reviewed(execution_id, suggestion_id, reviewer=reviewer, notes=notes)

    async def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = ""):
        return self.suggestion.mark_approved(execution_id, suggestion_id, approved_by=approver, note=notes)

    async def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = ""):
        return self.suggestion.reject(execution_id, suggestion_id, rejected_by=rejected_by, note=notes)

    async def promote_suggestion_to_hitl(
        self,
        suggestion_id: str,
        *,
        gate: str = "review",
        title: str = "",
        summary: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self.suggestion.promote_to_hitl(
            suggestion_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
        )

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        return await self.suggestion.attach_replay_directive(suggestion_id, replay)

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        return self.runner.governance_check(gate=gate, **kwargs)

    async def run_planning_gate(self, project_path: str, extra_context: Optional[Dict[str, Any]] = None):
        return await self.runner.run_planning_gate(project_path, extra_context=extra_context)

    async def run_review_gate(self, project_path: str):
        return await self.runner.run_review_gate(project_path)


def create_governance_facade(project_path: str, config: Any) -> GovernanceFacade:
    return GovernanceFacade(project_path=project_path, config=config)
