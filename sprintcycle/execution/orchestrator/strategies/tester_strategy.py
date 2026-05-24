"""Tester agent execution strategy."""

from typing import Any, Dict

from sprintcycle.domain.models import SprintBacklogItem
from .base_strategy import AgentStrategy
from ..constants import DRY_RUN_TESTER_TEMPLATE


class TesterStrategy(AgentStrategy):
    """Strategy for executing tester tasks."""

    async def execute(
        self,
        task: SprintBacklogItem,
        context: Dict[str, Any],
        build_context_func: Any,
    ) -> str:
        """Execute tester task."""
        if self.dry_run:
            return DRY_RUN_TESTER_TEMPLATE.format(desc=task.description[:80])

        from ..agents.tester import TesterAgent

        ctx = build_context_func(task, context.get("sprint_name", ""), context)
        agent = TesterAgent()
        
        if self.project_write_plan is not None:
            agent.set_project_write_plan(self.project_write_plan)
            
        res = await agent.execute(task.description, ctx)
        
        if not res.success:
            raise RuntimeError(res.error or "TesterAgent 执行失败")
            
        return res.output or ""
