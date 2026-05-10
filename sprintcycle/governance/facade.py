"""治理域统一入口 Facade。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .hitl.facade import HitlFacade, create_hitl_facade
from .runner import GovernanceRunner


class GovernanceFacade:
    """治理域统一入口。

    负责对外统一路由到 hitl / runner 等子能力。
    """

    def __init__(
        self,
        *,
        project_path: str,
        config: Any,
        hitl: Optional[HitlFacade] = None,
        runner: Optional[GovernanceRunner] = None,
    ) -> None:
        self._project_path = project_path
        self._config = config
        self._hitl = hitl
        self._runner = runner

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

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        return self.runner.governance_check(gate=gate, **kwargs)

    async def run_planning_gate(self, project_path: str, extra_context: Optional[Dict[str, Any]] = None):
        return await self.runner.run_planning_gate(project_path, extra_context=extra_context)

    async def run_review_gate(self, project_path: str):
        return await self.runner.run_review_gate(project_path)


def create_governance_facade(project_path: str, config: Any) -> GovernanceFacade:
    return GovernanceFacade(project_path=project_path, config=config)
