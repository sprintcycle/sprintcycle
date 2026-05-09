"""治理域统一入口 Facade。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .observability import ObservabilityFacade, create_observability_facade
from .runner import GovernanceRunner


class GovernanceFacade:
    """治理域统一入口。

    负责对外统一路由到 observability / runner 等子能力。
    """

    def __init__(
        self,
        *,
        project_path: str,
        config: Any,
        observability: Optional[ObservabilityFacade] = None,
        runner: Optional[GovernanceRunner] = None,
    ) -> None:
        self._project_path = project_path
        self._config = config
        self._observability = observability
        self._runner = runner

    @property
    def observability(self) -> ObservabilityFacade:
        if self._observability is None:
            self._observability = create_observability_facade(self._project_path, self._config)
        return self._observability

    @property
    def runner(self) -> GovernanceRunner:
        if self._runner is None:
            self._runner = GovernanceRunner(self._config)
        return self._runner

    async def observe(self, **kwargs: Any) -> None:
        await self.observability.observe(**kwargs)

    async def request_human_decision(self, **kwargs: Any):
        return await self.observability.request_human_decision(**kwargs)

    async def summary(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return await self.observability.summary(execution_id, limit)

    async def list_pending(self, execution_id: Optional[str] = None):
        return await self.observability.list_pending(execution_id)

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50):
        return await self.observability.list_history(execution_id, limit)

    async def get_request(self, request_id: str):
        return await self.observability.get_request(request_id)

    async def apply_context_patch(self, **kwargs: Any):
        return await self.observability.apply_context_patch(**kwargs)

    async def submit_decision(self, *args: Any, **kwargs: Any):
        return await self.observability.submit_decision(*args, **kwargs)

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        return self.runner.governance_check(gate=gate, **kwargs)

    async def run_planning_gate(self, project_path: str, extra_context: Optional[Dict[str, Any]] = None):
        return await self.runner.run_planning_gate(project_path, extra_context=extra_context)

    async def run_review_gate(self, project_path: str):
        return await self.runner.run_review_gate(project_path)


def create_governance_facade(project_path: str, config: Any) -> GovernanceFacade:
    return GovernanceFacade(project_path=project_path, config=config)
